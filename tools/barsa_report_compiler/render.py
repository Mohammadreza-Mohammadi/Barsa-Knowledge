"""Rendering the pack: English markdown and JSON, plus one Persian summary.

Decision 4: the canonical output language is English. Decision 5: exactly one
Persian file, README-FA.md, as a human-facing summary -- not a translation of
the pack, because two canonical languages drift apart.

Every markdown file carries the three-line provenance header of spec section
20, and every JSON file a `_provenance` object. `audit` fails the build if one
is missing, so the header cannot be forgotten on a file added later.
"""

import json

UNKNOWN = "**Unknown**"


class Pack:
    """The files to be written, keyed by path relative to the pack root."""

    def __init__(self, meta):
        self.meta = meta
        self.files = {}

    def md(self, path, title, sources, body):
        head = ["# " + title, ""]
        head.append("> **Source:** " + " · ".join(sources))
        head.append("> **dist commit:** " + (self.meta["distCommit"] or
                                             "unknown (dist/ not committed)"))
        head.append("> **compiled:** " + self.meta["compiledAt"] +
                    " · **scope:** " + self.meta["scope"])
        head.append("")
        self.files[path] = "\n".join(head + body).rstrip() + "\n"

    def json(self, path, doc, provenance):
        doc = dict(doc)
        doc["_provenance"] = {
            "source": provenance,
            "distCommit": self.meta["distCommit"],
            "compiledAt": self.meta["compiledAt"],
            "scope": self.meta["scope"],
            "compiler": "tools/report_compiler.py",
        }
        self.files[path] = json.dumps(doc, ensure_ascii=False, indent=1,
                                      sort_keys=True) + "\n"


def _yn(v):
    return "yes" if v else "no"


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c)
                                     for c in r) + " |")
    out.append("")
    return out


def _fence(doc):
    return ["```json", json.dumps(doc, ensure_ascii=False, indent=2), "```",
            ""]


# -- common/REPORT-CONTRACT.md ---------------------------------------------

def report_contract(pack, contract, gaps):
    obj = contract["objectContract"] or {}
    body = [
        "What may be written on a report object in an `AiChangeBatch`, taken "
        "from the write contract the Barsa binary builds at type-init. "
        "Classification, create and update flags are **Verified**; the "
        "grouping into sections is **Inferred** by this compiler and is the "
        "only thing here that dist/ does not state.",
        "",
        "## The object",
        "",
    ]
    body += _table(
        ["", "value"],
        [["objectType", "`report`"],
         ["supported operations", ", ".join(obj.get("supportedOperations")
                                            or ["Unknown"])],
         ["structural order", obj.get("structuralOrder")],
         ["identity", "`%s`" % obj.get("identitySemantics")],
         ["ordering semantics", _yn(obj.get("hasOrderingSemantics"))],
         ["runtime adapter", "`%s`" % obj.get("runtimeAdapterKey")],
         ["apply class", obj.get("applyClass")],
         ["confidence", obj.get("confidence")]])

    body += [
        "`structuralOrder` is what decides command order inside a batch: a "
        "report (120) is created before a folder (130) that points at it, and "
        "after the entity (100) and fields (110) it reads.",
        "",
        "## Writable properties, grouped",
        "",
        "%d named writable properties, in %d groups. Every one is in exactly "
        "one group; the build fails otherwise."
        % (contract["writableCount"], len(contract["groups"])),
        "",
        "The contract carries %d writable rows in total. The extra one has no "
        "property name at all -- it is the `RawJson` contract, which covers a "
        "raw payload rather than a named property, so there is nothing to "
        "group. It is described in `LIMITS.md`."
        % (contract["writableCount"] + len(contract["anonymousContracts"])),
        "",
    ]
    for g in contract["groups"]:
        body += ["### " + g["group"], "", g["purpose"], ""]
        rows = []
        for m in g["properties"]:
            if not m.get("presentInContract", True):
                rows.append(["`%s`" % m["property"], "MISSING FROM CONTRACT",
                             "", "", ""])
                continue
            rows.append([
                "`%s`" % m["property"],
                m.get("kind") or "unstated",
                _yn(m.get("writableOnCreate")),
                _yn(m.get("writableOnUpdate")),
                ("`%s`" % m["referenceTargetType"])
                if m.get("referenceTargetType") else "",
            ])
        body += _table(["property", "kind", "on create", "on update",
                        "reference to"], rows)

    unstated = sorted(m["property"] for g in contract["groups"]
                      for m in g["properties"]
                      if m.get("presentInContract", True) and not m.get("kind"))
    if unstated:
        body += [
            "## Properties whose value kind the contract does not state",
            "",
            "%d of the writable properties were registered through "
            "`RegisterWritableSet`, which records the name but no value kind. "
            "For these the contract proves *that* they may be written, not "
            "*what* a valid value looks like. See `report-shapes.json` for the "
            "ones an artifact happens to show, and `MISSING-FROM-DIST.md` for "
            "the rest." % len(unstated),
            "",
            ", ".join("`%s`" % p for p in unstated),
            "",
        ]
        gaps.add(
            "Value kinds for the RegisterWritableSet properties",
            "common/REPORT-CONTRACT.md: %d properties with no stated value "
            "kind" % len(unstated),
            "AiReportModel.ApplyReportPatch -- the single writer named by all "
            "of these rows. Its parameter handling states the accepted value "
            "shapes.",
            "The contract rows carry kind=null, which the Extractor writes "
            "only when the factory records no kind -- not when it failed to "
            "read one.",
            "A consumer can know a property is writable but not what value to "
            "put in it.")

    body += ["## Writer", "",
             "Every writable property above is applied by "
             + ", ".join("`%s`" % w for w in contract["writer"]) + ".", ""]
    pack.md("common/REPORT-CONTRACT.md", "Report write contract",
            ["dist/index/semantic-contract.json → propertyContracts.report"],
            body)


# -- common/LIMITS.md ------------------------------------------------------

def limits(pack, contract, shapes, gaps):
    body = [
        "What cannot be written, and what is not known. This is the most "
        "important file in the pack: a consumer that treats one of these as "
        "writable will produce a batch that fails, and one that fills an "
        "Unknown with a plausible value will produce a batch that is wrong "
        "without failing.",
        "",
        "## Not writable at all",
        "",
    ]
    body += _table(
        ["property", "classification", "kind", "declared reason"],
        [["`%s`" % r["property"], r["classification"], r.get("kind") or "",
          ("`%s`" % r["runtimeSource"]) if r.get("runtimeSource") else ""]
         for r in contract["nonWritable"]])
    body += [
        "Read these as written. Three consequences matter:",
        "",
        "1. **The target entity of a report cannot be changed.** `entity` is "
        "ReadOnly, so there is no update that moves a report to another "
        "entity. It is fixed at create time, and it comes from the command's "
        "`parent`, not from a property. Changing it means deleting the report "
        "and creating another.",
        "2. **The owning system cannot be changed either.** `system` is "
        "ReadOnly for the same reason, and reads from `Report.SystemId`.",
        "3. **The parameter panel layout cannot be reconstructed.** The "
        "contract's own words: *\"Report parameter XML layout is out of "
        "Semantic v15 reconstruction scope in v190\"*. This is a declared "
        "limitation, not an inference, and not a gap in this pack.",
        "",
    ]
    if contract["anonymousContracts"]:
        body += ["## The unnamed contract", ""]
        for a in contract["anonymousContracts"]:
            body += ["- factory `%s`, kind `%s`: %s Runtime source: `%s`."
                     % (a.get("factory"), a.get("kind"), a.get("note"),
                        a.get("runtimeSource")), ""]

    never = shapes["writableNeverObserved"]
    body += [
        "## Writable, but never observed",
        "",
        "%d of the writable properties appear in no supplied artifact. That "
        "is **not** evidence against them: the exporter omits a property "
        "sitting at its default, and the two supplied systems exercise a "
        "narrow slice of the designer. It does mean this pack can show no "
        "example of their value shape." % len(never),
        "",
        ", ".join("`%s`" % p for p in never) or "none",
        "",
        "## Unknowns a consumer must not fill",
        "",
        "- the comparison operator vocabulary in a condition",
        "- the semantics of a `parameters` entry, and the value vocabulary of "
        "its `kind` and `sourceOperator`",
        "- the parameter panel layout (declared out of scope, above)",
        "- which properties are meaningful for which `reportType`",
        "- whether a column may name a field reached through a relation",
        "- the print template format (`PrintView`); no `.mrt` sample exists",
        "",
        "Each has a row in `MISSING-FROM-DIST.md` saying where to look.",
        "",
        "## Not an authoring limit, but worth knowing",
        "",
        "The write path is not a symmetric importer. An `AiChangeBatch` is a "
        "change plan executed command by command, and the pipeline is "
        "deliberately non-atomic: a partial batch leaves partial state. "
        "`errorPolicy` accepts exactly one value, `continueIndependent`.",
        "",
    ]
    pack.md("common/LIMITS.md", "Limits", [
        "dist/index/semantic-contract.json → propertyContracts.report",
        "dist/formats/ai-export-single-json.md → Observed paths"], body)


