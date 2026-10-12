"""Verification — what takes the place of build, lint and test here.

A code workflow asks: does it compile, does it lint, do the tests pass. A Barsa
change has no compiler, so the four gates below are the equivalent, and they
are the reason this pipeline is worth having at all:

  lint       the batch passes the contract linter recovered from the binary,
             with zero findings -- warnings included
  selectors  every selector the batch names exists in the scope's index, or is
             a tempId created earlier in the same batch
  unknowns   the batch does not author anything the knowledge pack marks
             Unknown, and every value it does author is drawn from a
             vocabulary the pack can name. This is the no-guessing gate, and
             it is the one that stops a plausible-looking batch from being
             quietly wrong
  scope      the batch touches only the objects the task holds a lock on
  order      commands are ordered by structuralOrder, and a parent is created
             before its child

Every gate returns findings in one shape, so the reviewer's evidence table and
the console can treat them alike.
"""

import json
import os
import sys

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from barsa_extractor import change_batch as cb

GATES = ("lint", "selectors", "unknowns", "scope", "order")

# Properties nothing in the pack can describe, at any level.
UNKNOWN_PROPERTIES = {
    "parameterLayout": ("ReadOnly, and declared out of Semantic v15 "
                        "reconstruction scope in v190."),
}

CONDITION_KEYS = ("condition", "treeCondition")

# What a condition clause may carry. Keys beyond these are refused rather
# than passed through: an unrecognised key is either a typo or a part of the
# contract this pack does not know, and both are reasons to stop.
# `path` and `items` are substructure of `field`, not keys of a clause, so
# they are not listed here. The legacy shape (`type`/`group`/`conditions`/
# `valueType`) is refused on purpose: the document says only the compact
# shape is canonical for anything written.
CLAUSE_KEYS = ("field", "operator", "value", "parameter", "nullBehavior",
               "customSql", "enabled", "ignoreCase", "autoSetInNew",
               "dateComparisonMode")

# Without a vocabulary from the pack, these stay closed. The gate is only as
# permissive as the evidence it was given.
_CLOSED = {
    "operator": ("The comparison operator vocabulary is not in the pack, so "
                 "no filled condition can be checked. Write an empty "
                 "condition, or build dist/ with the Host's reference docs "
                 "under source/barsa-ai-host/."),
    "parameters": ("The shape of a report parameter is not in the pack. "
                   "Create the report without parameters and let a human add "
                   "them."),
    "kind": ("The folder kind vocabulary is not in the pack. Omit it; if the "
             "server requires it, it has to come from outside the pack."),
}


def finding(gate, severity, message, where=None, hint=None):
    return {"gate": gate, "severity": severity, "message": message,
            "where": where, "hint": hint}


# -- the gates -------------------------------------------------------------

def gate_lint(batch, contract):
    """The authoritative linter, reused rather than reimplemented."""
    out = []
    for f in cb.lint(batch, contract):
        out.append(finding(
            "lint",
            "error" if f.get("severity") != "warning" else "warning",
            f.get("message"), f.get("path")))
    return out


def gate_selectors(batch, index):
    """Every selector must resolve, or be a tempId created in this batch."""
    out = []
    known = set((index or {}).get("selectors") and
                [row["selector"] for row in index["selectors"]] or [])
    temp_ids = set()
    for change in batch.get("changes") or ():
        if change.get("tempId"):
            temp_ids.add(change["tempId"])

    for i, change in enumerate(batch.get("changes") or ()):
        for where, value in _selector_refs(change):
            path = "changes[%d].%s" % (i, where)
            if value.startswith("#<") and value.endswith(">"):
                out.append(finding(
                    "selectors", "error",
                    "placeholder %s was never replaced with a real selector"
                    % value, path,
                    "Copy the selector from the scope's selectors.json; never "
                    "type it -- Arabic and Persian letter forms are mixed in "
                    "this data."))
            elif not known:
                out.append(finding(
                    "selectors", "error",
                    "no selector index for this scope, so %s cannot be "
                    "resolved" % value, path,
                    "Compile a system-scoped report pack: "
                    "tools/report_compiler.py --scope system=<id>"))
            elif value not in known:
                out.append(finding(
                    "selectors", "error",
                    "selector %s is not in this scope's index" % value, path,
                    "A near-identical name may differ in its yeh or kaf form; "
                    "copy the string from selectors.json."))
        for where, value in _temp_refs(change):
            if value not in temp_ids:
                out.append(finding(
                    "selectors", "error",
                    "tempId %r is referenced but no command in this batch "
                    "creates it" % value, "changes[%d].%s" % (i, where)))
    return out


