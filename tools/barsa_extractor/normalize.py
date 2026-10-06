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

import os
import re

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
    src = pkg.path.replace("\\", "/").rsplit("/", 1)[-1]
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

# Normalized collection -> the "$type" values observed in real artifacts.
#
# Note the emitted "$type" is a *semantic* name ("entity", "field"), not the CLR
# record-type key the embedded profile is indexed by ("Barsa.Meta.TypeDef").
# Mapping on the profile keys alone matches nothing in an actual artifact.
AI_TYPE_TO_COLLECTION = {
    "system": "system",
    "entity": "entities",
    "field": "fields",
    # An AiExport "relation" is a relation *field* declared on an entity: it
    # carries target, dbName and fieldType. Its legacy counterpart is a
    # FieldDef with relationType set, or a RelationDef -- NOT a met_Relation
    # row, which is an instance link between two objects. Mapping it to
    # `relations` would compare definitions against instances and invent
    # differences, so it goes to `relationDefs`.
    "relation": "relationDefs",
    "report": "reports",
    "view": "views",
    "navigationRoot": "navigation",
    "navigationGroup": "navigation",
    "navigationPage": "navigation",
    "navigationReport": "navigation",
    "Barsa.Meta.MetaCode": "code",
}

# Observed "$type" values that are instances of user-defined dynamic entities
# rather than metamodel records. They are kept under `extensions`, grouped by
# type, rather than being dropped or forced into a metamodel collection.
AI_SCALAR_FIELD_TYPES = ("string", "int", "long", "decimal", "bool",
                         "boolean", "date", "dateTime", "text", "customField")

_CAPTION_KEYS = ("$caption", "caption", "Caption", "name", "Name")
_NAME_KEYS = ("DbName", "dbName", "name", "Name")


def _first(obj, keys):
    for k in keys:
        v = obj.get(k)
        if v not in (None, ""):
            return v
    return None