# -- common/REPORT-TYPES.md ------------------------------------------------

def report_types(pack, types, pairings, gaps):
    body = [
        "Barsa has two report-type vocabularies, and they are not the same "
        "words. Getting this wrong is the single easiest way to write a batch "
        "that is accepted and wrong.",
        "",
        "## The CLR enum",
        "",
        "`%s`, as the embedded export profile spells it out." % types["clrEnum"],
        "",
    ]
    body += _table(
        ["value", "member", "properties whose names line up (Inferred)"],
        [[t["enumValue"], "`%s`" % t["enumMember"],
          ", ".join("`%s`" % p for p in t["affineProperties"]) or UNKNOWN]
         for t in types["clrMembers"]])
    body += [
        "## The AiExport vocabulary",
        "",
        "The JSON projection writes its own `reportType` strings. Observed in "
        "the supplied artifacts: "
        + (", ".join("`%s`" % v for v in types["aiExportVocabulary"])
           or "none") + ".",
        "",
        "These are what an `AiChangeBatch` carries, because the batch speaks "
        "the semantic vocabulary, not the CLR one.",
        "",
        "## The mapping between them is Inferred",
        "",
        types["vocabularyMapping"]["note"],
        "",
    ]
    body += _table(
        ["AiExport value", "CLR candidate", "confidence", "basis"],
        [["`%s`" % c["aiExport"], "`%s`" % c["clrCandidate"], c["confidence"],
          c["basis"]]
         for c in types["vocabularyMapping"]["candidates"]])
    if pairings["pairings"]:
        body += [
            "## Corroboration from paired artifacts",
            "",
            "%d report ids appear on both sides -- in a legacy artifact and "
            "in an AiExport artifact. Each pairing shows the numeric "
            "ReportTypeEnum value and the AiExport string the *same report* "
            "carried:" % pairings["idsOnBothSides"],
            "",
        ]
        body += _table(
            ["AiExport value", "legacy enum value", "reports agreeing",
             "example ids"],
            [[("`%s`" % p["aiExport"]), p["legacyEnumValue"],
               p["matchCount"], ", ".join("`%s`" % i for i in p["reportIds"])]
             for p in pairings["pairings"]])
        body += [
            "This is stronger than name resemblance, and it is still not a "
            "promotion. " + pairings["caveat"],
            "",
            "What would settle it: a **same-build pair** -- one legacy and "
            "one AiExport artifact of the same system exported from the same "
            "Barsa build minutes apart. `dist/comparison/"
            "golden-pair-protocol.md` says how to produce one. Until then the "
            "mapping stays **Inferred**.",
            "",
        ]

    body += [
        "Every CLR member not named above has no known AiExport spelling, and "
        "every AiExport value not named above is unmapped. A consumer must "
        "not derive one from the other by lowercasing a member name: `list` "
        "is not a lowercasing of `ViewResults`.",
        "",
        "## The type × property matrix is Inferred, and thin",
        "",
        types["affinityBasis"],
        "",
        "So: for any report type, the properties named in the table above are "
        "a *guess at relevance from the name*, and every other property's "
        "relevance to that type is " + UNKNOWN + ". Nothing here says a "
        "property is rejected for a type -- only that this pack cannot say it "
        "is meaningful.",
        "",
    ]
    pack.md("common/REPORT-TYPES.md", "Report types", [
        "dist/index/ai-export-properties.json → enums",
        "dist/models/normalized-samples/ → reports[].reportType"], body)

    gaps.add(
        "reportType vocabulary mapping: AiExport strings ↔ ReportTypeEnum",
        "common/REPORT-TYPES.md: the mapping table is Inferred and covers 2 "
        "of %d CLR members" % len(types["clrMembers"]),
        "AiSemanticV15ExportPostProcessor, which writes the semantic "
        "discriminator, or the profile's enum rule for met_Report.reportType "
        "(the profile does map the column to Barsa.Meta.ReportTypeEnum, so "
        "the translation exists somewhere in that path).",
        "The profile records the column→enum mapping but the artifacts carry "
        "strings that are not enum member names, so a second translation step "
        "exists and is not in dist/.",
        "A consumer cannot author anything but a `list` or `form` report with "
        "confidence.")
    gaps.add(
        "Which properties are meaningful for which reportType",
        "common/REPORT-TYPES.md: the type × property matrix",
        "AiReportChangeProvider.ApplyReportPatch / "
        "AiReportModel.ApplyReportPatch -- the patch writer branches per type.",
        "No dist/ document contains a type-to-property relation of any kind; "
        "the matrix in this pack is name correspondence only.",
        "A consumer may set a property that the type ignores, with no error.")


# -- common/COLUMNS-AND-FIELDS.md ------------------------------------------

