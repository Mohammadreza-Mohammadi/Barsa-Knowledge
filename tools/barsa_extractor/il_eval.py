"""A constant-only IL evaluator, for recovering declarative tables from code.

Some contracts in Barsa are not data files: they are built at type-init time by
a run of static factory calls whose arguments are all compile-time constants.
`SemanticContractRegistry` is the important one -- its `.cctor` and
`BuildProperties` construct the entire per-objectType property contract by
calling `Obj(...)`, `Writable(...)`, `Reference(...)` and friends with literal
strings, ints and string arrays.

This module walks such a method's opcode stream keeping a symbolic stack of
constants, and records each call with the arguments it received. It evaluates
nothing: no branch is followed, no arithmetic is performed, and anything it
cannot model becomes `Unknown`. Since these methods are straight-line sequences
of pushes and calls, that is enough to recover the table exactly, and when it
is not enough the result says so rather than guessing.
"""

import struct

from .cli_metadata import (
    FIELD, MEMBERREF, METHODDEF, METHODSPEC, TYPEDEF, TYPEREF, TYPESPEC,
    walk_il,
)
from .signatures import parse_method_sig

# Opcodes that push a constant.
_LDC_I4_MAP = {
    0x15: -1, 0x16: 0, 0x17: 1, 0x18: 2, 0x19: 3,
    0x1A: 4, 0x1B: 5, 0x1C: 6, 0x1D: 7, 0x1E: 8,
}
NOP = 0x00
LDNULL = 0x14
LDC_I4_S = 0x1F
LDC_I4 = 0x20
LDC_I8 = 0x21
LDSTR = 0x72
NEWARR = 0x8D
DUP = 0x25
POP = 0x26
STELEM_REF = 0xA2
STELEM_I4 = 0x9E
CALL = 0x28
CALLVIRT = 0x6F
NEWOBJ = 0x73
RET = 0x2A
BR_S = 0x2B
BR = 0x38

# These assemblies are debug builds, so the straight-line table builders are
# full of nop, a local round-trip and a zero-displacement branch before the
# return. Modelling locals and ignoring a jump that targets the next
# instruction is what makes the tables recoverable; a non-zero jump is real
# control flow and stops the fold instead.
_LDLOC_MAP = {0x06: 0, 0x07: 1, 0x08: 2, 0x09: 3}
_STLOC_MAP = {0x0A: 0, 0x0B: 1, 0x0C: 2, 0x0D: 3}
LDLOC_S = 0x11
STLOC_S = 0x13
LDARG_0, LDARG_3 = 0x02, 0x05
LDARG_S = 0x0E
LDELEM_REF = 0x9A
LDLEN = 0x8E
ADD = 0x58

# Branches and comparisons are not followed, but their stack effect is honoured
# so that a loop does not leave junk behind and shift later call arguments.
_BRANCH_POP1 = (0x2C, 0x2D, 0x39, 0x3A)                  # brfalse/brtrue(.s)
_BRANCH_POP2 = (0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33,      # beq..bge.un(.s)
                0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40,
                0x41, 0x42, 0x43, 0x44)
_BINOP = (0x58, 0x59, 0x5A, 0x5B, 0x5D, 0x5F, 0x60, 0x61)

_fold_cache = {}

_TOKEN_TABLE = {0x06: METHODDEF, 0x0A: MEMBERREF, 0x2B: METHODSPEC,
                0x01: TYPEREF, 0x02: TYPEDEF, 0x1B: TYPESPEC, 0x04: FIELD}


class Unknown:
    """A value this evaluator declines to model."""

    __slots__ = ("why",)

    def __init__(self, why=""):
        self.why = why

    def __repr__(self):
        return "Unknown(%s)" % self.why


class AnyOf:
    """A value read out of a known array at an unknown index.

    `BuildProperties` registers one property set for several field subtypes by
    looping over an array of subtype names. The loop index is not a constant,
    so the element is not either -- but the *set* of possible values is known
    exactly, and for a registration that means "this applies to each of these".
    """

    __slots__ = ("options",)

    def __init__(self, options):
        self.options = [o for o in options if isinstance(o, str)]

    def __repr__(self):
        return "AnyOf(%r)" % (self.options,)


class ArrayVal:
    """A newarr result, filled in by the stelem sequence that follows it."""

    __slots__ = ("items",)

    def __init__(self, size):
        self.items = [None] * size if isinstance(size, int) and 0 <= size < 4096 \
            else []

    def to_list(self):
        return [i if not isinstance(i, (Unknown, ArrayVal)) else None
                for i in self.items]

    def __repr__(self):
        return "Array(%r)" % (self.items,)


