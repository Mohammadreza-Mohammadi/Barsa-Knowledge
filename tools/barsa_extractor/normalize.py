"""Adapters from each export format into one normalized system model.

Spec v3 sections 43-49.  The point is to separate the Barsa semantic model from
whichever serialization carried it, so a comparison runs on meaning rather than
on bytes.

The hard rule from section 47 is enforced here:

    []   = proven empty
    None = unknown / not extracted / not represented by this format

Every node carries `_provenance` so a reader can always get back to the
artifact, table or JSON path a value came from.
"""

SCHEMA_VERSION = "3.0"

# Normalized collection -> legacy DataSet table, as the AiExport profile itself
# declares the mapping (recordTypes[*].table).  Nothing here is guessed: each
# pair is confirmed by the profile and by the table being present in a sample.
COLLECTION_TABLES = {
    "system": ("MET_METASYSTEM", "Barsa.Meta.MetaSystem"),
    "entities": ("MET_TYPEDEF", "Barsa.Meta.TypeDef"),
    "fields": ("MET_FIELDDEF", "Barsa.Meta.FieldDef"),
    "relationDefs": ("MET_RELATIONDEF", "Barsa.Meta.RelationDef"),
    "relations": ("met_Relation", "Barsa.Meta.Relation"),
    "reports": ("met_Report", "Barsa.Meta.Report"),
    "views": ("MET_TYPEVIEWENTITY", "Barsa.Meta.TypeViewEntity"),
    "navigation": ("MET_FOLDER", "Barsa.Meta.Folder"),
    "code": ("MET_METACODE", "Barsa.Meta.MetaCode"),
    "commands": ("MET_METACOMMAND", "Barsa.Meta.MetaCommand"),
}

EMPTY_ENVELOPE_KEYS = (
    "system", "entities", "fields", "relations", "relationDefs", "reports",
    "views", "navigation", "businessRules", "workflows", "webServices",
    "code", "commands",
)


def _prov(fmt, source, path, confidence, evidence=None):
    return {
        "format": fmt,
        "source": source,
        "path": path,
        "confidence": confidence,
        "evidence": evidence or [],
    }


def _truthy(v):
    if v is None:
        return None
    return str(v).strip().lower() in ("true", "1", "yes")


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def empty_envelope():
    """An envelope where every collection is Unknown until something fills it."""
    env = {"schemaVersion": SCHEMA_VERSION}
    for k in EMPTY_ENVELOPE_KEYS:
        env[k] = None
    env["extensions"] = {}
    env["_availability"] = {}
    return env


# --- legacy ---------------------------------------------------------------