def columns(pack, ftypes, shapes, gaps):
    col = next((s for s in shapes["shapes"] if s["property"] == "columns"),
               None)
    body = [
        "A report's columns are the part a consumer changes most, and the one "
        "the legacy export cannot see at all.",
        "",
        "## The observed shape",
        "",
    ]
    if col and col["status"] == "Observed":
        body += _fence({"columns": col["example"]})
        body += _table(["key", "types", "times seen", "nullable"],
                       [["`%s`" % k["path"], ", ".join(k["types"]),
                         k["occurrences"], _yn(k["nullable"])]
                        for k in col["keys"]])
        body += [
            "`field` is a semantic selector, not an id. It resolves to a "
            "FieldDef under the report's own entity. `alias` is the column "
            "heading.",
            "",
            "Both keys appeared in all 149 observed column rows, so neither "
            "is optional in practice -- though the contract does not mark "
            "either required.",
            "",
        ]
    else:
        body += ["No artifact in dist/ carries a `columns` payload, so the "
                 "column shape is " + UNKNOWN + ".", ""]

    body += [
        "## Replacing, not patching",
        "",
        "`columns` is writable on create and on update, and the value is the "
        "whole list. dist/ shows no per-column patch form, so an update that "
        "changes one column sends every column.",
        "",
        "## Where the columns live on the legacy side",
        "",
        "They do not, in any readable form. On the legacy side a report's "
        "definition sits inside `met_Report.ReportData`, a binary blob whose "
        "decoder (`SerializeReportData`) the Extractor never ran. So a legacy "
        "`.metaexport` tells you a report exists and nothing about its "
        "columns, and only an AiExport artifact shows them.",
        "",
        "## What can be a column",
        "",
        "A column names a field, and this pack carries the field catalogue "
        "for the scope. Whether every field *subtype* may be a column is " +
        UNKNOWN + ": the contract classifies field properties and says "
        "nothing about column eligibility, and no artifact in dist/ pairs a "
        "column with its field's subtype.",
        "",
        "%d field subtypes exist, each with its own properties:"
        % ftypes["subtypeCount"],
        "",
    ]
    body += _table(["subtype", "own properties", "usable as a column"],
                   [[("`%s`" % s["subtype"]), len(s["ownProperties"]),
                     UNKNOWN] for s in ftypes["subtypes"]])
    body += [
        "A relation column -- naming a field reached through a relation "
        "rather than on the entity itself -- is " + UNKNOWN + ". "
        + ftypes["relationColumns"]["note"],
        "",
    ]
    pack.md("common/COLUMNS-AND-FIELDS.md", "Columns and fields", [
        "dist/formats/ai-export-single-json.md → Observed paths",
        "dist/index/semantic-contract.json → propertyContracts.field",
        "dist/formats/report-format.md"], body)

    gaps.add(
        "Which field subtypes may be a report column",
        "common/COLUMNS-AND-FIELDS.md: the eligibility column is Unknown for "
        "all %d subtypes" % ftypes["subtypeCount"],
        "The column editor's field filter, or an artifact whose columns cover "
        "varied field subtypes. Pairing each observed column selector with "
        "the subtype of the field it resolves to would settle it empirically.",
        "dist/ carries the column rows and the field subtypes but nothing "
        "joining them: the normalized samples drop `columns` entirely.",
        "A consumer may offer a field that cannot be a column.")
    gaps.add(
        "The contents of met_Report.ReportData",
        "common/COLUMNS-AND-FIELDS.md: the legacy side of a report "
        "definition is opaque",
        "SerializeReportData, the decoder the export profile names but which "
        "was never run against a sample.",
        "dist/formats/report-format.md marks the column base64Binary with "
        "contents Unknown; the profile's binaryDecoders map names the decoder "
        "without output.",
        "A legacy .metaexport cannot be used to understand an existing "
        "report's definition, only to know it exists.")


# -- common/CONDITIONS.md --------------------------------------------------

def conditions(pack, shapes, enums, gaps):
    cond = next((s for s in shapes["shapes"] if s["property"] == "condition"),
                None)
    comb = (enums["enums"].get("Barsa.Meta.CombinationOperator") or {})
    comp = (enums["enums"].get("Barsa.Meta.ComparisonOperator") or {})
    body = [
        "## How clauses combine",
        "",
        "A condition is an object with one combining key:",
        "",
    ]
    body += _fence({"condition": {"all": []}})
    body += [
        "`all` and `any` line up exactly with `Barsa.Meta.CombinationOperator`"
        " (" + ", ".join("%s = %s" % (v, k)
                         for k, v in sorted((comb.get("members") or {}).items()))
        + "). Two independent sources agree, so this is **CrossVerified**.",
        "",
        "`{\"all\": []}` is an empty condition: no clause, every row.",
        "",
        "## What a clause looks like",
        "",
    ]
    if cond and cond["status"] == "Observed":
        body += _table(["key", "types", "times seen", "nullable"],
                       [["`%s`" % k["path"], ", ".join(k["types"]),
                         k["occurrences"], _yn(k["nullable"])]
                        for k in cond["keys"]])
        body += [
            "So a clause carries a `field` (a selector, or an object with an "
            "`items` list when several fields are involved), an `operator`, "
            "and optionally a `value`, a `parameter` reference, a "
            "`nullBehavior`, or raw `customSql`.",
            "",
            "These keys are **Observed** -- 16 clauses in the supplied "
            "artifacts carried them.",
            "",
            "## But the operator values are Unknown",
            "",
            "This is the wall. `operator` is a string in all 16 observed "
            "clauses, and dist/ records that the key exists and its type, "
            "never the strings themselves.",
            "",
            "The profile's `Barsa.Meta.ComparisonOperator` has "
            "%d member%s: %s. That is far too few for a condition engine that "
            "also carries `nullBehavior` and multi-field clauses, so the real "
            "operator vocabulary is elsewhere and the profile maps only this "
            "one." % (comp.get("memberCount", 0),
                      "" if comp.get("memberCount") == 1 else "s",
                      ", ".join("`%s`" % v for v in
                                (comp.get("members") or {}).values())
                      or "none"),
            "",
            "**Therefore: do not author a non-empty condition.** A clause "
            "with a guessed operator name is a batch that lints clean and "
            "does the wrong thing. Write `{\"all\": []}` and let a human add "
            "the condition in the designer, or supply the operator string "
            "from a source outside this pack.",
            "",
        ]
    else:
        body += ["No artifact in dist/ carries a populated condition, so the "
                 "clause shape is " + UNKNOWN + ".", ""]

    body += [
        "## treeCondition",
        "",
        "A separate writable property, for the hierarchy side of a tree "
        "report. Its value shape is " + UNKNOWN + " -- no artifact carries "
        "one. `useHierarchyConditionForRoot` decides whether it also applies "
        "to root rows.",
        "",
        "## Ordering inside the batch",
        "",
        "The contract records `condition` as depending on `parameters`: a "
        "clause may reference a parameter, so parameters are applied first. "
        "`sorting` likewise depends on `columns`.",
        "",
    ]
    pack.md("common/CONDITIONS.md", "Conditions", [
        "dist/formats/ai-export-single-json.md → Observed paths",
        "dist/index/ai-export-properties.json → enums",
        "dist/index/semantic-contract.json → propertyContracts.report"], body)

    gaps.add(
        "The comparison operator vocabulary in a condition clause",
        "common/CONDITIONS.md: `operator` is a string whose accepted values "
        "are Unknown, which blocks every non-empty condition",
        "The condition builder, or the full comparison-operator enum -- the "
        "profile maps only AdvancedTextSearch2. An index of the string values "
        "observed in artifacts (not just the keys) would settle it from data "
        "already in source/.",
        "The observed-path table records keys and JSON types by design and "
        "carries no values, and the profile's enum has a single member, which "
        "cannot be the whole operator set of an engine that also supports "
        "nullBehavior and multi-field clauses.",
        "A consumer cannot write any filtering at all; it can only create "
        "reports with an empty condition.")


# -- common/PARAMETERS.md --------------------------------------------------

