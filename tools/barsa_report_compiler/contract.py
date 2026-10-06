"""The report write contract, taken from dist/ and grouped by purpose.

The grouping is the one thing this compiler adds that dist/ does not state, so
it is reported as Inferred (spec section 7). Every named writable property must
land in exactly one group; `audit` fails the build otherwise, which is what
keeps the grouping honest as the contract changes.
"""

OBJECT_TYPE = "report"

# Group -> property names. Derived from property names and from the enums each
# one lines up with; no dist/ document states this partition.
GROUPS = [
    ("identity", "What the report is called and where it belongs.",
     ["name", "description", "systemId"]),
    ("shape", "Which kind of report this is, and what it renders over.",
     ["reportType", "typeView", "parameterEntity"]),
    ("data", "Where the rows come from.",
     ["columns", "customSql", "additionalWhere", "extraQueryTemplate",
      "alternateRootTable", "rootTableAlias", "joinAliases", "isDistinct",
      "top", "includeDeleted", "oracleHint", "ignoreColumns"]),
    ("filtering", "Which rows survive.",
     ["condition", "treeCondition", "useHierarchyConditionForRoot",
      "ignoreAdvancedSecurityCondition"]),
    ("shaping", "How rows are ordered, grouped and aggregated.",
     ["sorting", "grouping", "sqlGrouping", "matrix", "useSummaryRow"]),
    ("presentation", "How the result looks.",
     ["gridViewStyle", "gridLines", "gridHideLines", "gridGrouping",
      "gridShowGroupBox", "gridShowSelectionChecks", "gridCustomKey",
      "gridHideColumnsWhenGrouped", "freeColumnSizing", "alternateRowMode",
      "disableColumnHeaders", "hideHeader", "hideRowIcon", "hideToolbar",
      "showRowNumber", "calendar", "formatConditions",
      "showRecordSignFormatting", "showWpfChart"]),
    ("paging", "How many rows at a time.",
     ["pagingType", "pageSize", "dontExecuteCount"]),
    ("permissions", "What a viewer may do with a row.",
     ["allowView", "allowEdit", "allowAddNew", "allowRemove",
      "allowInlineEdit", "autoInlineEdit", "allowAddToList",
      "allowRemoveFromList", "allowGridColumnSort", "useAdvancedAccess"]),
    ("preview", "The preview pane.",
     ["previewField", "showPreviewField", "previewState"]),
    ("insideView", "The report embedded inside another form.",
     ["insideViewActive", "insideViewHeight", "insideViewRelatedField",
      "listEditView"]),
    ("behaviour", "Runtime behaviour that is not presentation.",
     ["immediateExecute", "sharedScope", "logExecutions",
      "preserveUserViewState", "disableOptimizeForDisplay",
      "dontUseChildParentReport", "selfReferencingField"]),
    ("tree", "Tree-shaped reports.", ["treeAutoOpenLevels"]),
    ("parameters", "Operator-supplied parameters.",
     ["parameters", "parameterPanelHeight"]),
    ("composition", "Reports built from other reports.", ["subReports"]),
    ("other", "No grouping could be justified from the name alone.",
     ["forum", "commandDisplayMode", "alternateEditObjectColumn"]),
]

# Report types, keyed by the CLR enum member name, with the properties whose
# names line up with them. Inferred: no dist/ document states which property
# applies to which report type (spec section 11).
TYPE_AFFINITY = {
    "TreeView": ["treeCondition", "treeAutoOpenLevels",
                 "useHierarchyConditionForRoot", "selfReferencingField"],
    "HetrogeniousTree": ["treeCondition", "treeAutoOpenLevels",
                         "useHierarchyConditionForRoot"],
    "HetrogeniousTree_NoneGraphical": ["treeCondition", "treeAutoOpenLevels"],
    "MatrixView": ["matrix", "sqlGrouping"],
    "CalendarView": ["calendar"],
    "Statistics": ["useSummaryRow", "grouping", "sqlGrouping"],
    "FormView": ["typeView", "listEditView"],
    "ForumView": ["forum"],
    "Dashboard": ["showWpfChart"],
}


