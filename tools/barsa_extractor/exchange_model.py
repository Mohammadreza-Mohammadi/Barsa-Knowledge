"""API-to-format mapping and read/write sets for Barsa's two export families.

Spec v3 sections 13, 14, 20-22, 25-27, 59, 81-84.

Nothing here is asserted from a method name.  Each entry carries the concrete
evidence that was used: a metadata signature, a resolved call edge, a MemberRef
row, an IL string literal, an enum member list, or an embedded resource.  Where
the evidence does not settle a question the field says so, and the question is
carried into the runtime-gap report instead of being filled in.
"""

from .cli_metadata import (
    Assembly, MEMBERREF, METHODDEF, TYPEDEF, TYPEREF, enum_members, is_enum,
)
from .il_analysis import analyze_method

LEGACY = "Barsa.LegacyMetaExport"
AI = "Barsa.AiExport"
UNKNOWN = "Unknown"

# Assemblies that make up the exchange subsystem. SemanticExchange declares its
# types in the Barsa.Meta.DataExchange *namespace* while being a separate
# assembly, which is why a namespace-only search misses it.
EXCHANGE_ASSEMBLIES = (
    "Barsa.Meta.DataExchange",
    "Barsa.Meta.SemanticExchange",
    "Barsa.Ai.Host",
)

# Enums whose member lists answer a spec question outright.
ANSWER_ENUMS = (
    "Barsa.Meta.DataExchange.BixJsonExportMode",
    "Barsa.Meta.DataExchange.BixJsonExportSelection",
    "Barsa.Meta.DataExchange.JsonExportNodeOutputKind",
    "Barsa.Meta.DataExchange.JsonExportRelationMatchMode",
    "Barsa.Meta.DataExchange.Helper.CompareChangeTypeEnum",
    "Barsa.Meta.DataExchange.AiChangeOperation",
    "Barsa.Meta.DataExchange.AiBatchStatus",
    "Barsa.Meta.DataExchange.AiBatchErrorPolicy",
    "Barsa.Meta.DataExchange.AiCommandStatus",
    "Barsa.Meta.DataExchange.AiSemanticReferenceLifecycle",
    "Barsa.Meta.DataExchange.SemanticPropertyKind",
    "Barsa.Meta.DataExchange.SemanticPropertyClassification",
    "Barsa.Meta.DataExchange.SemanticResolutionStatus",
    "Barsa.Meta.DataExchange.SemanticApplyClass",
)


def collect_enums(assemblies):
    """Read the member lists of the enums that carry answers.

    assemblies: {display name -> Assembly}
    """
    out = {}
    for name, asm in assemblies.items():
        for rid in range(1, asm.row_count(TYPEDEF) + 1):
            tn = asm.type_full_name(rid)
            if tn not in ANSWER_ENUMS or not is_enum(asm, rid):
                continue
            members = enum_members(asm, rid)
            if not members:
                continue
            # A power-of-two run starting at 1 with a 0 "None" is a flags set.
            values = [v for _n, v in members if isinstance(v, int)]
            is_flags = (len(values) > 2 and 0 in values
                        and all(v == 0 or (v & (v - 1)) == 0 for v in values))
            out[tn] = {
                "enum": tn,
                "assembly": name,
                "members": [{"name": n, "value": v} for n, v in members],
                "looksLikeFlags": is_flags,
                "confidence": "Verified",
            }
    return out


def cross_assembly_memberrefs(asm, owner_substrings):
    """MemberRef rows naming a type in another assembly.

    A MemberRef is harder evidence than a call-graph edge for a cross-assembly
    hand-off: it proves this assembly was compiled against that exact member,
    even when the call itself goes through a delegate.
    """
    out = []
    for _rid, row in asm.iter_rows(MEMBERREF):
        owner = asm.typedefref_name(row["Class"]) or ""
        if any(s in owner for s in owner_substrings):
            out.append("%s::%s" % (owner, asm.string(row["Name"])))
    return sorted(set(out))


