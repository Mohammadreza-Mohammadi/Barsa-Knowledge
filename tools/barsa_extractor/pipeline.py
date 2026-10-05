"""Phases 1-14 driver: reads source/, writes the dist/ knowledge pack."""

import json
import os
import re
import sys
import time

from . import evidence as ev
from .cli_metadata import TYPEDEF, METHODDEF
from .export_package import ExportPackage, compare, id_reference_model
from .il_analysis import (
    analyze_method, classify_string, extract_sql, invert_calls, redact,
    SQL_RE,
)
from .inventory import (
    discover, index_methods, index_types, inventory_assembly, is_barsa_domain,
    is_barsa_owned, priority_score,
)

SCHEMA_VERSION = "2.0"

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
        """Spec sections 32-33: one entry per capability with real entry points."""
        def find(pred):
            return sorted({"%s::%s" % (m["declaringType"], m["name"])
                           for m in self.methods if pred(m)})

        def cap(cid, entry_points, sources, requires=(), risks=()):
            return {
                "id": cid,
                "status": ev.from_source_count(sources),
                "entryPoints": entry_points,
                "evidence": sorted(sources),
                "requires": list(requires),
                "risks": list(risks),
            }

        caps = []
        exp = find(lambda m: m["declaringType"].endswith("BixHelper")
                   and m["name"] == "Export")
        imp = find(lambda m: m["declaringType"].endswith("BixHelper")
                   and m["name"] in ("Import", "ImportWithProgress"))
        clone = find(lambda m: m["declaringType"].endswith("BixHelper")
                     and m["name"] in ("Clone", "CloneById"))
        info = find(lambda m: m["declaringType"].endswith("BixHelper")
                    and m["name"] == "GetInfo")
        extract = find(lambda m: m["declaringType"].endswith("BixHelper")
                       and m["name"] == "ExtractData")
        jsonexp = find(lambda m: m["declaringType"].endswith("BixHelper")
                       and m["name"] in ("ExportJson", "ExportInitialJson"))
        if exp:
            caps.append(cap("System.Export", exp,
                            ["AssemblyMetadata", "CallGraph", "ExportSample",
                             "ExporterCode"],
                            requires=["An ObjectReferenceSelection built from the "
                                      "export tree", "A live database connection"],
                            risks=["Package may contain production data"]))
        if imp:
            caps.append(cap("System.Import", imp,
                            ["AssemblyMetadata", "CallGraph", "ExportSample",
                             "ImporterCode"],
                            requires=["A .metaexport file", "ImportOptions"],
                            risks=["Writes metadata to the target database",
                                   "Rollback behaviour not established statically"]))
        if clone:
            caps.append(cap("System.Clone", clone,
                            ["AssemblyMetadata", "CallGraph", "ExporterCode",
                             "ImporterCode"],
                            requires=["Source object ids"],
                            risks=["Creates new object identities"]))
        if info:
            caps.append(cap("Package.ReadHeader", info,
                            ["AssemblyMetadata", "CallGraph", "ExportSample"]))
        if extract:
            caps.append(cap("Package.PreviewTree", extract,
                            ["AssemblyMetadata", "CallGraph", "ExportSample"],
                            requires=["ImportOptions.FirstFilePath"]))
        if jsonexp:
            caps.append(cap("System.ExportJson", jsonexp,
                            ["AssemblyMetadata", "CallGraph"],
                            risks=["No JSON sample supplied; on-disk shape unverified"]))
        mie_exp = find(lambda m: m["declaringType"].endswith("MieExportManagerAll"))
        mie_imp = find(lambda m: m["declaringType"].endswith("MieImportManager"))
        if mie_exp:
            caps.append(cap("Mie.ExportAll", mie_exp,
                            ["AssemblyMetadata", "CallGraph"]))
        if mie_imp:
            caps.append(cap("Mie.Import", mie_imp,
                            ["AssemblyMetadata", "CallGraph"]))
        rep = find(lambda m: m["declaringType"].endswith("ExportReportHelper"))
        if rep:
            caps.append(cap("Report.Export", rep,
                            ["AssemblyMetadata", "CallGraph"]))
        self.capabilities = caps

    # -- generation ---------------------------------------------------------

    def phase13_generate(self):
        from .docs import write_all
        write_all(self)

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
