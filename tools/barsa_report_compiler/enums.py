"""Selecting the enums a report author actually needs.

dist/ carries 54 enums from the embedded export profile. Most describe field
widgets or workflow shapes and have nothing to do with authoring a report, so
carrying them all would spend the size budget on noise.
"""

# Enums kept, with why each one is relevant. A name not listed is dropped, and
# `dropped` in the result says how many, so the selection is visible rather
# than silent.
RELEVANT = {
    "Barsa.Meta.ReportTypeEnum": "the kind of report",
    "Barsa.Meta.ReportPagingType": "the pagingType property",
    "Barsa.Meta.GridViewStyleEnum": "the gridViewStyle property",
    "Barsa.Meta.GridAlternateRowModeEnum": "the alternateRowMode property",
    "Barsa.Meta.CalendarTypeEnum": "the calendar property",
    "Barsa.Meta.AggreationTypeEnum": "aggregation in grouping and summary rows",
    "Barsa.Meta.CombinationOperator": "how condition clauses combine",
    "Barsa.Meta.ComparisonOperator": "how a single condition clause compares",
    "Barsa.Meta.ChartTypeEnum": "charts on a dashboard report",
    "Barsa.Meta.FolderType": "where a report is placed in the navigator",
    "Barsa.Meta.FieldInfoTypeEnum": "what a field is, when choosing columns",
    "Barsa.Meta.DisplayTypeEnum": "how a value is displayed",
    "Barsa.Meta.RightToLeftEnum": "column direction",
    "Barsa.Meta.GroupStyle2": "grouping presentation",
}

# Enums whose recovered member list is too small to be the whole story. Saying
# so is the point: a reader must not conclude the engine supports only these.
SUSPICIOUSLY_SMALL = {
    "Barsa.Meta.ComparisonOperator": (
        "One member only (AdvancedTextSearch2). Far too few for a condition "
        "engine, so the real operator set is almost certainly elsewhere and "
        "the profile maps just this one. Treat the operator vocabulary as "
        "Unknown."),
}


def build(dist):
    available = dist.enums
    kept = {}
    notes = []
    for name, why in sorted(RELEVANT.items()):
        members = available.get(name)
        if members is None:
            notes.append({"enum": name, "status": "NotInDist",
                          "relevance": why})
            continue
        kept[name] = {
            "members": {str(k): v for k, v in sorted(
                members.items(), key=lambda kv: _as_int(kv[0]))},
            "memberCount": len(members),
            "relevance": why,
            "caveat": SUSPICIOUSLY_SMALL.get(name),
            "confidence": "Verified",
        }
    return {
        "enums": kept,
        "keptCount": len(kept),
        "availableInDist": len(available),
        "droppedCount": max(0, len(available) - len(kept)),
        "notInDist": notes,
        "provenance": ("dist/index/ai-export-properties.json -> enums, which "
                       "the Extractor read from the embedded AI export "
                       "profile"),
        "selectionBasis": ("Hand-picked for the report-authoring task. The "
                           "selection is a judgement about relevance, not a "
                           "fact about Barsa."),
    }


def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 1 << 30
