"""Minimal, dependency-free reader for PE files that carry a .NET (ECMA-335) CLI image.

The container running the extractor has no ILSpy/mono/dotnet, so assembly facts are
read straight out of the metadata tables.  Everything exposed here is structural
evidence: table rows, heap strings and IL opcode streams.  Nothing is inferred.
"""

import hashlib
import struct

# --- metadata table ids -----------------------------------------------------

MODULE = 0x00
TYPEREF = 0x01
TYPEDEF = 0x02
FIELDPTR = 0x03
FIELD = 0x04
METHODPTR = 0x05
METHODDEF = 0x06
PARAMPTR = 0x07
PARAM = 0x08
INTERFACEIMPL = 0x09
MEMBERREF = 0x0A
CONSTANT = 0x0B
CUSTOMATTRIBUTE = 0x0C
FIELDMARSHAL = 0x0D
DECLSECURITY = 0x0E
CLASSLAYOUT = 0x0F
FIELDLAYOUT = 0x10
STANDALONESIG = 0x11
EVENTMAP = 0x12
EVENTPTR = 0x13
EVENT = 0x14
PROPERTYMAP = 0x15
PROPERTYPTR = 0x16
PROPERTY = 0x17
METHODSEMANTICS = 0x18
METHODIMPL = 0x19
MODULEREF = 0x1A
TYPESPEC = 0x1B
IMPLMAP = 0x1C
FIELDRVA = 0x1D
ENCLOG = 0x1E
ENCMAP = 0x1F
ASSEMBLY = 0x20
ASSEMBLYPROCESSOR = 0x21
ASSEMBLYOS = 0x22
ASSEMBLYREF = 0x23
ASSEMBLYREFPROCESSOR = 0x24
ASSEMBLYREFOS = 0x25
FILE = 0x26
EXPORTEDTYPE = 0x27
MANIFESTRESOURCE = 0x28
NESTEDCLASS = 0x29
GENERICPARAM = 0x2A
METHODSPEC = 0x2B
GENERICPARAMCONSTRAINT = 0x2C

# Coded index definitions: (name -> (list of table ids or None, tag bit count))
CODED = {
    "TypeDefOrRef": ([TYPEDEF, TYPEREF, TYPESPEC], 2),
    "HasConstant": ([FIELD, PARAM, PROPERTY], 2),
    "HasCustomAttribute": (
        [METHODDEF, FIELD, TYPEREF, TYPEDEF, PARAM, INTERFACEIMPL, MEMBERREF,
         MODULE, DECLSECURITY, PROPERTY, EVENT, STANDALONESIG, MODULEREF,
         TYPESPEC, ASSEMBLY, ASSEMBLYREF, FILE, EXPORTEDTYPE, MANIFESTRESOURCE,
         GENERICPARAM, GENERICPARAMCONSTRAINT, METHODSPEC], 5),
    "HasFieldMarshal": ([FIELD, PARAM], 1),
    "HasDeclSecurity": ([TYPEDEF, METHODDEF, ASSEMBLY], 2),
    "MemberRefParent": ([TYPEDEF, TYPEREF, MODULEREF, METHODDEF, TYPESPEC], 3),
    "HasSemantics": ([EVENT, PROPERTY], 1),
    "MethodDefOrRef": ([METHODDEF, MEMBERREF], 1),
    "MemberForwarded": ([FIELD, METHODDEF], 1),
    "Implementation": ([FILE, ASSEMBLYREF, EXPORTEDTYPE], 2),
    "CustomAttributeType": ([None, None, METHODDEF, MEMBERREF, None], 3),
    "ResolutionScope": ([MODULE, MODULEREF, ASSEMBLYREF, TYPEREF], 2),
    "TypeOrMethodDef": ([TYPEDEF, METHODDEF], 1),
}