def build(dist):
    """Assemble the report contract from dist/, grouped and annotated."""
    rows = dist.property_contracts(OBJECT_TYPE)
    obj = dist.object_contract(OBJECT_TYPE)

    by_name = {}
    anonymous = []
    for r in rows:
        if r.get("property"):
            by_name.setdefault(r["property"], r)
        else:
            anonymous.append(r)

    writable = {n: r for n, r in by_name.items()
                if r.get("classification") == "Writable"}
    non_writable = {n: r for n, r in by_name.items()
                    if r.get("classification") != "Writable"}

    grouped = []
    for name, purpose, props in GROUPS:
        members = []
        for p in props:
            r = writable.get(p)
            if r is None:
                # Reported, not silently dropped: a group naming a property the
                # contract no longer has is a drift the audit must see.
                members.append({"property": p, "presentInContract": False})
                continue
            # `presentInContract` is written only when it is False: a row
            # that is present says so by carrying contract data, and the flag
            # on all 80 of them cost 2 KB of a 120 KB budget.
            members.append({
                "property": p,
                "kind": r.get("kind"),
                "writableOnCreate": r.get("writableOnCreate"),
                "writableOnUpdate": r.get("writableOnUpdate"),
                "referenceTargetType": r.get("referenceTargetType"),
            })
        grouped.append({"group": name, "purpose": purpose,
                        "properties": members})

    return {
        "objectType": OBJECT_TYPE,
        "objectContract": obj,
        "groups": grouped,
        "groupingConfidence": "Inferred",
        "propertyWriterNote": ("Every writable property is applied by the "
                               "writer named in `writer` below; the per-row "
                               "value was identical on all of them and is "
                               "stated once rather than 80 times."),
        "groupingBasis": ("Property names and the enums they line up with. No "
                          "dist/ document states this partition."),
        "writableCount": len(writable),
        "nonWritable": [
            {"property": n, "classification": r.get("classification"),
             "kind": r.get("kind"), "runtimeSource": r.get("runtimeSource")}
            for n, r in sorted(non_writable.items())],
        "anonymousContracts": [
            {"factory": r.get("factory"), "kind": r.get("kind"),
             "runtimeSource": r.get("runtimeSource"),
             "writer": r.get("writer"),
             "note": ("The RawJson factory takes no property name, so this "
                      "contract covers a raw JSON payload rather than a named "
                      "property.")}
            for r in anonymous],
        "writer": sorted({r.get("writer") for r in rows if r.get("writer")}),
        "confidence": "Verified",
        "provenance": "dist/index/semantic-contract.json -> propertyContracts.report",
    }


def report_types(dist, contract):
    """Report types, with the Inferred property affinity and the open mapping."""
    enum = dist.enums.get("Barsa.Meta.ReportTypeEnum") or {}
    observed = _observed_report_types(dist)
    writable = set()
    for g in contract["groups"]:
        for m in g["properties"]:
            if m.get("presentInContract", True):
                writable.add(m["property"])

    types = []
    for value, member in sorted(enum.items(), key=lambda kv: int(kv[0])):
        affinity = [p for p in TYPE_AFFINITY.get(member, []) if p in writable]
        types.append({
            "enumValue": int(value),
            "enumMember": member,
            "affineProperties": affinity,
            "affinityConfidence": "Inferred" if affinity else "Unknown",
            # Everything not named above is Unknown for this type, not
            # "not applicable" (spec section 11).
            "otherPropertiesStatus": "Unknown",
        })

    return {
        "clrEnum": "Barsa.Meta.ReportTypeEnum",
        "clrMembers": types,
        "aiExportVocabulary": observed,
        "vocabularyMapping": {
            "status": "Inferred",
            "note": ("The AiExport projection writes its own reportType "
                     "vocabulary, which is not the CLR enum member names. The "
                     "mapping below rests on two observations and nothing "
                     "else."),
            "candidates": [
                {"aiExport": "list", "clrCandidate": "ViewResults",
                 "confidence": "Inferred",
                 "basis": "a list-shaped report in both supplied artifacts"},
                {"aiExport": "form", "clrCandidate": "FormView",
                 "confidence": "Inferred",
                 "basis": ("a report carrying typeView in the Push "
                           "Notification artifact")},
            ],
            "unmapped": [v for v in observed
                         if v not in ("list", "form")],
        },
        "affinityConfidence": "Inferred",
        "affinityBasis": ("Name correspondence only. No dist/ document states "
                          "which property applies to which report type; that "
                          "lives in AiReportChangeProvider.ApplyReportPatch, "
                          "which has not been decompiled."),
    }


