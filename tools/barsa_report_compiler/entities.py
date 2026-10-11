"""Per-system entity model, assembled from dist/'s full semantic indexes."""

COLLECTIONS = ("entities", "fields", "relationDefs", "reports", "views",
               "navigation")


def discover_systems(dist):
    """Every system id mentioned by any normalized sample, with its sources."""
    systems = {}
    for name, doc in _documents(dist):
        fmt = (doc.get("_source") or {}).get("format")
        for s in (doc.get("system") or ()):
            sid = s.get("id")
            if not sid:
                continue
            entry = systems.setdefault(sid, {
                "systemId": sid,
                "captions": [],
                "selectors": [],
                "sources": [],
                "formats": set(),
            })
            if s.get("caption") and s["caption"] not in entry["captions"]:
                entry["captions"].append(s["caption"])
            if s.get("selector") and s["selector"] not in entry["selectors"]:
                entry["selectors"].append(s["selector"])
            entry["sources"].append({"sample": name, "format": fmt})
            entry["formats"].add(fmt)
    out = []
    for sid, e in sorted(systems.items()):
        e["formats"] = sorted(f for f in e["formats"] if f)
        e["authorable"] = "Barsa.AiExport" in e["formats"]
        out.append(e)
    return out


def build(dist, system_id):
    """Assemble the model for one system."""
    systems = {s["systemId"]: s for s in discover_systems(dist)}
    info = systems.get(system_id)
    if info is None:
        return None

    ai_entities, legacy_entities = {}, {}
    ai_fields, legacy_fields = {}, {}
    ai_reports, legacy_reports = {}, {}
    views, relations, navigation = {}, {}, []
    truncation = {}
    contributing = []

    for name, doc in _documents(dist, system_id):
        fmt = (doc.get("_source") or {}).get("format")
        sample_systems = [s.get("id") for s in (doc.get("system") or ())]
        if system_id not in sample_systems:
            continue
        contributing.append({"sample": name, "format": fmt,
                             "systemsInSample": len(sample_systems)})

        # An AiExport artifact covers exactly one system, so everything in it
        # belongs to that system. A legacy artifact can cover several, so its
        # objects must be filtered by the systemId they carry.
        single = len(sample_systems) == 1
        is_ai = fmt == "Barsa.AiExport"

        for coll in COLLECTIONS:
            marker = doc.get("_truncated_" + coll)
            if marker:
                truncation.setdefault(coll, []).append(
                    {"sample": name, **marker})

        ent_ids = set()
        for e in (doc.get("entities") or ()):
            if not single and e.get("systemId") != system_id:
                continue
            if e.get("id"):
                ent_ids.add(str(e["id"]))
                (ai_entities if is_ai else legacy_entities)[str(e["id"])] = e

        for f in (doc.get("fields") or ()):
            owner = f.get("entityId") or f.get("_ownerId")
            if not single and owner is not None and str(owner) not in ent_ids:
                continue
            if f.get("id"):
                (ai_fields if is_ai else legacy_fields)[str(f["id"])] = f

        for r in (doc.get("reports") or ()):
            if not single and r.get("systemId") != system_id:
                continue
            if r.get("id"):
                (ai_reports if is_ai else legacy_reports)[str(r["id"])] = r

        for v in (doc.get("views") or ()):
            if not single and str(v.get("entityId") or v.get("_ownerId")) not in ent_ids:
                continue
            if v.get("id"):
                views.setdefault(str(v["id"]), {}).update(
                    {k: v2 for k, v2 in v.items() if v2 is not None})

        for rd in (doc.get("relationDefs") or ()):
            if rd.get("id"):
                relations.setdefault(str(rd["id"]), {}).update(
                    {k: v for k, v in rd.items() if v is not None})

        for n in (doc.get("navigation") or ()):
            navigation.append(n)

    entities = _merge_entities(ai_entities, legacy_entities)
    fields = _merge_fields(ai_fields, legacy_fields, entities)

    return {
        "systemId": system_id,
        "captions": info["captions"],
        "selectors": info["selectors"],
        "authorable": info["authorable"],
        "authorableBasis": (
            "An AiExport artifact for this system is present, so selectors "
            "are known." if info["authorable"] else
            "No AiExport artifact for this system is present, so no selector "
            "is known. An authored batch cannot refer to these objects."),
        "contributingSamples": contributing,
        "entities": entities,
        "fields": fields,
        "reports": _merge_reports(ai_reports, legacy_reports),
        "views": sorted(views.values(),
                        key=lambda v: str(v.get("name") or v.get("id"))),
        "relationDefs": sorted(relations.values(),
                               key=lambda r: str(r.get("id"))),
        "navigationRowCount": len(navigation),
        "folders": _folders(navigation, system_id),
        "truncation": truncation,
        "complete": not truncation,
        "completenessNote": (
            "Every assignable row in the canonical system index was carried."
            if not truncation
            else ("The Extractor truncates normalized samples to 25 rows per "
                  "collection, so this model is PARTIAL. The counts below are "
                  "what dist/ carries, not what the system contains.")),
        "confidence": "Verified",
        "provenance": "dist/index/systems/%s/semantic.json" % system_id,
    }


