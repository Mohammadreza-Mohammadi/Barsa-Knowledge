"""The build gates: budget, grouping coverage, confidence, provenance, gaps.

Each check here can fail the build. That is the point of the spec: a pack that
grows quietly, promotes a confidence quietly, or hides an Unknown quietly is
worse than no pack, because a consumer cannot tell.
"""

import json

# Spec section 4.
BUDGET_TOTAL = 512000
BUDGET_LARGEST_FILE = 153600
BUDGET_CONTRACT_ONLY = 122880

# Spec section 4's exception: these two grow with the entity count, so they are
# capped per system instead of counting against the whole-pack total.
PER_SYSTEM_EXEMPT = ("index/entity-model.json", "index/selectors.json")

CONFIDENCE_ORDER = ["Unknown", "Inferred", "Observed", "Verified",
                    "CrossVerified"]

# Seeded gap rows: things the report task needs that dist/ does not carry and
# that no renderer happens to touch. Everything else is added by the renderers
# as they write an Unknown, so this list stays short by design.
SEEDED = [
    {
        "topic": "The print template format (PrintView / Stimulsoft .mrt)",
        "neededFor": ["the PrintView report type cannot be described at all"],
        "whereToLook": ("A .mrt sample, or the Stimulsoft report definition "
                        "written into met_Report.ReportData. source/ carries "
                        "the Stimulsoft assemblies but no template."),
        "evidenceOfAbsence": ("dist/formats/report-format.md calls ReportData "
                              "an opaque blob and says an .mrt payload is "
                              "plausible but unconfirmed."),
        "blocks": "Nothing in print layout can be authored or explained.",
    },
    {
        "topic": ("Whether the legacy ReportData carries the same information "
                  "as the AiExport projection"),
        "neededFor": ["it is not known whether either side is lossy"],
        "whereToLook": ("Decode SerializeReportData for one report and "
                        "compare it field by field with the same report in an "
                        "AiExport artifact of the same build."),
        "evidenceOfAbsence": ("The two families were compared at object "
                              "level, never inside a report's definition, "
                              "because the legacy side is an undecoded blob."),
        "blocks": ("A consumer cannot tell whether a property absent from an "
                   "AiExport artifact is absent from the report or merely not "
                   "projected."),
    },
]


class AuditError(Exception):
    """A build gate failed."""


def _rank(level):
    try:
        return CONFIDENCE_ORDER.index(level)
    except ValueError:
        return -1


# -- the checks ------------------------------------------------------------

def check_grouping(contract):
    """Every named writable property in exactly one group (spec section 26)."""
    seen = {}
    drift = []
    for g in contract["groups"]:
        for m in g["properties"]:
            if not m.get("presentInContract", True):
                drift.append({"group": g["group"], "property": m["property"]})
                continue
            seen.setdefault(m["property"], []).append(g["group"])

    duplicated = {p: gs for p, gs in seen.items() if len(gs) > 1}
    findings = []
    if duplicated:
        findings.append({"check": "grouping", "severity": "error",
                         "message": "property in more than one group",
                         "detail": duplicated})
    if drift:
        findings.append({
            "check": "grouping", "severity": "error",
            "message": ("a group names a property the contract no longer "
                        "carries; the grouping has drifted from dist/"),
            "detail": drift})
    if len(seen) != contract["writableCount"]:
        findings.append({
            "check": "grouping", "severity": "error",
            "message": ("%d writable properties in the contract, %d grouped"
                        % (contract["writableCount"], len(seen))),
            "detail": None})
    return findings, {"grouped": len(seen),
                      "writable": contract["writableCount"],
                      "duplicated": len(duplicated), "drift": len(drift)}


