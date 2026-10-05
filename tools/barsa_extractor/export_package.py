"""Reader for Barsa .metaexport packages.

Observed container (both samples):

    GZip
      -> .NET BinaryFormatter graph
           -> System.Data.DataSet  (DataSet.RemotingVersion / XmlSchema / XmlDiffGram)

The DataSet travels as two UTF-8 strings inside the BinaryFormatter stream: an
XSD describing every table, and a DiffGram holding the rows.  Both are read
without running any Barsa or BinaryFormatter code.
"""

import gzip
import hashlib
import re
import xml.etree.ElementTree as ET

XS = "{http://www.w3.org/2001/XMLSchema}"
MSDATA = "{urn:schemas-microsoft-com:xml-msdata}"
DIFFGR = "{urn:schemas-microsoft-com:xml-diffgram-v1}"

GZIP_MAGIC = b"\x1f\x8b"
BF_HEADER = b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"

# Table-name prefixes that carry export-session bookkeeping rather than payload.
CONTROL_PREFIX = "$"

# Values never copied into the knowledge pack.
_SENSITIVE_COLUMN = re.compile(
    r"(?i)(password|pwd|secret|token|hash|credential|connectionstring)")


def _xml_name_decode(name):
    """DataSet XML-escapes names: Source_x0020_Db -> 'Source Db'."""
    return re.sub(r"_x([0-9A-Fa-f]{4})_",
                  lambda m: chr(int(m.group(1), 16)), name or "")


class ExportPackage:
    """A parsed .metaexport file."""

    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        self.file_size = len(raw)
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.container = []
        if raw[:2] == GZIP_MAGIC:
            self.container.append("gzip")
            data = gzip.decompress(raw)
        else:
            data = raw
        self.payload_size = len(data)
        self.binary_formatter = data[:len(BF_HEADER)] == BF_HEADER
        if self.binary_formatter:
            self.container.append("BinaryFormatter")
        self.serialized_type = self._sniff_type(data)
        if self.serialized_type:
            self.container.append(self.serialized_type)
        self.schema_xml, self.diffgram_xml = self._split(data)
        self.tables = {}
        self.header = {}
        if self.schema_xml:
            self.tables = self._parse_schema(self.schema_xml)
        if self.diffgram_xml:
            self._count_rows(self.diffgram_xml)

    # -- container ----------------------------------------------------------

    @staticmethod
    def _sniff_type(data):
        for cand in (b"System.Data.DataSet", b"System.Data.DataTable"):
            if data.find(cand, 0, 4096) != -1:
                return cand.decode()
        return None

    @staticmethod
    def _split(data):
        """Carve the XSD and DiffGram strings out of the BinaryFormatter stream."""
        schema = diff = None
        s = data.find(b"<?xml version")
        if s != -1:
            e = data.find(b"</xs:schema>", s)
            if e != -1:
                schema = data[s:e + len(b"</xs:schema>")].decode("utf-8", "replace")
        g = data.find(b"<diffgr:diffgram")
        if g != -1:
            ge = data.rfind(b"</diffgr:diffgram>")
            if ge != -1:
                diff = data[g:ge + len(b"</diffgr:diffgram>")].decode("utf-8", "replace")
        return schema, diff

    # -- schema -------------------------------------------------------------

    @staticmethod
    def _parse_schema(schema_xml):
        """-> {tableName: {'columns': [{name, type, nullable}], 'isControl': bool}}"""
        txt = schema_xml.replace('encoding="utf-16"', 'encoding="utf-8"', 1)
        root = ET.fromstring(txt)
        tables = {}
        for el in root.iter(XS + "element"):
            name = el.get("name")
            ct = el.find(XS + "complexType")
            if not name or ct is None:
                continue
            if el.get(MSDATA + "IsDataSet") == "true":
                continue
            cols = []
            for c in ct.iter(XS + "element"):
                cname = c.get("name")
                ctype = c.get("type")
                if not cname or not ctype:
                    continue
                cols.append({
                    "name": _xml_name_decode(cname),
                    "xsdType": ctype,
                    "nullable": c.get("minOccurs") == "0",
                })
            if not cols:
                continue
            tn = _xml_name_decode(name)
            tables[tn] = {
                "columns": cols,
                "isControl": tn.startswith(CONTROL_PREFIX),
            }
        return tables

    # -- rows ---------------------------------------------------------------

    def _count_rows(self, diffgram_xml):
        """Count rows per table and capture the $Header row (no payload values)."""
        counts = {}
        header = {}
        try:
            root = ET.fromstring(diffgram_xml)
        except ET.ParseError:
            self.row_counts = {}
            return
        for ds in root:
            for row in ds:
                tag = _xml_name_decode(row.tag.split("}")[-1])
                counts[tag] = counts.get(tag, 0) + 1
                if tag == "$Header" and not header:
                    for cell in row:
                        cname = _xml_name_decode(cell.tag.split("}")[-1])
                        header[cname] = cell.text
        self.row_counts = counts
        self.header = header

    def rows_of(self, table_name, limit=None, redact_sensitive=True):
        """Yield dicts for one table. Sensitive-looking columns are masked."""
        if not self.diffgram_xml:
            return
        try:
            root = ET.fromstring(self.diffgram_xml)
        except ET.ParseError:
            return
        want = table_name
        n = 0
        for ds in root:
            for row in ds:
                tag = _xml_name_decode(row.tag.split("}")[-1])
                if tag != want:
                    continue
                out = {}
                for cell in row:
                    cname = _xml_name_decode(cell.tag.split("}")[-1])
                    if redact_sensitive and _SENSITIVE_COLUMN.search(cname):
                        out[cname] = "***REDACTED***" if cell.text else None
                    else:
                        out[cname] = cell.text
                yield out
                n += 1
                if limit and n >= limit:
                    return

    # -- summaries ----------------------------------------------------------

    def summary(self):
        return {
            "file": self.path.split("/")[-1],
            "sha256": self.sha256,
            "fileSize": self.file_size,
            "payloadSize": self.payload_size,
            "container": self.container,
            "header": self.header,
            "tableCount": len(self.tables),
            "rowCounts": dict(sorted(getattr(self, "row_counts", {}).items())),
        }


