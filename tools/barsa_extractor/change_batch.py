"""The AiChangeBatch contract, derived from Barsa.Meta.SemanticExchange.

That assembly is not obfuscated, so the contract below is read from real
property names, real enum members and real IL string literals rather than
guessed from method names.

Evidence per section:

  shape        property tables of AiChangeBatch, AiSemanticChange,
               AiObjectReference, AiExecutionPolicy
  naming       BixWriteHelper.CreateJsonSettings installs
               CamelCasePropertyNamesContractResolver and a
               StringEnumConverter with CamelCaseText, so properties are
               camelCase and enum values are camelCase strings
  rules        SemanticV15Linter.ValidateRawBatch / ValidateToken /
               ValidateSelectorSyntax string literals, plus the forbidden-key
               set in its static constructor
  objectTypes  the literal each Ai*ChangeProvider matches in CanHandle
  errorCodes   AiChangePlanner / AiPatchHelper / AiProviderValidation literals
"""

import json
import re

PROFILE_VERSION = 15

# Ai*ChangeProvider.CanHandle literals. The planner also matches some of these
# case-insensitively (the literals "businessrule", "dynamiccommand",
# "uniqueconstraint" appear alongside the camelCase forms).
OBJECT_TYPES = (
    "system", "entity", "field", "relation", "view", "report", "folder",
    "workflow", "businessRule", "uniqueConstraint", "dynamicObject",
    "dynamicCommand",
)

# AiChangeOperation, camelCased by the StringEnumConverter.
OPERATIONS = ("create", "update", "delete")

# SemanticV15Linter's static forbidden-key set. An authored batch may not carry
# runtime identity: references go through selectors or tempIds instead.
FORBIDDEN_RUNTIME_KEYS = ("id", "rowId", "sourceId", "runtimeId",
                          "dependencyKey")

# AiBatchErrorPolicy has StopBatch, but the linter rejects it for an authored
# batch: "Semantic v15 supports only ContinueIndependent; StopBatch is not an
# executable authored policy."
ALLOWED_ERROR_POLICIES = ("continueIndependent",)

ERROR_CODES = (
    "assetHashInvalid", "assetPathInvalid", "assetPreflightFailed",
    "assetRootMissing", "assetSchemaInvalid", "batchFatalInfrastructure",
    "commandLocalValidationFailed", "dependencyKeyForbiddenV15",
    "infrastructureBindingUnresolved", "legacyReferenceAuthorityForbiddenV15",
    "planValidation", "runtimeAuthorityForbiddenV15",
    "semanticSelectorUnresolved", "targetInspectionFailed", "targetNotFound",
    "unknownTempId", "unsupportedProperty",
)

# SemanticSelectorCodec: '#' then a name, or a bracketed escaped key list.
SELECTOR_RE = re.compile(r"^#+(\[.*\]|[^\[\s].*)$")


