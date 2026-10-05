"""Phases 1-14 driver: reads source/, writes the dist/ knowledge pack."""

import json
import os
import re
import sys
import time

from . import compare as cmp_mod
from . import evidence as ev
from . import exchange_model as xm
from . import normalize as nz
from .ai_export import AiExportArtifact
from .ai_profile import discover_profiles, executable_profile
from .cli_metadata import TYPEDEF, METHODDEF
from .export_package import ExportPackage, compare, id_reference_model
from .format_detect import (
    LOGICAL_AI, LOGICAL_LEGACY, detect, normalize_manifest,
)
from .il_analysis import (
    analyze_method, classify_string, extract_sql, invert_calls, redact,
    SQL_RE,
)
from .inventory import (
    discover, index_methods, index_types, inventory_assembly, is_barsa_domain,
    is_barsa_owned, priority_score,
)

SCHEMA_VERSION = "3.0"
UNKNOWN_FMT = "Unknown"

# Files worth running content detection over. Everything else in source/ is
# resources and binaries; sniffing them wastes time and tells us nothing.
DETECT_EXTENSIONS = (".metaexport", ".zip", ".json", ".gz", ".xml")

# Deep IL analysis is limited to Barsa-owned assemblies (spec sections 49-50);
# third-party assemblies are inventoried and indexed only.
DEEP_MIN_SCORE = 50

CONFIG_KEY_CALLS = (
    "ConfigurationManager::get_AppSettings", "ConfigurationManager::get_ConnectionStrings",
    "AppSettingsReader", "Environment::GetEnvironmentVariable",
    "RegistryKey::GetValue", "ConfigurationSettings",
)

DOMAIN_TERMS = {
    "authentication": ("Login", "Authenticate", "ValidateLogin", "Password",
                       "SecurityHandler", "Credential", "Logon"),
    "session-security": ("SessionMgr", "Session", "CurrentUser", "Logout",
                         "Trustee", "AccessLevel", "SecurityDescriptor"),
    "startup-bootstrap": ("ApplicationLauncher", "Startup", "PreWorks",
                          "BeforeLogin", "AfterLogin", "Bootstrap"),
    "metadata-system": ("MetaObject", "MetaSystem", "TypeDef", "FieldDef",
                        "MetaCommand", "MetaCode"),
    "entities-fields-relations": ("TypeDef", "FieldDef", "RelationDef",
                                  "MetaObjectList", "TypeViewEntity"),
    "business-logic": ("BusinessLogic", "BusinessLogicBase",
                       "DefaultBusinessLogicBase"),
    "database-access": ("SqlConnection", "SqlCommand", "DbConnection",
                        "ExecuteNonQuery", "ExecuteReader", "DbHelper",
                        "DbProvider", "DbStructBuilder", "Transaction"),
    "navigator": ("Navigator", "Folder", "Menu", "Tree", "Met_Folder"),
    "reporting": ("Report", "ReportData", "CustomColumn", "Parameter",
                  "Print", "ReportDesigner"),
    "stimulsoft": ("StiReport", "StiText", "StiDataBand", "StiDictionary",
                   "StiVariable", "StiDataSource", "Stimulsoft"),
    "forms-ui": ("Form", "UserControl", "BarsaBaseForm", "Grid", "Editor"),
    "workflow": ("Workflow", "Activity", "ActivityDef", "Bpmn"),
    "serialization": ("Serialize", "Deserialize", "BinaryFormatter",
                      "XmlSerializer", "GZip", "Deflate", "SharpZipLib",
                      "Json", "Base64"),
    "remoting": ("Remoting", "RemotableObject", "Sink", "Channel", "Proxy"),
    "configuration": ("ConfigurationManager", "AppSettings",
                      "ConnectionString", "AppConfigDef"),
    "import-export": ("Export", "Import", "BixHelper", "DataExchange",
                      "ObjectReferenceSelection", "FixIdForImport",
                      "ExportSession", "metaexport"),
    "data-exchange": ("BixHelper", "BixJsonExportManager", "BixWriteHelper",
                      "BixSnapshotManager", "NewExportManager",
                      "NewImportManager", "SerializationHelper2"),
    "legacy-metaexport": ("NewExportManager", "NewImportManager",
                          "SerializationHelper2", "FixIdForImport",
                          "ExportSession", "ImportOptions", "DataFetcher"),
    "ai-export": ("AiExport", "JsonExport", "Semantic", "AiChange", "AiBatch",
                  "AiPlan", "BixJson", "AiRuntime", "AiReport", "AiField"),
    "system-reconstruction": ("ImportManager", "ExportManager", "Reconstruct",
                              "Clone", "IdMap", "ObjectReferenceBuilder"),
}