def _documents(dist, system_id=None):
    """Expose full index rows as source envelopes for the existing merger."""
    out = []
    for sid, index in sorted(dist.systems.items()):
        if system_id and sid != system_id:
            continue
        for src in index.get("sources", []):
            name = src.get("file")
            fmt = src.get("format")
            doc = {"_source": {"file": name, "format": fmt},
                   "system": [s for s in index["systems"]
                              if (s.get("_provenance") or {}).get("source") == name]}
            for coll, rows in index["collections"].items():
                doc[coll] = [r for r in rows
                             if (r.get("_provenance") or {}).get("source") == name
                             and (r.get("_provenance") or {}).get("format") == fmt]
            out.append(("index/systems/%s/semantic.json" % sid, doc))
    return out


def _folders(navigation, system_id):
    out = []
    for row in navigation:
        if row.get("isReportPlacement") or row.get("_aiType") == "navigationReport":
            continue
        if row.get("_aiType") == "navigationRoot":
            continue
        if row.get("folderType") and row.get("folderType") != "12":
            continue
        out.append({
            "objectType": "folder", "systemId": system_id,
            "selector": row.get("selector"),
            "name": row.get("name"), "caption": row.get("caption") or row.get("name"),
            "kind": row.get("kind"), "path": row.get("path"),
            "parentPath": row.get("parentPath"),
            "stableReference": ({"kind": "navigationPath", "systemId": system_id,
                                 "path": row["path"]}
                                if row.get("path") and
                                (row.get("_provenance") or {}).get("format")
                                == "Barsa.AiExport" else None),
            "authorableReference": False,
            "referenceEvidence": (
                "dist/index/references.json: "
                "AiSemanticReferenceResolver.Resolve delegates to "
                "SemanticRules.ResolveObject; its observed cases omit folder"),
            "provenance": [row["_provenance"]] if row.get("_provenance") else [],
        })
    return out


def _merge_reports(ai, legacy):
    """Keep the two reportType vocabularies apart.

    A legacy export writes the numeric ReportTypeEnum value and an AiExport
    writes its own string. Merging them into one key produced a `reportType`
    of `0` next to a semantic selector, which is two vocabularies in one
    column and exactly the confusion REPORT-TYPES.md warns about.
    """
    out = []
    for rid in sorted(set(ai) | set(legacy)):
        a, l = ai.get(rid, {}), legacy.get(rid, {})
        out.append({
            "id": rid,
            "selector": a.get("selector"),
            "provenance": [p for p in (a.get("_provenance"),
                                       l.get("_provenance")) if p],
            # The AiExport caption is the one a selector is built from; the
            # legacy name may be spelled with different Arabic letter forms.
            "name": a.get("caption") or a.get("name"),
            "legacyName": l.get("name"),
            "reportType": a.get("reportType"),
            "legacyReportTypeValue": l.get("reportType"),
            "systemId": a.get("systemId") or l.get("systemId"),
            "inAiExport": bool(a),
            "inLegacy": bool(l),
        })
    return sorted(out, key=lambda r: str(r.get("name") or r.get("legacyName")
                                         or r["id"]))


def _merge_entities(ai, legacy):
    out = {}
    for eid in sorted(set(ai) | set(legacy)):
        a, l = ai.get(eid, {}), legacy.get(eid, {})
        out[eid] = {
            "id": eid,
            "provenance": [p for p in (a.get("_provenance"),
                                       l.get("_provenance")) if p],
            # Only AiExport carries a selector, and it is what an authored
            # batch needs; legacy supplies the physical names.
            "selector": a.get("selector"),
            "caption": a.get("caption") or l.get("caption"),
            "dbName": a.get("dbName") or l.get("dbName") or a.get("name")
                      or l.get("name"),
            "isDynamic": l.get("isDynamic"),
            "parentId": l.get("parentId"),
            "defaultReportId": l.get("defaultReportId"),
            "inAiExport": bool(a),
            "inLegacy": bool(l),
        }
    return sorted(out.values(), key=lambda e: str(e.get("caption") or e["id"]))


def _merge_fields(ai, legacy, entities):
    by_id = {e["id"]: e for e in entities}
    out = []
    for fid in sorted(set(ai) | set(legacy)):
        a, l = ai.get(fid, {}), legacy.get(fid, {})
        owner = str(l.get("entityId") or a.get("_ownerId") or "") or None
        out.append({
            "id": fid,
            "provenance": [p for p in (a.get("_provenance"),
                                       l.get("_provenance")) if p],
            "selector": a.get("selector"),
            "caption": a.get("caption") or l.get("caption"),
            "dbName": a.get("dbName") or l.get("dbName"),
            # AiExport states the field's type outright; legacy hides it in an
            # undecoded FieldInfo blob, so a legacy-only field has no type.
            "fieldType": a.get("dataType"),
            "fieldTypeSource": ("AiExport dataType" if a.get("dataType")
                                else None),
            "entityId": owner,
            "entityCaption": (by_id.get(owner) or {}).get("caption"),
            "entitySelector": (by_id.get(owner) or {}).get("selector"),
            "orderNumber": l.get("orderNumber") or a.get("orderNumber"),
            "usableAsColumn": bool(a.get("selector")),
            "usableAsColumnBasis": (
                "A column entry needs a field selector."
                if not a.get("selector") else None),
            "inAiExport": bool(a),
            "inLegacy": bool(l),
        })
    return sorted(out, key=lambda f: (str(f.get("entityCaption") or ""),
                                      f.get("orderNumber") or 0,
                                      str(f.get("caption") or "")))