def _jsonable(v):
    if isinstance(v, ArrayVal):
        return v.to_list()
    if isinstance(v, AnyOf):
        return {"anyOf": v.options}
    if isinstance(v, Unknown):
        return None
    return v


class CallRecord:
    __slots__ = ("name", "args", "complete")

    def __init__(self, name, args, complete):
        self.name = name
        self.args = args
        self.complete = complete

    def arg(self, i, default=None):
        if i < len(self.args):
            return _jsonable(self.args[i])
        return default

    def __repr__(self):
        return "%s(%s)" % (self.name, ", ".join(repr(_jsonable(a))
                                                for a in self.args))


def _callee(asm, table, rid):
    """Printable name plus declared parameter count for a call target."""
    if table == METHODDEF:
        row = asm.row(METHODDEF, rid)
        if not row:
            return None, None, False
        sig = parse_method_sig(asm.blob(row["Signature"]), asm)
        name = asm.method_full_name(rid)
        has_this = bool(sig and sig["hasThis"])
        n = (len(sig["parameters"]) if sig else None)
        return name, n, has_this
    if table == MEMBERREF:
        row = asm.row(MEMBERREF, rid)
        if not row:
            return None, None, False
        owner = asm.typedefref_name(row["Class"]) or "?"
        sig = parse_method_sig(asm.blob(row["Signature"]), asm)
        has_this = bool(sig and sig["hasThis"])
        n = (len(sig["parameters"]) if sig else None)
        return "%s::%s" % (owner, asm.string(row["Name"])), n, has_this
    if table == METHODSPEC:
        row = asm.row(METHODSPEC, rid)
        if not row:
            return None, None, False
        return _callee(asm, *row["Method"])
    return None, None, False


def _step(asm, op, operand, stack, locals_):
    """Apply one instruction to the stack. Returns True if it was modelled."""
    if op == NOP:
        return True
    if op in _LDC_I4_MAP:
        stack.append(_LDC_I4_MAP[op])
        return True
    if op == LDC_I4_S and operand:
        stack.append(struct.unpack("<b", operand[:1])[0])
        return True
    if op == LDC_I4 and len(operand) == 4:
        stack.append(struct.unpack("<i", operand)[0])
        return True
    if op == LDC_I8 and len(operand) == 8:
        stack.append(struct.unpack("<q", operand)[0])
        return True
    if op == LDNULL:
        stack.append(None)
        return True
    if op == LDSTR and len(operand) == 4:
        tok = struct.unpack("<I", operand)[0]
        stack.append(asm.user_string(tok & 0xFFFFFF)
                     if tok >> 24 == 0x70 else Unknown("ldstr"))
        return True
    if op == NEWARR:
        stack.append(ArrayVal(stack.pop() if stack else None))
        return True
    if op == DUP:
        stack.append(stack[-1] if stack else Unknown("underflow"))
        return True
    if op == POP:
        if stack:
            stack.pop()
        return True
    if op in (STELEM_REF, STELEM_I4):
        value = stack.pop() if stack else None
        index = stack.pop() if stack else None
        arr = stack.pop() if stack else None
        if isinstance(arr, ArrayVal) and isinstance(index, int) \
                and 0 <= index < len(arr.items):
            arr.items[index] = value
        return True
    if op in _LDLOC_MAP:
        stack.append(locals_.get(_LDLOC_MAP[op], Unknown("unset local")))
        return True
    if op in _STLOC_MAP:
        locals_[_STLOC_MAP[op]] = stack.pop() if stack else Unknown("underflow")
        return True
    if op == LDLOC_S and operand:
        stack.append(locals_.get(operand[0], Unknown("unset local")))
        return True
    if op == STLOC_S and operand:
        locals_[operand[0]] = stack.pop() if stack else Unknown("underflow")
        return True
    if LDARG_0 <= op <= LDARG_3:
        stack.append(Unknown("ldarg"))
        return True
    if op == LDARG_S and operand:
        stack.append(Unknown("ldarg.s"))
        return True
    if op in (BR_S, BR):
        # In verifiable IL the evaluation stack is empty at a branch, so an
        # unconditional jump has no stack effect worth modelling.
        return True
    if op in _BRANCH_POP1:
        if stack:
            stack.pop()
        return True
    if op in _BRANCH_POP2:
        for _ in range(min(2, len(stack))):
            stack.pop()
        return True
    if op == LDELEM_REF:
        index = stack.pop() if stack else None
        arr = stack.pop() if stack else None
        if isinstance(arr, ArrayVal):
            if isinstance(index, int) and 0 <= index < len(arr.items):
                stack.append(arr.items[index])
            else:
                stack.append(AnyOf(arr.items))
        else:
            stack.append(Unknown("ldelem on non-array"))
        return True
    if op == LDLEN:
        if stack:
            stack.pop()
        stack.append(Unknown("ldlen"))
        return True
    if op in _BINOP:
        for _ in range(min(2, len(stack))):
            stack.pop()
        stack.append(Unknown("binop"))
        return True
    if op == 0xFE01 or (0xFE01 <= op <= 0xFE05):
        for _ in range(min(2, len(stack))):
            stack.pop()
        stack.append(Unknown("compare"))
        return True
    return False