def compare(packages):
    """Multi-sample structural comparison (spec section 17).

    Returns always-present / optional tables and, per shared table, which
    columns are present in every sample versus only some.
    """
    if not packages:
        return {}
    names = [set(p.tables) for p in packages]
    common = set.intersection(*names)
    union = set.union(*names)
    per_table = {}
    for t in sorted(common):
        col_sets = [{c["name"] for c in p.tables[t]["columns"]} for p in packages]
        always = set.intersection(*col_sets)
        any_ = set.union(*col_sets)
        per_table[t] = {
            "alwaysPresentColumns": sorted(always),
            "variantColumns": sorted(any_ - always),
        }
    return {
        "sampleCount": len(packages),
        "alwaysPresentTables": sorted(common),
        "variantTables": sorted(union - common),
        "perTable": per_table,
    }


def id_reference_model(packages):
    """Spec section 18: which columns look like identity vs reference.

    Classification is name-shaped, so it is reported as Inferred unless the
    package's own $IdEmbeddingFields table confirms the column.
    """
    declared = set()
    for p in packages:
        for row in p.rows_of("$IdEmbeddingFields"):
            tn, cn = row.get("TableName"), row.get("ColumnName")
            if tn and cn:
                declared.add((tn.lower(), cn.lower()))
    out = []
    seen = set()
    for p in packages:
        for tname, tinfo in p.tables.items():
            for col in tinfo["columns"]:
                cn = col["name"]
                key = (tname, cn)
                if key in seen:
                    continue
                seen.add(key)
                low = cn.lower()
                if low in ("id", "objectid"):
                    role = "identity"
                elif low.endswith("id") or low.endswith("ids"):
                    role = "reference"
                else:
                    continue
                is_declared = (tname.lower(), low) in declared
                out.append({
                    "table": tname,
                    "column": cn,
                    "role": role,
                    "declaredInIdEmbeddingFields": is_declared,
                    "confidence": "Verified" if is_declared else "Inferred",
                })
    return sorted(out, key=lambda r: (r["table"], r["column"]))