def gate_unknowns(batch, vocabulary=None):
    """Refuse to author what the pack cannot name.

    With no vocabulary this is the old rule: no filled condition, no
    parameters, no folder kind. With one, those become real checks -- every
    operator, nullBehavior and folder kind must be a value the pack can
    point at in a source document. Permissiveness here only ever comes from
    evidence, never from the absence of it.
    """
    out = []
    vocabulary = vocabulary or {}
    operators = _values(vocabulary, "comparisonOperators")
    null_behaviors = _values(vocabulary, "nullBehaviors")
    folder_kinds = _values(vocabulary, "folderKinds")
    parameter_keys = _values(vocabulary, "reportParameterKeys")
    temp_ref_keys = _values(vocabulary, "tempIdReferenceEncoding")

    for i, change in enumerate(batch.get("changes") or ()):
        props = change.get("properties") or {}
        otype = change.get("objectType")
        where = "changes[%d].properties" % i

        for name, why in UNKNOWN_PROPERTIES.items():
            if name in props:
                out.append(finding(
                    "unknowns", "error",
                    "%s is written here, but its shape is Unknown" % name,
                    "%s.%s" % (where, name), why))

        for key in CONDITION_KEYS:
            if key in props:
                out += _check_condition(props[key], "%s.%s" % (where, key),
                                        operators, null_behaviors)

        if "parameters" in props:
            out += _check_parameters(props["parameters"],
                                     "%s.parameters" % where, parameter_keys)

        if temp_ref_keys:
            out += _check_temp_refs(props, where, temp_ref_keys)

        if otype == "folder" and "kind" in props:
            kind = props["kind"]
            if not folder_kinds:
                out.append(finding("unknowns", "error",
                                   "folder.kind is written here",
                                   "%s.kind" % where, _CLOSED["kind"]))
            elif kind not in folder_kinds:
                out.append(finding(
                    "unknowns", "error",
                    "folder kind %r is not one the pack knows" % (kind,),
                    "%s.kind" % where,
                    "The pack lists: %s." % ", ".join(folder_kinds)))
    return out


def _check_temp_refs(value, where, required):
    """A same-batch reference must carry every key the document shows.

    The Host's folder reference writes one out as an object carrying both
    `objectType` and `tempId`. A bare `{"tempId": ...}` lints clean against
    the contract and is not the documented shape, so it is caught here
    rather than at apply time.
    """
    out = []
    if isinstance(value, dict):
        if "tempId" in value:
            missing = [k for k in required if k not in value]
            if missing:
                out.append(finding(
                    "unknowns", "error",
                    "%s is a same-batch reference missing %s"
                    % (where, ", ".join(missing)),
                    where,
                    "The Host's reference writes one as an object carrying "
                    "%s. Add the missing key(s)." % ", ".join(required)))
            return out
        for k, v in value.items():
            out += _check_temp_refs(v, "%s.%s" % (where, k), required)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += _check_temp_refs(v, "%s[%d]" % (where, i), required)
    return out


