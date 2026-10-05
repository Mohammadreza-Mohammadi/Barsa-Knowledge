"""IL-level evidence: call edges, string literals, SQL and config-key discovery.

Everything here is read off the opcode stream; no code is executed.
"""

import re
import struct

from .cli_metadata import (
    Assembly, walk_il, CALL_OPS, LDSTR, MEMBERREF, METHODDEF, METHODSPEC,
    TYPEDEF, TYPEREF, TYPESPEC, FIELD,
)

# A token is (table << 24) | rid.
_TOKEN_TABLE = {0x06: METHODDEF, 0x0A: MEMBERREF, 0x2B: METHODSPEC,
                0x01: TYPEREF, 0x02: TYPEDEF, 0x1B: TYPESPEC, 0x04: FIELD}

SQL_RE = re.compile(
    r"\b(SELECT\s+.+?\s+FROM\s|INSERT\s+INTO\s|UPDATE\s+\w+\s+SET\s|DELETE\s+FROM\s|"
    r"CREATE\s+(TABLE|VIEW|INDEX|PROCEDURE)\s|ALTER\s+TABLE\s|DROP\s+(TABLE|INDEX)\s|"
    r"TRUNCATE\s+TABLE\s|MERGE\s+INTO\s|EXEC(UTE)?\s+\w)",
    re.IGNORECASE | re.DOTALL)

_FROM_RE = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+\[?([A-Za-z_][\w$.]*)\]?",
                      re.IGNORECASE)
_OPERATION_RE = re.compile(r"^\s*\(*\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|"
                           r"DROP|TRUNCATE|MERGE|EXEC|EXECUTE)\b", re.IGNORECASE)

# Strings that look like credentials get redacted before they reach dist/.
SECRET_RE = re.compile(
    r"(?i)\b(password|pwd|secret|apikey|api_key|token|connectionstring)\s*=\s*[^;\s\"']+")


def redact(text):
    """Mask obvious credential values while keeping the surrounding structure."""
    return SECRET_RE.sub(lambda m: m.group(0).split("=")[0] + "=***REDACTED***", text)


def decode_token(asm, operand):
    if len(operand) != 4:
        return None
    tok = struct.unpack("<I", operand)[0]
    table = _TOKEN_TABLE.get(tok >> 24)
    rid = tok & 0xFFFFFF
    if table is None or rid == 0:
        return None
    return table, rid


def callee_name(asm, table, rid):
    """Printable 'Namespace.Type::Method' for a call target, or None."""
    if table == METHODDEF:
        return asm.method_full_name(rid)
    if table == MEMBERREF:
        mr = asm.row(MEMBERREF, rid)
        if not mr:
            return None
        owner = asm.typedefref_name(mr["Class"])
        if owner is None and mr["Class"][0] == METHODDEF:
            owner = asm.method_full_name(mr["Class"][1])
        return "%s::%s" % (owner or "?", asm.string(mr["Name"]))
    if table == METHODSPEC:
        ms = asm.row(METHODSPEC, rid)
        if not ms:
            return None
        t, r = ms["Method"]
        return callee_name(asm, t, r)
    return None


def analyze_method(asm, method_rid):
    """Return {'calls': [...], 'strings': [...]} for one method body."""
    code = asm.method_body(method_rid)
    if not code:
        return None
    calls = []
    strings = []
    seen_calls = set()
    for _off, op, operand in walk_il(code):
        if op in CALL_OPS:
            tok = decode_token(asm, operand)
            if not tok:
                continue
            nm = callee_name(asm, *tok)
            if nm and nm not in seen_calls:
                seen_calls.add(nm)
                calls.append(nm)
        elif op == LDSTR and len(operand) == 4:
            tok = struct.unpack("<I", operand)[0]
            if tok >> 24 == 0x70:
                s = asm.user_string(tok & 0xFFFFFF)
                if s:
                    strings.append(s)
    return {"calls": calls, "strings": strings}


def classify_string(s):
    """Bucket a literal into the categories the spec's string discovery asks for."""
    if len(s) > 4000:
        return "other"
    if SQL_RE.search(s):
        return "sql"
    if s.startswith(("http://", "https://", "ftp://", "net.tcp://", "tcp://")):
        return "url"
    if re.match(r"^[A-Za-z]:\\|^\\\\|^/[a-z]+/", s):
        return "path"
    if re.match(r"^[\w.]+\.(dll|exe|config|xml|mrt|json|zip|metaexport)$", s, re.I):
        return "fileName"
    if re.match(r"^(Met_|MET_|met_|Spl_|SPL_|spl_|Shr_|sec_|Sec_|m0[12]_|dyn_|"
                r"Ver_|ulog_|xapp_)\w+$", s):
        return "table"
    if re.match(r"^[A-Za-z][\w.]{2,60}$", s) and "." in s and " " not in s:
        return "typeOrConfigKey"
    return "other"


def extract_sql(s):
    """Pull operation + referenced tables out of a SQL-looking literal."""
    if not SQL_RE.search(s):
        return None
    m = _OPERATION_RE.match(s)
    op = m.group(1).upper() if m else "UNKNOWN"
    tables = sorted({t for t in _FROM_RE.findall(s)
                     if not t.upper() in ("SELECT", "WHERE", "AND", "OR", "SET")})
    return {"operation": op, "tables": tables}


def build_call_index(asm, type_filter=None):
    """Map method full name -> analysis for every method with a body.

    type_filter: optional callable(type_full_name) -> bool to limit the scan.
    """
    out = {}
    for trid in range(1, asm.row_count(TYPEDEF) + 1):
        tn = asm.type_full_name(trid)
        if not tn:
            continue
        if type_filter and not type_filter(tn):
            continue
        start, end = asm.type_method_range(trid)
        for m in range(start, end):
            res = analyze_method(asm, m)
            if res is None:
                continue
            name = "%s::%s" % (tn, asm.method_name(m))
            out[name] = res
    return out


def invert_calls(call_index):
    """Build the CalledBy direction from a call index."""
    back = {}
    for caller, info in call_index.items():
        for callee in info["calls"]:
            back.setdefault(callee, set()).add(caller)
    return {k: sorted(v) for k, v in back.items()}
