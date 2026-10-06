"""Worked AiChangeBatch recipes, validated by the authoritative linter.

Spec section 17: every recipe must pass `tools/lint_change_batch.py` with zero
errors and zero warnings. That validator is imported rather than reimplemented,
and the contract it checks against is the one in dist/, so a recipe cannot
drift from the contract without the build noticing.

Recipes bind real selectors when a system model supplies them. Where dist/ has
no selector for an object kind -- folders are the current case, because the ZIP
projection encodes navigation as directory structure and carries no selector --
the recipe keeps a placeholder and says so rather than inventing one.
"""

import copy
import os
import sys

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from barsa_extractor import change_batch as cb  # the authoritative validator

PLACEHOLDER_ENTITY = "#<entity>"
PLACEHOLDER_FIELD = "#<field>"
PLACEHOLDER_FIELD_2 = "#<field2>"
PLACEHOLDER_FOLDER = "#<parent-folder>"
PLACEHOLDER_VIEW = "#<view>"
PLACEHOLDER_REPORT = "#<existing-report>"


def _batch(*changes):
    return {
        "profileVersion": cb.PROFILE_VERSION,
        "policy": {"errorPolicy": "continueIndependent",
                   "ignoreUnsupported": False},
        "changes": list(changes),
    }


def definitions():
    """The recipe set, with placeholders and per-recipe notes."""
    return [
        {
            "id": "R1",
            "title": "A list report on an existing entity",
            "purpose": ("The smallest useful report: pick an entity, pick "
                        "columns, done."),
            "placeholders": ["entity", "field", "field2"],
            "notes": [
                ("The target entity is set by `parent`, not by a property. "
                 "`entity` is ReadOnly on a report, so this is the only way "
                 "to say which entity the report runs over -- and it cannot "
                 "be changed afterwards."),
                ("`reportType` uses the AiExport vocabulary (`list`), not the "
                 "CLR enum member (`ViewResults`). The mapping between them is "
                 "Inferred; see REPORT-TYPES.md."),
                ("`condition: {\"all\": []}` is an empty condition. `all` and "
                 "`any` line up with CombinationOperator. The comparison "
                 "operator vocabulary is Unknown, so no filled condition is "
                 "shown."),
            ],
            "batch": _batch({
                "commandId": "r1-create-report",
                "operation": "create",
                "objectType": "report",
                "parent": {"objectType": "entity",
                           "selector": PLACEHOLDER_ENTITY},
                "properties": {
                    "name": "Gate list",
                    "reportType": "list",
                    "columns": [
                        {"field": PLACEHOLDER_FIELD, "alias": "Title"},
                        {"field": PLACEHOLDER_FIELD_2, "alias": "Notes"},
                    ],
                    "condition": {"all": []},
                    "immediateExecute": True,
                },
            }),
        },
        {
            "id": "R2",
            "title": "A list report, placed under an existing folder",
            "purpose": ("A report nobody can navigate to is invisible. This "
                        "adds the placement row."),
            "placeholders": ["entity", "field", "parentFolder"],
            "notes": [
                ("Two commands, and the order matters: report is "
                 "structuralOrder 120 and folder is 130, so the report is "
                 "created first. The planner sorts by dependency anyway, but "
                 "writing them in this order matches what it will do."),
                ("A placement is a `folder` object whose `report` points at "
                 "the report. In the legacy tables that is a MET_FOLDER row "
                 "with FolderType=Report (9) under a FolderType=ReportFolder "
                 "(12) container."),
                ("`kind` is deliberately omitted. It is a create-only enum on "
                 "`folder` and its semantic value vocabulary is Unknown -- no "
                 "dist/ document lists the values the AiExport side uses. If "
                 "the server requires it, it has to be supplied."),
                ("The parent folder reference remains a placeholder. The "
                 "observed exports carry navigation paths, but no folder "
                 "selector; the inspected SemanticRules resolver also has no "
                 "folder selector case. See MISSING-FROM-DIST.md."),
            ],
            "batch": _batch(
                {
                    "commandId": "r2-create-report",
                    "operation": "create",
                    "objectType": "report",
                    "tempId": "tmpReport",
                    "parent": {"objectType": "entity",
                               "selector": PLACEHOLDER_ENTITY},
                    "properties": {
                        "name": "Gate list",
                        "reportType": "list",
                        "columns": [{"field": PLACEHOLDER_FIELD,
                                     "alias": "Title"}],
                        "condition": {"all": []},
                    },
                },
                {
                    "commandId": "r2-place-report",
                    "operation": "create",
                    "objectType": "folder",
                    "parent": {"objectType": "folder",
                               "selector": PLACEHOLDER_FOLDER},
                    "properties": {
                        "name": "Gate list",
                        "report": {"tempId": "tmpReport"},
                        "order": 1,
                    },
                },
            ),
            "unverified": [
                ("Encoding a same-batch reference as `{\"tempId\": \"...\"}` "
                 "inside a Reference property is not demonstrated by any "
                 "supplied artifact. The linter accepts it and the tempId "
                 "resolves within the batch, but whether the provider reads "
                 "that shape is Unknown. The command order and structure are "
                 "sound; this one encoding may need adjusting."),
            ],
        },
        {
            "id": "R3",
            "title": "Change the columns of an existing report",
            "purpose": "The most common edit.",
            "placeholders": ["existingReport", "field", "field2"],
            "notes": [
                ("`columns` is writable on update, so the whole column list is "
                 "replaced. There is no evidence in dist/ of a per-column "
                 "patch, so replacing the list is the only form shown."),
                ("The report is addressed by `target`, by selector. `entity` "
                 "and `system` cannot appear here: both are ReadOnly."),
            ],
            "batch": _batch({
                "commandId": "r3-update-columns",
                "operation": "update",
                "objectType": "report",
                "target": {"objectType": "report",
                           "selector": PLACEHOLDER_REPORT},
                "properties": {
                    "columns": [
                        {"field": PLACEHOLDER_FIELD, "alias": "Title"},
                        {"field": PLACEHOLDER_FIELD_2, "alias": "Notes"},
                    ],
                },
            }),
        },
        {
            "id": "R4",
            "title": "Delete a report",
            "purpose": "Included because `report` supports Delete and the shape differs.",
            "placeholders": ["existingReport"],
            "notes": [
                ("A delete carries no `properties`. `report` lists Delete "
                 "among its supported operations, so the operation is "
                 "available; what it does to the report's placement rows is "
                 "Unknown."),
            ],
            "batch": _batch({
                "commandId": "r4-delete-report",
                "operation": "delete",
                "objectType": "report",
                "target": {"objectType": "report",
                           "selector": PLACEHOLDER_REPORT},
            }),
        },
        {
            "id": "R5",
            "title": "A form report over a view",
            "purpose": "The second reportType actually observed in an artifact.",
            "placeholders": ["entity", "view"],
            "notes": [
                ("`reportType: \"form\"` and a `typeView` selector is the "
                 "shape the Push Notification artifact shows."),
                ("`typeView` is writable on create and update, and takes a "
                 "view selector."),
            ],
            "batch": _batch({
                "commandId": "r5-create-form-report",
                "operation": "create",
                "objectType": "report",
                "parent": {"objectType": "entity",
                           "selector": PLACEHOLDER_ENTITY},
                "properties": {
                    "name": "Gate form",
                    "reportType": "form",
                    "typeView": PLACEHOLDER_VIEW,
                    "condition": {"all": []},
                },
            }),
        },
        {
            "id": "R6",
            "title": "A read-only list report with paging",
            "purpose": ("Shows the permission and paging groups, which are "
                        "where most of the 80 properties live."),
            "placeholders": ["entity", "field"],
            "notes": [
                ("Every property here is writable on both create and update, "
                 "so the same body works as an update with `target` instead "
                 "of `parent`."),
                ("`pagingType` takes a ReportPagingType member; see "
                 "`index/report-enums.json`."),
            ],
            "batch": _batch({
                "commandId": "r6-create-readonly-report",
                "operation": "create",
                "objectType": "report",
                "parent": {"objectType": "entity",
                           "selector": PLACEHOLDER_ENTITY},
                "properties": {
                    "name": "Gate list, read only",
                    "reportType": "list",
                    "columns": [{"field": PLACEHOLDER_FIELD,
                                 "alias": "Title"}],
                    "condition": {"all": []},
                    "allowView": True,
                    "allowEdit": False,
                    "allowAddNew": False,
                    "allowRemove": False,
                    "allowGridColumnSort": True,
                    "pagingType": "Automatic",
                    "pageSize": 50,
                    "showRowNumber": True,
                },
            }),
        },
    ]


