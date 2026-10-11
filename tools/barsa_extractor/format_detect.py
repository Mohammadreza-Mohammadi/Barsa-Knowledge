"""Physical and logical format detection (spec v3 sections 3, 88).

Extension is a hint only.  A file named `.zip` may hold a plain JSON document,
so detection always starts at the bytes.
"""

import gzip
import hashlib
import io
import json
import os
import zipfile

GZIP_MAGIC = b"\x1f\x8b"
ZIP_MAGIC = b"PK\x03\x04"
ZIP_EMPTY = b"PK\x05\x06"
BF_HEADER = b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
UTF8_BOM = b"\xef\xbb\xbf"

PHYSICAL_GZIP = "GZip"
PHYSICAL_ZIP = "ZIP"
PHYSICAL_JSON = "PlainJson"
PHYSICAL_XML = "XML"
PHYSICAL_PE = "PE"
PHYSICAL_BINARY = "Binary"
PHYSICAL_UNKNOWN = "Unknown"

LOGICAL_LEGACY = "Barsa.LegacyMetaExport"
LOGICAL_AI = "Barsa.AiExport"
LOGICAL_UNKNOWN = "Unknown"

VARIANT_LEGACY = "Legacy.DataSet.BinaryFormatter"
VARIANT_AI_SINGLE = "AiExport.SingleJson"
VARIANT_AI_ZIP = "AiExport.ZipJsonPackage"
VARIANT_UNKNOWN = "Unknown"

# A manifest naming this format is the logical marker the writers emit.
AI_FORMAT_VALUE = "Barsa.AiExport"


def _sniff_physical(head):
    if head[:2] == GZIP_MAGIC:
        return PHYSICAL_GZIP
    if head[:4] in (ZIP_MAGIC, ZIP_EMPTY):
        return PHYSICAL_ZIP
    if head[:2] == b"MZ":
        return PHYSICAL_PE
    probe = head[3:] if head[:3] == UTF8_BOM else head
    stripped = probe.lstrip(b" \t\r\n")
    if stripped[:1] in (b"{", b"["):
        return PHYSICAL_JSON
    if stripped[:1] == b"<":
        return PHYSICAL_XML
    return PHYSICAL_BINARY if head else PHYSICAL_UNKNOWN


def _json_logical(doc):
    """Classify a parsed JSON document by its own manifest, not its filename."""
    if not isinstance(doc, dict):
        return LOGICAL_UNKNOWN, None
    manifest = doc.get("manifest")
    if isinstance(manifest, dict):
        if manifest.get("format") == AI_FORMAT_VALUE:
            return LOGICAL_AI, manifest
        return LOGICAL_UNKNOWN, manifest
    if doc.get("format") == AI_FORMAT_VALUE:
        return LOGICAL_AI, doc
    return LOGICAL_UNKNOWN, None


def detect(path, read_limit=4 * 1024 * 1024):
    """Return a format record for one file. Never raises on content."""
    rec = {
        "path": path,
        "fileName": os.path.basename(path),
        "extension": os.path.splitext(path)[1].lower(),
        "size": None,
        "sha256": None,
        "physicalFormat": PHYSICAL_UNKNOWN,
        "logicalFormat": LOGICAL_UNKNOWN,
        "variant": VARIANT_UNKNOWN,
        "manifest": None,
        "encoding": None,
        "entries": None,
        "warnings": [],
        "errors": [],
        "confidence": "Unknown",
    }
    try:
        raw = open(path, "rb").read()
    except OSError as exc:
        rec["errors"].append({"kind": "PhysicalFormatDetectionError",
                              "message": str(exc)})
        return rec
    rec["size"] = len(raw)
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["physicalFormat"] = _sniff_physical(raw[:512])

    phys = rec["physicalFormat"]
    if phys == PHYSICAL_GZIP:
        _detect_gzip(rec, raw)
    elif phys == PHYSICAL_ZIP:
        _detect_zip(rec, raw)
    elif phys == PHYSICAL_JSON:
        _detect_json(rec, raw, read_limit)

    # Spec section 88: a mismatch is a warning, never a parse failure.
    expected = {
        PHYSICAL_ZIP: (".zip",),
        PHYSICAL_GZIP: (".metaexport", ".gz"),
        PHYSICAL_JSON: (".json",),
    }.get(phys)
    if expected and rec["extension"] and rec["extension"] not in expected:
        rec["warnings"].append({
            "kind": "ExtensionDoesNotMatchPhysicalFormat",
            "message": ("extension %s but physical format is %s"
                        % (rec["extension"], phys)),
        })
    return rec


