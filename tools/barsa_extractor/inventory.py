"""Phases 1-5: input discovery, assembly inventory, type/method index, IL evidence."""

import hashlib
import os
import re

from .cli_metadata import (
    Assembly, NotManagedError, TYPEDEF, METHODDEF, FIELD, PROPERTY,
    MANIFESTRESOURCE,
)
from .signatures import parse_method_sig, parse_field_sig

ASSEMBLY_EXT = {".dll", ".exe", ".ocx"}
CONFIG_EXT = {".config", ".default", ".rsp"}
EXPORT_EXT = {".metaexport"}
SUPPLEMENTAL_EXT = {".mrt", ".json", ".xml", ".bwt", ".bil"}
SOURCE_EXT = {".cs", ".vb", ".js", ".ts"}

# Spec section 49: Barsa-owned and infrastructure assemblies get deep analysis.
BARSA_PREFIXES = ("barsa", "wsm", "metabase")

# Barsa-branded but not Barsa domain code: these are rebranded third-party
# control, charting, document and script-editor suites (Janus, Xara and
# friends) shipped under the Barsa name.  They carry two thirds of all methods
# in source/ and say nothing about how Barsa models or exchanges a system, so
# they are inventoried and type-counted but not indexed member-by-member.
REBRANDED_LIBRARY_PREFIXES = (
    "barsa.spl.win.",
    "barsa.xara.",
    "barsa.spl.documents",
    "barsa.spl.excel",
    "barsa.spl.common",
    "barsa.spl.diagram",
    "barsa.imagelibrary",
    "barsa.metascriptengine",
    "barsa.scriptengine",
    "barsa.office.",
)

# Spec section 59-61: priority search terms.
HIGH_PRIORITY_TERMS = (
    "SecurityHandler", "SessionMgr", "ApplicationLauncher", "BusinessLogic",
    "MetaObject", "MetaSystem", "TypeDef", "FieldDef", "RelationDef",
    "Report", "ReportData", "DbBuilder", "DbStructBuilder", "RemotableObject",
    "Export", "Import", "Serialize", "Deserialize", "Package",
    "Navigator", "Folder", "Workflow", "Stimulsoft", "DataFetcher",
    "ObjectReference", "FixId", "IdMap", "Login", "Authenticate", "CurrentUser",
)


