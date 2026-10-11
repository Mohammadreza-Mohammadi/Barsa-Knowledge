"""The JSON value shapes of a report's structured properties.

The semantic contract says `columns` is writable; it does not say what a
column *is*. The normalized samples are no help either -- they drop the
payload, because on the legacy side it lives inside the opaque
`met_Report.ReportData` blob whose decoder was never run.

The one place in dist/ that records these shapes is the observed-path table of
the AiExport documents: every key seen in a supplied artifact, with its JSON
types and how often it occurred. That is evidence about **keys**, never about
values -- so a key set recovered here is Observed, and the vocabulary of the
string values under it stays Unknown.
"""

# The report object appears at two roots across the two artifacts: inline in
# the SingleJson tree, and as its own file in the ZIP projection, where the
# report *is* the document root.
#
# Only the first root is self-identifying. The bare `$` root is shared by every
# per-file document in the ZIP -- entities, views, folders -- so a key seen
# there is not necessarily a report's. It is therefore used only to corroborate
# a property the MetaReport root already named, never to introduce one.
ROOT_REPORT = "$.tree[*].MetaReport[*]"
ROOT_FILE = "$"
ROOTS = (ROOT_REPORT, ROOT_FILE)

# Structured properties worth spelling out, with what each one is for.
STRUCTURED = {
    "columns": "which fields become columns, and under what heading",
    "condition": "which rows survive",
    "parameters": "operator-supplied parameters",
    "sorting": "row order",
    "grouping": "row grouping",
    "sqlGrouping": "grouping pushed into SQL",
    "matrix": "the matrix (cross-tab) layout",
    "formatConditions": "conditional formatting",
    "subReports": "nested reports",
    "joinAliases": "aliases for joined tables",
    "calendar": "the calendar layout",
}


def build(dist, contract):
    """Observed key shapes per report property, plus what was never seen."""
    writable = set()
    for g in contract["groups"]:
        for m in g["properties"]:
            if m.get("presentInContract", True):
                writable.add(m["property"])

    # property -> relative path -> row.
    props = {}
    for root in ROOTS:
        corroborate_only = root == ROOT_FILE
        for row in dist.observed_paths(root):
            rel = row["path"][len(root):]
            if not rel.startswith("."):
                continue
            rel = rel[1:]
            head = rel.split(".", 1)[0].split("[", 1)[0]
            if not head:
                continue
            if corroborate_only and head not in props:
                continue
            entry = props.setdefault(head, {})
            prev = entry.get(rel)
            if prev is None or row["occurrences"] > prev["occurrences"]:
                entry[rel] = dict(row, relativePath=rel)

    observed_props = sorted(props)
    shapes = []
    for name, purpose in sorted(STRUCTURED.items()):
        rows = props.get(name)
        if not rows:
            shapes.append({
                "property": name,
                "purpose": purpose,
                "status": "NotObserved",
                "keys": [],
                "confidence": "Unknown",
            })
            continue
        keys = [{"path": r["relativePath"], "types": r["types"],
                 "occurrences": r["occurrences"], "nullable": r["nullable"]}
                for r in sorted(rows.values(), key=lambda r: r["relativePath"])]
        shapes.append({
            "property": name,
            "purpose": purpose,
            "status": "Observed",
            "keys": keys,
            "example": _EXAMPLES.get(name),
            "valueVocabulary": "Unknown",
            "confidence": "Observed",
        })

    return {
        "shapes": shapes,
        "notObservedNote": ("No supplied artifact carried the property, so "
                            "its value shape is Unknown. Not observed is not "
                            "the same as unsupported: the contract lists it "
                            "as writable."),
        "valueVocabularyNote": ("The observed-path table records keys and "
                                "JSON types, never values. Any string value "
                                "under an observed key -- an operator name, a "
                                "parameter kind -- is Unknown from dist/."),
        "observedProperties": observed_props,
        "observedAndWritable": sorted(set(observed_props) & writable),
        "writableNeverObserved": sorted(writable - set(observed_props)),
        "neverObservedNote": (
            "A writable property that no artifact carried. The exporter omits "
            "a property at its default, so absence here is weak evidence of "
            "anything except that these were not exercised by the two "
            "supplied systems."),
        "roots": {"naming": ROOT_REPORT, "corroboratingOnly": ROOT_FILE},
        "confidence": "Observed",
        "provenance": ("dist/formats/ai-export-single-json.md -> Observed "
                       "paths, which the Extractor built by walking the "
                       "supplied AiExport artifacts"),
    }


# Shapes written out as JSON, each one a direct transcription of the key set
# above -- no key appears in an example that the table does not carry.
_EXAMPLES = {
    "columns": [{"field": "#<field>", "alias": "Heading"}],
    "condition": {"all": [{"field": "#<field>", "operator": "<Unknown>",
                           "value": None}]},
    "parameters": [{"name": "<name>", "caption": "<caption>",
                    "field": "#<field>", "kind": "<Unknown>"}],
}


def legacy_report_columns(dist):
    """The met_Report column table, for the comprehension consumer."""
    doc = dist.text.get("legacyReportTable")
    if not doc:
        return {"columns": [], "status": "NotInDist"}
    cols = []
    for line in doc.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        cols.append({
            "column": cells[0].strip("`"),
            "xsdType": cells[1],
            "nullable": cells[2],
            "reading": cells[3] or None,
        })
    return {
        "table": "met_Report",
        "columns": cols,
        "confidence": "Verified",
        "provenance": "dist/formats/report-format.md",
    }