def from_ai_export(artifact, profile=None):
    """AiExport artifact -> normalized model (spec v3 sections 44, 86).

    Both physical variants reduce to the same shape, which is what section 86
    asks for: Normalize(SingleJson) and Normalize(ZipJson) must agree for the
    same scope.
    """
    env = empty_envelope()
    src = artifact.path.replace("\\", "/").rsplit("/", 1)[-1]
    fmt = "Barsa.AiExport"

    buckets = {}
    unmapped = {}
    nav_locations = {}
    for src_file, doc in artifact.files.items():
        if src_file == "_assets":
            continue
        if os.path.basename(src_file).lower() == "manifest.json":
            continue
        nav_locations.update(_navigation_locations(doc))
        for obj, path, owner in _iter_ai_objects_with_path(doc, "$"):
            t = obj.get("$type")
            if not isinstance(t, str):
                continue
            coll = AI_TYPE_TO_COLLECTION.get(t)
            if coll is None:
                unmapped.setdefault(t, []).append(
                    {"id": obj.get("id"), "selector": obj.get("selector"),
                     "caption": _first(obj, _CAPTION_KEYS),
                     "source": {"file": src_file, "path": path}})
                continue
            buckets.setdefault(coll, []).append(
                (src_file, path, obj, owner))

    for coll, items in buckets.items():
        env[coll] = []
        for src_file, path, obj, owner in items:
            node = {
                "id": _str_or_none(obj.get("id")),
                "selector": obj.get("selector"),
                "caption": _first(obj, _CAPTION_KEYS),
                "name": _first(obj, _NAME_KEYS),
                "_provenance": _prov(fmt, src, "%s :: %s" % (src_file, path),
                                     "Verified"),
                "_aiType": obj["$type"],
                "_ownerId": _str_or_none(owner),
            }
            if coll == "fields":
                # AiExport carries the field's data type outright. The legacy
                # format hides it inside the FieldInfo blob, so this is the one
                # place AiExport is strictly more informative.
                node["dataType"] = obj.get("fieldType")
                node["dbName"] = obj.get("dbName")
                node["orderNumber"] = _int(obj.get("orderNumber"))
                node["nullable"] = None
                node["defaultValue"] = obj.get("defaultValue")
            elif coll == "relationDefs":
                node["relationType"] = obj.get("fieldType")
                node["targetSelector"] = obj.get("target")
                node["dbName"] = obj.get("dbName")
                node["orderNumber"] = _int(obj.get("orderNumber"))
            elif coll == "entities":
                node["dbName"] = obj.get("DbName")
                node["isDynamic"] = None
            elif coll == "reports":
                node["entitySelector"] = obj.get("entity")
                node["reportType"] = obj.get("reportType")
                # The legacy ReportData blob is opaque; here the query is
                # already decoded into columns plus a condition tree.
                cols = obj.get("columns")
                node["customColumns"] = (
                    [c.get("field") for c in cols if isinstance(c, dict)]
                    if isinstance(cols, list) else None)
                node["query"] = ("decoded" if obj.get("condition") is not None
                                 else None)
            elif coll == "navigation":
                node["objectType"] = "folder"
                node["kind"] = obj.get("kind")
                node["reportSelector"] = obj.get("report")
                node.update(nav_locations.get(id(obj), {}))
            env[coll].append(node)

    # The ZIP variant encodes navigation as directory structure rather than as
    # navigation records: a folder becomes a directory and a report placement
    # becomes a JSON file inside it. Without reading the paths, a legacy
    # MET_FOLDER row set looks entirely absent from the AiExport side.
    folder_nav = _navigation_from_paths(artifact, fmt, src)
    if folder_nav:
        existing = env.get("navigation") or []
        have = {(n.get("selector"), n.get("name")) for n in existing}
        for n in folder_nav:
            if (n.get("selector"), n.get("name")) not in have:
                existing.append(n)
        env["navigation"] = existing

    # Likewise code: the profile's "code-file-if-large" transform keeps short
    # code inline on the owning field instead of emitting a MetaCode record.
    inline_code = _inline_code(artifact, fmt, src)
    if inline_code:
        existing = env.get("code") or []
        existing.extend(inline_code)
        env["code"] = existing

    if unmapped:
        env["extensions"] = {
            "unmappedTypes": {
                t: {"count": len(v), "samples": v[:5]}
                for t, v in sorted(unmapped.items())
            },
            "note": ("These $type values have no normalized-collection "
                     "mapping. Most are instances of user-defined dynamic "
                     "entities or UI settings objects. They are recorded here "
                     "rather than dropped, and rather than being forced into a "
                     "metamodel collection."),
        }

    env["_availability"] = {}
    for coll in EMPTY_ENVELOPE_KEYS:
        present = coll in buckets
        entry = {
            "presentInArtifact": present,
            "rowCount": len(buckets.get(coll, ())) if present else None,
            "status": "Verified" if present else "NotObservedInThisArtifact",
        }
        if coll == "relations":
            entry["note"] = (
                "Legacy met_Relation rows are instance links between objects. "
                "No AiExport $type was observed carrying those; AiExport "
                "projects relation *definitions* (as entity fields) instead. "
                "Recorded as a representation difference, not as data loss.")
        env["_availability"][coll] = entry

    env["_source"] = {
        "format": fmt,
        "file": src,
        "sha256": artifact.format.get("sha256"),
        "variant": artifact.variant,
        "manifest": artifact.manifest,
        "typeCatalog": [e["type"] for e in artifact.type_catalog()],
        "jsonFiles": len([k for k in artifact.files if k != "_assets"]),
    }
    return env


# Group folders the profile declares; a path segment in brackets is a group
# marker, not a user-visible folder name.
_GROUP_SEGMENT = re.compile(r"^\[.*\]$")


def _navigation_locations(doc):
    """Carry the observed navigation hierarchy without creating selectors."""
    locations = {}

    def walk(value, parents=()):
        if isinstance(value, dict):
            kind = value.get("$type")
            next_parents = parents
            if kind in ("navigationRoot", "navigationPage",
                        "navigationGroup", "navigationReport"):
                name = value.get("name")
                if kind == "navigationReport":
                    name = value.get("report")
                next_parents = parents + ((name,) if name else ())
                locations[id(value)] = {
                    "path": "/".join(next_parents) or None,
                    "parentPath": "/".join(parents) or None,
                }
            for child in value.values():
                walk(child, next_parents)
        elif isinstance(value, list):
            for child in value:
                walk(child, parents)

    walk(doc)
    return locations