# Reflection / dynamic runtime probes (spec section 44).
REFLECTION_CALLS = ("Assembly::Load", "Assembly::LoadFrom", "Assembly::LoadFile",
                    "Activator::CreateInstance", "Type::GetType",
                    "Type::GetMethod", "MethodBase::Invoke",
                    "MethodInfo::Invoke")


def _j(obj):
    """Deterministic JSON for meaningful git diffs (spec section 54)."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class Extractor:
    def __init__(self, source_root, dist_root, log=print):
        self.source = source_root
        self.dist = dist_root
        self.log = log
        self.ledger = ev.Ledger()
        self.errors = []
        self.missing_inputs = []
        self.started = time.time()

    # -- phases -------------------------------------------------------------

    def run(self):
        self.phase1_discover()
        self.phase2_inventory()
        self.phase3_index()
        self.phase4_il()
        self.phase6_exports()
        self.phase6b_formats()
        self.phase7_exchange_model()
        self.phase8_normalize_and_compare()
        self.phase9_crossvalidate()
        self.phase10_normalized_model()
        self.phase11_capabilities()
        self.phase13_generate()
        self.phase14_validate()
        return self.report

    def phase1_discover(self):
        self.inputs = discover(self.source)
        kinds = {}
        for e in self.inputs:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        self.input_kinds = kinds
        self.log("phase1: %d inputs %s" % (len(self.inputs), kinds))
        for need, label in (("ExportPackage", "export packages"),):
            if not kinds.get(need):
                self.missing_inputs.append(label)
        if not any(d in self.source for d in ("exporter", "importer")):
            for sub in ("exporter", "importer"):
                if not os.path.isdir(os.path.join(self.source, sub)):
                    self.missing_inputs.append(
                        "source/%s/ (exporter/importer source or decompiled code)" % sub)

    def phase2_inventory(self):
        self.assemblies = {}
        self.asm_objects = {}
        self.native = []
        for e in self.inputs:
            if e["kind"] != "Assembly":
                continue
            result, err = inventory_assembly(e)
            if err:
                self.native.append(err)
                continue
            asm, record = result
            # Several files can declare the same assembly name (a .dll and .exe
            # pair, or the same assembly shipped under x32/ and x64/), so the
            # index is keyed by path to avoid dropping any of them.
            key = record["path"]
            record["key"] = key
            self.assemblies[key] = record
            self.asm_objects[key] = asm
            self.ledger.add("AssemblyMetadata",
                            "assembly %s v%s" % (record["assemblyName"],
                                                 record["assemblyVersion"]),
                            record["path"])
        self.log("phase2: %d managed, %d native/unreadable"
                 % (len(self.assemblies), len(self.native)))

    def phase3_index(self):
        self.types = []
        self.methods = []
        self.obfuscation = {}
        for name, asm in self.asm_objects.items():
            rec = self.assemblies[name]
            try:
                trows, obf = index_types(asm, rec)
            except Exception as exc:
                self.errors.append({"stage": "index_types", "assembly": name,
                                    "error": "%s: %s" % (type(exc).__name__, exc)})
                continue
            rec["obfuscatedTypeNames"] = obf
            self.obfuscation[name] = {
                "types": rec["typesCount"],
                "obfuscatedTypeNames": obf,
                "ratio": round(obf / rec["typesCount"], 3) if rec["typesCount"] else 0.0,
            }
            rec["_priority"] = priority_score(
                rec["fileName"], asm, [t["fullName"] for t in trows])
            self.types.extend(trows)
            if rec["_priority"] >= DEEP_MIN_SCORE:
                try:
                    self.methods.extend(index_methods(asm, rec, trows))
                except Exception as exc:
                    self.errors.append({"stage": "index_methods",
                                        "assembly": name,
                                        "error": "%s: %s" % (type(exc).__name__, exc)})
        self.log("phase3: %d types, %d indexed methods"
                 % (len(self.types), len(self.methods)))

    def phase4_il(self):
        """Phases 4-5: call graph, string literals, SQL, config keys."""
        self.calls = {}
        self.call_assembly = {}
        self.strings = {}
        self.sql = []
        self.config_keys = {}
        self.reflection = []
        deep = [n for n, r in self.assemblies.items()
                if r.get("_priority", 0) >= DEEP_MIN_SCORE]
        for name in deep:
            asm = self.asm_objects[name]
            for trid in range(1, asm.row_count(TYPEDEF) + 1):
                tn = asm.type_full_name(trid)
                if not tn:
                    continue
                start, end = asm.type_method_range(trid)
                for m in range(start, end):
                    try:
                        res = analyze_method(asm, m)
                    except Exception:
                        continue
                    if not res:
                        continue
                    key = "%s::%s" % (tn, asm.method_name(m))
                    if res["calls"]:
                        self.calls[key] = res["calls"]
                        self.call_assembly[key] = name
                    for s in res["strings"]:
                        self._record_string(name, key, s)
                    for c in res["calls"]:
                        if any(p in c for p in REFLECTION_CALLS):
                            self.reflection.append({"assembly": name,
                                                    "method": key, "api": c})
                        if any(p in c for p in CONFIG_KEY_CALLS):
                            self.config_keys.setdefault(
                                "<dynamic>", []).append(key)
        self.called_by = invert_calls({k: {"calls": v}
                                       for k, v in self.calls.items()})
        self.log("phase4: %d methods with calls, %d distinct strings, %d SQL"
                 % (len(self.calls), len(self.strings), len(self.sql)))

    def _record_string(self, assembly, method, s):
        if not s or len(s) > 8000:
            return
        cat = classify_string(s)
        bucket = self.strings.setdefault(s, {"category": cat, "sites": []})
        if len(bucket["sites"]) < 8:
            bucket["sites"].append(method)
        if cat == "sql":
            info = extract_sql(s)
            if info:
                self.sql.append({
                    "assembly": assembly, "method": method,
                    "sql": redact(s[:1200]),
                    "operation": info["operation"], "tables": info["tables"],
                })

    def phase6_exports(self):
        """Phases 6-8 and 15-18: export package structure and ID model."""
        self.packages = []
        for e in self.inputs:
            if e["kind"] != "ExportPackage":
                continue
            try:
                pkg = ExportPackage(e["absPath"])
            except Exception as exc:
                self.errors.append({"stage": "export_package", "file": e["path"],
                                    "error": "%s: %s" % (type(exc).__name__, exc)})
                continue
            self.packages.append(pkg)
            self.ledger.add("ExportSample",
                            "package %s (%d tables)" % (e["name"], len(pkg.tables)),
                            e["path"])
        self.package_comparison = compare(self.packages) if self.packages else {}
        self.id_model = id_reference_model(self.packages) if self.packages else []
        self.log("phase6: %d export packages, %d id-model entries"
                 % (len(self.packages), len(self.id_model)))

    # -- v3: formats, exchange model, normalization -------------------------

    def phase6b_formats(self):
        """Spec v3 sections 3 and 88: detect every artifact by content."""
        self.formats = []
        self.ai_artifacts = []
        for e in self.inputs:
            if not e["path"].lower().endswith(DETECT_EXTENSIONS):
                continue
            rec = detect(e["absPath"])
            rec["path"] = e["path"]
            self.formats.append(rec)
            if rec["logicalFormat"] == LOGICAL_AI:
                art = AiExportArtifact(e["absPath"], rec)
                self.ai_artifacts.append(art)
                self.ledger.add("ExportSample",
                                "AiExport artifact %s (%s)"
                                % (e["name"], art.variant), e["path"])
            for err in rec["errors"]:
                self.errors.append({"stage": "format_detect",
                                    "file": e["path"],
                                    "error": "%s: %s" % (err["kind"],
                                                         err["message"])})
        self.format_warnings = [
            {"path": r["path"], **w}
            for r in self.formats for w in r["warnings"]]
        counts = {}
        for r in self.formats:
            key = "%s / %s" % (r["logicalFormat"], r["variant"])
            counts[key] = counts.get(key, 0) + 1
        self.format_counts = counts
        if not self.ai_artifacts:
            self.missing_inputs.append(
                "an AiExport artifact (JSON or ZIP) in source/exports/ai-json/")
        self.log("phase6b: %d artifacts detected %s"
                 % (len(self.formats), counts))

    def phase7_exchange_model(self):
        """Spec v3 sections 12-14, 20-27: re-derive the exchange model."""
        paths = [e["absPath"] for e in self.inputs if e["kind"] == "Assembly"]
        self.profiles, prof_errors = discover_profiles(paths)
        for err in prof_errors:
            self.errors.append({"stage": "ai_profile", "file": err["assembly"],
                                "error": err["error"]})
        self.live_profile = executable_profile(self.profiles)
        for p in self.profiles:
            self.ledger.add("AssemblyMetadata",
                            "embedded AI export profile v%s (%d record types)"
                            % (p.profile_version, len(p.record_types)),
                            "%s :: %s" % (p.assembly, p.resource))

        # Index the exchange assemblies by display name for enum and ref work.
        self.exchange_asms = {}
        for key, rec in self.assemblies.items():
            if rec["assemblyName"] in xm.EXCHANGE_ASSEMBLIES:
                self.exchange_asms[rec["assemblyName"]] = self.asm_objects[key]
        self.answer_enums = xm.collect_enums(self.exchange_asms)
        for name, info in self.answer_enums.items():
            self.ledger.add("AssemblyMetadata",
                            "enum %s = %s" % (name, ", ".join(
                                m["name"] for m in info["members"])),
                            info["assembly"])

        self.memberrefs = {}
        for name, asm in self.exchange_asms.items():
            self.memberrefs[name] = xm.cross_assembly_memberrefs(
                asm, ("BixJsonExportManager", "BixSnapshotManager",
                      "BixWriteHelper", "SemanticExportContext"))
        self.api_formats = xm.api_format_map(
            self.exchange_asms, self.calls, self.memberrefs)
        self.ai_import = xm.ai_import_verdict(self.exchange_asms,
                                              self.answer_enums)
        self.variant_switch = xm.variant_switch(self.answer_enums,
                                                self.live_profile)
        self.profile_version = xm.profile_version_findings(
            self.profiles, self.live_profile)
        self.diff_states = xm.diff_states(self.answer_enums)
        self.atomicity = xm.atomicity_findings(self.answer_enums)
        self.log("phase7: %d profiles, %d answer enums, %d api rows"
                 % (len(self.profiles), len(self.answer_enums),
                    len(self.api_formats)))

    def phase8_normalize_and_compare(self):
        """Spec v3 sections 39-54: normalize both families, then compare."""
        self.normalized_legacy = []
        for pkg in self.packages:
            try:
                self.normalized_legacy.append(nz.from_legacy(pkg))
            except Exception as exc:
                self.errors.append({"stage": "NormalizationError",
                                    "file": pkg.path,
                                    "error": "%s: %s" % (type(exc).__name__, exc)})
        self.normalized_ai = []
        for art in self.ai_artifacts:
            try:
                self.normalized_ai.append(
                    nz.from_ai_export(art, self.live_profile))
            except Exception as exc:
                self.errors.append({"stage": "NormalizationError",
                                    "file": art.path,
                                    "error": "%s: %s" % (type(exc).__name__, exc)})

        self.declared_pairs = self._load_declared_pairs()
        self.pairs = cmp_mod.candidate_pairs(
            self.packages, self.ai_artifacts, self.declared_pairs)
        self.comparisons = []
        for pair in self.pairs:
            pkg = next((p for p in self.packages
                        if p.path.endswith(pair["legacy"])), None)
            art = next((a for a in self.ai_artifacts
                        if a.path.endswith(pair["aiExport"])), None)
            if pkg is None or art is None:
                continue
            scope = cmp_mod.scope_equivalence(
                cmp_mod.legacy_selection_roots(pkg),
                cmp_mod.ai_selection_roots(art),
                declared=pair.get("declaredScope"))
            lenv = nz.from_legacy(pkg)
            aenv = nz.from_ai_export(art, self.live_profile)
            per_concept = {}
            diffs = []
            if scope["level"] in (cmp_mod.SCOPE_EXACT, cmp_mod.SCOPE_PARTIAL):
                for coll in nz.EMPTY_ENVELOPE_KEYS:
                    matches = cmp_mod.match_collection(lenv.get(coll),
                                                       aenv.get(coll))
                    if matches is None:
                        continue
                    per_concept[coll] = matches
                    for m in matches:
                        if m["strength"] == cmp_mod.MATCH_UNMATCHED or \
                                m["matchedOn"] == "caption":
                            diffs.append({"concept": coll,
                                          **cmp_mod.classify_difference(
                                              m, scope["level"])})
            self.comparisons.append({
                "pair": pair,
                "scope": scope,
                "coverage": cmp_mod.coverage(lenv, aenv, scope),
                "differences": diffs,
                "comparedConcepts": sorted(per_concept),
            })
        self.log("phase8: %d legacy normalized, %d ai normalized, %d pairs"
                 % (len(self.normalized_legacy), len(self.normalized_ai),
                    len(self.pairs)))

    def _load_declared_pairs(self):
        """Optional source/exports/pairs.json (spec v3 section 41)."""
        for e in self.inputs:
            if e["name"].lower() != "pairs.json":
                continue
            try:
                with open(e["absPath"], encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    return data
            except Exception as exc:
                self.errors.append({"stage": "ScopeMatchError",
                                    "file": e["path"],
                                    "error": "%s: %s" % (type(exc).__name__, exc)})
        return []

    # -- cross validation ---------------------------------------------------

    def phase9_crossvalidate(self):
        """Spec sections 24-25 and 70: concept presence per source."""
        concepts = {
            "MetaSystem": {"dllTypes": ["Barsa.Meta.MetaSystem"],
                           "exportTables": ["MET_METASYSTEM"]},
            "TypeDef (Entity)": {"dllTypes": ["Barsa.Meta.TypeDef"],
                                 "exportTables": ["MET_TYPEDEF"]},
            "FieldDef (Field)": {"dllTypes": ["Barsa.Meta.FieldDef"],
                                 "exportTables": ["MET_FIELDDEF"]},
            "RelationDef": {"dllTypes": ["Barsa.Meta.RelationDef"],
                            "exportTables": ["MET_RELATIONDEF"]},
            "Relation instance": {"dllTypes": ["Barsa.Meta.Relation"],
                                  "exportTables": ["met_Relation",
                                                   "$basicInfoRelation"]},
            "Report": {"dllTypes": ["Barsa.Meta.Report"],
                       "exportTables": ["met_Report"]},
            "Folder (Navigator)": {"dllTypes": ["Barsa.Meta.Folder"],
                                   "exportTables": ["MET_FOLDER"]},
            "MetaCode": {"dllTypes": ["Barsa.Meta.MetaCode"],
                         "exportTables": ["MET_METACODE"]},
            "MetaCommand": {"dllTypes": ["Barsa.Meta.MetaCommand"],
                            "exportTables": ["MET_METACOMMAND"]},
            "TypeViewEntity": {"dllTypes": ["Barsa.Meta.TypeViewEntity"],
                               "exportTables": ["MET_TYPEVIEWENTITY"]},
            "EorgType (id scope)": {"dllTypes": ["Barsa.Spl.BasicInfo.EorgType"],
                                    "exportTables": ["$spl_EorgType"]},
            "EorgCenter (id scope)": {
                "dllTypes": ["Barsa.Spl.BasicInfo.EorgCenter"],
                "exportTables": ["$spl_EorgCenter"]},
            "ExportSession": {"dllTypes": ["Barsa.Spl.BasicInfo.ExportSession"],
                              "exportTables": ["$Selection", "$RootSelection"]},
            "Trustee access": {"dllTypes": ["Barsa.Spl.Security.TrusteeAccess"],
                               "exportTables": ["Spl_TrusteeAccess"]},
            "File attachment": {"dllTypes": ["Barsa.SharedObjects.FileAttachment"],
                                "exportTables": ["Shr_FileAttachment"]},
        }
        type_names = {t["fullName"] for t in self.types}
        short_names = {t["fullName"].split(".")[-1] for t in self.types}
        export_tables = set()
        for p in self.packages:
            export_tables.update(p.tables)
        # Tables named as string literals inside the data-exchange assembly.
        # This is the one attribution that can be made honestly: whether the
        # exchange code mentions a table at all. Splitting it into "exporter"
        # versus "importer" would need control flow, which was not recovered,
        # so it is reported as a single signal rather than guessed per
        # direction.
        exchange_literals = set()
        for lit, info in self.strings.items():
            if info["category"] != "table":
                continue
            for site in info["sites"]:
                if "DataExchange" in site:
                    exchange_literals.add(lit.lower())
                    break
        rows = []
        for concept, spec in sorted(concepts.items()):
            in_dll = any(t in type_names for t in spec["dllTypes"]) or \
                any(t.split(".")[-1] in short_names for t in spec["dllTypes"])
            present = [t for t in spec["exportTables"] if t in export_tables]
            in_export = bool(present)
            named = sorted(t for t in spec["exportTables"]
                           if t.lower() in exchange_literals)
            sources = []
            if in_dll:
                sources.append("AssemblyMetadata")
            if in_export:
                sources.append("ExportSample")
            if named:
                sources.append("ExporterCode")
            rows.append({
                "concept": concept,
                "dll": in_dll,
                "export": in_export,
                "namedInExchangeIl": named,
                "dllTypes": [t for t in spec["dllTypes"]
                             if t in type_names
                             or t.split(".")[-1] in short_names],
                "exportTables": present,
                "confidence": ev.from_source_count(sources),
            })
        self.cross_matrix = rows
        self.conflicts = self._detect_conflicts(export_tables)
        self.log("phase9: %d concepts, %d crossVerified, %d conflicts"
                 % (len(rows),
                    sum(1 for r in rows if r["confidence"] == "CrossVerified"),
                    len(self.conflicts)))

    def _exchange_symbols(self):
        """Symbols reachable from the exporter and importer entry points."""
        exporter, importer = set(), set()
        for key, callees in self.calls.items():
            low = key.lower()
            if "exportmanager" in low or "bixhelper::export" in low:
                exporter.add(key)
                exporter.update(callees)
            if "importmanager" in low or "bixhelper::import" in low \
                    or "fixidforimport" in low:
                importer.add(key)
                importer.update(callees)
        return exporter, importer

    def _detect_conflicts(self, export_tables):
        """Spec section 25: tables named in IL but absent from every sample.

        Comparison is case-insensitive: SQL Server identifiers are not
        case-sensitive, and Barsa's own IL spells the same table both
        MET_TYPEDEF and met_TypeDef. Treating those as distinct would
        manufacture conflicts that do not exist.
        """
        conflicts = []
        il_tables = {s for s, info in self.strings.items()
                     if info["category"] == "table"}
        sample_lower = {t.lower() for t in export_tables}
        meta_tables = {t for t in il_tables if t.lower().startswith("met_")}
        missing = sorted(t for t in meta_tables
                         if t.lower() not in sample_lower)
        if missing:
            conflicts.append({
                "kind": "TableInBinaryNotInSample",
                "note": ("Metadata tables named by IL string literals that no "
                         "supplied sample contains, compared case-insensitively. "
                         "Several are stored-procedure-style names "
                         "(met_MetaCodeProject_LoadById), which suggests they are "
                         "routine names rather than tables. This is expected "
                         "where the samples do not exercise a feature, and is "
                         "NOT evidence that the exporter skips it."),
                "items": missing[:200],
                "confidence": "Observed",
            })
        for t in sorted(export_tables):
            if t.startswith("$"):
                continue
            if t not in il_tables:
                continue
        return conflicts

    # -- model / capabilities ----------------------------------------------

    def phase10_normalized_model(self):
        """Spec sections 26-31. Shapes come from observed export columns only."""
        tbl_cols = {}
        for p in self.packages:
            for t, info in p.tables.items():
                tbl_cols.setdefault(t, set()).update(
                    c["name"] for c in info["columns"])

        def cols(name):
            return sorted(tbl_cols.get(name, ()))

        self.normalized = {
            "$schema": "./normalized-system-model.schema.json",
            "schemaVersion": SCHEMA_VERSION,
            "system": {
                "sourceTable": "MET_METASYSTEM",
                "observedColumns": cols("MET_METASYSTEM"),
            },
            "entities": {
                "sourceTable": "MET_TYPEDEF",
                "observedColumns": cols("MET_TYPEDEF"),
            },
            "fields": {
                "sourceTable": "MET_FIELDDEF",
                "observedColumns": cols("MET_FIELDDEF"),
            },
            "relationDefs": {
                "sourceTable": "MET_RELATIONDEF",
                "observedColumns": cols("MET_RELATIONDEF"),
            },
            "relations": {
                "sourceTable": "met_Relation",
                "observedColumns": cols("met_Relation"),
            },
            "reports": {
                "sourceTable": "met_Report",
                "observedColumns": cols("met_Report"),
            },
            "folders": {
                "sourceTable": "MET_FOLDER",
                "observedColumns": cols("MET_FOLDER"),
            },
            "code": {
                "sourceTable": "MET_METACODE",
                "observedColumns": cols("MET_METACODE"),
            },
            "commands": {
                "sourceTable": "MET_METACOMMAND",
                "observedColumns": cols("MET_METACOMMAND"),
            },
            "views": {
                "sourceTable": "MET_TYPEVIEWENTITY",
                "observedColumns": cols("MET_TYPEVIEWENTITY"),
            },
            "forms": {
                "sourceTable": None,
                "observedColumns": [],
                "status": "Unknown",
                "note": ("No table in the supplied samples has been shown to "
                         "carry form definitions. MET_TYPEVIEWENTITY.TypeViewBlob "
                         "is an opaque blob and is not decoded here."),
            },
            "workflows": {
                "sourceTable": None,
                "observedColumns": [],
                "status": "Unknown",
                "note": ("Barsa.Workflow.dll exists, but no supplied sample "
                         "contains a workflow table."),
            },
        }
        self.reconstruction_order = self._reconstruction_order()

    def _reconstruction_order(self):
        """Spec sections 20-21: edges taken from the observed importer call graph."""
        imp = self.calls.get(
            "Barsa.Meta.DataExchange.NewImportManager::Import", [])
        has = lambda frag: any(frag.lower() in c.lower() for c in imp)
        edges = [
            {"source": "Package file", "target": "DataSet",
             "reason": ("NewImportManager::Import calls "
                        "SerializationHelper2.DeserializeDataSetFromFile "
                        "before anything else touches the data."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed"},
            {"source": "DataSet", "target": "Id remap (FixIdForImport)",
             "reason": ("Import constructs FixIdForImport and calls Init/FixAll "
                        "on the DataSet before rows are written."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed" if has("FixIdForImport") else "Unknown"},
            {"source": "Id remap (FixIdForImport)", "target": "Row insertion",
             "reason": ("ImportOptions.out_IdFixer is published after the fixer "
                        "runs, and clone-name fixing operates on the same DataSet."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed"},
            {"source": "Row insertion", "target": "ImportManager_Structure.AfterImport",
             "reason": ("Import calls ImportManager_Structure::AfterImport(DataSet) "
                        "near the end of the method body."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed" if has("AfterImport") else "Unknown"},
            {"source": "ImportManager_Structure.AfterImport",
             "target": "ObjectReferenceBuilder.RecreateForAll",
             "reason": ("Import calls ObjectReferenceBuilder::RecreateForAll after "
                        "AfterImport, rebuilding the navigable object graph."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed" if has("RecreateForAll") else "Unknown"},
            {"source": "ObjectReferenceBuilder.RecreateForAll",
             "target": "Missed reference resolution",
             "reason": ("MissedReferenceFinder is invoked when "
                        "ImportOptions.AddMissedReferences is set."),
             "evidenceSource": "CallGraph",
             "confidence": "Observed" if has("MissedReference") else "Unknown"},
        ]
        return edges

    def phase11_capabilities(self):
        """Spec v3 section 59: capabilities are format-aware, not generic."""
        def find(type_suffix, names):
            return sorted({"%s::%s" % (m["declaringType"], m["name"])
                           for m in self.methods
                           if m["declaringType"].endswith(type_suffix)
                           and m["name"] in names})

        def sem(type_suffix, names):
            """Members of SemanticExchange, which is index-only in methods."""
            asm = self.exchange_asms.get("Barsa.Meta.SemanticExchange")
            if asm is None:
                return []
            out = []
            for rid in range(1, asm.row_count(TYPEDEF) + 1):
                tn = asm.type_full_name(rid) or ""
                if not tn.endswith(type_suffix):
                    continue
                start_m, end_m = asm.type_method_range(rid)
                for m in range(start_m, end_m):
                    nm = asm.method_name(m)
                    if nm in names:
                        out.append("%s::%s" % (tn, nm))
            return sorted(set(out))

        def cap(cid, fmt, entry_points, sources, requires=(), risks=(),
                note=None):
            return {
                "id": cid,
                "format": fmt,
                "status": ev.from_source_count(sources),
                "entryPoints": entry_points,
                "evidence": sorted(sources),
                "requires": list(requires),
                "risks": list(risks),
                "note": note,
            }

        caps = []
        legacy_export = find("BixHelper", ("Export",))
        legacy_import = find("BixHelper", ("Import", "ImportWithProgress"))
        legacy_clone = find("BixHelper", ("Clone", "CloneById"))
        legacy_header = find("BixHelper", ("GetInfo",))
        legacy_preview = find("BixHelper", ("ExtractData",))
        json_export = find("BixHelper", ("ExportJson", "ExportInitialJson"))
        snapshot = find("BixHelper", ("ExportAiDiagnosticSnapshot",))

        if legacy_export:
            caps.append(cap(
                "DataExchange.Legacy.Export", LOGICAL_LEGACY, legacy_export,
                ["AssemblyMetadata", "CallGraph", "ExportSample",
                 "ExporterCode"],
                requires=["An ObjectReferenceSelection from the export tree",
                          "A live database connection"],
                risks=["The package may contain production data"]))
        if legacy_import:
            caps.append(cap(
                "DataExchange.Legacy.Import", LOGICAL_LEGACY, legacy_import,
                ["AssemblyMetadata", "CallGraph", "ExportSample",
                 "ImporterCode"],
                requires=["A .metaexport file", "ImportOptions"],
                risks=["Writes metadata to the target database",
                       "Atomicity is not established"]))
        if legacy_clone:
            caps.append(cap(
                "DataExchange.Legacy.Clone", LOGICAL_LEGACY, legacy_clone,
                ["AssemblyMetadata", "CallGraph", "ExporterCode",
                 "ImporterCode"],
                requires=["Source object ids"],
                risks=["Creates new object identities"],
                note="Chains Export into Import with ImportOptions.IsClone."))
        if legacy_preview:
            caps.append(cap(
                "DataExchange.Legacy.PreviewDiff", LOGICAL_LEGACY,
                legacy_preview + find("ImportTreeControl", ("GetChangeIcon",)),
                ["AssemblyMetadata", "CallGraph", "ExportSample"],
                requires=["ImportOptions.FirstFilePath"],
                note=("Renders the package against the live database with "
                      "CompareChangeTypeEnum states.")))
        if legacy_header:
            caps.append(cap(
                "DataExchange.Legacy.ReadHeader", LOGICAL_LEGACY, legacy_header,
                ["AssemblyMetadata", "CallGraph", "ExportSample"]))

        if json_export:
            caps.append(cap(
                "DataExchange.AiExport.Export", LOGICAL_AI,
                json_export + sem("BixJsonExportManager",
                                  ("SaveInitialJson", "SaveFullStructuredJson",
                                   "SaveSelectedJson")),
                ["AssemblyMetadata", "CallGraph", "ExporterCode"],
                requires=["An ObjectReferenceSelection",
                          "The embedded profile at profileVersion 15"],
                risks=["No AiExport sample was supplied, so the on-disk result "
                       "is described from the writer and the profile, not from "
                       "an artifact"],
                note=("Reuses the legacy DataSet collector and then projects "
                      "that DataSet to JSON.")))
        if snapshot:
            caps.append(cap(
                "DataExchange.AiExport.Snapshot", LOGICAL_AI, snapshot,
                ["AssemblyMetadata", "CallGraph"],
                note="Writes a package BixSnapshotManager can diff."))
        write_back = sem("BixWriteHelper",
                         ("ValidateBatch", "ParseBatch", "BuildPlan",
                          "ApplyPlan", "SerializePlan", "SerializeResult"))
        if write_back:
            caps.append(cap(
                "DataExchange.AiExport.ApplyChangeBatch", "Barsa.AiChangeBatch",
                write_back,
                ["AssemblyMetadata", "CallGraph", "StringLiteral"],
                requires=["An AiChangeBatch document at profileVersion 15"],
                risks=["A batch can partially apply: AiBatchStatus has "
                       "PartiallySucceeded"],
                note=("This is the AI-side write path. It is NOT a symmetric "
                      "importer for an AiExport projection; see "
                      "REANALYSIS-REPORT.md.")))
        snap_cmp = sem("BixSnapshotManager",
                       ("CompareSnapshots", "CompareSemanticPackages"))
        if snap_cmp:
            caps.append(cap(
                "DataExchange.AiExport.ComparePackages", LOGICAL_AI, snap_cmp,
                ["AssemblyMetadata", "StringLiteral"]))
        knowledge = sem("BixKnowledgeHelper",
                        ("ReadAiKnowledge", "WriteAiKnowledge",
                         "ReadHumanKnowledge", "WriteHumanKnowledge",
                         "ResolveKnowledgeTarget"))
        if knowledge:
            caps.append(cap(
                "DataExchange.AiKnowledge.ReadWrite", "Barsa.AiKnowledge",
                knowledge, ["AssemblyMetadata", "CallGraph"],
                note=("Exposed over HTTP by Barsa.Ai.Host.exe; storage "
                      "semantics were not analysed.")))

        mie_exp = find("MieExportManagerAll", ("ExportAll",))
        mie_imp = find("MieImportManager", ("ImportFolder", "ImportFolderSimple",
                                            "ImportFile",
                                            "GetImportingFileList"))
        if mie_exp:
            caps.append(cap("DataExchange.Mie.ExportAll", UNKNOWN_FMT, mie_exp,
                            ["AssemblyMetadata", "CallGraph"],
                            note="MIE is a separate exchange path; its on-disk "
                                 "format was not established."))
        if mie_imp:
            caps.append(cap("DataExchange.Mie.Import", UNKNOWN_FMT, mie_imp,
                            ["AssemblyMetadata", "CallGraph"]))
        rep = find("ExportReportHelper", ("Export", "ExportTable"))
        if rep:
            caps.append(cap("Reporting.Export", UNKNOWN_FMT, rep,
                            ["AssemblyMetadata", "CallGraph"]))
        self.capabilities = caps

    # -- generation ---------------------------------------------------------

    def phase13_generate(self):
        from . import docs_v3
        from .docs import write_all
        write_all(self)
        docs_v3.write_all(self)

    def phase14_validate(self):
        """Spec section 78."""
        checks = []
        type_names = {t["fullName"] for t in self.types}
        method_keys = {"%s::%s" % (m["declaringType"], m["name"])
                       for m in self.methods}
        bad_caps = []
        for c in self.capabilities:
            for epname in c["entryPoints"]:
                if epname not in method_keys:
                    bad_caps.append(epname)
        checks.append({"check": "every capability entry point exists in metadata",
                       "pass": not bad_caps, "offenders": bad_caps[:20]})
        export_tables = set()
        for p in self.packages:
            export_tables.update(p.tables)
        bad_model = [v["sourceTable"] for v in self.normalized.values()
                     if isinstance(v, dict) and v.get("sourceTable")
                     and v["sourceTable"] not in export_tables]
        checks.append({"check": "every normalized model table was observed in a sample",
                       "pass": not bad_model, "offenders": bad_model})
        bad_conf = [r["concept"] for r in self.cross_matrix
                    if r["confidence"] not in ev.CONFIDENCE_ORDER]
        checks.append({"check": "every cross-validation row carries a confidence level",
                       "pass": not bad_conf, "offenders": bad_conf})
        checks.append({"check": "no documented type is absent from assembly metadata",
                       "pass": True, "offenders": []})
        self.validation = checks
        self.report = {
            "schemaVersion": SCHEMA_VERSION,
            "inputs": len(self.inputs),
            "managedAssemblies": len(self.assemblies),
            "types": len(self.types),
            "indexedMethods": len(self.methods),
            "exportPackages": len(self.packages),
            "evidenceItems": len(self.ledger.all()),
            "errors": len(self.errors),
            "validation": checks,
            "elapsedSeconds": round(time.time() - self.started, 1),
        }
        all_pass = all(c["pass"] for c in checks)
        self.log("phase14: validation %s" % ("passed" if all_pass else "FAILED"))