def from_legacy(pkg, row_limit=None):
    """Legacy .metaexport DataSet -> normalized model (spec section 43)."""
    env = empty_envelope()
    src = pkg.path.split("/")[-1]
    fmt = "Barsa.LegacyMetaExport"

    def present(table):
        return table in pkg.tables

    def rows(table):
        return list(pkg.rows_of(table, limit=row_limit))

    # system
    if present("MET_METASYSTEM"):
        env["system"] = []
        for r in rows("MET_METASYSTEM"):
            env["system"].append({
                "id": r.get("ID"),
                "name": r.get("SystemKey"),
                "caption": r.get("Caption"),
                "version": r.get("Version"),
                "rootFolderId": r.get("rootFolderId"),
                "isInactive": _truthy(r.get("IsInactive")),
                "_provenance": _prov(fmt, src, "$.MET_METASYSTEM[*]",
                                     "Verified"),
            })

    if present("MET_TYPEDEF"):
        env["entities"] = []
        for r in rows("MET_TYPEDEF"):
            env["entities"].append({
                "id": r.get("ID"),
                "name": r.get("DbName"),
                "caption": r.get("caption"),
                "dbName": r.get("DbName"),
                "systemId": r.get("systemId"),
                "parentId": r.get("parentid"),
                "isDynamic": _truthy(r.get("isDynamic")),
                "isDeleted": _truthy(r.get("IsDeleted")),
                "defaultFieldId": r.get("DefaultFieldId"),
                "previewFieldId": r.get("previewFieldId"),
                "defaultReportId": r.get("defaultReportId"),
                "_provenance": _prov(fmt, src, "$.MET_TYPEDEF[*]", "Verified"),
            })

    if present("MET_FIELDDEF"):
        env["fields"] = []
        for r in rows("MET_FIELDDEF"):
            env["fields"].append({
                "id": r.get("ID"),
                "name": r.get("dbName"),
                "caption": r.get("caption"),
                "dbName": r.get("dbName"),
                "entityId": r.get("typeDefId"),
                "orderNumber": _int(r.get("orderNumber")),
                "fieldInfoType": r.get("fieldInfoType"),
                "relationType": r.get("relationType"),
                # The profile routes FieldDef.Settings through the FieldInfo
                # decoder, so the data type lives inside an opaque blob here.
                "dataType": None,
                "nullable": None,
                "defaultValue": None,
                "_provenance": _prov(fmt, src, "$.MET_FIELDDEF[*]", "Verified"),
            })

    if present("MET_RELATIONDEF"):
        env["relationDefs"] = []
        for r in rows("MET_RELATIONDEF"):
            env["relationDefs"].append({
                "id": r.get("ID"),
                "title": r.get("Title"),
                "reverseTitle": r.get("ReverseTitle"),
                "sourceEntity": r.get("SourceTypeId"),
                "targetEntity": r.get("DestTypeId"),
                "relationType": r.get("RelationType"),
                "max": _int(r.get("Max")),
                "isBilateral": _truthy(r.get("isBilateral")),
                "sourceFieldDefId": r.get("SourceFieldDefId"),
                "_provenance": _prov(fmt, src, "$.MET_RELATIONDEF[*]",
                                     "Verified"),
            })

    rel_tables = [t for t in ("met_Relation", "$basicInfoRelation")
                  if present(t)]
    if rel_tables:
        env["relations"] = []
        for t in rel_tables:
            for r in rows(t):
                env["relations"].append({
                    "id": r.get("ID"),
                    "sourceId": r.get("SourceId"),
                    "destId": r.get("DestId"),
                    "role": r.get("Role"),
                    "relationDefId": r.get("RelationDefId"),
                    "_provenance": _prov(fmt, src, "$.%s[*]" % t, "Verified"),
                })

    if present("met_Report"):
        env["reports"] = []
        for r in rows("met_Report"):
            env["reports"].append({
                "id": r.get("ID"),
                "name": r.get("Name"),
                "systemId": r.get("systemId"),
                "reportType": r.get("reportType"),
                "searchObjectId": r.get("SearchObjectId"),
                # ReportData has a declared decoder (SerializeReportData) but
                # is not decoded by this extractor.
                "query": None,
                "template": None,
                "parameters": None,
                "customColumns": None,
                "_provenance": _prov(fmt, src, "$.met_Report[*]", "Verified"),
            })

    if present("MET_TYPEVIEWENTITY"):
        env["views"] = []
        for r in rows("MET_TYPEVIEWENTITY"):
            env["views"].append({
                "id": r.get("ID"),
                "name": r.get("Name"),
                "entityId": r.get("TypeDefId"),
                "parentId": r.get("ParentId"),
                # TypeViewBlob routes through the TypeView decoder.
                "layout": None,
                "_provenance": _prov(fmt, src, "$.MET_TYPEVIEWENTITY[*]",
                                     "Verified"),
            })

    if present("MET_FOLDER"):
        env["navigation"] = []
        for r in rows("MET_FOLDER"):
            env["navigation"].append({
                "id": r.get("ID"),
                "name": r.get("Name"),
                "parentId": r.get("ParentId"),
                "path": r.get("Path"),
                "orderNo": _int(r.get("OrderNo")),
                "folderType": r.get("FolderType"),
                "reportId": r.get("ReportId"),
                "containingTypeDefId": r.get("ContainingTypeDefId"),
                "_provenance": _prov(fmt, src, "$.MET_FOLDER[*]", "Verified"),
            })

    if present("MET_METACODE"):
        env["code"] = []
        for r in rows("MET_METACODE"):
            env["code"].append({
                "id": r.get("ID"),
                "systemId": r.get("SystemId"),
                "targetObjectId": r.get("TargetObjectId"),
                "codeLocation": r.get("CodeLocation"),
                "codeLayer": r.get("CodeLayer"),
                "codeLanguage": r.get("CodeLanguage"),
                "addressInTarget": r.get("AddressInTarget"),
                # Code text itself is deliberately not copied into dist/.
                "code": None,
                "_provenance": _prov(fmt, src, "$.MET_METACODE[*]", "Verified"),
            })

    if present("MET_METACOMMAND"):
        env["commands"] = []
        for r in rows("MET_METACOMMAND"):
            env["commands"].append({
                "id": r.get("ID"),
                "caption": r.get("Caption"),
                "targetId": r.get("TargetId"),
                "systemId": r.get("SystemId"),
                "location": r.get("Location"),
                "isGlobal": _truthy(r.get("IsGlobal")),
                "_provenance": _prov(fmt, src, "$.MET_METACOMMAND[*]",
                                     "Verified"),
            })

    env["_availability"] = _legacy_availability(pkg)
    env["_source"] = {
        "format": fmt,
        "file": src,
        "sha256": pkg.sha256,
        "header": pkg.header,
        "tableCount": len(pkg.tables),
    }
    return env