def json_schema():
    """A JSON Schema for an authored AiChangeBatch."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://barsa.local/schemas/ai-change-batch.v15.json",
        "title": "Barsa AiChangeBatch (profileVersion 15)",
        "description": (
            "The document BixWriteHelper.ParseBatch accepts. Derived from the "
            "property tables and linter rules of Barsa.Meta.SemanticExchange, "
            "not from a supplied sample: no AiChangeBatch artifact was "
            "available. Treat it as Verified for shape and rules, Unknown for "
            "whatever the server enforces beyond them."),
        "type": "object",
        "required": ["profileVersion", "changes"],
        "additionalProperties": False,
        "properties": {
            "profileVersion": {
                "const": PROFILE_VERSION,
                "description": ("Hard-gated. ValidateBatch rejects anything "
                                "else: 'Runtime accepts only explicit "
                                "profileVersion=15 input.'"),
            },
            "changes": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/change"},
                "description": ("Required and non-empty: 'AiChangeBatch must "
                                "contain changes[].' Null or non-object "
                                "entries are rejected by index."),
            },
            "policy": {"$ref": "#/$defs/policy"},
            "assetRoot": {
                "type": ["string", "null"],
                "description": ("Base path for asset references. Related "
                                "error codes: assetRootMissing, "
                                "assetPathInvalid, assetHashInvalid."),
            },
        },
        "$defs": {
            "policy": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "errorPolicy": {
                        "enum": list(ALLOWED_ERROR_POLICIES),
                        "description": (
                            "AiBatchErrorPolicy also defines StopBatch, but an "
                            "authored batch may only use ContinueIndependent."),
                    },
                    "ignoreUnsupported": {"type": "boolean"},
                },
            },
            "objectReference": {
                "type": "object",
                "additionalProperties": False,
                "description": ("How a command points at an object. Use "
                                "selector, or tempId for something created "
                                "earlier in the same batch. The id property "
                                "exists on the CLR type but is forbidden in an "
                                "authored document."),
                "properties": {
                    "objectType": {"enum": list(OBJECT_TYPES)},
                    "tempId": {"type": "string"},
                    "selector": {"$ref": "#/$defs/selector"},
                    "name": {"type": "string"},
                    "caption": {"type": "string"},
                },
            },
            "selector": {
                "type": "string",
                "pattern": "^#",
                "description": ("A semantic selector as SemanticSelectorCodec "
                                "writes it: '#Name', or a bracketed escaped "
                                "key list when a component needs escaping."),
            },
            "change": {
                "type": "object",
                "required": ["commandId", "operation", "objectType"],
                "additionalProperties": False,
                "properties": {
                    "commandId": {
                        "type": "string",
                        "description": ("Unique within the batch; duplicates "
                                        "are rejected."),
                    },
                    "operation": {"enum": list(OPERATIONS)},
                    "objectType": {"enum": list(OBJECT_TYPES)},
                    "tempId": {
                        "type": "string",
                        "description": ("Declares a handle for an object this "
                                        "command creates. Only valid on a "
                                        "create, and only once per batch."),
                    },
                    "target": {"$ref": "#/$defs/objectReference"},
                    "parent": {"$ref": "#/$defs/objectReference"},
                    "properties": {
                        "type": "object",
                        "description": ("The object's properties, in the same "
                                        "vocabulary an AiExport projection "
                                        "uses for that $type. Unknown "
                                        "properties raise unsupportedProperty."),
                    },
                },
            },
        },
    }


def example():
    """A worked batch that satisfies every rule the linter enforces."""
    return {
        "_comment": (
            "Illustrative, not taken from a real artifact. It creates an "
            "entity, then a field on it by tempId, then a report over it by "
            "selector -- which exercises tempId declaration, tempId reference "
            "and selector reference in one batch."),
        "profileVersion": PROFILE_VERSION,
        "policy": {"errorPolicy": "continueIndependent",
                   "ignoreUnsupported": False},
        "changes": [
            {
                "commandId": "c1-create-entity",
                "operation": "create",
                "objectType": "entity",
                "tempId": "tmpGate",
                "parent": {"objectType": "system", "selector": "#بارکد"},
                # dbName, not DbName: the contract is camelCase throughout,
                # unlike the AiExport projection which keeps the CLR casing.
                "properties": {"caption": "گیت", "dbName": "dyn_gate"},
            },
            {
                "commandId": "c2-create-field",
                "operation": "create",
                "objectType": "field",
                "tempId": "tmpGateTitle",
                "parent": {"objectType": "entity", "tempId": "tmpGate"},
                # orderNumber is ReconstructionOnly in the contract, so it is
                # not authorable here even though it appears in an export.
                "properties": {"caption": "عنوان", "fieldType": "string",
                               "maximumLength": 200},
            },
            {
                "commandId": "c3-update-report",
                "operation": "update",
                "objectType": "report",
                "target": {"objectType": "report", "selector": "#گیت ها"},
                "properties": {"reportType": "list"},
            },
        ],
    }


# --- linter ----------------------------------------------------------------

def load_contract(path=None):
    """Load the recovered semantic contract, if it has been generated.

    The contract is recovered from the assembly by `semantic_contract`, so the
    linter can check `properties` against it without the DLL being present.
    """
    import os
    candidates = [path] if path else []
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates += [
        os.path.join(here, "..", "dist", "index", "semantic-contract.json"),
        os.path.join(here, "dist", "index", "semantic-contract.json"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            try:
                with open(c, encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, ValueError):
                continue
    return None


def authorable_properties(contract, object_type, operation, subtype=None):
    """Property names the contract allows for this objectType and operation.

    Mirrors SemanticContractRegistry.GetAuthorablePropertyNames: a property is
    authorable when its classification is Writable and the matching
    writableOnCreate / writableOnUpdate flag is set. A property restricted to
    subtypes only applies when that subtype is in play, and since an authored
    batch need not state the subtype, every subtype-scoped name is accepted
    unless one was given.
    """
    if not contract:
        return None
    rows = (contract.get("propertyContracts") or {}).get(object_type)
    if rows is None:
        return None
    allowed = set()
    for r in rows:
        if r.get("classification") != "Writable":
            continue
        if operation == "create" and not r.get("writableOnCreate"):
            continue
        if operation == "update" and not r.get("writableOnUpdate"):
            continue
        subs = r.get("subtypes") or []
        if subs and subtype and subtype not in subs:
            continue
        if r.get("property"):
            allowed.add(r["property"])
    return allowed


def lint(doc, contract=None):
    """Reproduce SemanticV15Linter.ValidateRawBatch offline.

    Returns a list of findings, each with the rule and the literal the binary
    uses for it, so a failure here can be matched to the message the server
    would produce. This is a convenience, not a substitute: the server does
    more than the raw lint.

    When a recovered semantic contract is supplied, `properties` is additionally
    checked against the authorable set for that objectType and operation. That
    check is not part of SemanticV15Linter -- the server raises
    `unsupportedProperty` later, during planning -- so those findings are
    reported as warnings rather than lint errors.
    """
    out = []

    def err(path, rule, message):
        out.append({"path": path, "rule": rule, "message": message,
                    "severity": "error"})

    if doc is None:
        err("$", "rootNotNull", "AiChangeBatch JSON root is null.")
        return out
    if not isinstance(doc, dict):
        err("$", "rootIsObject", "AiChangeBatch JSON root must be an object.")
        return out

    if "externalDataMappings" in doc:
        err("$.externalDataMappings", "noLegacyExternalDataMappings",
            "Semantic v15 authored package root must not contain legacy "
            "externalDataMappings.")

    pv = doc.get("profileVersion")
    if pv != PROFILE_VERSION:
        err("$.profileVersion", "profileVersionGate",
            "Runtime accepts only explicit profileVersion=15 input. Found: %r"
            % (pv,))

    policy = doc.get("policy")
    if isinstance(policy, dict):
        ep = policy.get("errorPolicy")
        if ep is not None and str(ep)[:1].lower() + str(ep)[1:] \
                not in ALLOWED_ERROR_POLICIES:
            err("$.policy.errorPolicy", "errorPolicyContinueIndependentOnly",
                "Semantic v15 supports only ContinueIndependent; StopBatch is "
                "not an executable authored policy.")

    changes = doc.get("changes")
    if not isinstance(changes, list) or not changes:
        err("$.changes", "changesRequired",
            "AiChangeBatch must contain changes[].")
        return out

    command_ids = set()
    declared_temp = set()
    # tempId declarations are collected first: a reference may legally appear
    # before its declaration in document order, since the planner orders
    # commands by dependency rather than by position.
    for i, ch in enumerate(changes):
        if isinstance(ch, dict) and ch.get("tempId"):
            declared_temp.add(ch["tempId"])

    for i, ch in enumerate(changes):
        base = "$.changes[%d]" % i
        if not isinstance(ch, dict):
            err(base, "changeIsObject",
                "changes[] cannot contain null/non-object values at index %d."
                % i)
            continue

        cid = ch.get("commandId")
        if not cid:
            err(base + ".commandId", "commandIdRequired",
                "commandId is required.")
        elif cid in command_ids:
            err(base + ".commandId", "commandIdUnique",
                "Duplicate commandId: %s" % cid)
        else:
            command_ids.add(cid)

        op = ch.get("operation")
        if op not in OPERATIONS:
            err(base + ".operation", "operationKnown",
                "operation must be one of %s. Found: %r"
                % (", ".join(OPERATIONS), op))

        ot = ch.get("objectType")
        if ot is not None and ot not in OBJECT_TYPES \
                and ot.lower() not in [t.lower() for t in OBJECT_TYPES]:
            err(base + ".objectType", "objectTypeKnown",
                "objectType has no registered provider. Known: %s"
                % ", ".join(OBJECT_TYPES))

        if ch.get("tempId") and op != "create":
            err(base + ".tempId", "tempIdCreateOnly",
                "Semantic v15 tempId can only be declared by create commands: "
                "%s" % ch["tempId"])

        _lint_token(ch, base, declared_temp, err, is_root_change=True)

        if contract and isinstance(ch.get("properties"), dict) \
                and op in ("create", "update") and ot:
            allowed = authorable_properties(
                contract, ot, op, ch["properties"].get("fieldType"))
            if allowed is None:
                out.append({
                    "path": base + ".objectType",
                    "rule": "contractUnknownObjectType",
                    "message": ("the recovered contract has no property table "
                                "for objectType %r" % ot),
                    "severity": "warning"})
            else:
                for key in sorted(ch["properties"]):
                    if key in allowed:
                        continue
                    out.append({
                        "path": "%s.properties.%s" % (base, key),
                        "rule": "unsupportedProperty",
                        "message": ("%r is not authorable on %s/%s per the "
                                    "recovered contract" % (key, ot, op)),
                        "severity": "warning"})

    seen_temp = set()
    for i, ch in enumerate(changes):
        if not isinstance(ch, dict):
            continue
        t = ch.get("tempId")
        if not t:
            continue
        if t in seen_temp:
            err("$.changes[%d].tempId" % i, "tempIdUniqueDeclaration",
                "Duplicate Semantic v15 tempId declaration: %s" % t)
        seen_temp.add(t)
    return out


def _lint_token(node, path, declared_temp, err, is_root_change=False):
    """Walk a value, applying the per-token rules."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = "%s.%s" % (path, key)
            # A change's own tempId is a declaration; anywhere else it is a
            # reference and must resolve within the batch.
            if key == "tempId" and isinstance(value, str):
                if not is_root_change and value not in declared_temp:
                    err(child, "tempIdReferenceDeclared",
                        "Semantic v15 tempId reference is not declared in this "
                        "logical batch at %s: %s." % (child, value))
            elif key in FORBIDDEN_RUNTIME_KEYS:
                err(child, "runtimeAuthorityForbiddenV15",
                    "Semantic v15 forbids Runtime authority '%s' at %s."
                    % (key, child))
            elif key == "selector":
                if not isinstance(value, str):
                    err(child, "selectorIsString",
                        "Semantic selector property must be a string at %s."
                        % child)
                elif not SELECTOR_RE.match(value):
                    err(child, "selectorSyntax",
                        "Semantic selector property is not valid selector "
                        "syntax at %s." % child)
            _lint_token(value, child, declared_temp, err)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _lint_token(value, "%s[%d]" % (path, i), declared_temp, err)