def _observed_report_types(dist):
    """reportType values actually seen in the normalized AiExport samples."""
    seen = set()
    for _name, doc in dist.samples:
        if (doc.get("_source") or {}).get("format") != "Barsa.AiExport":
            continue
        for rep in (doc.get("reports") or ()):
            v = rep.get("reportType")
            if isinstance(v, str) and v:
                seen.add(v)
    return sorted(seen)


def field_types(dist):
    """Field subtypes, and what dist/ can and cannot say about columns.

    A column names a field by selector, so the field catalogue matters when
    choosing columns. Which subtypes may legitimately *be* a column is a
    different question, and dist/ does not answer it: the contract classifies
    properties, not column eligibility.
    """
    rows = dist.property_contracts("field")
    subtypes = {}
    shared = []
    for r in rows:
        if not r.get("property"):
            continue
        subs = r.get("subtypes") or []
        if not subs:
            if r.get("classification") == "Writable":
                shared.append(r["property"])
            continue
        for s in subs:
            subtypes.setdefault(s, []).append(r["property"])

    return {
        "subtypes": [
            {"subtype": s,
             "ownProperties": sorted(set(props)),
             "usableAsReportColumn": "Unknown"}
            for s, props in sorted(subtypes.items())],
        "usableAsReportColumnBasis": (
            "Unknown for every subtype, and stated once here rather than per "
            "row: the contract classifies field properties and says nothing "
            "about which field subtypes may be a report column, and no "
            "artifact in dist/ pairs a column with its field's subtype."),
        "sharedProperties": sorted(set(shared)),
        "subtypeCount": len(subtypes),
        "columnReference": {
            "shape": "columns[*].field is a semantic selector, not an id",
            "resolvesTo": "a FieldDef under the report's own entity",
            "confidence": "Observed",
            "basis": ("columns[*].field is a string in every one of the 149 "
                      "observed column rows; the field contract's identity is "
                      "'FieldDef.Id under entity'."),
        },
        "relationColumns": {
            "status": "Unknown",
            "note": ("Whether a column may name a field reached through a "
                     "relation is not stated anywhere in dist/, and no "
                     "observed column does so provably. Unknown, not "
                     "unsupported."),
        },
        "confidence": "Verified",
        "provenance": ("dist/index/semantic-contract.json -> "
                       "propertyContracts.field"),
    }


def report_type_pairings(dist):
    """Report ids seen on both sides, with the two reportType values each had.

    A report that appears in a legacy artifact and in an AiExport artifact
    under the same id pairs the numeric ReportTypeEnum value with the AiExport
    string. That is corroboration for the vocabulary mapping, from data rather
    than from name resemblance -- but it is not a promotion: the two artifacts
    are not a same-build pair, so a value could in principle have been
    reassigned between them.
    """
    ai, legacy = {}, {}
    for _name, doc in dist.samples:
        fmt = (doc.get("_source") or {}).get("format")
        bucket = ai if fmt == "Barsa.AiExport" else legacy
        for r in (doc.get("reports") or ()):
            if r.get("id") is None or r.get("reportType") is None:
                continue
            bucket[str(r["id"])] = r["reportType"]

    pairs = {}
    for rid, ai_value in sorted(ai.items()):
        if rid not in legacy:
            continue
        key = (str(ai_value), str(legacy[rid]))
        row = pairs.setdefault(key, {"aiExport": key[0],
                                     "legacyEnumValue": key[1],
                                     "reportIds": []})
        row["reportIds"].append(rid)

    out = sorted(pairs.values(),
                 key=lambda r: (-len(r["reportIds"]), r["aiExport"]))
    for row in out:
        row["matchCount"] = len(row["reportIds"])
        row["reportIds"] = row["reportIds"][:5]
    return {
        "pairings": out,
        "idsOnBothSides": len(set(ai) & set(legacy)),
        "confidence": "Observed",
        "caveat": ("Matched by report id across artifacts that are not a "
                   "same-build pair. A pairing is evidence, not proof: the "
                   "two sides were exported months apart, so a report could "
                   "have been edited in between."),
        "provenance": "dist/models/normalized-samples/",
    }
