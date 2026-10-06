"""The semantic write pipeline, traced from AiChangeBatch to the database.

Every stage below is a resolved call edge in `Barsa.Meta.SemanticExchange`,
which is not obfuscated, so the method names are real. What static analysis
gives here is the set of stages and the order they appear in each method body;
what it does not give is the branch conditions, so "when" a stage runs is
reported only where a guard is visible as a property read or a literal.

The terminal fact is the useful one: every provider ends at
`Barsa.Spl.ActiveObject.Create` / `Update` / `Delete` / `CRUD`, reached through
the typed metamodel (`TypeDef`, `FieldDef`, `MetaSystem`, `Report`, `Folder`),
not through SQL of its own.
"""

import re

from .cli_metadata import TYPEDEF, enum_members, is_enum
from .il_analysis import analyze_method

CORE_CALL = re.compile(r"^Barsa\.(Meta|Spl|Workflow)\.")
PERSIST = ("ActiveObject::Create", "ActiveObject::Update",
           "ActiveObject::Delete", "ActiveObject::CRUD")

# Shared helpers on AiChangeProviderBase that persist on a provider's behalf.
# The entity and field providers call these instead of ActiveObject directly,
# so a provider with no persistence call of its own is not one that fails to
# write -- it writes through the base.
BASE_PERSIST_HELPERS = ("AiChangeProviderBase::PrepareAndSave",
                        "AiChangeProviderBase::SaveSettingsAndReload")

STAGES = [
    {
        "stage": "1. Structural lint",
        "entryPoint": "BixWriteHelper.ValidateBatch(string)",
        "implementation": "SemanticV15Linter.ValidateRawBatch",
        "reads": "the raw JSON, before any deserialization",
        "produces": "a throw, or nothing",
        "notes": ("Twelve rules, all of them literals in the linter. The "
                  "forbidden-runtime-key set and the ContinueIndependent-only "
                  "policy rule live here. `tools/lint_change_batch.py` "
                  "reproduces this stage offline."),
    },
    {
        "stage": "2. Parse",
        "entryPoint": "BixWriteHelper.ParseBatch(string)",
        "implementation": "Newtonsoft.Json with the camelCase resolver",
        "reads": "the linted JSON",
        "produces": "AiChangeBatch",
        "notes": "No validation of its own beyond deserialization.",
    },
    {
        "stage": "3. Plan",
        "entryPoint": "BixWriteHelper.BuildPlan(AiChangeBatch)",
        "implementation": "AiChangePlanner.Build",
        "reads": "AiChangeBatch; the live metamodel, for target inspection",
        "produces": "AiChangePlan + AiPlanSummary + AiPlanDiagnostic[]",
        "notes": ("Re-gates profileVersion and the error policy, resolves a "
                  "provider per command, validates, resolves infrastructure "
                  "capabilities, fingerprints each command, collects temp "
                  "references into dependencies, plans dbName remaps, then "
                  "sorts by dependency. Nothing is written."),
    },
    {
        "stage": "4. Apply",
        "entryPoint": "BixWriteHelper.ApplyPlan(AiChangePlan)",
        "implementation": "AiBatchExecutor.Apply",
        "reads": "AiChangePlan",
        "produces": "AiApplyResult + AiCommandResult[] + AiBatchStatus",
        "notes": ("Re-gates the plan's profileVersion, preflights for targets "
                  "that changed since planning, then runs each command in "
                  "structural-phase order, then the deferred phase-3 stages, "
                  "then read-back verification."),
    },
    {
        "stage": "5. Mutate",
        "entryPoint": "IAiChangeProvider.Apply(AiSemanticChange, AiBatchExecutionContext)",
        "implementation": "one Ai*ChangeProvider per objectType",
        "reads": "the command's properties, with references already resolved",
        "produces": "AiProviderApplyResult carrying the new RealId",
        "notes": ("The provider loads or constructs the typed metamodel object "
                  "and persists it through Barsa.Spl.ActiveObject. This is the "
                  "only stage that writes."),
    },
    {
        "stage": "6. Verify",
        "entryPoint": "AiRuntimeVerifier.FinalReadBackAndVerify(plan, result)",
        "implementation": "AiRuntimeVerifier, with a Verify* per objectType",
        "reads": "the database, freshly",
        "produces": ("AiRuntimeObject[] on AiApplyResult.RuntimeReadBack, plus "
                     "per-command VerificationSucceeded"),
        "notes": ("Reads each written object back and compares it against what "
                  "was asked for, canonicalizing both sides first. Sibling "
                  "order is verified separately for fields and folders."),
    },
]