def parameters(pack, shapes, gaps):
    par = next((s for s in shapes["shapes"] if s["property"] == "parameters"),
               None)
    body = [
        "Parameters exist, are referenced, and are not authorable from this "
        "pack. The short version:",
        "",
    ]
    body += _table(
        ["", "status"],
        [["that a report can have parameters", "**Verified**"],
         ["that parameters are referenced and normalized on verify",
          "**Verified**"],
         ["the key set of a parameter entry", "**Observed**"],
         ["the semantics of those keys", UNKNOWN],
         ["the value vocabulary of `kind` and `sourceOperator`", UNKNOWN],
         ["the parameter panel layout", "**declared out of scope**"]])
    body += [
        "## Writable, per the contract",
        "",
        "`parameters`, `parameterEntity` and `parameterPanelHeight` are "
        "writable on create and update. `parameterLayout` is ReadOnly, with "
        "the contract's declared reason: *\"Report parameter XML layout is "
        "out of Semantic v15 reconstruction scope in v190\"*.",
        "",
        "## Referenced, per the pipeline",
        "",
        "The verifier carries `BuildReportParameterIdMap` and "
        "`NormalizeReportParameterReferences`, which only make sense if "
        "parameters are referred to by identity elsewhere in the report and "
        "have to be renumbered after a write. `ReportParametersPatchMatches` "
        "then checks the result.",
        "",
        "## The observed key set",
        "",
    ]
    if par and par["status"] == "Observed":
        body += _table(["key", "types", "times seen", "nullable"],
                       [["`%s`" % k["path"], ", ".join(k["types"]),
                         k["occurrences"], _yn(k["nullable"])]
                        for k in par["keys"]])
        body += [
            "Two of those keys deserve attention: `value.unsupported` "
            "(boolean) and `value.warning` (string). The exporter itself "
            "marks a parameter value it could not represent. So some "
            "parameter values are known to be outside what the semantic "
            "projection can carry -- which means a round trip through this "
            "format is not guaranteed to preserve them.",
            "",
            "**This key set is not a specification.** It is what two systems "
            "happened to contain. What `kind` accepts, how `sourceOperator` "
            "relates to a condition's `operator`, whether `external` and "
            "`input` are independent, and which keys are required are all " +
            UNKNOWN + ".",
            "",
            "**Therefore: do not author `parameters`.** Decision: parameter "
            "shape stays Unknown until an artifact or the patch writer says "
            "otherwise. Create the report without parameters and let a human "
            "add them.",
            "",
        ]
    else:
        body += ["No artifact in dist/ carries a `parameters` payload, so the "
                 "shape is " + UNKNOWN + ".", ""]
    pack.md("common/PARAMETERS.md", "Parameters", [
        "dist/index/semantic-contract.json → propertyContracts.report",
        "dist/index/write-pipeline.json",
        "dist/formats/ai-export-single-json.md → Observed paths"], body)

    gaps.add(
        "The semantics of a report parameter entry",
        "common/PARAMETERS.md: the key set is Observed but every key's "
        "meaning and value vocabulary is Unknown",
        "AiReportModel.ApplyReportPatch for the accepted shape, and "
        "AiRuntimeVerifier.BuildReportParameterIdMap for how a parameter is "
        "identified. An artifact whose parameters exercise each `kind` would "
        "give the vocabulary.",
        "dist/ carries the keys (12 parameter entries observed) and no "
        "values, and no document describes any key's meaning.",
        "A consumer cannot author a parameterized report.")
    gaps.add(
        "The report parameter panel layout",
        "common/PARAMETERS.md and common/LIMITS.md: parameterLayout is "
        "ReadOnly",
        "Nowhere, for now. This one is **declared**, not missing: the "
        "contract says the XML layout is out of Semantic v15 reconstruction "
        "scope in v190. It is listed here so that a reader does not look for "
        "it in dist/.",
        "The contract row's own runtimeSource text states the exclusion.",
        "Panel arrangement cannot be written or read back; it is a designer "
        "task.")


# -- common/PLACEMENT.md ---------------------------------------------------

def placement(pack, dist, enums, recipes, gaps):
    folder_obj = dist.object_contract("folder") or {}
    report_obj = dist.object_contract("report") or {}
    ftype = (enums["enums"].get("Barsa.Meta.FolderType") or {})
    rows = dist.property_contracts("folder")
    body = [
        "A report nobody can navigate to is invisible. Creating the report is "
        "half the job; the other half is a placement row in the navigator.",
        "",
        "## The two folder rows involved",
        "",
    ]
    body += _table(["FolderType", "member", "meaning here"],
                   [[k, "`%s`" % v,
                     {"Report": "a placement of one report",
                      "ReportFolder": "the container folder",
                      "ReportRoot": "the root of the report tree",
                      "MainRoot": "the navigator root"}.get(v, "")]
                    for k, v in sorted((ftype.get("members") or {}).items(),
                                       key=lambda kv: int(kv[0]))])
    body += [
        "Use the member name, not the number. Both are in dist/ and the name "
        "is harder to get wrong.",
        "",
        "## Order inside the batch is Verified",
        "",
        "`report` has structuralOrder %s and `folder` has %s, so the report "
        "is created first and the folder refers to it. The planner sorts by "
        "dependency regardless, but writing the commands in this order "
        "matches what it will do."
        % (report_obj.get("structuralOrder"),
           folder_obj.get("structuralOrder")),
        "",
        "## What may be written on a folder",
        "",
    ]
    body += _table(
        ["property", "classification", "kind", "on create", "on update",
         "runtime source"],
        [["`%s`" % r["property"], r["classification"], r.get("kind") or "",
          _yn(r.get("writableOnCreate")), _yn(r.get("writableOnUpdate")),
          ("`%s`" % r["runtimeSource"]) if r.get("runtimeSource") else ""]
         for r in rows if r.get("property")])
    body += [
        "`report` is a Reference to a report, and `order` carries ordering "
        "semantics, so sibling order is writable.",
        "",
        "`kind` is an Enum, writable on create only, and its value "
        "vocabulary is " + UNKNOWN + ": no dist/ document lists the strings "
        "the semantic side uses for a folder kind. The recipes omit it. If "
        "the server requires it, it has to come from outside this pack.",
        "",
        "## The two-command recipe",
        "",
        "`common/RECIPES.md` recipe R2. One caution carried from there: the "
        "parent folder is named by a selector. Observed exports carry "
        "navigation paths but no folder selectors, and the inspected "
        "SemanticRules resolver has no folder case. See "
        "`MISSING-FROM-DIST.md`.",
        "",
    ]
    pack.md("common/PLACEMENT.md", "Placement in the navigator", [
        "dist/index/semantic-contract.json → objectContracts, "
        "propertyContracts.folder",
        "dist/index/ai-export-properties.json → enums.Barsa.Meta.FolderType"],
        body)

    gaps.add(
        "Existing-folder semantic reference support",
        "common/PLACEMENT.md and the R2 recipe: the parent folder cannot be "
        "named with a supported selector",
        "Inspect a newer Barsa semantic resolver or obtain a runtime-proven "
        "folder reference contract. The current SemanticRules.ResolveObject "
        "supports system, entity, field, view, report and workflow only.",
        "AiExport SingleJson navigation objects and ZIP directory paths "
        "carry no folder selectors. AiSemanticReferenceResolver delegates "
        "selectors to SemanticRules.ResolveObject, which has no folder case.",
        "A consumer cannot place a report under an existing folder without "
        "a runtime-supported reference.")

    gaps.add(
        "Semantic folder kind vocabulary",
        "common/PLACEMENT.md and R2: kind is omitted",
        "Extract the accepted semantic values from "
        "AiFolderChangeProvider.Validate and InferCreateKind into dist/.",
        "The folder property contract only says Enum; no dist/ index carries "
        "the accepted values.",
        "A consumer cannot choose a folder kind from this pack.")


# -- common/SELECTORS.md ---------------------------------------------------