def _pick_bindings(model):
    """Real selectors for the placeholders, from a system model."""
    if not model or not model.get("authorable"):
        return {}, ["No AiExport artifact for this system, so no selector is "
                    "known and every placeholder stays unbound."]

    notes = []
    bindings = {}

    columnable = [f for f in model["fields"] if f.get("usableAsColumn")]
    by_entity = {}
    for f in columnable:
        if f.get("entitySelector"):
            by_entity.setdefault(f["entitySelector"], []).append(f)
    # Prefer an entity with at least two usable columns so R1 and R3 can show
    # a real two-column report.
    entity_sel = None
    for sel, fields in sorted(by_entity.items(), key=lambda kv: -len(kv[1])):
        entity_sel = sel
        break
    if entity_sel:
        bindings[PLACEHOLDER_ENTITY] = entity_sel
        fields = by_entity[entity_sel]
        bindings[PLACEHOLDER_FIELD] = fields[0]["selector"]
        if len(fields) > 1:
            bindings[PLACEHOLDER_FIELD_2] = fields[1]["selector"]
        else:
            notes.append(
                "Only one column-usable field exists on the chosen entity, so "
                "the second column placeholder stays unbound.")
    else:
        notes.append("No entity in this system has a column-usable field.")

    view = next((v for v in model["views"] if v.get("selector")), None)
    if view:
        bindings[PLACEHOLDER_VIEW] = view["selector"]
    else:
        notes.append("No view with a selector, so the form-report recipe keeps "
                     "its placeholder.")

    report = next((r for r in model["reports"] if r.get("selector")), None)
    if report:
        bindings[PLACEHOLDER_REPORT] = report["selector"]
    else:
        notes.append("No existing report with a selector, so the update and "
                     "delete recipes keep their placeholders.")

    notes.append(
        "Folder selectors are not bound: the observed navigation paths are "
        "identities for retrieval, but the SemanticRules resolver has no "
        "folder selector case. A path cannot be used as a batch selector.")
    return bindings, notes