def check_inferences(parts):
    """The two Inferred additions must still carry content.

    This guard exists because a refactor once emptied the type affinity
    silently: every row fell back to Unknown and no other check noticed,
    because declaring everything Unknown passes an honesty check trivially.
    Hiding knowledge is as much a defect as inventing it.
    """
    from . import contract as contract_mod
    findings = []
    published = {t["enumMember"]: t["affineProperties"]
                 for t in parts["types"]["clrMembers"]}
    empty = sorted(m for m in contract_mod.TYPE_AFFINITY
                   if not published.get(m))
    if empty:
        findings.append({
            "check": "inference", "severity": "error",
            "message": ("the type affinity table names properties for these "
                        "report types but published none: %s"
                        % ", ".join(empty)),
            "detail": None})
    grouped = sum(len(g["properties"]) for g in parts["contract"]["groups"])
    if grouped < parts["contract"]["writableCount"]:
        findings.append({
            "check": "inference", "severity": "error",
            "message": "the grouping published %d rows for %d properties"
                       % (grouped, parts["contract"]["writableCount"]),
            "detail": None})
    return findings, {"typesWithAffinity": sum(1 for v in published.values()
                                               if v),
                      "groupedRows": grouped}


def check_recipes(built, scope):
    """Spec section 18 and decision 15: a warning fails the build too."""
    findings = []
    for r in built["recipes"]:
        for f in r["lint"]["errors"]:
            findings.append({"check": "recipe", "severity": "error",
                             "message": "%s (%s): %s"
                                        % (r["id"], scope, f.get("message")),
                             "detail": f})
        for f in r["lint"]["warnings"]:
            findings.append({"check": "recipe", "severity": "error",
                             "message": "%s (%s) has a linter warning: %s"
                                        % (r["id"], scope, f.get("message")),
                             "detail": f})
    return findings, {"recipes": len(built["recipes"]),
                      "clean": sum(1 for r in built["recipes"]
                                   if r["lint"]["clean"])}


def check_confidence(dist, parts):
    """No fact may leave the compiler at a higher confidence than its source.

    Only two things in the pack are allowed to be the compiler's own, and both
    must be Inferred: the property grouping and the report-type affinity.
    """
    findings = []
    source = (dist.contract.get("confidence")
              or {"objectContracts": "Verified"})
    if isinstance(source, dict):
        src_level = source.get("objectContracts") or "Verified"
    else:
        src_level = source

    pub = parts["contract"]["confidence"]
    if _rank(pub) > _rank(src_level):
        findings.append({
            "check": "confidence", "severity": "error",
            "message": ("report contract published as %s but "
                        "dist/index/semantic-contract.json states %s"
                        % (pub, src_level)),
            "detail": None})

    for label, level in (("property grouping",
                          parts["contract"]["groupingConfidence"]),
                         ("report type affinity",
                          parts["types"]["affinityConfidence"])):
        if level != "Inferred":
            findings.append({
                "check": "confidence", "severity": "error",
                "message": ("%s is the compiler's own addition and must be "
                            "published as Inferred, not %s" % (label, level)),
                "detail": None})

    for s in parts["shapes"]["shapes"]:
        if s["status"] == "Observed" and _rank(s["confidence"]) > _rank(
                "Observed"):
            findings.append({
                "check": "confidence", "severity": "error",
                "message": ("shape of %s rests on observed artifacts and may "
                            "not be published above Observed" % s["property"]),
                "detail": None})
        if s["status"] == "NotObserved" and s["confidence"] != "Unknown":
            findings.append({
                "check": "confidence", "severity": "error",
                "message": ("%s was never observed, so its shape must be "
                            "Unknown" % s["property"]),
                "detail": None})
    return findings, {"sourceLevel": src_level, "published": pub}