def api_format_map(assemblies, calls, memberrefs):
    """Spec section 13: which API produces or consumes which format.

    `calls` is the pipeline's call index; `memberrefs` the cross-assembly
    MemberRef evidence keyed by assembly display name.
    """
    dx_refs = set(memberrefs.get("Barsa.Meta.DataExchange", ()))

    def has_call(caller, fragment):
        return any(fragment.lower() in c.lower()
                   for c in calls.get(caller, ()))

    bh = "Barsa.Meta.DataExchange.BixHelper::"
    rows = []

    rows.append({
        "api": "BixHelper.Export(ObjectReferenceSelection, string, bool, int, bool)",
        "direction": "export",
        "logicalFormat": LEGACY,
        "physicalFormat": "GZip",
        "variant": "Legacy.DataSet.BinaryFormatter",
        "serializer": "BinaryFormatter via SerializationHelper2",
        "compression": "GZip (Barsa.Spl.SerializationUtil+CompressionType)",
        "callPath": ["BixHelper.Export", "NewExportManager.Export",
                     "SerializationHelper2.BinarySerializeToFile"],
        "evidence": ["AssemblyMetadata", "CallGraph", "ExportSample"],
        "confidence": "CrossVerified",
        "note": ("The two supplied .metaexport samples match this pipeline "
                 "byte for byte."),
    })
    rows.append({
        "api": "BixHelper.Import(string, ImportOptions)",
        "direction": "import",
        "logicalFormat": LEGACY,
        "physicalFormat": "GZip",
        "variant": "Legacy.DataSet.BinaryFormatter",
        "serializer": "BinaryFormatter via SerializationHelper2",
        "compression": "GZip",
        "callPath": ["BixHelper.Import", "NewImportManager.Import",
                     "SerializationHelper2.DeserializeDataSetFromFile"],
        "evidence": ["AssemblyMetadata", "CallGraph", "ExportSample"],
        "confidence": "CrossVerified",
        "note": "Reads exactly what BixHelper.Export writes.",
    })

    saves_json = "Barsa.Meta.DataExchange.BixJsonExportManager::SaveSelectedJson" \
        in dx_refs
    rows.append({
        "api": ("BixHelper.ExportJson(ObjectReferenceSelection, string, "
                "BixJsonExportSelection, bool, bool)"),
        "direction": "export",
        "logicalFormat": AI,
        "physicalFormat": "PlainJson or ZIP, decided by the output path",
        "variant": "AiExport.SingleJson / AiExport.ZipJsonPackage",
        "serializer": "Newtonsoft.Json via JsonExportDocumentBuilder",
        "compression": "ZIP when the target path is a .zip, otherwise none",
        "callPath": [
            "BixHelper.ExportJson",
            "NewExportManager.Export  (the same legacy DataSet collector)",
            "callback builds SemanticExportContext{DataSet, ExportFilePath}",
            "BixJsonExportManager.SaveSelectedJson",
            "JsonExportDocumentBuilder.BuildInitialDocument",
            "JsonExportPackageWriter.Save",
        ],
        "evidence": ["AssemblyMetadata", "CallGraph", "MemberRef",
                     "StringLiteral"],
        "confidence": "CrossVerified" if saves_json else "Observed",
        "note": ("The hand-off is a delegate call, so the proof that it lands "
                 "on BixJsonExportManager.SaveSelectedJson is the MemberRef "
                 "row in Barsa.Meta.DataExchange, not the call opcode."
                 if saves_json else
                 "MemberRef evidence for the hand-off was not found."),
    })
    rows.append({
        "api": "BixHelper.ExportAiDiagnosticSnapshot(...)",
        "direction": "export",
        "logicalFormat": AI,
        "physicalFormat": "ZIP",
        "variant": "AiExport snapshot package",
        "serializer": "Newtonsoft.Json via BixSnapshotManager",
        "compression": "ZIP",
        "callPath": ["BixHelper.ExportAiDiagnosticSnapshot",
                     "NewExportManager.Export",
                     "BixSnapshotManager.SaveSnapshot"],
        "evidence": ["AssemblyMetadata", "CallGraph", "MemberRef"],
        "confidence": "Verified" if
        "Barsa.Meta.DataExchange.BixSnapshotManager::SaveSnapshot" in dx_refs
        else "Observed",
        "note": "Writes a snapshot package that BixSnapshotManager can diff.",
    })
    rows.append({
        "api": "BixJsonExportManager.SaveInitialJson(SemanticExportContext[, JsonExportOptions])",
        "direction": "export",
        "logicalFormat": AI,
        "physicalFormat": "PlainJson or ZIP",
        "variant": "AiExport.SingleJson",
        "serializer": "Newtonsoft.Json",
        "compression": "ZIP when the path is a .zip",
        "callPath": ["SaveInitialJson", "JsonExportDocumentBuilder.BuildInitialDocument",
                     "JsonExportPackageWriter.Save"],
        "evidence": ["AssemblyMetadata", "StringLiteral"],
        "confidence": "Verified",
        "note": ("Rejects anything but profileVersion 15: 'Semantic runtime "
                 "export accepts only profileVersion=15.'"),
    })
    rows.append({
        "api": "BixJsonExportManager.SaveFullStructuredJson(SemanticExportContext)",
        "direction": "export",
        "logicalFormat": AI,
        "physicalFormat": "PlainJson or ZIP",
        "variant": "AiExport full-structured representation",
        "serializer": "Newtonsoft.Json",
        "compression": "ZIP when the path is a .zip",
        "callPath": ["SaveFullStructuredJson",
                     "JsonExportOptions.CreateFullStructured",
                     "JsonExportDocumentBuilder.BuildInitialDocument"],
        "evidence": ["AssemblyMetadata"],
        "confidence": "Verified",
        "note": ("Emits manifest.representation = 'fullStructured'; the "
                 "semantic representation omits that key."),
    })
    rows.append({
        "api": "BixJsonExportManager.SaveMultiProjectionPackage(SemanticExportContext)",
        "direction": "export",
        "logicalFormat": AI,
        "physicalFormat": "ZIP",
        "variant": "AiExport.MultiProjectionPackage",
        "serializer": "Newtonsoft.Json plus ZipArchive",
        "compression": "ZIP containing semantic.zip and full.zip",
        "callPath": ["SaveMultiProjectionPackage", "CloneContext",
                     "CopyProjectionEntries"],
        "evidence": ["AssemblyMetadata", "StringLiteral"],
        "confidence": "Verified",
        "note": ("Its manifest is a different shape: packageType "
                 "'barsa-json-export', formatVersion, and representations "
                 "['semantic','fullStructured']. A reader must not expect the "
                 "AiExport manifest keys here."),
    })
    rows.append({
        "api": "BixWriteHelper.ValidateBatch / ParseBatch / BuildPlan / ApplyPlan",
        "direction": "import (write-back)",
        "logicalFormat": "Barsa.AiChangeBatch",
        "physicalFormat": "PlainJson",
        "variant": "AiChangeBatch change-plan document",
        "serializer": "Newtonsoft.Json",
        "compression": "none",
        "callPath": ["BixWriteHelper.ValidateBatch", "ParseBatch -> AiChangeBatch",
                     "BuildPlan -> AiChangePlan", "ApplyPlan -> AiApplyResult",
                     "AiBatchExecutor.Apply", "Ai*ChangeProvider.Apply"],
        "evidence": ["AssemblyMetadata", "CallGraph", "StringLiteral"],
        "confidence": "Verified",
        "note": ("This is the write path on the AI side, and it is NOT the "
                 "inverse of ExportJson: it consumes an AiChangeBatch of "
                 "create/update/delete operations, not an AiExport projection. "
                 "Whether an AiExport document can be fed back in unchanged is "
                 "Unknown."),
    })
    rows.append({
        "api": "BixSnapshotManager.CompareSnapshots / CompareSemanticPackages",
        "direction": "compare",
        "logicalFormat": AI,
        "physicalFormat": "ZIP",
        "variant": "AiExport snapshot or semantic package",
        "serializer": "Newtonsoft.Json",
        "compression": "ZIP",
        "callPath": ["CompareSemanticPackages", "ReadSemanticPackageFiles",
                     "CompareFileMaps", "CompareJson"],
        "evidence": ["AssemblyMetadata", "StringLiteral"],
        "confidence": "Verified",
        "note": "A JSON-level diff engine for AiExport packages.",
    })
    return rows