def selectors(pack, cb, gaps):
    body = [
        "In an `AiChangeBatch`, a selector is the **only** way to refer to an "
        "object that already exists. Runtime identity is forbidden.",
        "",
        "## The form",
        "",
        "```text",
        "#Name                a single '#' followed by the object's name",
        "#[Name]              bracketed, when a component needs escaping",
        "```",
        "",
        "Written and read by `SemanticSelectorCodec`. The bracketed form is "
        "the codec's escape path, not the normal case: in the supplied "
        "artifacts every selector is the plain `#Name` form.",
        "",
        "## Keys that are forbidden",
        "",
        ", ".join("`%s`" % k for k in cb.FORBIDDEN_RUNTIME_KEYS)
        + ". A batch carrying any of them is rejected by the linter before "
          "anything else happens -- this is a structural rule, not a "
          "convention.",
        "",
        "## Referring to something created in the same batch",
        "",
        "Use `tempId` on the creating command and `{\"tempId\": \"...\"}` "
        "where the reference is needed. The planner collects temp references "
        "into its dependency graph and sorts commands accordingly.",
        "",
        "## The letter trap",
        "",
        "This is the most common way a correct-looking selector fails to "
        "resolve.",
        "",
        "Arabic and Persian letter forms are mixed in this data. `ي` "
        "(U+064A, Arabic yeh) and `ی` (U+06CC, Farsi yeh) look nearly "
        "identical in most fonts, as do `ك` (U+0643) and `ک` (U+06A9). The "
        "same object is spelled one way in a legacy export and the other in "
        "an AiExport -- the Extractor has to fold these letters before it can "
        "match an object across the two families.",
        "",
        "A selector is matched by name. A selector typed with the wrong yeh "
        "will not resolve, and the failure says the object does not exist.",
        "",
        "**So: copy selectors, never type them.** In a system-scoped pack, "
        "`systems/<id>/index/selectors.json` carries them verbatim. Copy the "
        "string.",
        "",
        "## Scope",
        "",
        "A selector is resolved within a scope -- a field selector under its "
        "entity, a report selector under its system. The same name under a "
        "different entity is a different object, so a selector is not "
        "globally unique.",
        "",
    ]
    pack.md("common/SELECTORS.md", "Selectors", [
        "dist/formats/ai-export.md",
        "dist/formats/ai-change-batch.md",
        "dist/comparison/match-report.md"], body)


# -- RECIPES.md ------------------------------------------------------------

def recipes_doc(pack, built, dist, path, scope_note, gaps):
    pipeline = dist.docs.get("writePipeline") or {}
    stages = pipeline.get("stages") or []
    body = [
        "Complete `AiChangeBatch` documents for the common report tasks. "
        "Every one below was validated during the build by "
        "`barsa_extractor.change_batch.lint` -- the same code path "
        "`tools/lint_change_batch.py` runs, against the contract in "
        "`dist/index/semantic-contract.json`. The build fails on any error or "
        "warning, so a recipe in this file linted clean at compile time.",
        "",
        scope_note,
        "",
    ]
    if built["bindings"]:
        body += ["## Bound selectors", "",
                 "The placeholders below were replaced with real selectors "
                 "from this scope:", ""]
        body += _table(["placeholder", "bound to"],
                       [["`%s`" % k, "`%s`" % v]
                        for k, v in built["bindings"].items()])
    if built["bindingNotes"]:
        body += ["Notes on binding:", ""]
        body += ["- " + n for n in built["bindingNotes"]] + [""]

    for r in built["recipes"]:
        body += ["## %s — %s" % (r["id"], r["title"]), "", r["purpose"], ""]
        body += _fence(r["batch"])
        if r["notes"]:
            body += ["Why it looks like this:", ""]
            body += ["- " + n for n in r["notes"]] + [""]
        if r["unverified"]:
            body += ["Not verified:", ""]
            body += ["- " + n for n in r["unverified"]] + [""]
        if r["selectorsUnbound"]:
            body += ["Placeholders still to fill: "
                     + ", ".join("`%s`" % s for s in r["selectorsUnbound"])
                     + ".", ""]
        if r["selectorsNotInIndex"]:
            body += ["Selectors not found in this scope's index: "
                     + ", ".join("`%s`" % s
                                 for s in r["selectorsNotInIndex"]) + ".", ""]
        body += ["Lint: %d error(s), %d warning(s)."
                 % (len(r["lint"]["errors"]), len(r["lint"]["warnings"])), ""]

    if stages:
        body += ["## What happens to a batch after you send it", ""]
        body += _table(["stage", "entry point", "produces"],
                       [[s.get("stage"), "`%s`" % s.get("entryPoint"),
                         s.get("produces")] for s in stages])
        body += [
            "The pipeline is a change-plan executor, not an importer, and it "
            "is deliberately non-atomic: commands that fail are reported "
            "per-command and the rest proceed. A batch is therefore not a "
            "transaction -- keep batches small enough that partial "
            "application is recoverable by hand.",
            "",
        ]
    pack.md(path, "Recipes", [
        "dist/index/semantic-contract.json (validated against)",
        "dist/index/write-pipeline.json"], body)


# -- PROVENANCE.md ---------------------------------------------------------

def provenance(pack, dist, meta):
    rows = []
    for rel in sorted(dist.hashes):
        rows.append(["`dist/%s`" % rel, dist.hashes[rel][:16] + "…"])
    body = [
        "Every input this pack was compiled from, with the hash it had at "
        "compile time. If a hash no longer matches, the pack is stale: "
        "`python3 tools/report_compiler.py --check` says so and exits "
        "non-zero.",
        "",
        "## Inputs",
        "",
    ]
    body += _table(["dist/ file", "sha256"], rows)
    body += [
        "## Which part of the pack came from where",
        "",
    ]
    body += _table(
        ["pack file", "dist/ source", "what the Extractor read it from"],
        [["`common/REPORT-CONTRACT.md`, `common/index/report-contract.json`",
          "`index/semantic-contract.json`",
          "SemanticContractRegistry type-init, by constant IL evaluation"],
         ["`common/LIMITS.md`", "`index/semantic-contract.json`",
          "the same, ReadOnly rows"],
         ["`common/REPORT-TYPES.md`, `common/index/report-types.json`",
          "`index/ai-export-properties.json`, `models/normalized-samples/`",
          "the embedded AI export profile resource, and the supplied "
          "artifacts"],
         ["`common/index/report-enums.json`",
          "`index/ai-export-properties.json`",
          "enum members from the profile resource"],
         ["`common/COLUMNS-AND-FIELDS.md`, `common/CONDITIONS.md`, "
          "`common/PARAMETERS.md`, `common/index/report-shapes.json`",
          "`formats/ai-export-single-json.md`",
          "a walk over the supplied AiExport artifacts, recording keys and "
          "types"],
         ["`common/index/field-types.json`", "`index/semantic-contract.json`",
          "propertyContracts.field"],
         ["`common/PLACEMENT.md`",
          "`index/semantic-contract.json`, `index/ai-export-properties.json`",
          "objectContracts and the FolderType enum"],
         ["`common/RECIPES.md`, `common/index/recipes.json`",
          "`index/semantic-contract.json`, `index/write-pipeline.json`",
          "written by this compiler, validated against the contract"],
         ["`systems/*/`", "`models/normalized-samples/`",
          "the supplied legacy and AiExport artifacts, normalized"]])
    body += [
        "## What this pack adds that dist/ does not state",
        "",
        "Two things, both marked **Inferred** wherever they appear:",
        "",
        "1. the grouping of the writable properties into sections "
        "(`common/REPORT-CONTRACT.md`)",
        "2. the report type × property affinity, and the AiExport ↔ CLR "
        "report type mapping (`common/REPORT-TYPES.md`)",
        "",
        "Everything else carries the confidence its dist/ source carried. The "
        "build checks this: a fact whose provenance is a dist/ file may not "
        "be published at a higher confidence than the source states.",
        "",
    ]
    pack.md("PROVENANCE.md", "Provenance", ["every input listed below"], body)


# -- systems/<id>/ ---------------------------------------------------------

MD_FIELD_LIMIT = 400