def check_provenance(pack):
    """Every markdown file carries the three-line header; every JSON a block."""
    findings = []
    for path, content in sorted(pack.files.items()):
        if path.endswith(".md"):
            head = content.splitlines()[:6]
            for needle in ("> **Source:**", "> **dist commit:**",
                           "> **compiled:**"):
                if not any(l.startswith(needle) for l in head):
                    findings.append({
                        "check": "provenance", "severity": "error",
                        "message": "%s is missing its %s header line"
                                   % (path, needle.strip("> *:")),
                        "detail": None})
        elif path.endswith(".json"):
            try:
                doc = json.loads(content)
            except ValueError as exc:
                findings.append({"check": "provenance", "severity": "error",
                                 "message": "%s is not valid JSON: %s"
                                            % (path, exc), "detail": None})
                continue
            if not isinstance(doc, dict) or "_provenance" not in doc:
                findings.append({
                    "check": "provenance", "severity": "error",
                    "message": "%s has no _provenance block" % path,
                    "detail": None})
    return findings, {"files": len(pack.files)}


def check_budget(pack, budget_total=BUDGET_TOTAL):
    """Fail, do not grow (spec section 4)."""
    findings = []
    sizes = {p: len(c.encode("utf-8")) for p, c in pack.files.items()}
    exempt = {p: n for p, n in sizes.items()
              if p.startswith("systems/") and p.endswith(PER_SYSTEM_EXEMPT)}
    counted = {p: n for p, n in sizes.items() if p not in exempt}
    total = sum(counted.values())
    contract_only = sum(n for p, n in sizes.items()
                        if not p.startswith("systems/"))

    if total > budget_total:
        findings.append({
            "check": "budget", "severity": "error",
            "message": ("the pack is %d bytes, over the %d byte budget. The "
                        "fix is to carry less, not to raise the budget."
                        % (total, budget_total)),
            "detail": sorted(counted.items(), key=lambda kv: -kv[1])[:5]})
    for path, n in sorted(sizes.items()):
        cap = BUDGET_LARGEST_FILE
        if n > cap:
            findings.append({
                "check": "budget", "severity": "error",
                "message": "%s is %d bytes, over the %d byte per-file cap"
                           % (path, n, cap),
                "detail": None})
    if contract_only > BUDGET_CONTRACT_ONLY:
        findings.append({
            "check": "budget", "severity": "error",
            "message": ("the scope-independent part of the pack is %d bytes, "
                        "over the %d byte budget"
                        % (contract_only, BUDGET_CONTRACT_ONLY)),
            "detail": None})
    return findings, {
        "totalBytes": total,
        "exemptBytes": sum(exempt.values()),
        "contractOnlyBytes": contract_only,
        "largestFile": (max(sizes.items(), key=lambda kv: kv[1])
                        if sizes else None),
        "fileCount": len(sizes),
        "budget": {"total": budget_total,
                   "largestFile": BUDGET_LARGEST_FILE,
                   "contractOnly": BUDGET_CONTRACT_ONLY,
                   "perSystemExempt": list(PER_SYSTEM_EXEMPT)},
    }


def check_gaps(gaps):
    """Spec section 26: an empty register means the compiler hid something."""
    if len(gaps) == 0:
        return [{
            "check": "gaps", "severity": "error",
            "message": ("MISSING-FROM-DIST.md came out empty. Every Unknown "
                        "in this pack is supposed to register a gap, so an "
                        "empty register means the renderers stopped recording "
                        "-- not that dist/ became complete."),
            "detail": None}], {"gaps": 0}
    return [], {"gaps": len(gaps)}


# -- MISSING-FROM-DIST.md --------------------------------------------------