def _check_condition(value, where, operators, null_behaviors):
    """An empty condition always passes; a filled one must be checkable."""
    clauses = _condition_clauses(value)
    if clauses is None:
        return [finding(
            "unknowns", "error", "%s is not an all/any condition" % where,
            where,
            'A condition is {"all": [...]} or {"any": [...]}, nested '
            'recursively.')]
    if not clauses:
        return []
    if not operators:
        return [finding(
            "unknowns", "error",
            "%s carries %d clause(s) and the operator vocabulary is not in "
            "the pack" % (where, len(clauses)), where, _CLOSED["operator"])]

    out = []
    for j, clause in enumerate(clauses):
        at = "%s[%d]" % (where, j)
        if not isinstance(clause, dict):
            out.append(finding("unknowns", "error",
                               "a clause must be an object", at))
            continue
        # A clause may itself be a nested group.
        if _condition_clauses(clause) is not None:
            out += _check_condition(clause, at, operators, null_behaviors)
            continue
        operator = clause.get("operator")
        if operator is None:
            out.append(finding("unknowns", "error",
                               "a clause without an operator", at))
        elif operator not in operators:
            out.append(finding(
                "unknowns", "error",
                "operator %r is not one the pack knows" % (operator,),
                "%s.operator" % at,
                "The pack lists %d: %s." % (len(operators),
                                            ", ".join(operators))))
        behavior = clause.get("nullBehavior")
        if behavior is not None and null_behaviors \
                and behavior not in null_behaviors:
            out.append(finding(
                "unknowns", "error",
                "nullBehavior %r is not one the pack knows" % (behavior,),
                "%s.nullBehavior" % at,
                "The pack lists: %s." % ", ".join(null_behaviors)))
        for key in clause:
            if key not in CLAUSE_KEYS:
                out.append(finding(
                    "unknowns", "error",
                    "a clause key the pack does not know: %r" % key,
                    "%s.%s" % (at, key),
                    "Known keys: %s." % ", ".join(CLAUSE_KEYS)))
    return out


def _check_parameters(value, where, parameter_keys):
    if not parameter_keys:
        return [finding("unknowns", "error",
                        "parameters are written here", where,
                        _CLOSED["parameters"])]
    if not isinstance(value, list):
        return [finding("unknowns", "error",
                        "parameters must be a list", where)]
    out = []
    for j, row in enumerate(value):
        at = "%s[%d]" % (where, j)
        if not isinstance(row, dict):
            out.append(finding("unknowns", "error",
                               "a parameter must be an object", at))
            continue
        if not row.get("name"):
            out.append(finding("unknowns", "error",
                               "a parameter without a name", at))
        for key in row:
            if key not in parameter_keys:
                out.append(finding(
                    "unknowns", "error",
                    "a parameter key the pack does not know: %r" % key,
                    "%s.%s" % (at, key),
                    "The pack lists: %s." % ", ".join(parameter_keys)))
    return out


def _values(vocabulary, name):
    row = (vocabulary or {}).get(name)
    return tuple(row.get("values") or ()) if isinstance(row, dict) else ()


def gate_scope(batch, scope):
    """The batch may touch only objects the task holds a lock on."""
    out = []
    allow = set((scope or {}).get("allow") or ())
    deny = set((scope or {}).get("deny") or ())
    if not allow:
        return [finding("scope", "error",
                        "the task holds no scope, so no object may be touched",
                        None,
                        "scope.allow is set from the architect's plan.")]
    for i, change in enumerate(batch.get("changes") or ()):
        for entry in _scope_entries(change):
            if entry in deny:
                out.append(finding("scope", "error",
                                   "%s is in scope.deny" % entry,
                                   "changes[%d]" % i))
            elif entry not in allow and not _covered(entry, allow):
                out.append(finding(
                    "scope", "error",
                    "%s is outside this task's scope" % entry,
                    "changes[%d]" % i,
                    "Either the plan is wrong or the batch widened it. The "
                    "scope lock exists so two tasks cannot change the same "
                    "object."))
    return out


def gate_order(batch, contract):
    """structuralOrder ordering, and parents before children."""
    out = []
    orders = {}
    for row in contract.get("objectContracts") or ():
        orders[row.get("objectType")] = row.get("structuralOrder")

    created = set()
    previous = None
    for i, change in enumerate(batch.get("changes") or ()):
        otype = change.get("objectType")
        order = orders.get(otype)
        if order is None:
            out.append(finding("order", "error",
                               "objectType %r has no structuralOrder in the "
                               "contract" % otype, "changes[%d]" % i))
            continue
        if previous is not None and order < previous[1]:
            out.append(finding(
                "order", "error",
                "%s (structuralOrder %s) comes after %s (%s); a batch is "
                "written in structural order"
                % (otype, order, previous[0], previous[1]),
                "changes[%d]" % i,
                "The planner sorts by dependency anyway, but writing them out "
                "of order hides a real dependency mistake."))
        previous = (otype, order)

        parent = change.get("parent") or {}
        temp = parent.get("tempId") if isinstance(parent, dict) else None
        if temp and temp not in created:
            out.append(finding(
                "order", "error",
                "parent tempId %r is used before the command that creates it"
                % temp, "changes[%d].parent" % i))
        if change.get("tempId"):
            created.add(change["tempId"])
    return out