def _legacy_availability(pkg):
    """Per-collection availability, distinguishing proven-absent from unknown."""
    out = {}
    for coll, (table, btype) in sorted(COLLECTION_TABLES.items()):
        in_sample = table in pkg.tables
        out[coll] = {
            "sourceTable": table,
            "barsaType": btype,
            "presentInArtifact": in_sample,
            "rowCount": pkg.row_counts.get(table, 0) if in_sample else None,
            "status": "Verified" if in_sample else "NotObservedInThisArtifact",
        }
    for coll in ("businessRules", "workflows", "webServices"):
        out[coll] = {
            "sourceTable": None,
            "barsaType": None,
            "presentInArtifact": False,
            "rowCount": None,
            # Spec section 91: not observed is not unsupported.
            "status": "NotObservedInThisArtifact",
        }
    return out


# --- AiExport -------------------------------------------------------------

# Normalized collection -> the profile record types that feed it.
AI_RECORD_TO_COLLECTION = {
    "Barsa.Meta.MetaSystem": "system",
    "Barsa.Meta.TypeDef": "entities",
    "Barsa.Meta.FieldDef": "fields",
    "Barsa.Meta.RelationDef": "relationDefs",
    "Barsa.Meta.Report": "reports",
    "Barsa.Meta.TypeViewEntity": "views",
    "Barsa.Meta.Folder": "navigation",
    "Barsa.Meta.MetaCode": "code",
    "Barsa.Meta.MetaCommand": "commands",
    "Barsa.Meta.BRRule": "businessRules",
    "Barsa.Workflow.WorkflowDef": "workflows",
    "Barsa.Workflow.ActivityDef": "workflows",
}


def from_ai_export(artifact, profile=None):
    """AiExport artifact -> normalized model (spec section 44).

    Both physical variants reduce to the same shape, which is what section 86
    asks for.  Mapping is driven by the artifact's own `$type` values and, where
    available, by the embedded profile's record-type table.
    """
    env = empty_envelope()
    src = artifact.path.split("/")[-1]
    fmt = "Barsa.AiExport"
    catalog = {e["type"]: e for e in artifact.type_catalog()}

    buckets = {}
    for src_file, doc in artifact.files.items():
        if src_file == "_assets":
            continue
        for obj in _iter_ai_objects(doc):
            t = obj.get("$type")
            if not isinstance(t, str):
                continue
            coll = AI_RECORD_TO_COLLECTION.get(t)
            if coll is None:
                continue
            buckets.setdefault(coll, []).append((src_file, obj))

    for coll, items in buckets.items():
        env[coll] = []
        for src_file, obj in items:
            node = {
                "id": obj.get("id"),
                "selector": obj.get("selector"),
                "caption": obj.get("$caption") or obj.get("caption"),
                "name": obj.get("DbName") or obj.get("Name")
                        or obj.get("name"),
                "_raw$type": obj.get("$type"),
                "_provenance": _prov(fmt, src, "%s :: $.%s"
                                     % (src_file, obj.get("$type")),
                                     "Verified"),
            }
            env[coll].append(node)

    env["_availability"] = {
        coll: {
            "presentInArtifact": coll in buckets,
            "rowCount": len(buckets.get(coll, ())) if coll in buckets else None,
            "status": "Verified" if coll in buckets
                      else "NotObservedInThisArtifact",
        }
        for coll in EMPTY_ENVELOPE_KEYS
    }
    env["_source"] = {
        "format": fmt,
        "file": src,
        "sha256": artifact.format.get("sha256"),
        "variant": artifact.variant,
        "manifest": artifact.manifest,
        "typeCatalog": sorted(catalog),
    }
    return env


def _iter_ai_objects(node, depth=0):
    if depth > 40:
        return
    if isinstance(node, dict):
        yield node
        for v in node.values():
            for x in _iter_ai_objects(v, depth + 1):
                yield x
    elif isinstance(node, list):
        for v in node:
            for x in _iter_ai_objects(v, depth + 1):
                yield x