def _substitute(node, bindings):
    if isinstance(node, dict):
        return {k: _substitute(v, bindings) for k, v in node.items()}
    if isinstance(node, list):
        return [_substitute(v, bindings) for v in node]
    if isinstance(node, str):
        return bindings.get(node, node)
    return node


def build(dist, model=None):
    """Bind, validate and return the recipes. Validation is the build gate."""
    contract = dist.contract
    bindings, binding_notes = _pick_bindings(model)
    known_selectors = _known_selectors(model)

    out = []
    for spec in definitions():
        batch = _substitute(copy.deepcopy(spec["batch"]), bindings)
        used = sorted(_collect_selectors(batch))
        unbound = [s for s in used if s.startswith("#<")]
        unknown = [s for s in used
                   if not s.startswith("#<") and known_selectors is not None
                   and s not in known_selectors]

        findings = cb.lint(batch, contract)
        errors = [f for f in findings if f.get("severity") != "warning"]
        warnings = [f for f in findings if f.get("severity") == "warning"]

        out.append({
            "id": spec["id"],
            "title": spec["title"],
            "purpose": spec["purpose"],
            "notes": spec["notes"],
            "unverified": spec.get("unverified", []),
            "batch": batch,
            "selectorsUsed": used,
            "selectorsUnbound": unbound,
            "selectorsNotInIndex": unknown,
            "selectorsBound": not unbound,
            "lint": {"errors": errors, "warnings": warnings,
                     "clean": not findings},
        })
    return {
        "recipes": out,
        "bindings": {k: v for k, v in sorted(bindings.items())},
        "bindingNotes": binding_notes,
        "validator": ("barsa_extractor.change_batch.lint, the same code path "
                      "tools/lint_change_batch.py runs"),
        "validatedAgainst": "dist/index/semantic-contract.json",
    }


def _known_selectors(model):
    if not model:
        return None
    sels = set()
    for coll in ("entities", "fields", "reports", "views", "folders"):
        for row in model.get(coll) or ():
            if row.get("selector"):
                sels.add(row["selector"])
    for s in model.get("selectors") or ():
        sels.add(s)
    return sels


def _collect_selectors(node, out=None):
    if out is None:
        out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("selector", "field", "typeView", "entity") \
                    and isinstance(v, str) and v.startswith("#"):
                out.add(v)
            else:
                _collect_selectors(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_selectors(v, out)
    return out