# Column kinds: ('u8'|'u16'|'u32', 'str', 'guid', 'blob', ('rid', table), ('coded', name))
SCHEMA = {
    MODULE: [("Generation", "u16"), ("Name", "str"), ("Mvid", "guid"),
             ("EncId", "guid"), ("EncBaseId", "guid")],
    TYPEREF: [("ResolutionScope", ("coded", "ResolutionScope")),
              ("Name", "str"), ("Namespace", "str")],
    TYPEDEF: [("Flags", "u32"), ("Name", "str"), ("Namespace", "str"),
              ("Extends", ("coded", "TypeDefOrRef")),
              ("FieldList", ("rid", FIELD)), ("MethodList", ("rid", METHODDEF))],
    FIELDPTR: [("Field", ("rid", FIELD))],
    FIELD: [("Flags", "u16"), ("Name", "str"), ("Signature", "blob")],
    METHODPTR: [("Method", ("rid", METHODDEF))],
    METHODDEF: [("RVA", "u32"), ("ImplFlags", "u16"), ("Flags", "u16"),
                ("Name", "str"), ("Signature", "blob"),
                ("ParamList", ("rid", PARAM))],
    PARAMPTR: [("Param", ("rid", PARAM))],
    PARAM: [("Flags", "u16"), ("Sequence", "u16"), ("Name", "str")],
    INTERFACEIMPL: [("Class", ("rid", TYPEDEF)),
                    ("Interface", ("coded", "TypeDefOrRef"))],
    MEMBERREF: [("Class", ("coded", "MemberRefParent")), ("Name", "str"),
                ("Signature", "blob")],
    CONSTANT: [("Type", "u8"), ("Padding", "u8"),
               ("Parent", ("coded", "HasConstant")), ("Value", "blob")],
    CUSTOMATTRIBUTE: [("Parent", ("coded", "HasCustomAttribute")),
                      ("Type", ("coded", "CustomAttributeType")),
                      ("Value", "blob")],
    FIELDMARSHAL: [("Parent", ("coded", "HasFieldMarshal")),
                   ("NativeType", "blob")],
    DECLSECURITY: [("Action", "u16"), ("Parent", ("coded", "HasDeclSecurity")),
                   ("PermissionSet", "blob")],
    CLASSLAYOUT: [("PackingSize", "u16"), ("ClassSize", "u32"),
                  ("Parent", ("rid", TYPEDEF))],
    FIELDLAYOUT: [("Offset", "u32"), ("Field", ("rid", FIELD))],
    STANDALONESIG: [("Signature", "blob")],
    EVENTMAP: [("Parent", ("rid", TYPEDEF)), ("EventList", ("rid", EVENT))],
    EVENTPTR: [("Event", ("rid", EVENT))],
    EVENT: [("EventFlags", "u16"), ("Name", "str"),
            ("EventType", ("coded", "TypeDefOrRef"))],
    PROPERTYMAP: [("Parent", ("rid", TYPEDEF)),
                  ("PropertyList", ("rid", PROPERTY))],
    PROPERTYPTR: [("Property", ("rid", PROPERTY))],
    PROPERTY: [("Flags", "u16"), ("Name", "str"), ("Type", "blob")],
    METHODSEMANTICS: [("Semantics", "u16"), ("Method", ("rid", METHODDEF)),
                      ("Association", ("coded", "HasSemantics"))],
    METHODIMPL: [("Class", ("rid", TYPEDEF)),
                 ("MethodBody", ("coded", "MethodDefOrRef")),
                 ("MethodDeclaration", ("coded", "MethodDefOrRef"))],
    MODULEREF: [("Name", "str")],
    TYPESPEC: [("Signature", "blob")],
    IMPLMAP: [("MappingFlags", "u16"),
              ("MemberForwarded", ("coded", "MemberForwarded")),
              ("ImportName", "str"), ("ImportScope", ("rid", MODULEREF))],
    FIELDRVA: [("RVA", "u32"), ("Field", ("rid", FIELD))],
    ENCLOG: [("Token", "u32"), ("FuncCode", "u32")],
    ENCMAP: [("Token", "u32")],
    ASSEMBLY: [("HashAlgId", "u32"), ("MajorVersion", "u16"),
               ("MinorVersion", "u16"), ("BuildNumber", "u16"),
               ("RevisionNumber", "u16"), ("Flags", "u32"),
               ("PublicKey", "blob"), ("Name", "str"), ("Culture", "str")],
    ASSEMBLYPROCESSOR: [("Processor", "u32")],
    ASSEMBLYOS: [("OSPlatformID", "u32"), ("OSMajorVersion", "u32"),
                 ("OSMinorVersion", "u32")],
    ASSEMBLYREF: [("MajorVersion", "u16"), ("MinorVersion", "u16"),
                  ("BuildNumber", "u16"), ("RevisionNumber", "u16"),
                  ("Flags", "u32"), ("PublicKeyOrToken", "blob"),
                  ("Name", "str"), ("Culture", "str"), ("HashValue", "blob")],
    ASSEMBLYREFPROCESSOR: [("Processor", "u32"),
                           ("AssemblyRef", ("rid", ASSEMBLYREF))],
    ASSEMBLYREFOS: [("OSPlatformId", "u32"), ("OSMajorVersion", "u32"),
                    ("OSMinorVersion", "u32"),
                    ("AssemblyRef", ("rid", ASSEMBLYREF))],
    FILE: [("Flags", "u32"), ("Name", "str"), ("HashValue", "blob")],
    EXPORTEDTYPE: [("Flags", "u32"), ("TypeDefId", "u32"), ("TypeName", "str"),
                   ("TypeNamespace", "str"),
                   ("Implementation", ("coded", "Implementation"))],
    MANIFESTRESOURCE: [("Offset", "u32"), ("Flags", "u32"), ("Name", "str"),
                       ("Implementation", ("coded", "Implementation"))],
    NESTEDCLASS: [("NestedClass", ("rid", TYPEDEF)),
                  ("EnclosingClass", ("rid", TYPEDEF))],
    GENERICPARAM: [("Number", "u16"), ("Flags", "u16"),
                   ("Owner", ("coded", "TypeOrMethodDef")), ("Name", "str")],
    METHODSPEC: [("Method", ("coded", "MethodDefOrRef")),
                 ("Instantiation", "blob")],
    GENERICPARAMCONSTRAINT: [("Owner", ("rid", GENERICPARAM)),
                             ("Constraint", ("coded", "TypeDefOrRef"))],
}