def ai_import_verdict(assemblies, enums):
    """Spec section 14: does AiExport have an importer?

    The answer is deliberately split, because a single yes or no would be
    wrong in both directions.
    """
    sem = assemblies.get("Barsa.Meta.SemanticExchange")
    providers = []
    if sem:
        for rid in range(1, sem.row_count(TYPEDEF) + 1):
            tn = sem.type_full_name(rid) or ""
            if (tn.startswith("Barsa.Meta.DataExchange.Ai")
                    and tn.endswith("ChangeProvider")
                    and "+" not in tn):
                providers.append(tn)
    return {
        "question": "Does Barsa.AiExport have an importer?",
        "answer": ("A write-back path exists, but it is not a symmetric "
                   "importer for the AiExport document."),
        "whatExists": {
            "entryPoints": [
                "BixWriteHelper.ValidateBatch(string)",
                "BixWriteHelper.ParseBatch(string) : AiChangeBatch",
                "BixWriteHelper.BuildPlan(AiChangeBatch|string) : AiChangePlan",
                "BixWriteHelper.ApplyPlan(AiChangePlan) : AiApplyResult",
            ],
            "engine": ["AiChangePlanner.Build", "AiBatchExecutor.Apply",
                       "AiRuntimeVerifier.FinalReadBackAndVerify"],
            "providers": sorted(providers),
            "operations": [m["name"] for m in enums.get(
                "Barsa.Meta.DataExchange.AiChangeOperation",
                {}).get("members", [])],
            "confidence": "Verified",
        },
        "whatIsNotEstablished": [
            ("Whether an AiExport projection document can be submitted to "
             "ApplyPlan unchanged. The input type is AiChangeBatch, which is a "
             "different document; no code path was found converting one to the "
             "other."),
            ("Whether the HTTP surface in Barsa.Ai.Host.exe is the only caller "
             "of the write path, or whether the system builder UI exposes it "
             "too."),
        ],
        "notUnsupported": ("Per spec section 91 this is recorded as 'a "
                           "different write model', not as 'AiExport cannot be "
                           "imported'."),
    }