def system_docs(pack, model, built, dist, gaps):
    sid = model["systemId"]
    base = "systems/%s" % sid
    caption = (model["captions"] or ["(unnamed)"])[0]

    body = [
        "System `%s`%s." % (sid, (" — " + caption) if caption else ""),
        "",
    ]
    body += _table(
        ["", "value"],
        [["captions", ", ".join(model["captions"]) or "none"],
         ["system selector", ", ".join("`%s`" % s
                                       for s in model["selectors"]) or "none"],
         ["report-authorable", _yn(model["authorable"])],
         ["entities carried", len(model["entities"])],
         ["fields carried", len(model["fields"])],
         ["existing reports carried", len(model["reports"])],
         ["views carried", len(model["views"])],
         ["folder containers carried", len(model["folders"])],
         ["model complete", _yn(model["complete"])]])
    body += [model["authorableBasis"], "", model["completenessNote"], ""]
    if model["truncation"]:
        body += ["## What is missing from this model", ""]
        rows = []
        for coll, marks in sorted(model["truncation"].items()):
            for m in marks:
                rows.append([coll, m.get("kept"), m.get("total"),
                             m.get("sample")])
        body += _table(["collection", "rows carried", "rows in the artifact",
                        "sample"], rows)
        body += [
            "The Extractor caps each collection of a normalized sample. "
            "Anything above the cap is not in dist/ and so not here. **Do not "
            "read a count in this model as the system's real count**, and do "
            "not conclude a field does not exist because it is absent.",
            "",
        ]
    body += ["## Files here", "",
             "- `ENTITY-MODEL.md` — entities and fields, with their selectors",
             "- `RECIPES.md` — the recipes with this system's selectors bound",
             "- `index/entity-model.json` — full rows when within the file "
             "budget, otherwise a summary with a retrieval command",
             "- `index/selectors.json` — selectors when within the file "
             "budget, otherwise a retrieval command",
             "- `index/recipes.json` — the bound recipes", ""]
    body += ["The complete searchable index is "
             "`dist/index/systems/%s/semantic.json`. Search it through "
             "`python tools/report_retrieve.py --system %s --kind field "
             "--query <name-or-id>`. This returns bounded candidates with "
             "provenance; it does not infer identity from a caption."
             % (sid, sid), ""]
    pack.md(base + "/README.md", "System %s" % sid,
            ["dist/index/systems/%s/semantic.json" % sid], body)

    # ENTITY-MODEL.md
    ebody = [
        "Entities and fields in this system, as dist/ carries them. The "
        "selector column is the one that matters for authoring: it is what a "
        "batch uses to name the object. Copy it, do not type it -- see "
        "`../../common/SELECTORS.md` on the Arabic/Persian letter forms.",
        "",
        "## Entities",
        "",
    ]
    ebody += _table(
        ["caption", "selector", "db name", "in AiExport", "in legacy"],
        [[e.get("caption"), ("`%s`" % e["selector"]) if e.get("selector")
          else "— none, cannot be named in a batch",
          ("`%s`" % e["dbName"]) if e.get("dbName") else "",
          _yn(e.get("inAiExport")), _yn(e.get("inLegacy"))]
         for e in model["entities"]])

    ebody += ["## Fields", ""]
    fields = model["fields"]
    shown = fields[:MD_FIELD_LIMIT]
    ebody += _table(
        ["entity", "caption", "selector", "type", "usable as a column"],
        [[f.get("entityCaption"), f.get("caption"),
          ("`%s`" % f["selector"]) if f.get("selector") else "— none",
          f.get("fieldType") or UNKNOWN,
          _yn(f.get("usableAsColumn"))]
         for f in shown])
    if len(fields) > len(shown):
        ebody += ["%d further fields are in `index/entity-model.json` but not "
                  "tabulated here, to keep this file inside the size budget."
                  % (len(fields) - len(shown)), ""]
    ebody += [
        "`usable as a column` means only that the field has a selector, so a "
        "batch *can* name it. Whether its type may be a column is " + UNKNOWN
        + " -- see `../../common/COLUMNS-AND-FIELDS.md`.",
        "",
        "A field with no selector is in the legacy export only. It exists, "
        "but nothing in this pack can refer to it.",
        "",
    ]
    no_type = [f for f in fields if not f.get("fieldType")]
    if no_type:
        ebody += ["%d of %d fields have no known type: the legacy export "
                  "hides the type inside an undecoded `FieldInfo` blob, and "
                  "only an AiExport artifact states it outright."
                  % (len(no_type), len(fields)), ""]

    if model["reports"]:
        ebody += ["## Reports that already exist", "",
                  "Useful as update or delete targets, and as examples.", ""]
        ebody += _table(
            ["name (AiExport)", "selector", "reportType (AiExport)",
             "name (legacy)", "reportType (legacy enum value)"],
            [[r.get("name") or "— not in the AiExport artifact",
              ("`%s`" % r["selector"]) if r.get("selector") else "— none",
              r.get("reportType") or UNKNOWN,
              r.get("legacyName"),
              r.get("legacyReportTypeValue")
              if r.get("legacyReportTypeValue") is not None else ""]
             for r in model["reports"][:200]])
        ebody += [
            "The two name columns are not always the same string. A legacy "
            "export and an AiExport can spell the same object with different "
            "Arabic and Persian letter forms, and the selector follows the "
            "AiExport spelling. **Never build a selector from a name "
            "column** -- copy the selector itself.",
            "",
            "The two reportType columns are two different vocabularies: a "
            "string on the AiExport side, the numeric ReportTypeEnum value on "
            "the legacy side. See `../../common/REPORT-TYPES.md`; the mapping "
            "between them is Inferred.",
            "",
        ]
    if model["views"]:
        ebody += ["## Views", "",
                  "A `form` report names a view through `typeView`.", ""]
        ebody += _table(
            ["name", "selector"],
            [[v.get("name") or v.get("caption"),
              ("`%s`" % v["selector"]) if v.get("selector") else "— none"]
             for v in model["views"][:200]])
    if model["folders"]:
        ebody += ["## Navigation folders", "",
                  "`path` is an observed navigation location for retrieval. "
                  "It is not a supported AiChangeBatch selector.", ""]
        ebody += _table(
            ["name", "kind", "path", "selector"],
            [[f.get("name"), f.get("kind") or UNKNOWN,
              f.get("path"), f.get("selector") or "unresolved"]
             for f in model["folders"][:100]])
    pack.md(base + "/ENTITY-MODEL.md", "Entity model: system %s" % sid,
            ["dist/index/systems/%s/semantic.json" % sid], ebody)

    recipes_doc(pack, built, dist, base + "/RECIPES.md",
                "Scope: system `%s`. Placeholders are bound to this system's "
                "real selectors where dist/ supplies them." % sid, gaps)

    pack.json(base + "/index/entity-model.json", _bounded_model(model),
              "dist/index/systems/%s/semantic.json" % sid)
    pack.json(base + "/index/selectors.json", _bounded_selectors(model),
              "dist/index/systems/%s/semantic.json" % sid)
    pack.json(base + "/index/recipes.json", built,
              "written by this compiler, validated against "
              "dist/index/semantic-contract.json")

    if model["truncation"]:
        gaps.add(
            "Untruncated normalized samples",
            "systems/%s: the entity model is partial" % sid,
            "The Extractor's normalized-sample writer caps each collection at "
            "25 rows. A report-authoring consumer needs the whole field list "
            "for the system it is working in, so the cap should be lifted for "
            "the AiExport side, or a separate per-system full model emitted.",
            "The samples carry explicit `_truncated_<collection>` markers "
            "giving kept and total counts, so the loss is recorded rather "
            "than inferred.",
            "A consumer cannot see most of the fields of a large system, and "
            "must not conclude that a missing field does not exist.")