TABLE_NAMES = {
    MODULE: "Module", TYPEREF: "TypeRef", TYPEDEF: "TypeDef", FIELD: "Field",
    METHODDEF: "MethodDef", PARAM: "Param", MEMBERREF: "MemberRef",
    PROPERTY: "Property", EVENT: "Event", MODULEREF: "ModuleRef",
    TYPESPEC: "TypeSpec", ASSEMBLY: "Assembly", ASSEMBLYREF: "AssemblyRef",
    MANIFESTRESOURCE: "ManifestResource", NESTEDCLASS: "NestedClass",
    METHODSPEC: "MethodSpec",
}


class NotManagedError(Exception):
    """Raised when a PE file carries no CLI header (native DLL/OCX)."""


class _Reader:
    __slots__ = ("buf", "pos")

    def __init__(self, buf, pos=0):
        self.buf = buf
        self.pos = pos

    def u8(self):
        v = self.buf[self.pos]
        self.pos += 1
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.buf, self.pos)[0]
        self.pos += 2
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def idx(self, wide):
        return self.u32() if wide else self.u16()


def _compressed_uint(buf, pos):
    """ECMA-335 II.23.2 compressed unsigned integer -> (value, next_pos)."""
    b = buf[pos]
    if b & 0x80 == 0:
        return b, pos + 1
    if b & 0xC0 == 0x80:
        return ((b & 0x3F) << 8) | buf[pos + 1], pos + 2
    return (((b & 0x1F) << 24) | (buf[pos + 1] << 16)
            | (buf[pos + 2] << 8) | buf[pos + 3]), pos + 4