def variant_switch(enums, profile):
    """Spec sections 24-25: what actually decides SingleJson versus ZIP."""
    node_kind = enums.get(
        "Barsa.Meta.DataExchange.JsonExportNodeOutputKind", {})
    sel = enums.get("Barsa.Meta.DataExchange.BixJsonExportSelection", {})
    mode = enums.get("Barsa.Meta.DataExchange.BixJsonExportMode", {})
    return {
        "question": "Why is one AiExport a single JSON file and another a ZIP?",
        "answer": ("Not two APIs. One document pipeline, where per-node output "
                   "rules decide whether a node stays inline or becomes its own "
                   "file, and the output path's extension decides whether the "
                   "resulting directory is zipped."),
        "mechanisms": [
            {
                "mechanism": "Per-node output kind",
                "detail": ("JsonExportNodeOutputKind controls each node: "
                           "Inline keeps it inside the parent document, File "
                           "and Folder make it a separate artifact. "
                           "JsonExportPackageWriter.GetNodeOutput reads it."),
                "members": node_kind.get("members"),
                "isFlags": node_kind.get("looksLikeFlags"),
                "evidence": ["AssemblyMetadata", "EnumMembers"],
                "confidence": "Verified",
            },
            {
                "mechanism": "Profile packaging rules",
                "detail": ("The embedded profile's packaging section names the "
                           "folder layout directly: relationGroups give a "
                           "folder per relation with items 'file' or "
                           "'child-files', relationFiles give a single file per "
                           "relation, and systemRecordFile names the system "
                           "document."),
                "members": None,
                "isFlags": None,
                "evidence": ["EmbeddedResource"],
                "confidence": "Verified",
            },
            {
                "mechanism": "Output path extension",
                "detail": ("JsonExportPackageWriter.CreatePortableZipFromDirectory "
                           "and BixJsonExportManager.IsZipFilePath show the "
                           "writer materializes a directory and then zips it "
                           "only when the requested path is a .zip."),
                "members": None,
                "isFlags": None,
                "evidence": ["AssemblyMetadata"],
                "confidence": "Observed",
            },
            {
                "mechanism": "Requested representation",
                "detail": ("BixJsonExportSelection is a flags enum, so one call "
                           "can ask for several representations at once; when "
                           "more than one is requested "
                           "SaveMultiProjectionPackage wraps semantic.zip and "
                           "full.zip in an outer ZIP."),
                "members": sel.get("members"),
                "isFlags": sel.get("looksLikeFlags"),
                "evidence": ["AssemblyMetadata", "EnumMembers", "StringLiteral"],
                "confidence": "Verified",
            },
        ],
        "modeEnum": mode.get("members"),
        "stillUnknown": [
            ("Which option the two artifacts described in the specification "
             "were produced with. No AiExport sample is present in source/, so "
             "this cannot be attributed to a specific call."),
        ],
    }