def _bounded_model(model):
    """Keep the context pack small; the uncut truth stays in dist/."""
    if len(json.dumps(model, ensure_ascii=False).encode("utf-8")) <= 120000:
        return model
    sid = model["systemId"]
    return {
        "systemId": sid, "captions": model["captions"],
        "authorable": model["authorable"], "complete": model["complete"],
        "counts": {k: len(model[k]) for k in
                   ("entities", "fields", "reports", "views", "folders",
                    "relationDefs")},
        "contextProjection": "summary; full rows are retrieved from dist/",
        "fullIndexPath": "dist/index/systems/%s/semantic.json" % sid,
        "retrievalCommand": ("python tools/report_retrieve.py --system %s "
                             "--kind field --query <name-or-id>" % sid),
        "contributingSamples": model["contributingSamples"],
    }


def _bounded_selectors(model):
    index = _selector_index(model)
    if len(json.dumps(index, ensure_ascii=False).encode("utf-8")) <= 120000:
        return index
    return {
        "systemId": model["systemId"], "count": index["count"],
        "contextProjection": "summary; full selectors are retrieved from dist/",
        "fullIndexPath": "dist/index/systems/%s/semantic.json"
                         % model["systemId"],
        "retrievalCommand": ("python tools/report_retrieve.py --system %s "
                             "--kind field --query <name-or-id>"
                             % model["systemId"]),
    }


def _selector_index(model):
    out = {"systemId": model["systemId"], "selectors": []}
    for kind, coll, extra in (("entity", "entities", "dbName"),
                              ("field", "fields", "entityCaption"),
                              ("report", "reports", "reportType"),
                              ("view", "views", None),
                              ("folder", "folders", "path")):
        for row in model.get(coll) or ():
            if not row.get("selector"):
                continue
            item = {"objectType": kind, "selector": row["selector"],
                    "caption": row.get("caption") or row.get("name")}
            item["provenance"] = row.get("provenance") or (
                [row["_provenance"]] if row.get("_provenance") else [])
            if extra and row.get(extra) is not None:
                item[extra] = row[extra]
            if kind == "field":
                item["entitySelector"] = row.get("entitySelector")
                item["fieldType"] = row.get("fieldType")
            out["selectors"].append(item)
    out["selectors"].sort(key=lambda s: (s["objectType"], s["selector"]))
    out["count"] = len(out["selectors"])
    out["note"] = ("Copy these strings verbatim. Arabic and Persian letter "
                   "forms are mixed in this data and a mistyped yeh or kaf "
                   "will not resolve.")
    return out


# -- README.md and README-FA.md -------------------------------------------

def readme(pack, parts, meta, model):
    c = parts["contract"]
    body = [
        "A small pack about one task: **building and understanding a report "
        "in Barsa**. It is compiled from the general knowledge pack in "
        "`dist/` and contains nothing else -- no Barsa architecture, no "
        "format archaeology, no assembly inventory.",
        "",
        "Two kinds of consumer are intended:",
        "",
        "- **Authoring** — produce an `AiChangeBatch` that creates or changes "
        "a report, and have it accepted. Start at `common/RECIPES.md`.",
        "- **Comprehension** — explain an existing report, or say why "
        "something cannot be changed. Start at `common/REPORT-CONTRACT.md` "
        "and `common/LIMITS.md`.",
        "",
        "## The rule this pack is built on",
        "",
        "No fact without evidence. Anything that could not be shown from "
        "`dist/` is marked **Unknown**, and a consumer must not fill an "
        "Unknown with a plausible value. *Not observed* is never written as "
        "*unsupported*.",
        "",
        "```text",
        "CrossVerified > Verified > Observed > Inferred > Unknown",
        "```",
        "",
        "Exactly two things in this pack are **Inferred**, both this "
        "compiler's own additions: the grouping of the writable properties, "
        "and the report type × property affinity. Everything else carries "
        "the confidence its `dist/` source carried.",
        "",
        "## Reading order",
        "",
    ]
    body += _table(
        ["file", "what it answers"],
        [["`common/REPORT-CONTRACT.md`",
          "what may be written on a report, on create and on update"],
         ["`common/LIMITS.md`",
          "what cannot be written, and what is not known -- read this second"],
         ["`common/RECIPES.md`",
          "complete batches for the common tasks, lint-clean at build time"],
         ["`common/REPORT-TYPES.md`",
          "the two report-type vocabularies, and why they must not be "
          "conflated"],
         ["`common/COLUMNS-AND-FIELDS.md`", "what can be a column"],
         ["`common/CONDITIONS.md`",
          "how filtering is shaped, and why a non-empty condition cannot be "
          "authored"],
         ["`common/PARAMETERS.md`", "why parameters are not authorable"],
         ["`common/PLACEMENT.md`", "how a report becomes visible"],
         ["`common/SELECTORS.md`", "how objects are named, and the letter trap"],
         ["`PROVENANCE.md`", "where each part came from"],
         ["`MISSING-FROM-DIST.md`",
          "what the Extractor would have to add next, and why it matters"]])

    body += ["## Six things this pack can answer", "",
             "1. *Can I create a list report?* Yes — `common/RECIPES.md` R1, "
             "with %d writable properties documented in "
             "`common/REPORT-CONTRACT.md`." % c["writableCount"],
             "2. *Can I change which entity a report runs over?* No. `entity` "
             "is ReadOnly; it is fixed by the create command's `parent`. "
             "`common/LIMITS.md`.",
             "3. *Which fields can be columns on this entity?* In a "
             "system-scoped pack, search the full `dist/` system index with "
             "`tools/report_retrieve.py`; whether a given field *type* may "
             "be a column is Unknown.",
             "4. *What order do commands go in?* `report` is structuralOrder "
             "120 and `folder` is 130, so the report is created before the "
             "folder that points at it. `common/PLACEMENT.md`.",
             "5. *What do you not know?* `MISSING-FROM-DIST.md`, and the "
             "Unknown section of `common/LIMITS.md`. The short list: "
             "condition operators, parameter semantics, panel layout, the "
             "type × property matrix.",
             "6. *What is the exact selector for a field?* "
             "`systems/<id>/index/selectors.json` — copy the string, do not "
             "retype it.",
             ""]

    body += ["## Scope", "",
             "This pack was compiled at scope `%s`." % meta["scope"], ""]
    if model:
        body += ["It carries the entity model for system `%s`%s."
                 % (model["systemId"],
                    "" if model["complete"] else
                    ", which dist/ only carries partially -- see that "
                    "system's README"), ""]
        body += ["The full canonical index is "
                 "`dist/index/systems/%s/semantic.json`. Retrieve a bounded "
                 "field candidate set with "
                 "`python tools/report_retrieve.py --system %s --kind field "
                 "--query <name-or-id>`. Search results retain provenance; "
                 "check the owning entity before using a selector."
                 % (model["systemId"], model["systemId"]), ""]
    else:
        body += ["Contract only: no entity model, so every selector in the "
                 "recipes is a placeholder. Recompile with "
                 "`--scope system=<id>` to get a pack with real selectors.",
                 ""]
    body += ["## Staleness", "",
             "`PROVENANCE.md` lists every input with its hash. "
             "`python3 tools/report_compiler.py --check` compares them "
             "against `dist/` as it is now and exits non-zero if the pack is "
             "stale.",
             ""]
    pack.md("README.md", "Barsa report designer pack",
            ["dist/, compiled by tools/report_compiler.py"], body)