# -- running them all ------------------------------------------------------

def run(batch, contract, scope, index, gates=GATES, vocabulary=None):
    """Run the gates and return (findings, summary)."""
    findings = []
    if "lint" in gates:
        findings += gate_lint(batch, contract)
    if "selectors" in gates:
        findings += gate_selectors(batch, index)
    if "unknowns" in gates:
        findings += gate_unknowns(batch, vocabulary)
    if "scope" in gates:
        findings += gate_scope(batch, scope)
    if "order" in gates:
        findings += gate_order(batch, contract)

    summary = {}
    for gate in gates:
        rows = [f for f in findings if f["gate"] == gate]
        summary[gate] = {
            "errors": sum(1 for f in rows if f["severity"] == "error"),
            "warnings": sum(1 for f in rows if f["severity"] == "warning"),
            "passed": not rows,
        }
    summary["passed"] = not findings
    return findings, summary


def load_selector_index(repo_root, system_id, pack="dist-report"):
    """The scope's selector index, from the compiled report pack."""
    if not system_id:
        return None
    path = os.path.join(repo_root, pack, "systems", str(system_id), "index",
                        "selectors.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_vocabulary(repo_root, dist="dist"):
    """The vocabularies the Host's own documents state, if dist/ has them."""
    path = os.path.join(repo_root, dist, "index", "host-vocabulary.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_contract(repo_root, dist="dist"):
    path = os.path.join(repo_root, dist, "index", "semantic-contract.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# -- walking a change ------------------------------------------------------

_SELECTOR_KEYS = ("selector", "field", "typeView", "entity", "report",
                  "parent", "target", "previewField", "selfReferencingField")


def _selector_refs(node, prefix="", out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for key, value in node.items():
            where = "%s.%s" % (prefix, key) if prefix else key
            if key in _SELECTOR_KEYS and isinstance(value, str) \
                    and value.startswith("#"):
                out.append((where, value))
            else:
                _selector_refs(value, where, out)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _selector_refs(value, "%s[%d]" % (prefix, i), out)
    return out


def _temp_refs(node, prefix="", out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for key, value in node.items():
            where = "%s.%s" % (prefix, key) if prefix else key
            if key == "tempId" and isinstance(value, str) and prefix:
                # A tempId nested inside a property is a reference; the one at
                # the top of a command is a declaration.
                out.append((where, value))
            else:
                _temp_refs(value, where, out)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _temp_refs(value, "%s[%d]" % (prefix, i), out)
    return out


def _scope_entries(change):
    """Which Barsa objects this command touches, as scope entries."""
    out = []
    otype = change.get("objectType")
    for key in ("target", "parent"):
        ref = change.get(key)
        if isinstance(ref, dict) and ref.get("selector"):
            out.append("%s:%s" % (ref.get("objectType") or otype,
                                  ref["selector"]))
    if change.get("operation") == "create":
        name = (change.get("properties") or {}).get("name")
        if name:
            out.append("%s:#%s" % (otype, name))
    return out


def _covered(entry, allow):
    """`report:*` covers every report; an exact entry covers only itself."""
    otype = entry.split(":", 1)[0]
    return ("%s:*" % otype) in allow


def _condition_clauses(value):
    """The clause list of an all/any condition, or None if it is not one."""
    if not isinstance(value, dict) or len(value) != 1:
        return None
    key, clauses = next(iter(value.items()))
    if key not in ("all", "any") or not isinstance(clauses, list):
        return None
    return clauses