def render_missing(pack, gaps, meta):
    rows = SEEDED + gaps.rows()
    rows.sort(key=lambda r: r["topic"])
    body = [
        "What the report task needed and `dist/` does not carry, with where "
        "the Extractor should go looking.",
        "",
        "This file is **generated**: every place a renderer had to write "
        "Unknown registers a row here, so the list cannot drift from what the "
        "pack actually says. Two rows are seeded by hand, for gaps no "
        "renderer touches.",
        "",
        "A row here is a gap in the Extractor, never a licence to guess. "
        "Until a row is filled, the corresponding part of the pack says "
        "Unknown and a consumer must stop there.",
        "",
        "%d gap%s." % (len(rows), "" if len(rows) == 1 else "s"),
        "",
    ]
    for i, r in enumerate(rows, 1):
        body += ["## %d. %s" % (i, r["topic"]), ""]
        body += ["**Where this pack says Unknown**", ""]
        body += ["- " + n for n in r["neededFor"]] + [""]
        body += ["**Where to look**", "", r["whereToLook"], ""]
        body += ["**Why we can say it is absent, not merely unseen**", "",
                 r["evidenceOfAbsence"], ""]
        if r.get("blocks"):
            body += ["**What a consumer cannot do until it is filled**", "",
                     r["blocks"], ""]
    pack.md("MISSING-FROM-DIST.md", "Missing from dist/",
            ["generated by tools/report_compiler.py from the Unknowns it "
             "rendered"], body)
    return rows


# -- the manifest ----------------------------------------------------------

def render_manifest(pack, dist, meta, parts, results, budget):
    doc = {
        "compiledAt": meta["compiledAt"],
        "compiler": "tools/report_compiler.py",
        "compilerVersion": meta["version"],
        "distCommit": meta["distCommit"],
        "scope": meta["scope"],
        "inputs": [{"path": "dist/" + rel, "sha256": dist.hashes[rel]}
                   for rel in sorted(dist.hashes)],
        "missingInputs": dist.missing,
        "sizeBytes": budget["totalBytes"],
        "exemptBytes": budget["exemptBytes"],
        "contractOnlyBytes": budget["contractOnlyBytes"],
        "fileCount": budget["fileCount"],
        "budget": budget["budget"],
        "checks": results,
        "confidenceOrder": CONFIDENCE_ORDER,
        "compilerAdditions": [
            {"what": "the grouping of writable report properties",
             "confidence": "Inferred"},
            {"what": "the report type × property affinity, and the AiExport ↔ "
                     "ReportTypeEnum mapping",
             "confidence": "Inferred"},
        ],
    }
    pack.json("common/index/report-pack.json", doc,
              "the compiler itself; inputs hashed from dist/")
    return doc


def run(dist, pack, parts, gaps, meta, budget_total=BUDGET_TOTAL):
    """Every gate, then MISSING-FROM-DIST.md and the manifest.

    Returns (findings, results). A non-empty findings list must fail the build.
    """
    findings = []
    results = {}

    for name, (f, r) in (
            ("grouping", check_grouping(parts["contract"])),
            ("confidence", check_confidence(dist, parts)),
            ("inference", check_inferences(parts)),
            ("recipes-contract", check_recipes(parts["recipes"], "contract")),
    ):
        findings += f
        results[name] = r

    if parts["model"]:
        f, r = check_recipes(parts["systemRecipes"],
                             "system=%s" % parts["model"]["systemId"])
        findings += f
        results["recipes-system"] = r

    # MISSING-FROM-DIST.md is rendered before the budget runs, because it is
    # part of the pack and has to be weighed with it.
    rows = render_missing(pack, gaps, meta)
    f, r = check_gaps(gaps)
    findings += f
    results["gaps"] = dict(r, rendered=len(rows))

    f, r = check_provenance(pack)
    findings += f
    results["provenance"] = r

    # The manifest states the pack's own size, and writing it changes that
    # size. Iterate until the figure it states is the figure it produces, so
    # the manifest is not quietly describing a pack one file smaller than the
    # one on disk. Converges in two or three passes; the guard is there so a
    # pathological oscillation cannot loop forever.
    budget = None
    for _ in range(6):
        f, budget = check_budget(pack, budget_total)
        results["budget"] = {k: v for k, v in budget.items() if k != "budget"}
        before = pack.files.get("common/index/report-pack.json")
        render_manifest(pack, dist, meta, parts, results, budget)
        if pack.files["common/index/report-pack.json"] == before:
            break
    f, budget = check_budget(pack, budget_total)
    findings += f
    results["budget"] = {k: v for k, v in budget.items() if k != "budget"}
    return findings, results