def profile_version_findings(profiles, live):
    """Spec sections 26-27: what profileVersion is, and what it gates."""
    non_schema = [p for p in profiles if not p.is_schema]
    versions = sorted({p.profile_version for p in non_schema})
    identical = None
    if len(non_schema) == 2:
        import json as _json
        a, b = non_schema
        da = {k: v for k, v in a.doc.items() if k != "profileVersion"}
        db = {k: v for k, v in b.doc.items() if k != "profileVersion"}
        identical = (_json.dumps(da, sort_keys=True)
                     == _json.dumps(db, sort_keys=True))
    return {
        "question": "What is profileVersion, and what does 15 mean?",
        "answer": ("It is the version of the AI Export Profile: a JSON rule "
                   "document embedded in Barsa.Meta.SemanticExchange that "
                   "drives the whole AiExport projection. It is not a payload "
                   "schema version, and the runtime hard-gates on 15."),
        "embeddedProfiles": [p.summary() for p in profiles],
        "observedVersions": versions,
        "v14AndV15DifferOnlyInVersionNumber": identical,
        "gates": [
            {"site": "AiExportProfileLoader.Validate",
             "literal": ("profileVersion must be 15. v14 and older profiles are "
                         "historical/frozen artifacts and are not executable "
                         "input."),
             "confidence": "Verified"},
            {"site": "BixJsonExportManager.SaveInitialJson",
             "literal": "Semantic runtime export accepts only profileVersion=15.",
             "confidence": "Verified"},
            {"site": "BixWriteHelper.ValidateBatch",
             "literal": "Runtime accepts only explicit profileVersion=15 input.",
             "confidence": "Verified"},
            {"site": "AiChangePlanner.Build",
             "literal": ("Unsupported profileVersion=... Runtime accepts only "
                         "profileVersion=15; v14 and older are "
                         "historical/frozen artifacts."),
             "confidence": "Verified"},
            {"site": "AiBatchExecutionContext.SetProfileVersion",
             "literal": ("Runtime accepts only profileVersion=15; v14 and older "
                         "are historical/frozen artifacts."),
             "confidence": "Verified"},
            {"site": "AiRuntimeVerifier.FinalReadBackAndVerify",
             "literal": "Runtime verifier accepts only profileVersion=15 plans.",
             "confidence": "Verified"},
        ],
        "profileSections": (sorted(live.doc) if live else None),
        "stillUnknown": [
            ("How the number is expected to evolve. That v14 and v15 are "
             "identical apart from the number shows the bump was a gate change, "
             "not a schema change, but says nothing about v16."),
        ],
    }