def contract_rows():
    """The documented contract, for rendering into the knowledge pack."""
    return [
        {"type": "AiChangeBatch", "role": "the authored input document",
         "properties": ["profileVersion", "changes", "policy", "assetRoot"]},
        {"type": "AiSemanticChange", "role": "one command inside changes[]",
         "properties": ["commandId", "operation", "objectType", "tempId",
                        "target", "parent", "properties"]},
        {"type": "AiObjectReference", "role": "how a command names an object",
         "properties": ["objectType", "id (forbidden when authored)", "tempId",
                        "selector", "name", "caption"]},
        {"type": "AiExecutionPolicy", "role": "batch-level behaviour",
         "properties": ["errorPolicy", "ignoreUnsupported"]},
        {"type": "AiChangePlan", "role": "BuildPlan output, not authored",
         "properties": ["planId", "createdAt", "isValid", "batch", "summary",
                        "changes", "warnings", "errors"]},
        {"type": "AiPlannedChange", "role": "one planned command",
         "properties": ["order", "profileVersion", "change", "provider",
                        "dependencies", "status", "fingerprint", "warnings",
                        "deferredValidations", "errors", "diagnostics",
                        "infrastructureBindings", "referenceBindings",
                        "dbNameRemaps", "requiresApplyValidation"]},
        {"type": "AiApplyResult", "role": "ApplyPlan output",
         "properties": ["planId", "status", "commands", "temporaryIds",
                        "affectedSystemIds", "runtimeReadBack", "dbNameRemaps",
                        "deferredBindings", "mutationApplied",
                        "partialMutation", "needsReconcile",
                        "verificationSucceeded", "reconstruction",
                        "succeededCount", "failedCount", "skippedCount"]},
        {"type": "AiCommandResult", "role": "per-command outcome",
         "properties": ["commandId", "objectType", "operation", "status",
                        "realId", "tempId", "message", "phase", "failureClass",
                        "semanticIdentity", "mutationStage", "mutationApplied",
                        "partialMutation", "needsReconcile",
                        "verificationSucceeded", "warnings", "errors"]},
    ]