# AiChangePlanner.Build, in body order.
PLAN_STEPS = [
    ("guard", "null batch, profileVersion != 15, or StopBatch policy -> plan is invalid"),
    ("AiChangePlanner.AssignStableIds", "give every command a stable identity"),
    ("AiChangePlanner.BuildTempOwners", "map each tempId to the command that declares it"),
    ("AiProviderResolver.Resolve", "pick the provider whose CanHandle matches objectType"),
    ("AiChangePlanner.ValidateV15SemanticAuthority",
     "reject runtime identity that survived the lint"),
    ("AiSocWriteProjection.ValidateSoc", "separation-of-concerns check on the payload"),
    ("AiChangePlanner.PrepareV15ChangeForPlanInspection",
     "normalize the command so it can be inspected without mutating"),
    ("AiProviderPayloadPolicy.Prepare", "apply the provider's payload policy"),
    ("AiChangePlanner.ProjectCreateForStructuralValidation",
     "project a create far enough to validate its structure"),
    ("IAiChangeProvider.Validate", "the provider's own validation -> AiProviderValidation"),
    ("AiChangePlanner.ValidatePortableTransport", "asset and portability checks"),
    ("AiInfrastructureCapabilityResolver.ResolveForPlan",
     "bind required infrastructure capabilities, or fail with infrastructureBindingUnresolved"),
    ("IAiChangeProvider.BuildFingerprint",
     "record what the target looked like at plan time"),
    ("AiChangePlanner.CollectTempReferences",
     "derive Dependencies and RequiresApplyValidation"),
    ("AiChangePlanner.PlanDbNameRemaps", "plan physical column renames"),
    ("AiChangePlanner.ApplyFieldSiblingReconstructionOrder", "order sibling fields"),
    ("AiChangePlanner.SortByDependencies", "topologically order the commands"),
    ("AiChangePlanner.UpdateSummary", "fill AiPlanSummary"),
]

# AiBatchExecutor.Apply, in body order.
APPLY_STEPS = [
    ("guard", "null plan, or a non-v15 planned command -> rejected before mutation"),
    ("AiBatchExecutionContext", "created, then SetProfileVersion and SetAssetRoot"),
    ("AiBatchExecutor.PreflightConflicts",
     "'Target changed between plan and apply.' -- the fingerprint is rechecked"),
    ("AiBatchExecutor.PrepareChangeForExecution", "per command"),
    ("AiSocWriteProjection.ProjectForProvider", "project the payload for its provider"),
    ("AiBatchExecutor.ExtractInternalStages",
     "split off properties the lifecycle policy defers to phase 3"),
    ("AiApplyLifecyclePolicy.StructuralPhase", "decide the command's phase"),
    ("AiBatchExecutionContext.BeginCommand", "open a per-command scope"),
    ("AiBatchExecutor.ResolveReferencesForValidation",
     "resolve selectors and tempIds to runtime ids"),
    ("AiBatchExecutor.ApplyStructuredDbNameRemaps", "apply planned column renames"),
    ("IAiChangeProvider.Validate",
     "re-validated at apply time when RequiresApplyValidation is set"),
    ("IAiChangeProvider.Apply", "the mutation; returns RealId"),
    ("AiBatchExecutionContext.RecordPersistedObject", "remember what was written"),
    ("AiBatchExecutionContext.RegisterTemporaryId", "bind the tempId to its new real id"),
    ("AiRuntimeVerifier.ReconcilePartialMutation",
     "when a command applied only partially and can be reconciled immediately"),
    ("AiBatchExecutor.OrderPhase3Stages", "order the deferred stages"),
    ("AiBatchExecutor.ExecuteInternalStages", "run them -- the FinalWiring pass"),
    ("AiBatchExecutor.ApplyFieldSiblingRuntimeOrder", "fix sibling order in the database"),
    ("AiRuntimeVerifier.FinalReadBackAndVerify", "read back and compare"),
    ("AiBatchExecutor.CalculateBatchStatus", "-> AiBatchStatus"),
]