def _detect_gzip(rec, raw):
    try:
        payload = gzip.decompress(raw)
    except Exception as exc:
        rec["errors"].append({"kind": "GZipDecodeError", "message": str(exc)})
        return
    rec["encoding"] = "binary"
    markers = []
    if payload[:len(BF_HEADER)] == BF_HEADER:
        markers.append("BinaryFormatterHeader")
    if payload.find(b"System.Data.DataSet", 0, 8192) != -1:
        markers.append("System.Data.DataSet")
    if payload.find(b"XmlDiffGram", 0, 8192) != -1:
        markers.append("XmlDiffGram")
    rec["legacyMarkers"] = markers
    if "BinaryFormatterHeader" in markers and "System.Data.DataSet" in markers:
        rec["logicalFormat"] = LOGICAL_LEGACY
        rec["variant"] = VARIANT_LEGACY
        rec["confidence"] = "Verified"
    else:
        rec["confidence"] = "Observed"


def _detect_zip(rec, raw):
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        names = sorted(zf.namelist())
    except Exception as exc:
        rec["errors"].append({"kind": "ZipPackageError", "message": str(exc)})
        return
    rec["entries"] = names
    manifest_name = next(
        (n for n in names if os.path.basename(n).lower() == "manifest.json"),
        None)
    if manifest_name is None:
        rec["errors"].append({
            "kind": "ManifestError",
            "message": "no manifest.json in package"})
        rec["confidence"] = "Observed"
        return
    try:
        doc = json.loads(zf.read(manifest_name).decode("utf-8-sig"))
    except Exception as exc:
        rec["errors"].append({"kind": "ManifestError", "message": str(exc)})
        return
    rec["manifest"] = doc
    rec["manifestEntry"] = manifest_name
    if doc.get("format") == AI_FORMAT_VALUE:
        rec["logicalFormat"] = LOGICAL_AI
        rec["variant"] = VARIANT_AI_ZIP
        rec["confidence"] = "Verified"
    elif doc.get("packageType") == "barsa-json-export":
        # BixJsonExportManager.SaveMultiProjectionPackage writes this wrapper:
        # a ZIP whose entries are themselves semantic.zip / full.zip.
        rec["logicalFormat"] = LOGICAL_AI
        rec["variant"] = "AiExport.MultiProjectionPackage"
        rec["confidence"] = "Verified"
    else:
        rec["confidence"] = "Observed"


def _detect_json(rec, raw, read_limit):
    body = raw[3:] if raw[:3] == UTF8_BOM else raw
    rec["encoding"] = "utf-8-bom" if raw[:3] == UTF8_BOM else "utf-8"
    if len(body) > read_limit:
        rec["warnings"].append({
            "kind": "JsonTooLargeForFullParse",
            "message": "%d bytes exceeds the %d byte parse limit"
                       % (len(body), read_limit)})
    try:
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception as exc:
        rec["errors"].append({"kind": "JsonParseError", "message": str(exc)})
        return
    logical, manifest = _json_logical(doc)
    rec["logicalFormat"] = logical
    rec["manifest"] = manifest
    rec["rootKeys"] = sorted(doc) if isinstance(doc, dict) else None
    if logical == LOGICAL_AI:
        rec["variant"] = VARIANT_AI_SINGLE
        rec["confidence"] = "Verified"
    else:
        rec["confidence"] = "Observed"


def normalize_manifest(rec):
    """Spec v3 section 87: one manifest shape for both AiExport variants."""
    m = rec.get("manifest")
    if not isinstance(m, dict):
        return None
    return {
        "format": m.get("format"),
        "profileVersion": m.get("profileVersion"),
        "producer": m.get("producer"),
        "producerVersion": m.get("producerVersion"),
        "buildId": m.get("buildId"),
        "representation": m.get("representation"),
        "packageType": m.get("packageType"),
        "formatVersion": m.get("formatVersion"),
        "representations": m.get("representations"),
        # Spec section 23: absent means absent, not null-by-assumption.
        "_absentFields": sorted(
            k for k in ("format", "profileVersion", "producer",
                        "producerVersion", "buildId")
            if k not in m),
        "_source": rec.get("manifestEntry") or "root.manifest",
    }