def _navigation_from_paths(artifact, fmt, src):
    """Reconstruct navigation nodes from a ZIP package's directory layout."""
    if artifact.variant != "AiExport.ZipJsonPackage":
        return []
    nav = []
    seen = set()
    for name in sorted(artifact.files):
        if name in ("_assets",) or os.path.basename(name).lower() == "manifest.json":
            continue
        parts = name.split("/")
        # Locate the navigation group folder, whose name the profile gives as
        # packaging.relationGroups[].folder for the main-folder relation.
        try:
            gi = next(i for i, seg in enumerate(parts)
                      if _GROUP_SEGMENT.match(seg) and "پوشه" in seg)
        except StopIteration:
            continue
        chain = parts[gi + 1:]
        for depth in range(len(chain)):
            seg = chain[depth]
            is_leaf = depth == len(chain) - 1
            label = os.path.splitext(seg)[0] if is_leaf else seg
            key = "/".join(chain[:depth + 1])
            if key in seen:
                continue
            seen.add(key)
            nav.append({
                "id": None,
                "selector": None,
                "objectType": "folder",
                "caption": label,
                "name": label,
                "path": "/".join(chain[:depth + 1]),
                "parentPath": "/".join(chain[:depth]) or None,
                "reportSelector": (artifact.files.get(name) or {}).get("selector")
                if is_leaf and isinstance(artifact.files.get(name), dict)
                else None,
                "isReportPlacement": is_leaf,
                "_derivedFrom": "packageDirectoryStructure",
                "_provenance": _prov(
                    fmt, src, name,
                    # The node is read off a real path, but that a directory
                    # corresponds to a MET_FOLDER row is a reading of the
                    # layout, not a declared mapping.
                    "Observed"),
            })
    return nav


_CODE_KEYS = ("code", "Code")


def _inline_code(artifact, fmt, src):
    """Code carried inline on a record rather than as a MetaCode record."""
    out = []
    for src_file, doc in artifact.files.items():
        if src_file == "_assets":
            continue
        for obj, path, owner in _iter_ai_objects_with_path(doc, "$"):
            formula = obj.get("formula")
            if isinstance(formula, dict) and formula.get("code"):
                out.append({
                    "id": None,
                    "selector": obj.get("selector"),
                    "caption": _first(obj, _CAPTION_KEYS),
                    "name": None,
                    "targetObjectId": _str_or_none(obj.get("id")),
                    "codeKind": formula.get("type"),
                    "executionTime": formula.get("executionTime"),
                    # Code text itself is not copied into dist/.
                    "code": None,
                    "codeLength": len(formula["code"]),
                    "_derivedFrom": "inlineFormula",
                    "_provenance": _prov(fmt, src,
                                         "%s :: %s.formula" % (src_file, path),
                                         "Verified"),
                })
    return out


def _str_or_none(v):
    return None if v is None else str(v)


def _iter_ai_objects_with_path(node, path, depth=0, owner=None):
    """Yield (object, json path, owning record id) for every object.

    The owner is the id of the nearest enclosing record that has one. Fields
    are nested inside their entity, so this is how a field learns which entity
    it belongs to -- which in turn makes its dbName ("F1", "F2") usable as an
    identity key, since those names repeat across entities.
    """
    if depth > 40:
        return
    if isinstance(node, dict):
        yield node, path, owner
        child_owner = node.get("id") if node.get("id") is not None else owner
        for k, v in node.items():
            for item in _iter_ai_objects_with_path(
                    v, "%s.%s" % (path, k), depth + 1, child_owner):
                yield item
    elif isinstance(node, list):
        for v in node:
            for item in _iter_ai_objects_with_path(
                    v, path + "[*]", depth + 1, owner):
                yield item


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