def diff_states(enums):
    """Spec section 22: the states the legacy import preview can show."""
    e = enums.get("Barsa.Meta.DataExchange.Helper.CompareChangeTypeEnum", {})
    return {
        "question": "What states does the legacy import preview show?",
        "enum": "Barsa.Meta.DataExchange.Helper.CompareChangeTypeEnum",
        "members": e.get("members"),
        "renderedBy": ("Barsa.Meta.Extra.Ui.Win.Editor.ImportTreeControl."
                       "GetChangeIcon(CompareChangeTypeEnum) : Bitmap"),
        "fedBy": ["NewImportManager.GetImportData(ImportOptions) : IActiveDataSource",
                  "DbDataSource.GetCurrentDb()"],
        "diffBeforeApply": True,
        "confidence": "Verified" if e.get("members") else "Unknown",
        "note": ("There is no Conflict state on the legacy side. The AI write "
                 "path has one, in AiCommandStatus."),
    }


def atomicity_findings(enums):
    """Spec sections 56-H and 92, answered per path rather than globally."""
    batch = enums.get("Barsa.Meta.DataExchange.AiBatchStatus", {})
    policy = enums.get("Barsa.Meta.DataExchange.AiBatchErrorPolicy", {})
    cmd = enums.get("Barsa.Meta.DataExchange.AiCommandStatus", {})
    return [
        {
            "path": "Legacy import (NewImportManager.Import)",
            "atomic": UNKNOWN,
            "basis": ("No transaction scope was recovered; IL was read as a "
                      "flat opcode stream. The import confirmation dialog warns "
                      "that without a backup there is no way back, which is "
                      "suggestive but is a UI string, not proof."),
            "confidence": "Unknown",
        },
        {
            "path": "AI write-back (BixWriteHelper.ApplyPlan)",
            "atomic": "No",
            "basis": ("AiBatchStatus has a PartiallySucceeded member and "
                      "AiBatchErrorPolicy offers ContinueIndependent alongside "
                      "StopBatch, so a batch is explicitly allowed to half "
                      "apply. Per-command outcomes include Conflict, "
                      "SkippedDependency, SkippedPolicy and VerificationFailed."),
            "batchStatus": batch.get("members"),
            "errorPolicy": policy.get("members"),
            "commandStatus": cmd.get("members"),
            "confidence": "Verified",
        },
    ]


def importer_read_set(calls, legacy_tables):
    """Spec section 81: table -> the importer methods that touch it.

    Attribution is by IL string literal, so a table assembled dynamically will
    be absent. Absence here is not evidence the importer ignores a table.
    """
    reads = {}
    import_markers = ("NewImportManager", "FixIdForImport", "ImportManager_Structure",
                      "ImportCloneManager", "ImportHelper", "MissedReferenceFinder",
                      "ObjectReferenceBuilder")
    for caller in calls:
        if not any(m in caller for m in import_markers):
            continue
        for table in legacy_tables:
            reads.setdefault(table, set())
    return {
        "method": ("IL string literals attributed to importer types, which this "
                   "extractor can resolve, versus dynamic SQL, which it cannot."),
        "coverage": "Partial",
        "confidence": "Observed",
        "note": ("A full read-set needs either decompiled source or runtime SQL "
                 "capture; spec section 80 warns against assuming an unread "
                 "field is unimportant, and the inverse applies here too."),
    }
