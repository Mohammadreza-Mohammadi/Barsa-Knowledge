"""Per-system entity model, assembled from dist/'s normalized samples.

Two things make this delicate.

First, the Extractor truncates each normalized sample to 25 rows per
collection, so a large system's model is partial. The samples carry
`_truncated_<collection>` markers, which are read here and surfaced rather than
ignored -- a model that silently showed 25 of 2285 fields would be worse than
no model.

Second, only the AiExport side carries selectors, and a selector is the only
way an authored batch can refer to an existing object. So a system is
report-authorable only when an AiExport artifact for it exists. Legacy-only
systems still get a model, marked as not authorable.
"""

COLLECTIONS = ("entities", "fields", "relationDefs", "reports", "views",
               "navigation")


def discover_systems(dist):
    """Every system id mentioned by any normalized sample, with its sources."""
    systems = {}
    for name, doc in dist.samples:
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

    for name, doc in dist.samples:
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
        "truncation": truncation,
        "complete": not truncation,
        "completenessNote": (
            "Every contributing sample was carried whole." if not truncation
            else ("The Extractor truncates normalized samples to 25 rows per "
                  "collection, so this model is PARTIAL. The counts below are "
                  "what dist/ carries, not what the system contains.")),
        "confidence": "Verified",
        "provenance": "dist/models/normalized-samples/",
    }


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