def classify_input(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in EXPORT_EXT:
        return "ExportPackage"
    if ext in ASSEMBLY_EXT:
        return "Assembly"
    if ext in CONFIG_EXT:
        return "Config"
    if ext in SOURCE_EXT:
        return "SourceCode"
    if ext in SUPPLEMENTAL_EXT:
        return "Supplemental"
    if ext in (".png", ".gif", ".jpg", ".bmp", ".svg", ".ico", ".wav", ".avi"):
        return "Resource"
    if ext in (".html", ".htm", ".css", ".chm", ".txt", ".doc", ".log"):
        return "Document"
    return "Unknown"


def discover(source_root):
    """Phase 1. Recursive scan; both the flat and the source/dll/ layout work."""
    found = []
    for dirpath, _dirs, files in os.walk(source_root):
        for fn in sorted(files):
            full = os.path.join(dirpath, fn)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            found.append({
                "path": os.path.relpath(full, os.path.dirname(source_root)),
                "absPath": full,
                "name": fn,
                "size": size,
                "kind": classify_input(full),
            })
    return sorted(found, key=lambda e: e["path"])


def is_barsa_owned(name):
    low = name.lower()
    return any(low.startswith(p) for p in BARSA_PREFIXES)


def is_barsa_domain(name):
    """Barsa-owned and not one of the rebranded third-party library suites."""
    low = name.lower()
    if not is_barsa_owned(low):
        return False
    return not any(low.startswith(p) for p in REBRANDED_LIBRARY_PREFIXES)


def priority_score(asm_name, asm, type_names):
    """Spec section 49 scoring, used to decide deep vs index-only analysis.

    Ownership is the gate, not a bonus: a third-party report engine matches
    plenty of high-priority terms ("Report", "Export", "Parameter") without
    telling us anything about Barsa, and IL-scanning it costs far more than it
    returns.  Non-Barsa assemblies are inventoried and type-indexed only.
    """
    if not is_barsa_owned(asm_name):
        return 0
    score = 50
    joined = " ".join(type_names)
    for term in HIGH_PRIORITY_TERMS:
        if term in joined:
            score += 3
    score += min(asm.row_count(TYPEDEF) // 100, 10)
    return score


def inventory_assembly(entry):
    """Phase 2 facts for one file; returns None for native/unparseable PEs."""
    data = open(entry["absPath"], "rb").read()
    try:
        asm = Assembly(entry["absPath"], data)
    except NotManagedError as exc:
        return None, {"path": entry["path"], "reason": str(exc)}
    except Exception as exc:  # malformed metadata is evidence too
        return None, {"path": entry["path"],
                      "reason": "%s: %s" % (type(exc).__name__, exc)}
    info = asm.assembly_info() or {}
    mod = asm.module_info() or {}
    record = {
        "fileName": entry["name"],
        "path": entry["path"],
        "assemblyName": info.get("name") or mod.get("name") or entry["name"],
        "assemblyVersion": info.get("version"),
        "culture": info.get("culture"),
        "publicKeyToken": info.get("publicKeyToken"),
        "targetFramework": asm.target_framework(),
        "runtimeVersion": asm.runtime_version,
        "architecture": asm.pe.architecture(),
        "moduleVersionId": mod.get("mvid"),
        "sha256": asm.sha256,
        "size": asm.size,
        "isExecutable": bool(asm.entry_point_token),
        "typesCount": asm.row_count(TYPEDEF),
        "methodsCount": asm.row_count(METHODDEF),
        "fieldsCount": asm.row_count(FIELD),
        "propertiesCount": asm.row_count(PROPERTY),
        "resourcesCount": asm.row_count(MANIFESTRESOURCE),
        "referencedAssemblies": sorted(
            {r["name"] for r in asm.assembly_refs()}),
        "barsaOwned": is_barsa_owned(entry["name"]),
    }
    return (asm, record), None


_OBFUSCATED = re.compile(r"^#|^<")


def index_types(asm, asm_record):
    """Phase 3. One row per TypeDef plus obfuscation statistics."""
    out = []
    obf = 0
    for rid in range(1, asm.row_count(TYPEDEF) + 1):
        full = asm.type_full_name(rid)
        if not full:
            continue
        td = asm.row(TYPEDEF, rid)
        name = asm.string(td["Name"])
        if _OBFUSCATED.match(name):
            obf += 1
        flags = td["Flags"]
        vis = flags & 0x7
        start, end = asm.type_method_range(rid)
        fstart, fend = asm.type_field_range(rid)
        out.append({
            "assembly": asm_record["assemblyName"],
            "assemblyKey": asm_record["key"],
            "fullName": full,
            "namespace": asm.string(td["Namespace"]),
            "visibility": "public" if vis in (1, 2) else "internal",
            "isInterface": bool(flags & 0x20),
            "isAbstract": bool(flags & 0x80),
            "isSealed": bool(flags & 0x100),
            "baseType": asm.typedefref_name(td["Extends"]),
            "interfaces": [i for i in asm.interfaces_of(rid) if i],
            "methodCount": max(0, end - start),
            "fieldCount": max(0, fend - fstart),
            "properties": asm.properties_of(rid),
            "events": asm.events_of(rid),
            "obfuscatedName": bool(_OBFUSCATED.match(name)),
            "_rid": rid,
        })
    return out, obf


def index_methods(asm, asm_record, type_rows):
    """Phase 3/10. Signature-level index for non-obfuscated members."""
    out = []
    for t in type_rows:
        start, end = asm.type_method_range(t["_rid"])
        for m in range(start, end):
            r = asm.row(METHODDEF, m)
            if not r:
                continue
            name = asm.string(r["Name"])
            sig = parse_method_sig(asm.blob(r["Signature"]), asm)
            flags = r["Flags"]
            vis = flags & 0x7
            out.append({
                "assembly": asm_record["assemblyName"],
                "assemblyKey": asm_record["key"],
                "declaringType": t["fullName"],
                "name": name,
                "visibility": {1: "private", 2: "protected internal",
                               3: "internal", 4: "protected",
                               5: "protected or internal",
                               6: "public"}.get(vis, "unknown"),
                "static": bool(flags & 0x10),
                "abstract": bool(flags & 0x400),
                "virtual": bool(flags & 0x40),
                "returnType": sig["returnType"] if sig else None,
                "parameters": sig["parameters"] if sig else None,
                "hasBody": r["RVA"] != 0,
                "obfuscatedName": bool(_OBFUSCATED.match(name)),
                "_rid": m,
            })
    return out