def lifecycle(asm):
    """The deferral model: phases, deferred kinds and subtype resolution."""
    phases = {}
    for rid in range(1, asm.row_count(TYPEDEF) + 1):
        tn = asm.type_full_name(rid) or ""
        if tn.endswith("AiSemanticReferenceLifecycle") and is_enum(asm, rid):
            phases = {v: n for n, v in enum_members(asm, rid)}
    return {
        "phases": [{"value": k, "name": v} for k, v in sorted(phases.items())],
        "policy": "AiApplyLifecyclePolicy",
        "deferralDecision": "AiApplyLifecyclePolicy.ShouldDeferToPhase3(change, property)",
        "deferredKinds": ["dependentDetail", "logic", "reference",
                          "semanticValue"],
        "placeholder": ("AiApplyLifecyclePolicy.CreateStructuralPlaceholder "
                        "stands in for a reference that cannot resolve yet; "
                        "the executor notes a runtime placeholder of -1 where "
                        "a provider needs one."),
        "subtypeResolution": ("AiApplyLifecyclePolicy.ResolveSubtype reads "
                              "`fieldType` for a field and `relationKind` for "
                              "a relation."),
        "stageType": "AiInternalExecutionStage",
        "stageProperties": ["Planned", "Change", "Lifecycle", "Name",
                            "PropertyPath", "DependsOnPropertyPaths"],
        "confidence": "Verified",
    }


def provider_mutations(asm):
    """Per provider: the typed metamodel it touches and how it persists."""
    out = []
    for rid in range(1, asm.row_count(TYPEDEF) + 1):
        tn = asm.type_full_name(rid) or ""
        short = tn.split(".")[-1]
        if "+" in tn or not (short.startswith("Ai")
                             and short.endswith(("ChangeProvider",
                                                 "ChangeProviderBase"))):
            continue
        start, end = asm.type_method_range(rid)
        core = set()
        object_types = set()
        via_base = set()
        for m in range(start, end):
            res = analyze_method(asm, m)
            if not res:
                continue
            if asm.method_name(m) == "CanHandle":
                object_types.update(res["strings"])
            for c in res["calls"]:
                if CORE_CALL.match(c) and "DataExchange" not in c:
                    core.add(c)
                for helper in BASE_PERSIST_HELPERS:
                    if helper in c:
                        via_base.add(helper.split("::")[-1])
        types_touched = sorted({c.split("::")[0] for c in core})
        persists = sorted({p for p in PERSIST
                           if any(p in c for c in core)})
        out.append({
            "provider": short,
            "objectTypes": sorted(object_types),
            "barsaTypesTouched": types_touched,
            "persistenceCalls": persists,
            "persistsViaBaseHelpers": sorted(via_base),
            "writes": bool(persists or via_base),
            "coreCallCount": len(core),
        })
    return sorted(out, key=lambda r: r["provider"])


def summary(asm):
    mutations = provider_mutations(asm)
    return {
        "stages": STAGES,
        "planSteps": [{"step": a, "what": b} for a, b in PLAN_STEPS],
        "applySteps": [{"step": a, "what": b} for a, b in APPLY_STEPS],
        "lifecycle": lifecycle(asm),
        "providerMutations": mutations,
        "persistenceBase": ("Barsa.Spl.ActiveObject -- Create, Update, Delete "
                            "and CRUD. No provider issues SQL of its own."),
        "persistenceNote": (
            "A provider with no ActiveObject call of its own persists through "
            "AiChangeProviderBase.PrepareAndSave or SaveSettingsAndReload, "
            "which run TypeDef.CheckTypeDefCRUDForUniqueness, then "
            "ActiveObject.CRUD, then TypeDefCacheNew.Reload. The entity and "
            "field providers take that route."),
        "providersWithNoTracedWrite": sorted(
            p["provider"] for p in mutations if not p["writes"]),
        "confidence": "Observed",
        "limits": ("Stage order is the order the calls appear in each method "
                   "body. Branch conditions were not reconstructed, so which "
                   "stages run for a given command is Unknown except where a "
                   "guard is visible as a property read or a literal."),
    }