def constant_return(asm, method_rid, _depth=0, _cache=None):
    """If a method just builds and returns a constant, return that constant.

    `SemanticContractRegistry` reaches for tiny helpers like `Crud()` and
    `CreateUpdate()` that return a fixed string array. Without folding them the
    operation lists come back as Unknown, so the recovered table would be
    missing exactly the part that says which operations an object supports.
    """
    if _cache is None:
        _cache = _fold_cache.setdefault(id(asm), {})
    if method_rid in _cache:
        return _cache[method_rid]
    if _depth > 4:
        return Unknown("fold depth")
    _cache[method_rid] = Unknown("folding")  # guards recursion
    key = method_rid
    code = asm.method_body(method_rid)
    if not code:
        _cache[key] = Unknown("no body")
        return _cache[key]
    stack = []
    locals_ = {}
    result = Unknown("not constant")
    for _off, op, operand in walk_il(code):
        if op == RET:
            result = stack[-1] if stack else Unknown("empty")
            break
        if not _step(asm, op, operand, stack, locals_):
            _cache[key] = Unknown("op 0x%02X" % op)
            return _cache[key]
    _cache[key] = result
    return result


def evaluate(asm, method_rid, interesting=None):
    """Record the constant-argument calls a method makes, in body order.

    `interesting`: optional set of substrings; only calls whose name contains
    one are recorded, though every call is still simulated so the stack stays
    aligned.
    """
    code = asm.method_body(method_rid)
    if not code:
        return []

    stack = []
    locals_ = {}
    out = []

    def pop():
        return stack.pop() if stack else Unknown("stack underflow")

    for _off, op, operand in walk_il(code):
        if op in (CALL, CALLVIRT, NEWOBJ):
            tok = (struct.unpack("<I", operand)[0] if len(operand) == 4
                   else 0)
            table = _TOKEN_TABLE.get(tok >> 24)
            rid = tok & 0xFFFFFF
            name, n_params, has_this = (_callee(asm, table, rid)
                                        if table else (None, None, False))
            n = n_params if n_params is not None else 0
            if has_this and op != NEWOBJ:
                n += 1
            args = []
            complete = len(stack) >= n
            for _ in range(min(n, len(stack))):
                args.append(pop())
            args.reverse()
            if has_this and op != NEWOBJ and args:
                args = args[1:]
            if name and (interesting is None
                         or any(s in name for s in interesting)):
                out.append(CallRecord(name, args, complete))
            # The return value is opaque, which is fine: these factories feed
            # straight into Register(...) and are not inspected further.
            if op == NEWOBJ:
                stack.append(Unknown("newobj %s" % name))
            else:
                sig_ret = None
                if table == METHODDEF:
                    row = asm.row(METHODDEF, rid)
                    sig = parse_method_sig(asm.blob(row["Signature"]), asm) \
                        if row else None
                    sig_ret = sig["returnType"] if sig else None
                elif table == MEMBERREF:
                    row = asm.row(MEMBERREF, rid)
                    sig = parse_method_sig(asm.blob(row["Signature"]), asm) \
                        if row else None
                    sig_ret = sig["returnType"] if sig else None
                if sig_ret not in (None, "void"):
                    folded = Unknown("return of %s" % name)
                    if table == METHODDEF:
                        c = constant_return(asm, rid)
                        if not isinstance(c, Unknown):
                            folded = c
                    stack.append(folded)
        elif op == RET:
            continue
        elif not _step(asm, op, operand, stack, locals_):
            # Anything not modelled invalidates the stack rather than silently
            # shifting argument positions.
            stack.append(Unknown("op 0x%02X" % op))
    return out


def find_method(asm, type_suffix, method_name):
    for rid in range(1, asm.row_count(TYPEDEF) + 1):
        tn = asm.type_full_name(rid) or ""
        if not tn.endswith(type_suffix):
            continue
        start, end = asm.type_method_range(rid)
        for m in range(start, end):
            if asm.method_name(m) == method_name:
                return m
    return None
