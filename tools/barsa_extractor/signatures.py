"""Decoder for ECMA-335 II.23.2 metadata signature blobs."""

from .cli_metadata import _compressed_uint, TYPEDEF, TYPEREF, TYPESPEC

ELEMENT_TYPES = {
    0x01: "void", 0x02: "bool", 0x03: "char", 0x04: "sbyte", 0x05: "byte",
    0x06: "short", 0x07: "ushort", 0x08: "int", 0x09: "uint", 0x0A: "long",
    0x0B: "ulong", 0x0C: "float", 0x0D: "double", 0x0E: "string",
    0x16: "TypedReference", 0x18: "IntPtr", 0x19: "UIntPtr", 0x1C: "object",
}

_CODED_TDR = (TYPEDEF, TYPEREF, TYPESPEC)


def _type_def_or_ref(buf, pos):
    """Decode a TypeDefOrRefOrSpecEncoded coded index."""
    val, pos = _compressed_uint(buf, pos)
    return (_CODED_TDR[val & 3] if (val & 3) < 3 else None, val >> 2), pos


def parse_type(buf, pos, asm):
    """Return (printable type name, next position)."""
    if pos >= len(buf):
        return "?", pos
    et = buf[pos]
    pos += 1
    if et in ELEMENT_TYPES:
        return ELEMENT_TYPES[et], pos
    if et in (0x11, 0x12):  # VALUETYPE | CLASS
        coded, pos = _type_def_or_ref(buf, pos)
        return (asm.typedefref_name(coded) or "?"), pos
    if et == 0x1D:  # SZARRAY
        inner, pos = parse_type(buf, pos, asm)
        return inner + "[]", pos
    if et == 0x0F:  # PTR
        inner, pos = parse_type(buf, pos, asm)
        return inner + "*", pos
    if et == 0x10:  # BYREF
        inner, pos = parse_type(buf, pos, asm)
        return inner + "&", pos
    if et == 0x45:  # PINNED
        return parse_type(buf, pos, asm)
    if et == 0x1F or et == 0x20:  # CMOD_REQD / CMOD_OPT
        _coded, pos = _type_def_or_ref(buf, pos)
        return parse_type(buf, pos, asm)
    if et == 0x13:  # VAR (class generic parameter)
        n, pos = _compressed_uint(buf, pos)
        return "!%d" % n, pos
    if et == 0x1E:  # MVAR (method generic parameter)
        n, pos = _compressed_uint(buf, pos)
        return "!!%d" % n, pos
    if et == 0x15:  # GENERICINST
        _kind = buf[pos]
        pos += 1
        coded, pos = _type_def_or_ref(buf, pos)
        base = asm.typedefref_name(coded) or "?"
        argc, pos = _compressed_uint(buf, pos)
        args = []
        for _ in range(argc):
            a, pos = parse_type(buf, pos, asm)
            args.append(a)
        base = base.split("`")[0]
        return "%s<%s>" % (base, ", ".join(args)), pos
    if et == 0x14:  # ARRAY
        inner, pos = parse_type(buf, pos, asm)
        rank, pos = _compressed_uint(buf, pos)
        nsizes, pos = _compressed_uint(buf, pos)
        for _ in range(nsizes):
            _v, pos = _compressed_uint(buf, pos)
        nlo, pos = _compressed_uint(buf, pos)
        for _ in range(nlo):
            _v, pos = _compressed_uint(buf, pos)
        return inner + "[" + ("," * (rank - 1)) + "]", pos
    if et == 0x1B:  # FNPTR
        return "fnptr", pos
    return "?0x%02X" % et, pos


def parse_method_sig(blob, asm):
    """Decode a MethodDefSig/MethodRefSig -> dict with return type and params."""
    if not blob:
        return None
    pos = 0
    flags = blob[pos]
    pos += 1
    generic_count = 0
    if flags & 0x10:  # GENERIC
        generic_count, pos = _compressed_uint(blob, pos)
    param_count, pos = _compressed_uint(blob, pos)
    try:
        ret, pos = parse_type(blob, pos, asm)
        params = []
        for _ in range(param_count):
            if pos < len(blob) and blob[pos] == 0x41:  # SENTINEL (varargs)
                pos += 1
            t, pos = parse_type(blob, pos, asm)
            params.append(t)
    except (IndexError, KeyError):
        return None
    return {
        "hasThis": bool(flags & 0x20),
        "genericCount": generic_count,
        "returnType": ret,
        "parameters": params,
    }


def parse_field_sig(blob, asm):
    """Decode a FieldSig -> printable type name."""
    if not blob or blob[0] != 0x06:
        return None
    try:
        t, _pos = parse_type(blob, 1, asm)
    except (IndexError, KeyError):
        return None
    return t


def parse_property_sig(blob, asm):
    """Decode a PropertySig -> printable type name."""
    if not blob or (blob[0] & 0x08) == 0:
        return None
    pos = 1
    try:
        _count, pos = _compressed_uint(blob, pos)
        t, _pos = parse_type(blob, pos, asm)
    except (IndexError, KeyError):
        return None
    return t