class PEImage:
    """PE container: sections, data directories and RVA translation."""

    def __init__(self, data):
        self.data = data
        if data[:2] != b"MZ":
            raise NotManagedError("not a PE file")
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if data[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise NotManagedError("missing PE signature")
        coff = e_lfanew + 4
        (self.machine, n_sections, self.timestamp, _sym, _nsym,
         opt_size, self.characteristics) = struct.unpack_from("<HHIIIHH", data, coff)
        opt = coff + 20
        magic = struct.unpack_from("<H", data, opt)[0]
        self.pe32_plus = magic == 0x20B
        # Data directories start after the fixed part of the optional header.
        dd_off = opt + (0x70 if self.pe32_plus else 0x60)
        self.n_dirs = struct.unpack_from("<I", data, dd_off - 4)[0]
        self.dirs = []
        for i in range(min(self.n_dirs, 16)):
            rva, size = struct.unpack_from("<II", data, dd_off + i * 8)
            self.dirs.append((rva, size))
        self.sections = []
        sec = opt + opt_size
        for i in range(n_sections):
            name, vsize, vaddr, rawsize, rawptr = struct.unpack_from(
                "<8sIIII", data, sec + i * 40)
            self.sections.append(
                (name.rstrip(b"\0").decode("ascii", "replace"),
                 vaddr, vsize, rawptr, rawsize))

    def rva_to_offset(self, rva):
        for _name, vaddr, vsize, rawptr, rawsize in self.sections:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                delta = rva - vaddr
                if delta < rawsize:
                    return rawptr + delta
                return None
        return None

    def architecture(self):
        return {0x014C: "x86", 0x8664: "x64", 0x0200: "IA64",
                0x01C4: "ARM", 0xAA64: "ARM64"}.get(self.machine,
                                                    "0x%04X" % self.machine)


class Assembly:
    """A parsed managed assembly: heaps, tables and IL access."""

    def __init__(self, path, data=None):
        self.path = path
        self.data = data if data is not None else open(path, "rb").read()
        self.size = len(self.data)
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        self.pe = PEImage(self.data)
        self._load_cli()
        self._load_metadata()
        self._load_tables()
        self._typedef_name_cache = None

    # -- image layout -------------------------------------------------------

    def _load_cli(self):
        if len(self.pe.dirs) < 15:
            raise NotManagedError("no COM descriptor directory")
        rva, size = self.pe.dirs[14]
        if rva == 0 or size == 0:
            raise NotManagedError("no CLI header")
        off = self.pe.rva_to_offset(rva)
        if off is None:
            raise NotManagedError("CLI header RVA unmapped")
        d = self.data
        self.cli_runtime = (struct.unpack_from("<H", d, off + 4)[0],
                            struct.unpack_from("<H", d, off + 6)[0])
        self.md_rva, self.md_size = struct.unpack_from("<II", d, off + 8)
        self.cli_flags = struct.unpack_from("<I", d, off + 16)[0]
        self.entry_point_token = struct.unpack_from("<I", d, off + 20)[0]
        self.resources_rva, self.resources_size = struct.unpack_from(
            "<II", d, off + 24)
        self.strong_name_rva = struct.unpack_from("<I", d, off + 32)[0]

    def _load_metadata(self):
        base = self.pe.rva_to_offset(self.md_rva)
        if base is None or self.data[base:base + 4] != b"BSJB":
            raise NotManagedError("bad metadata root")
        self.md_base = base
        d = self.data
        ver_len = struct.unpack_from("<I", d, base + 12)[0]
        self.runtime_version = d[base + 16:base + 16 + ver_len].rstrip(
            b"\0").decode("utf-8", "replace")
        p = base + 16 + ver_len
        p += 2  # flags
        n_streams = struct.unpack_from("<H", d, p)[0]
        p += 2
        self.streams = {}
        for _ in range(n_streams):
            s_off, s_size = struct.unpack_from("<II", d, p)
            p += 8
            end = d.index(b"\0", p)
            name = d[p:end].decode("ascii", "replace")
            p = end + 1
            p = (p + 3) & ~3  # name is padded to a 4-byte boundary
            self.streams[name] = (base + s_off, s_size)

    # -- heaps --------------------------------------------------------------

    def string(self, offset):
        if "#Strings" not in self.streams:
            return ""
        base, size = self.streams["#Strings"]
        if offset >= size:
            return ""
        end = self.data.index(b"\0", base + offset)
        return self.data[base + offset:end].decode("utf-8", "replace")

    def blob(self, offset):
        if "#Blob" not in self.streams:
            return b""
        base, size = self.streams["#Blob"]
        if offset >= size:
            return b""
        length, p = _compressed_uint(self.data, base + offset)
        return self.data[p:p + length]

    def guid(self, index):
        if index == 0 or "#GUID" not in self.streams:
            return None
        base, _ = self.streams["#GUID"]
        raw = self.data[base + (index - 1) * 16:base + index * 16]
        if len(raw) != 16:
            return None
        a, b, c = struct.unpack_from("<IHH", raw, 0)
        return "%08x-%04x-%04x-%s-%s" % (
            a, b, c, raw[8:10].hex(), raw[10:16].hex())

    def user_string(self, offset):
        """#US entry: UTF-16LE with a trailing flag byte."""
        if "#US" not in self.streams:
            return None
        base, size = self.streams["#US"]
        if offset >= size:
            return None
        length, p = _compressed_uint(self.data, base + offset)
        if length == 0:
            return ""
        return self.data[p:p + length - 1].decode("utf-16-le", "replace")

    # -- tables -------------------------------------------------------------

    def _load_tables(self):
        name = "#~" if "#~" in self.streams else "#-"
        if name not in self.streams:
            raise NotManagedError("no table stream")
        base, _size = self.streams[name]
        d = self.data
        heap_sizes = d[base + 6]
        self.str_wide = bool(heap_sizes & 0x01)
        self.guid_wide = bool(heap_sizes & 0x02)
        self.blob_wide = bool(heap_sizes & 0x04)
        valid, sorted_mask = struct.unpack_from("<QQ", d, base + 8)
        self.sorted_mask = sorted_mask
        p = base + 24
        self.rows = {}
        for t in range(64):
            if valid >> t & 1:
                self.rows[t] = struct.unpack_from("<I", d, p)[0]
                p += 4
        self._row_widths = {}
        self._table_offsets = {}
        for t in sorted(self.rows):
            width = self._row_width(t)
            self._row_widths[t] = width
            self._table_offsets[t] = p
            p += width * self.rows[t]
        self._row_cache = {}

    def _col_width(self, kind):
        if kind == "u8":
            return 1
        if kind == "u16":
            return 2
        if kind == "u32":
            return 4
        if kind == "str":
            return 4 if self.str_wide else 2
        if kind == "guid":
            return 4 if self.guid_wide else 2
        if kind == "blob":
            return 4 if self.blob_wide else 2
        if kind[0] == "rid":
            return 4 if self.rows.get(kind[1], 0) >= 0x10000 else 2
        tables, bits = CODED[kind[1]]
        limit = 1 << (16 - bits)
        for tbl in tables:
            if tbl is not None and self.rows.get(tbl, 0) >= limit:
                return 4
        return 2

    def _row_width(self, table):
        cols = SCHEMA.get(table)
        if cols is None:
            # Unknown/ENC table in a stream we still have to walk past.
            raise NotManagedError("unsupported metadata table 0x%02X" % table)
        return sum(self._col_width(k) for _n, k in cols)

    def row_count(self, table):
        return self.rows.get(table, 0)

    def row(self, table, rid):
        """1-based row access -> dict of column name to raw value."""
        if rid < 1 or rid > self.rows.get(table, 0):
            return None
        key = (table, rid)
        cached = self._row_cache.get(key)
        if cached is not None:
            return cached
        cols = SCHEMA[table]
        p = self._table_offsets[table] + (rid - 1) * self._row_widths[table]
        r = _Reader(self.data, p)
        out = {}
        for nm, kind in cols:
            if kind == "u8":
                out[nm] = r.u8()
            elif kind == "u16":
                out[nm] = r.u16()
            elif kind == "u32":
                out[nm] = r.u32()
            elif kind == "str":
                out[nm] = r.idx(self.str_wide)
            elif kind == "guid":
                out[nm] = r.idx(self.guid_wide)
            elif kind == "blob":
                out[nm] = r.idx(self.blob_wide)
            elif kind[0] == "rid":
                out[nm] = r.idx(self._col_width(kind) == 4)
            else:
                raw = r.idx(self._col_width(kind) == 4)
                tables, bits = CODED[kind[1]]
                tag = raw & ((1 << bits) - 1)
                tgt = tables[tag] if tag < len(tables) else None
                out[nm] = (tgt, raw >> bits)
        self._row_cache[key] = out
        return out

    def iter_rows(self, table):
        for rid in range(1, self.rows.get(table, 0) + 1):
            yield rid, self.row(table, rid)

    # -- convenience --------------------------------------------------------

    def assembly_info(self):
        r = self.row(ASSEMBLY, 1)
        if not r:
            return None
        pk = self.blob(r["PublicKey"])
        token = ""
        if pk:
            token = hashlib.sha1(pk).digest()[-8:][::-1].hex()
        return {
            "name": self.string(r["Name"]),
            "version": "%d.%d.%d.%d" % (r["MajorVersion"], r["MinorVersion"],
                                        r["BuildNumber"], r["RevisionNumber"]),
            "culture": self.string(r["Culture"]) or "neutral",
            "publicKeyToken": token or None,
            "flags": r["Flags"],
        }

    def module_info(self):
        r = self.row(MODULE, 1)
        if not r:
            return None
        return {"name": self.string(r["Name"]), "mvid": self.guid(r["Mvid"])}

    def assembly_refs(self):
        out = []
        for _rid, r in self.iter_rows(ASSEMBLYREF):
            tok = self.blob(r["PublicKeyOrToken"])
            out.append({
                "name": self.string(r["Name"]),
                "version": "%d.%d.%d.%d" % (
                    r["MajorVersion"], r["MinorVersion"],
                    r["BuildNumber"], r["RevisionNumber"]),
                "publicKeyToken": tok.hex() if tok else None,
            })
        return out

    def target_framework(self):
        """Read [assembly: TargetFramework("...")] when present."""
        for _rid, r in self.iter_rows(CUSTOMATTRIBUTE):
            if r["Parent"][0] != ASSEMBLY:
                continue
            if self.custom_attribute_name(r) != "TargetFrameworkAttribute":
                continue
            val = self.blob(r["Value"])
            if len(val) > 3 and val[0] == 0x01 and val[1] == 0x00:
                ln, p = _compressed_uint(val, 2)
                return val[p:p + ln].decode("utf-8", "replace")
        return None

    def custom_attribute_name(self, ca_row):
        tgt, rid = ca_row["Type"]
        if tgt == MEMBERREF:
            mr = self.row(MEMBERREF, rid)
            if not mr:
                return None
            ptgt, prid = mr["Class"]
            if ptgt == TYPEREF:
                tr = self.row(TYPEREF, prid)
                return self.string(tr["Name"]) if tr else None
            if ptgt == TYPEDEF:
                td = self.row(TYPEDEF, prid)
                return self.string(td["Name"]) if td else None
        elif tgt == METHODDEF:
            owner = self.method_owner(rid)
            if owner:
                td = self.row(TYPEDEF, owner)
                return self.string(td["Name"])
        return None

    def manifest_resources(self):
        return [self.string(r["Name"]) for _rid, r in
                self.iter_rows(MANIFESTRESOURCE)]

    # -- type/method naming --------------------------------------------------

    def type_full_name(self, rid):
        td = self.row(TYPEDEF, rid)
        if not td:
            return None
        name = self.string(td["Name"])
        ns = self.string(td["Namespace"])
        enclosing = self.enclosing_of(rid)
        if enclosing:
            parent = self.type_full_name(enclosing)
            if parent:
                return parent + "+" + name
        return (ns + "." + name) if ns else name

    def _build_nesting(self):
        self._nesting = {}
        for _rid, r in self.iter_rows(NESTEDCLASS):
            self._nesting[r["NestedClass"]] = r["EnclosingClass"]

    def enclosing_of(self, rid):
        if not hasattr(self, "_nesting"):
            self._build_nesting()
        return self._nesting.get(rid)

    def typedefref_name(self, coded):
        """Resolve a TypeDefOrRef coded index to a printable name."""
        tgt, rid = coded
        if tgt is None or rid == 0:
            return None
        if tgt == TYPEDEF:
            return self.type_full_name(rid)
        if tgt == TYPEREF:
            tr = self.row(TYPEREF, rid)
            if not tr:
                return None
            ns = self.string(tr["Namespace"])
            nm = self.string(tr["Name"])
            scope = tr["ResolutionScope"]
            if scope[0] == TYPEREF:
                outer = self.typedefref_name(scope)
                return (outer + "+" + nm) if outer else nm
            return (ns + "." + nm) if ns else nm
        if tgt == TYPESPEC:
            return "<TypeSpec#%d>" % rid
        return None

    def type_method_range(self, rid):
        td = self.row(TYPEDEF, rid)
        if not td:
            return (0, 0)
        start = td["MethodList"]
        nxt = self.row(TYPEDEF, rid + 1)
        end = nxt["MethodList"] if nxt else self.rows.get(METHODDEF, 0) + 1
        return (start, end)

    def type_field_range(self, rid):
        td = self.row(TYPEDEF, rid)
        if not td:
            return (0, 0)
        start = td["FieldList"]
        nxt = self.row(TYPEDEF, rid + 1)
        end = nxt["FieldList"] if nxt else self.rows.get(FIELD, 0) + 1
        return (start, end)

    def _build_method_owner(self):
        self._method_owner = {}
        for rid in range(1, self.rows.get(TYPEDEF, 0) + 1):
            start, end = self.type_method_range(rid)
            for m in range(start, end):
                self._method_owner[m] = rid

    def method_owner(self, method_rid):
        if not hasattr(self, "_method_owner"):
            self._build_method_owner()
        return self._method_owner.get(method_rid)

    def method_name(self, method_rid):
        r = self.row(METHODDEF, method_rid)
        return self.string(r["Name"]) if r else None

    def method_full_name(self, method_rid):
        owner = self.method_owner(method_rid)
        tn = self.type_full_name(owner) if owner else "<global>"
        return "%s::%s" % (tn, self.method_name(method_rid))

    def properties_of(self, type_rid):
        if not hasattr(self, "_propmap"):
            self._propmap = {}
            rowsn = list(self.iter_rows(PROPERTYMAP))
            total = self.rows.get(PROPERTY, 0)
            for i, (_rid, r) in enumerate(rowsn):
                start = r["PropertyList"]
                end = rowsn[i + 1][1]["PropertyList"] if i + 1 < len(rowsn) else total + 1
                self._propmap[r["Parent"]] = (start, end)
        rng = self._propmap.get(type_rid)
        if not rng:
            return []
        return [self.string(self.row(PROPERTY, p)["Name"])
                for p in range(rng[0], rng[1]) if self.row(PROPERTY, p)]

    def events_of(self, type_rid):
        if not hasattr(self, "_eventmap"):
            self._eventmap = {}
            rowsn = list(self.iter_rows(EVENTMAP))
            total = self.rows.get(EVENT, 0)
            for i, (_rid, r) in enumerate(rowsn):
                start = r["EventList"]
                end = rowsn[i + 1][1]["EventList"] if i + 1 < len(rowsn) else total + 1
                self._eventmap[r["Parent"]] = (start, end)
        rng = self._eventmap.get(type_rid)
        if not rng:
            return []
        return [self.string(self.row(EVENT, e)["Name"])
                for e in range(rng[0], rng[1]) if self.row(EVENT, e)]

    def interfaces_of(self, type_rid):
        if not hasattr(self, "_ifaces"):
            self._ifaces = {}
            for _rid, r in self.iter_rows(INTERFACEIMPL):
                self._ifaces.setdefault(r["Class"], []).append(r["Interface"])
        return [self.typedefref_name(c) for c in self._ifaces.get(type_rid, [])]

    # -- IL -----------------------------------------------------------------

    def method_body(self, method_rid):
        """Return the raw IL byte stream of a method, or None."""
        r = self.row(METHODDEF, method_rid)
        if not r or r["RVA"] == 0:
            return None
        off = self.pe.rva_to_offset(r["RVA"])
        if off is None:
            return None
        d = self.data
        first = d[off]
        if first & 0x03 == 0x02:  # tiny header
            size = first >> 2
            return d[off + 1:off + 1 + size]
        if first & 0x03 == 0x03:  # fat header
            hdr_words = (struct.unpack_from("<H", d, off)[0] >> 12) & 0xF
            code_size = struct.unpack_from("<I", d, off + 4)[0]
            start = off + hdr_words * 4
            return d[start:start + code_size]
        return None


# --- IL opcode walking ------------------------------------------------------

# Operand size by single-byte opcode; entries absent here take no operand.
_OPERAND_1 = {
    0x28: 4, 0x6F: 4, 0x73: 4, 0x72: 4,  # call, callvirt, newobj, ldstr
    0x27: 4, 0x71: 4, 0x74: 4, 0x75: 4, 0x79: 4, 0x7B: 4, 0x7C: 4, 0x7D: 4,
    0x7E: 4, 0x7F: 4, 0x80: 4, 0x81: 4, 0x8C: 4, 0x8D: 4, 0x8F: 4, 0xA3: 4,
    0xA4: 4, 0xA5: 4, 0xC2: 4, 0xC6: 4, 0xD0: 4, 0x70: 4, 0x20: 4, 0x22: 4,
    0x38: 4, 0x39: 4, 0x3A: 4, 0x3B: 4, 0x3C: 4, 0x3D: 4, 0x3E: 4, 0x3F: 4,
    0x40: 4, 0x41: 4, 0x42: 4, 0x43: 4, 0x44: 4,
    0x23: 8, 0x21: 8,
    0x1F: 1, 0x0E: 1, 0x0F: 1, 0x10: 1, 0x11: 1, 0x12: 1, 0x13: 1,
    0x2B: 1, 0x2C: 1, 0x2D: 1, 0x2E: 1, 0x2F: 1, 0x30: 1, 0x31: 1, 0x32: 1,
    0x33: 1, 0x34: 1, 0x35: 1, 0x36: 1, 0x37: 1, 0xDE: 1,
    0x24: 0,
}
# 0xFE-prefixed two-byte opcodes that carry a 4-byte operand.
_OPERAND_2_4 = {0x06, 0x07, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x15, 0x1C}
_SWITCH = 0x45


def walk_il(code):
    """Yield (offset, opcode, operand_bytes). opcode is int, 0xFE00|x if prefixed."""
    i = 0
    n = len(code)
    while i < n:
        start = i
        op = code[i]
        i += 1
        if op == 0xFE:
            if i >= n:
                return
            op2 = code[i]
            i += 1
            full = 0xFE00 | op2
            if op2 in _OPERAND_2_4:
                yield start, full, code[i:i + 4]
                i += 4
            elif op2 == 0x12:  # unaligned.
                yield start, full, code[i:i + 1]
                i += 1
            else:
                yield start, full, b""
            continue
        if op == _SWITCH:
            if i + 4 > n:
                return
            count = struct.unpack_from("<I", code, i)[0]
            i += 4 + count * 4
            yield start, op, b""
            continue
        size = _OPERAND_1.get(op, 0)
        if size:
            yield start, op, code[i:i + size]
            i += size
        else:
            yield start, op, b""


CALL_OPS = (0x28, 0x6F, 0x73)  # call, callvirt, newobj
LDSTR = 0x72
LDTOKEN = 0xD0
_SFLD_OPS = (0x7E, 0x7F, 0x80, 0x81, 0x7B, 0x7C, 0x7D)