def readme_fa(pack, parts, meta, model, gap_count):
    c = parts["contract"]
    lines = [
        "# بستهٔ ساخت گزارش برسا",
        "",
        # The header keys stay in English: the audit checks for them
        # literally, on every file of the pack.
        "> **Source:** dist/ — ساخته‌شده توسط tools/report_compiler.py",
        "> **dist commit:** " + (meta["distCommit"] or "نامشخص"),
        "> **compiled:** " + meta["compiledAt"] + " · **scope:** "
        + meta["scope"],
        "",
        "این تنها فایل فارسی بسته است و یک خلاصهٔ انسانی است، نه ترجمهٔ بسته. "
        "زبان رسمی خروجی انگلیسی است؛ دو زبان رسمی از هم واگرا می‌شوند.",
        "",
        "## این بسته چیست",
        "",
        "خلاصه‌ای کوچک از `dist/` بزرگ، فقط برای یک کار: **ساختن و فهمیدن یک "
        "گزارش در برسا**. هیچ چیز دیگری در آن نیست.",
        "",
        "## اصل حاکم",
        "",
        "هیچ واقعیتی بدون شاهد. هر چیزی که از `dist/` قابل اثبات نبود "
        "**Unknown** علامت خورده، و مصرف‌کننده نباید جای Unknown را با حدس پر "
        "کند. «دیده نشده» هرگز «پشتیبانی نمی‌شود» نوشته نشده است.",
        "",
        "```text",
        "CrossVerified > Verified > Observed > Inferred > Unknown",
        "```",
        "",
        "دقیقاً دو چیز در این بسته **Inferred** است و هر دو افزودهٔ خود "
        "Compiler است: گروه‌بندی propertyها، و ماتریس نوع گزارش × property.",
        "",
        "## چه چیزی را می‌دانیم",
        "",
        "- %d property قابل نوشتن روی گزارش، با تفکیک create و update "
        "(**Verified**)" % c["writableCount"],
        "- چهار property که قابل نوشتن نیستند — از جمله `entity` و `system`، "
        "یعنی **موجودیت هدف یک گزارش را نمی‌توان با update عوض کرد** "
        "(**Verified**)",
        "- شکل `columns`: فهرستی از `{field, alias}` که `field` یک selector "
        "است، نه id (**Observed** — ۱۴۹ سطر ستون در artifactها)",
        "- اینکه `all` و `any` در شرط دقیقاً با `CombinationOperator` "
        "می‌خوانند (**CrossVerified**)",
        "- ترتیب فرمان‌ها در یک batch: گزارش (۱۲۰) پیش از پوشه (۱۳۰) "
        "(**Verified**)",
        "",
        "## چه چیزی را نمی‌دانیم",
        "",
        "- **عملگرهای مقایسه در شرط.** کلیدِ `operator` دیده شده، مقدارهایش "
        "نه. پس شرط غیرخالی نباید نوشته شود.",
        "- **معنای ورودی‌های `parameters`.** مجموعهٔ کلیدها دیده شده، معنا و "
        "واژگان مقدارها نه. پس پارامتر نباید نوشته شود.",
        "- **چیدمان پنل پارامتر.** این یکی اعلام‌شده است: قرارداد خودش "
        "می‌گوید خارج از scope بازسازی Semantic v15 در v190 است.",
        "- **نگاشت `reportType`** بین واژگان AiExport (`list`, `form`) و "
        "`ReportTypeEnum` — فقط Inferred.",
        "- **اینکه کدام property برای کدام نوع گزارش معنا دارد.**",
        "- **selector پوشه‌ها**، که در `dist/` هیچ کدام نیست؛ پس جای‌گذاری "
        "گزارش در navigator از این بسته قابل تکمیل نیست.",
        "",
        "%d شکاف در `MISSING-FROM-DIST.md` ثبت شده، با آدرس دقیق اینکه "
        "Extractor کجا باید دنبالشان برود." % gap_count,
        "",
        "## از کجا شروع کنیم",
        "",
        "| فایل | پاسخ چه سؤالی |",
        "|---|---|",
        "| `common/RECIPES.md` | نمونهٔ کامل batch برای کارهای رایج |",
        "| `common/REPORT-CONTRACT.md` | چه چیزی قابل نوشتن است |",
        "| `common/LIMITS.md` | چه چیزی نیست، و چه چیزی را نمی‌دانیم |",
        "| `common/SELECTORS.md` | تلهٔ حروف عربی/فارسی در selector |",
        "| `MISSING-FROM-DIST.md` | کار بعدی Extractor |",
        "",
        "## یک هشدار عملی",
        "",
        "شکل‌های حروف `ي`/`ی` و `ك`/`ک` در این داده‌ها در هم به کار رفته‌اند. "
        "selectorی که با حرف اشتباه تایپ شود resolve نمی‌شود و خطا می‌گوید "
        "شیء وجود ندارد. selector را از "
        "`systems/<id>/index/selectors.json` **کپی** کنید، تایپ نکنید.",
        "",
    ]
    if model:
        lines += [
            "## scope این بسته",
            "",
            "سیستم `%s`%s. %s"
            % (model["systemId"],
               (" — " + model["captions"][0]) if model["captions"] else "",
               "مدل کامل است." if model["complete"]
               else "**مدل ناقص است**: Extractor هر مجموعه را به ۲۵ سطر "
                    "محدود می‌کند، پس شمارش‌های این مدل شمارش واقعی سیستم "
                    "نیست."),
            "",
        ]
    pack.files["README-FA.md"] = "\n".join(lines).rstrip() + "\n"


# -- the whole pack --------------------------------------------------------

def build(dist, parts, meta, gaps):
    """Render every file of the pack. Returns a Pack."""
    pack = Pack(meta)
    contract = parts["contract"]

    report_contract(pack, contract, gaps)
    limits(pack, contract, parts["shapes"], gaps)
    report_types(pack, parts["types"], parts["pairings"], gaps)
    columns(pack, parts["fieldTypes"], parts["shapes"], gaps)
    conditions(pack, parts["shapes"], parts["enums"], gaps)
    parameters(pack, parts["shapes"], gaps)
    placement(pack, dist, parts["enums"], parts["recipes"], gaps)
    selectors(pack, parts["cb"], gaps)
    recipes_doc(pack, parts["recipes"], dist, "common/RECIPES.md",
                "Scope: `%s`." % meta["scope"]
                + ("" if parts["model"] else
                   " Contract scope, so every selector below is a "
                   "placeholder of the form `#<thing>`, to be replaced with a "
                   "real selector before sending."),
                gaps)
    provenance(pack, dist, meta)

    pack.json("common/index/report-contract.json", contract,
              "dist/index/semantic-contract.json → propertyContracts.report")
    pack.json("common/index/report-type-pairings.json", parts["pairings"],
              "dist/models/normalized-samples/ → reports matched by id")
    pack.json("common/index/report-types.json", parts["types"],
              "dist/index/ai-export-properties.json → enums, and "
              "dist/models/normalized-samples/")
    pack.json("common/index/report-enums.json", parts["enums"],
              "dist/index/ai-export-properties.json → enums")
    pack.json("common/index/field-types.json", parts["fieldTypes"],
              "dist/index/semantic-contract.json → propertyContracts.field")
    pack.json("common/index/report-shapes.json", parts["shapes"],
              "dist/formats/ai-export-single-json.md → Observed paths")
    pack.json("common/index/legacy-report-table.json", parts["legacyTable"],
              "dist/formats/report-format.md")
    pack.json("common/index/recipes.json", parts["recipes"],
              "written by this compiler, validated against "
              "dist/index/semantic-contract.json")

    if parts["model"]:
        system_docs(pack, parts["model"], parts["systemRecipes"], dist, gaps)

    readme(pack, parts, meta, parts["model"])
    return pack
