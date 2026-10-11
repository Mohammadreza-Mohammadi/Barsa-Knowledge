"""Spec v3 deliverables: format docs, comparison, reanalysis report."""

import json
import os
import time

from .docs import BANNER, _j, _jl, _table, _write, _yn
from . import system_index

LEGACY_LABEL = "Barsa.LegacyMetaExport"
AI_LABEL = "Barsa.AiExport"


def write_all(x):
    d = x.dist
    _format_detection(x, d)
    _legacy_docs(x, d)
    _ai_docs(x, d)
    _version_matrix(x, d)
    _comparison(x, d)
    _match_report(x, d)
    _change_batch(x, d)
    _golden_pair(x, d)
    _semantic_contract_doc(x, d)
    _write_pipeline_doc(x, d)
    _reanalysis(x, d)
    _v3_indexes(x, d)
    _v3_scenarios(x, d)


# --- formats ---------------------------------------------------------------

ZIP_SIG = "`PK` 03 04, or `PK` 05 06 for an empty archive"
JSON_SIG = "optional UTF-8 BOM, then an opening brace or bracket"
BF_SIG = ("GZip payload begins with the BinaryFormatter header "
          "00 01 00 00 00 FF FF FF FF and names `System.Data.DataSet`")


def _format_detection(x, d):
    physical_table = _table(
        ["Physical format", "Signature", "Where it leads"], [
            ["GZip", "1F 8B",
             "decompress, then look for BinaryFormatter and DataSet markers"],
            ["ZIP", ZIP_SIG, "read `manifest.json` from the archive"],
            ["PlainJson", JSON_SIG,
             "parse, then read `manifest` or `format`"],
            ["XML", "a leading `<`", "not an export family seen here"],
            ["PE", "`MZ`", "an assembly, handled by the inventory phases"],
        ])
    logical_table = _table(
        ["Logical format", "Marker", "Confidence when matched"], [
            ["`" + LEGACY_LABEL + "`", BF_SIG, "Verified"],
            ["`" + AI_LABEL + "`",
             ("a manifest whose `format` is `Barsa.AiExport`, either at "
              "`$.manifest` in a single document or in `manifest.json` inside "
              "a ZIP"), "Verified"],
            ["`AiExport.MultiProjectionPackage`",
             "a ZIP manifest whose `packageType` is `barsa-json-export`",
             "Verified"],
        ])
    rows = [[f"`{r['path']}`", r["physicalFormat"], r["logicalFormat"],
             r["variant"], r["confidence"],
             len(r["warnings"]) or "", len(r["errors"]) or ""]
            for r in sorted(x.formats, key=lambda r: r["path"])]
    warn = [[f"`{w['path']}`", w["kind"], w["message"]]
            for w in x.format_warnings]
    _write(d, "formats/format-detection.md", f"""# Format detection

{BANNER}
Spec v3 section 3. Detection runs on bytes, never on the file name. A `.zip`
that holds a plain JSON document is classified as JSON with a warning, not
rejected as a broken ZIP.

## Order of inference

```
magic bytes  ->  physical format
                      |
                      v
  embedded markers / manifest  ->  logical format
                      |
                      v
            structure  ->  variant
                      |
                      v
                 parser choice
```

## Physical signatures used

{physical_table}

## Logical markers

{logical_table}

The `Barsa.AiExport` literal is not a guess: `JsonExportDocumentBuilder.BuildInitialDocument`
and `JsonExportPackageWriter.WriteManifest` both write it, and
`MetadataPackageWatcher.IsSemanticProjectionManifest` reads it back.

## Artifacts detected this run

{_table(["Path", "Physical", "Logical", "Variant", "Confidence", "Warnings", "Errors"], rows)
 if rows else "_No candidate artifacts found._"}

Totals: {", ".join("`%s` x%d" % (k, v) for k, v in sorted(x.format_counts.items())) or "_none_"}

## Warnings

{_table(["Path", "Kind", "Message"], warn) if warn else "_None._"}

## Error model

Failures are format-specific per spec v3 section 63, so a bad ZIP and a bad
GZip are not reported as the same thing: `PhysicalFormatDetectionError`,
`GZipDecodeError`, `LegacyPayloadParseError`, `JsonParseError`,
`ZipPackageError`, `ManifestError`, `NormalizationError`, `ScopeMatchError`,
`SemanticMatchError`.
""")


def _legacy_docs(x, d):
    p0 = x.packages[0] if x.packages else None
    _write(d, "formats/legacy-metaexport.md", f"""# Legacy MetaExport format

{BANNER}
**Logical format:** `{LEGACY_LABEL}` · **Confidence: CrossVerified**

## Container

```
<file>.metaexport
  └── GZip                                  (1F 8B, "max speed")
        └── .NET BinaryFormatter graph      (00 01 00 00 00 FF FF FF FF)
              └── System.Data.DataSet
                    ├── "DataSet.RemotingVersion" -> System.Version
                    ├── "XmlSchema"               -> XSD, one xs:element per table
                    └── "XmlDiffGram"             -> one node per row
```

Writer and reader, from assembly metadata:

```
SerializationHelper2.BinarySerializeToFile(string, System.Data.DataSet)
SerializationHelper2.DeserializeDataSetFromFile(string) : System.Data.DataSet
```

The compression argument type is `Barsa.Spl.SerializationUtil+CompressionType`.

The embedded XML declares `utf-16` but the bytes are UTF-8, because
BinaryFormatter writes strings as UTF-8. A reader must ignore the declaration.

> **Security.** Deserializing an untrusted BinaryFormatter payload is a remote
> code execution risk. This extractor never deserializes; it lifts the two XML
> strings straight out of the byte stream (spec v3 section 61).

## Not a ZIP, and not JSON

The legacy family is its own thing. The `.zip` filter in the export file dialog
belongs to the **AiExport** path, not to this one.

## Samples analysed

{_table(["File", "Core version", "Tables", "Rows", "Pages"],
        [[p.path.split("/")[-1], p.header.get("Core Version", "?"),
          len(p.tables), sum(p.row_counts.values()),
          p.header.get("PageCount", "?")] for p in x.packages])
 if x.packages else "_None supplied._"}

## Where the detail lives

- Table and column inventory: `formats/legacy-dataset-schema.md`
- ID remapping: `formats/id-reference-model.md`
- Import flow: `scenarios/import-system-legacy.md`
- Preview and diff: `scenarios/preview-import-diff.md`
""")

    if p0:
        ctrl = sorted(t for t in p0.tables if t.startswith("$"))
        data = sorted(t for t in p0.tables if not t.startswith("$"))
        _write(d, "formats/legacy-dataset-schema.md", f"""# Legacy DataSet schema

{BANNER}
Spec v3 section 16. Read from each sample's own embedded XSD, so the table and
column lists are **Verified**; the meaning ascribed to a column is only as
strong as its stated evidence.

## Control tables

Export-session bookkeeping and importer instructions rather than payload.

{_table(["Table", "Columns", "Role"], [
 [f"`{t}`", len(p0.tables[t]["columns"]),
  {
   "$Header": "Provenance: source database, core version, export time, page count.",
   "$RootSelection": "The nodes the operator picked in the export tree.",
   "$Selection": "The full closure exported after reference expansion.",
   "$DeletedRecords": "Tombstones so the importer can propagate deletions.",
   "$spl_EorgType": "Type id scope.",
   "$spl_EorgCenter": "Centre id scope; carries IsImported.",
   "$IdEmbeddingFields": "Per-column ID remap instructions.",
   "$Data_TypeDefDbNames": "TypeDef id -> physical table name.",
   "$Data_FieldDefDbNames": "FieldDef id -> physical column name.",
   "$basicInfoRelation": "Relation rows in the shared-infrastructure scope.",
  }.get(t, "Unknown")]
 for t in ctrl])}

## Payload tables in the first sample

{_table(["Table", "Columns", "Rows"],
        [[f"`{t}`", len(p0.tables[t]["columns"]), p0.row_counts.get(t, 0)]
         for t in data])}

## Dynamic naming

`dyn_*` and `m0*_*` table names are not stable across systems. The package
carries `$Data_TypeDefDbNames` and `$Data_FieldDefDbNames` to resolve a TypeDef
or FieldDef id to its physical table and column. A reader that hard-codes a
`dyn_` name will break on the next system.

The AiExport profile corroborates this from the other side: each of its record
types declares the legacy table it comes from, and `JsonExportDocumentBuilder`
loads `LoadTableNameByLocalId` / `LoadDataTypeDefInfo` / `LoadDataFieldDefInfo`
from exactly these control tables.

Full machine-readable inventory: `index/legacy-dataset-tables.json`.
""")


def _ai_docs(x, d):
    live = x.live_profile
    pv = x.profile_version
    vs = x.variant_switch
    ai = x.ai_import

    _write(d, "formats/ai-export.md", f"""# Barsa.AiExport format

{BANNER}
**Logical format:** `{AI_LABEL}` · **Producer:** `Barsa.Meta.SemanticExchange`

## The headline

AiExport is **not** a second extraction path. It is a **projection of the same
DataSet** the legacy export collects:

```mermaid
graph LR
  SEL["ObjectReferenceSelection<br/>(export tree)"] --> NEM["NewExportManager.Export"]
  NEM --> DS["System.Data.DataSet<br/>(the common intermediate)"]
  DS --> BF["SerializationHelper2<br/>BinarySerializeToFile"]
  BF --> LEG[".metaexport<br/>GZip + BinaryFormatter"]
  DS --> SEC["SemanticExportContext"]
  SEC --> BJEM["BixJsonExportManager<br/>SaveSelectedJson"]
  BJEM --> JDB["JsonExportDocumentBuilder<br/>BuildInitialDocument"]
  JDB --> JPW["JsonExportPackageWriter.Save"]
  JPW --> AIJ["JSON document or ZIP package"]
```

Evidence for the shared trunk: `BixHelper.ExportJson` constructs a
`NewExportManager` and calls its `Export`, passing a callback that builds a
`SemanticExportContext` from `ExportSaveContext.DataSet`. The hand-off into the
semantic engine is a delegate call, so the proof is the MemberRef row in
`Barsa.Meta.DataExchange` naming
`BixJsonExportManager::SaveSelectedJson` — compiled-against evidence, stronger
than a name match. **Confidence: CrossVerified.**

A consequence worth stating plainly: AiExport can never carry source data the
legacy DataSet did not collect. Differences between the two are projection
differences, not collection differences.

## Assembly layout, and why v2 missed this

`Barsa.Meta.SemanticExchange.dll` declares its types in the
`Barsa.Meta.DataExchange` **namespace** while being a separate assembly, and it
does not reference `Barsa.Meta.DataExchange.dll` (the dependency runs the other
way). A namespace-scoped search finds nothing. It is also **not obfuscated**,
so its member names are real.

{_table(["Assembly", "Version", "Obfuscated", "Role"], [
 ["`Barsa.Meta.DataExchange`",
  x.assemblies and next((r["assemblyVersion"] for r in x.assemblies.values()
                         if r["assemblyName"] == "Barsa.Meta.DataExchange"), "?"),
  "yes (private members)", "legacy export/import, and the BixHelper facade"],
 ["`Barsa.Meta.SemanticExchange`",
  next((r["assemblyVersion"] for r in x.assemblies.values()
        if r["assemblyName"] == "Barsa.Meta.SemanticExchange"), "?"),
  "no", "AiExport projection, change planning, write-back"],
 ["`Barsa.Ai.Host`",
  next((r["assemblyVersion"] for r in x.assemblies.values()
        if r["assemblyName"] == "Barsa.Ai.Host"), "?"),
  "no", "HTTP surface over the semantic engine"],
])}

## The profile is the specification

`AiExportProfileLoader.LoadEmbedded` reads a JSON rule document shipped as a
manifest resource. That document, not a sample, is the authoritative description
of the format.

{_table(["Resource", "profileVersion", "Bytes", "Record types", "Serialized types", "Enums", "Binary decoders"],
        [[f"`{os.path.basename(p.resource)}`", p.profile_version, p.raw_size,
          len(p.record_types), len(p.serialized_types), len(p.enums),
          len(p.binary_decoders)] for p in x.profiles])}

Sections: {", ".join("`%s`" % s for s in (sorted(live.doc) if live else [])) or "_unavailable_"}

### Engine rules (v15)

{_table(["Rule", "Value", "Reading"], [
 ["`unknownRecordType`", (live.engine.get("unknownRecordType") if live else "?"),
  "a record type with no rule is still emitted"],
 ["`unknownField`", (live.engine.get("unknownField") if live else "?"),
  "a column with no rule is kept"],
 ["`omitNull`", (live.engine.get("omitNull") if live else "?"),
  "null-valued properties are dropped from the output"],
 ["`omitDefault`", (live.engine.get("omitDefault") if live else "?"),
  "a property equal to its declared default is dropped"],
 ["`binary.unknownBinary`", (live.engine.get("binary", {}).get("unknownBinary") if live else "?"),
  "a binary column with no decoder is dropped"],
 ["`binary.onDecodeError`", (live.engine.get("binary", {}).get("onDecodeError") if live else "?"),
  "a decode failure is written as an error marker rather than failing the export"],
 ["`largeCode.mode`", (live.engine.get("largeCode", {}).get("mode") if live else "?"),
  "long code values become separate files"],
 ["`largeCode.thresholdChars`", (live.engine.get("largeCode", {}).get("thresholdChars") if live else "?"),
  "the length at which that happens"],
]) if live else "_Profile unavailable._"}

`omitNull` and `omitDefault` both being true matters for any comparison: an
absent property in AiExport may mean "null or default", not "missing". Treating
absence as loss would produce false positives.

### Record types

{len(live.record_types) if live else 0} record types, each naming the legacy
table it projects from. This is Barsa's own Legacy-to-AiExport mapping.

{_table(["Record type", "Legacy table", "Output", "Fields", "Omitted", "References", "Decoders"],
        [[f"`{r['recordType']}`",
          f"`{r['legacyTable']}`" if r["legacyTable"] else "—",
          r["output"] or "—", r["fieldCount"], len(r["omittedFields"]),
          len(r["referenceFields"]), len(r["decoderFields"])]
         for r in (live.record_type_rows() if live else [])])}

### Binary decoders

The legacy format's opaque blobs are **not** opaque to AiExport: the profile
names a decoder for each one.

{_table(["Record type", "Field", "Decoder", "Implementation"],
        [[f"`{t['recordType']}`", f"`{t['field']}`", f"`{t['decoder']}`",
          f"`{t['implementation']}`" if t["implementation"] else "—"]
         for t in (live.decoder_targets() if live else [])])}

This resolves two things the v2 pack recorded as Unknown: `met_Report.ReportData`
has a declared decoder (`SerializeReportData`), and
`MET_TYPEVIEWENTITY.TypeViewBlob` routes through `SerializeTypeView`. The
decoders are **named**; their output shape is still Unknown, because this
extractor does not run them.

### Enums spelled out

{len(live.enums) if live else 0} enums are expanded from numeric values to
names in the profile, so AiExport output is readable where the legacy DataSet
stores integers. Full list: `index/ai-export-properties.json`.

## See also

- `formats/ai-export-single-json.md`
- `formats/ai-export-zip-package.md`
- `formats/ai-export-profile-version.md`
- `comparison/legacy-vs-ai-export.md`

## Caveat on samples

{"No AiExport artifact is present in `source/`." if not x.ai_artifacts else
 "%d AiExport artifact(s) were analysed." % len(x.ai_artifacts)}
Everything above is read from the binary and the embedded profile. Where a
statement would need an artifact to confirm, it is marked as such.
""")

    pk = live.packaging_rules() if live else {}
    _write(d, "formats/ai-export-zip-package.md", f"""# AiExport: ZIP JSON package

{BANNER}
Spec v3 section 29. **Variant:** `AiExport.ZipJsonPackage`

## Layout, from the profile's packaging rules

The bracketed folder names the specification asks about are declared outright in
the embedded profile. They are Persian labels, used literally as directory
names.

{_table(["Rule", "Value", "Meaning"], [
 ["`systemRecordFile`", f"`{pk.get('systemRecordFile')}`",
  "the file holding the system record"],
 ["`unmappedRecordsFile`", f"`{pk.get('unmappedRecordsFile')}`",
  "records with no record-type rule"],
 ["`includeUnmappedRecords`", str(pk.get("includeUnmappedRecords")),
  "whether that file is written at all"],
]) if pk else "_Profile unavailable._"}

### Relation groups — a folder per relation

{_table(["Relation", "Folder", "Items", "Match mode"],
        [[f"`{g.get('relation')}`", f"`{g.get('folder')}`",
          g.get("items"), g.get("match")]
         for g in pk.get("relationGroups", [])])}

`items` chooses between one file per related object (`file`) and one file per
child (`child-files`). `match` is `exact` or `contains`, which lines up exactly
with the `JsonExportRelationMatchMode` enum in the binary — profile and binary
agree, so **CrossVerified**.

Note the deliberate duplicates: `فرآيند` and `فرآیند` both map to the same
folder. Those two strings differ in one character (Arabic yeh versus Persian
yeh). The profile handles both spellings, which is a real-world detail a reader
must preserve rather than normalize away.

### Single-file relations

{_table(["Relation", "File", "Match mode"],
        [[f"`{r.get('relation')}`", f"`{r.get('file')}`", r.get("match")]
         for r in pk.get("relationFiles", [])]) if pk.get("relationFiles") else "_None._"}

### Omitted relations

{", ".join("`%s`" % r for r in pk.get("omitRelations", [])) or "_None._"}

## Does the directory hierarchy carry meaning?

Yes. `JsonExportPackageWriter` has dedicated writers per group —
`WriteEntityGroup`, `WriteWorkflowGroup`, `WriteSystemCodeGroup`,
`WriteMainFolderGroup`, `WriteFolderTreeNode` — and the group is chosen by
`IsEntityGroup` / `IsWorkflowGroup` / `IsSystemCodeGroup` / `IsMainFolderGroup`
matching the relation name against the profile. So a file's location is derived
from its relation, not incidental. **Confidence: Observed** (from metadata and
the profile; no artifact was available to confirm the resulting tree).

## Are file names identifiers or captions?

Captions, made filesystem-safe. `GetNodeFileNameBase`, `MakeSafeFileName`,
`NormalizeCaption`, `ShortenSafeName`, `FitSafeNameWithSuffix`,
`GetStablePathHash` and `GetUniqueFileName` together show names are derived from
display text, truncated to a path-length budget, and disambiguated with a hash
when they collide. **A file name is therefore not a stable identity.** Identity
lives in the file's `selector` and `id`.

## Can files be reordered?

Unknown. `OrderNavigationChildren` and `GetNavigationSemanticOrder` show
navigation children are written in a computed order, and several records carry
an explicit `OrderNumber`, so order is at least partly data rather than
filesystem order. Whether a consumer may reorder files was not established.

## Assets

`MaterializePortableAssets` and `ExternalizeLargeCodeValues` write non-JSON
payloads next to the records: code longer than the profile's
`thresholdChars` becomes a file whose extension comes from `CodeLayer`
({", ".join("`%s` -> `%s`" % (k, v) for k, v in sorted(
    (live.engine.get("largeCode", {}).get("extensionRule", {}).get("map", {})
     if live else {}).items())) or "no map"},
default `{live.engine.get("largeCode", {}).get("extensionRule", {}).get("defaultExtension") if live else "?"}`).
""")

    _write(d, "formats/ai-export-single-json.md", f"""# AiExport: single JSON document

{BANNER}
Spec v3 sections 24 and 28. **Variant:** `AiExport.SingleJson`

## Root shape

`JsonExportDocumentBuilder.BuildInitialDocument` writes these root properties:

```json
{{
  "tree": [ ... ],
  "manifest": {{
    "format": "Barsa.AiExport",
    "profileVersion": 15
  }},
  "unmappedRecords": [ ... ]
}}
```

`tree` and `manifest` are **Verified** from the builder's own string literals.
`unmappedRecords` is written only when the profile's
`includeUnmappedRecords` is true, which in the v15 profile is
`{(x.live_profile.packaging_rules().get("includeUnmappedRecords") if x.live_profile else "?")}`.
`manifest.representation` is set to `fullStructured` for the full-structured
projection and absent for the semantic one — so **absence of that key is
meaningful**, and a reader must not default it.

`JsonExportPackageWriter.AddProducerIdentity` adds the producer fields; see
`formats/version-matrix.md`.

## Why this is the same pipeline as the ZIP

{vs["answer"]}

{_table(["Mechanism", "How it works", "Evidence", "Confidence"],
        [[m["mechanism"], m["detail"], ", ".join(m["evidence"]), m["confidence"]]
         for m in vs["mechanisms"]])}

### Node output kinds

{_table(["Member", "Value"],
        [[f"`{m['name']}`", m["value"]] for m in
         (vs["mechanisms"][0]["members"] or [])])
 if vs["mechanisms"][0]["members"] else "_Enum unavailable._"}

`Inline` keeps a node inside its parent document; `File` and `Folder` make it a
separate artifact. A document where every node is `Inline` **is** the single-JSON
variant. That is the mechanism the specification was asking after.

### Requested representations

{_table(["Member", "Value"],
        [[f"`{m['name']}`", m["value"]] for m in
         (vs["mechanisms"][3]["members"] or [])])
 if vs["mechanisms"][3]["members"] else "_Enum unavailable._"}

A flags enum, so one call can request several representations; when more than
one is asked for, `SaveMultiProjectionPackage` wraps `semantic.zip` and
`full.zip` in an outer ZIP with its own `packageType: barsa-json-export`
manifest.

## Still unknown

{chr(10).join("- " + u for u in vs["stillUnknown"])}

## Observed paths

{"_No AiExport artifact was supplied, so no JSON path inventory could be built. The schema above comes from the writer and the profile._" if not x.ai_artifacts else _table(["Path", "Types", "Occurrences", "Nullable"], [[f"`{r['path']}`", ", ".join(r["observedTypes"]), r["occurrences"], _yn(r["nullable"])] for a in x.ai_artifacts for r in a.json_paths()[:400]])}
""")

    _write(d, "formats/ai-export-profile-version.md", f"""# profileVersion

{BANNER}
Spec v3 sections 26 and 27.

## What it is

{pv["answer"]}

## Observed values

Embedded in `Barsa.Meta.SemanticExchange`:

{_table(["Resource", "profileVersion", "Is schema", "Bytes"],
        [[f"`{os.path.basename(p['resource'])}`", p["profileVersion"],
          _yn(p["isSchema"]), p["sizeBytes"]] for p in pv["embeddedProfiles"]])}

## v14 and v15 differ only in the version number

**{pv["v14AndV15DifferOnlyInVersionNumber"]}** — the two profile documents are
byte-identical apart from the `profileVersion` value itself.

That is a precise answer to "is 15 a schema version?": **no**. Nothing about the
rules changed between 14 and 15. The bump exists to make v14 artifacts
non-executable while keeping the rules the same. The assembly keeps the v14 copy
and the runtime refuses it.

## The gates

Six independent sites refuse anything but 15. **Confidence: Verified.**

{_table(["Site", "Message"],
        [[f"`{g['site']}`", g["literal"]] for g in pv["gates"]])}

So for the AI path, spec v3 question J — is a version actually validated — is
answered **yes, hard**. (The legacy path's `$Header.Core Version` is a separate
question and remains Unknown; see `formats/import-compatibility.md`.)

## Still unknown

{chr(10).join("- " + u for u in pv["stillUnknown"])}
""")


def _version_matrix(x, d):
    rows = []
    for p in x.profiles:
        if p.is_schema:
            continue
        rows.append([f"`{os.path.basename(p.resource)}`",
                     "embedded profile", p.assembly, p.profile_version,
                     "n/a", "n/a"])
    for r in x.formats:
        m = normalize_manifest_safe(r)
        rows.append([f"`{r['path']}`", r["logicalFormat"],
                     (m or {}).get("producer") or "—",
                     (m or {}).get("profileVersion") or "—",
                     r["variant"], r["physicalFormat"]])
    producers = {}
    for key, rec in x.assemblies.items():
        if rec["assemblyName"] in ("Barsa.Meta.DataExchange",
                                   "Barsa.Meta.SemanticExchange",
                                   "Barsa.Ai.Host"):
            producers[rec["assemblyName"]] = rec["assemblyVersion"]
    _write(d, "formats/version-matrix.md", f"""# Version matrix

{BANNER}
Spec v3 sections 27 and 89.

## Producer assemblies

`JsonExportPackageWriter.AddProducerIdentity` stamps the producing assembly into
the manifest. Cross-checking a manifest's `producerVersion` against these is how
an artifact is tied to a build.

{_table(["Assembly", "Assembly version"],
        [[f"`{k}`", v] for k, v in sorted(producers.items())])}

The specification reports a manifest carrying
`producer: Barsa.Meta.DataExchange`, `producerVersion: 4.1.203.0`. That version
**matches** the assembly versions above, so the two are consistent. The
`producer` value naming `Barsa.Meta.DataExchange` while the writer lives in
`Barsa.Meta.SemanticExchange` is worth noting: the stamp is the subsystem name,
not necessarily the assembly that wrote the file. Since no AiExport artifact is
present in `source/`, this is recorded from the specification text as
**UserProvided, pending re-verification**, not as a measured fact.

## Artifacts

{_table(["Artifact", "Logical format", "Producer", "profileVersion", "Variant", "Physical"], rows)
 if rows else "_None._"}

## Legacy versioning

The legacy package carries `$Header.Core Version`
({", ".join(sorted({p.header.get("Core Version", "?") for p in x.packages})) or "none"})
plus the `Ver_MetaSystemInfo` and `Ver_MetaSystemVersion` tables, whose columns
include `BackwardCompatible` and `ForwardCompatible`. That the package *models*
compatibility is Verified. Whether the importer enforces it is Unknown.
""")


def normalize_manifest_safe(rec):
    from .format_detect import normalize_manifest
    try:
        return normalize_manifest(rec)
    except Exception:
        return None


# --- comparison ------------------------------------------------------------

def _comparison(x, d):
    ai = x.ai_import
    _write(d, "comparison/scope-equivalence.json", _j({
        "schemaVersion": "3.0",
        "rule": ("Spec v3 section 39: two exports are compared in full only "
                 "when their selection scope is equivalent. Equal filenames "
                 "prove nothing."),
        "levels": ["Exact", "Partial", "Candidate", "Different", "Unknown"],
        "declaredPairs": x.declared_pairs,
        "candidatePairs": x.pairs,
        "assessments": [c["scope"] for c in x.comparisons],
        "note": ("No AiExport artifact is present in source/, so no "
                 "cross-format pair could be assessed."
                 if not x.ai_artifacts else None),
    }))

    missing = [dd for c in x.comparisons for dd in c["differences"]
               if dd["differenceType"] == "MissingInAiExport"]
    extra = [dd for c in x.comparisons for dd in c["differences"]
             if dd["differenceType"] == "ExtraInAiExport"]
    _write(d, "comparison/missing-in-ai-export.json", _j(missing))
    _write(d, "comparison/extra-in-ai-export.json", _j(extra))
    _write(d, "comparison/mismatched-values.json", _j(
        [dd for c in x.comparisons for dd in c["differences"]
         if dd["differenceType"] == "ValueMismatch"]))
    _write(d, "comparison/mismatched-types.json", _j(
        [dd for c in x.comparisons for dd in c["differences"]
         if dd["differenceType"] == "TypeMismatch"]))
    _write(d, "comparison/id-mapping-differences.json", _j({
        "legacy": {
            "model": "declared per column in $IdEmbeddingFields",
            "operationalTypes": ["pk", "fk", "idpattern", "idlist"],
            "consumer": "FixIdForImport.Init / FixAll",
            "idScopeTables": ["$spl_EorgType", "$spl_EorgCenter"],
            "confidence": "CrossVerified",
        },
        "aiExport": {
            "model": ("semantic selectors plus raw ids; the profile marks "
                      "reference fields with a 'reference' rule whose value "
                      "is 'meta'"),
            "selectorCodec": "SemanticSelectorCodec",
            "dbNameRemap": ["AiDbNameRemapContract", "AiDbNameRemapEntry"],
            "referenceContract": ["AiSemanticReferenceContract",
                                  "AiSemanticReferenceResolver",
                                  "AiPlanReferenceBinding"],
            "deferredBinding": "AiDeferredBindingEntry",
            "lifecycle": [m["name"] for m in x.answer_enums.get(
                "Barsa.Meta.DataExchange.AiSemanticReferenceLifecycle",
                {}).get("members", [])],
            "confidence": "Verified",
        },
        "keyDifference": ("Legacy remaps numeric ids after the fact, driven by "
                          "a table the package carries. AiExport carries "
                          "semantic selectors that are resolved against the "
                          "target at apply time, with explicit lifecycle "
                          "phases and a deferred-binding mechanism for "
                          "references that cannot resolve yet."),
    }))

    cov_rows = []
    for c in x.comparisons:
        for r in c["coverage"]["rows"]:
            cov_rows.append([c["pair"]["legacy"], c["pair"]["aiExport"],
                             r["concept"], r["legacy"], r["aiExport"],
                             r["legacyCount"], r["aiCount"]])

    # Schema-level coverage from the profile, which needs no artifact pair.
    live = x.live_profile
    table_map = live.legacy_table_map() if live else {}
    legacy_tables = set()
    for p in x.packages:
        legacy_tables.update(t.lower() for t in p.tables)
    schema_rows = []
    for rt, table in sorted(table_map.items()):
        schema_rows.append([
            f"`{rt}`", f"`{table}`",
            _yn(table and table.lower() in legacy_tables),
            "CrossVerified" if (table and table.lower() in legacy_tables)
            else "Verified"])

    pct_lines = []
    for c in x.comparisons:
        cov = c["coverage"]
        pct = cov.get("compatibilityPercentage")
        pct_lines.append("### %s" % c["pair"]["legacy"])
        pct_lines.append("")
        pct_lines.append("Scope: **%s**" % c["scope"]["level"])
        pct_lines.append("")
        if pct is None:
            pct_lines.append("**Not computable.** " + cov["percentageNote"])
        else:
            pct_lines.append("**%s%%** of legacy objects found a counterpart."
                             % pct)
            pct_lines.append("")
            pct_lines.append(cov["percentageNote"])
            pct_lines.append("")
            pct_lines.append(_table(
                ["Concept", "Legacy objects", "Matched", "Percent"],
                [[b["concept"], b["legacyObjects"], b["matched"],
                  "%s%%" % b["percent"] if b["percent"] is not None else "-"]
                 for b in cov.get("percentageBreakdown", [])]))
        pct_lines.append("")
    pct_section = ("\n".join(pct_lines) if pct_lines else
                   "No pair exists, so no percentage is produced.")

    _write(d, "comparison/semantic-coverage.md", f"""# Semantic coverage

{BANNER}
Spec v3 sections 50 and 53.

## Artifact-level comparison

{"**Not performed.** No AiExport artifact is present in `source/`, so there is no pair to compare. Per spec v3 section 54 no compatibility percentage is produced." if not x.comparisons else _table(["Legacy", "AiExport", "Concept", "In legacy", "In AiExport", "Legacy count", "AiExport count"], cov_rows)}

## Schema-level coverage

This does not need a pair. The embedded profile declares, for each AiExport
record type, the legacy table it projects from — so the two formats' concept
coverage can be compared directly at the schema level.

{_table(["AiExport record type", "Legacy table", "Table seen in a supplied sample", "Confidence"], schema_rows)
 if schema_rows else "_Profile unavailable._"}

### Record types with no legacy table

These are AiExport record types the profile does not tie to a legacy table.
They may be computed, may come from elsewhere, or may be AiExport-only.
**Status: Unknown** — not "extra", and not "missing".

{", ".join("`%s`" % r["recordType"] for r in (live.record_type_rows() if live else []) if not r["legacyTable"]) or "_None._"}

## Compatibility percentage

{pct_section}
""")

    _write(d, "comparison/legacy-vs-ai-export.md", f"""# Legacy MetaExport versus Barsa.AiExport

{BANNER}
Spec v3 sections 7 and 50. Legacy is the comparison baseline because it has a
proven importer — but per section 7 it is **not** assumed to contain every Barsa
feature.

## Side by side

{_table(["Aspect", LEGACY_LABEL, AI_LABEL], [
 ["Physical form", "GZip", "plain JSON, or ZIP of JSON files"],
 ["Serializer", ".NET BinaryFormatter", "Newtonsoft.Json"],
 ["Payload", "`System.Data.DataSet` (XSD + DiffGram)", "a `tree` of records plus a `manifest`"],
 ["Producing assembly", "`Barsa.Meta.DataExchange`", "`Barsa.Meta.SemanticExchange`"],
 ["Collection engine", "`NewExportManager`", "`NewExportManager` — the same one"],
 ["Identity", "numeric ids, scope-qualified", "semantic selectors plus ids"],
 ["Enum values", "stored as integers", "expanded to names by the profile"],
 ["Binary blobs", "opaque columns", "decoded by named decoders, or marked as errors"],
 ["Long code", "inline in the column", "externalized to a file past a threshold"],
 ["Null and default", "present as rows", "omitted (`omitNull`, `omitDefault`)"],
 ["Read-back path", "`NewImportManager.Import`, a symmetric importer", "`BixWriteHelper.ApplyPlan`, a change-batch executor"],
 ["Diff tooling", "`ImportTreeForm` against the live database", "`BixSnapshotManager.CompareSemanticPackages`"],
 ["Version gate", "Unknown", "hard-gated at `profileVersion` 15"],
 ["Human readable", "no", "yes"],
])}

## The relationship

AiExport is a **projection** of the legacy DataSet, not an alternative
extraction. Both start from one `ObjectReferenceSelection`, both run
`NewExportManager.Export`, and both end up holding the same `DataSet`. Only the
serialization downstream differs.

Two consequences follow, and they are the practically important part:

1. **AiExport cannot contain source data the legacy DataSet did not collect.**
   Any concept missing from AiExport but present in Legacy is a projection gap —
   a profile rule, an omitted field, a missing record type — never a collection
   gap.
2. **An absent property in AiExport is ambiguous.** With `omitNull` and
   `omitDefault` both true, absence means "null, or equal to the default, or not
   projected". Reading absence as data loss produces false positives, which is
   exactly what spec v3 section 52 warns against.

## Read-back is not symmetric

{ai["answer"]}

What exists:

{chr(10).join("- `%s`" % e for e in ai["whatExists"]["entryPoints"])}

Engine: {", ".join("`%s`" % e for e in ai["whatExists"]["engine"])}

Change providers ({len(ai["whatExists"]["providers"])}):
{", ".join("`%s`" % p.split(".")[-1] for p in ai["whatExists"]["providers"])}

Operations: {", ".join("`%s`" % o for o in ai["whatExists"]["operations"]) or "unknown"}

What is **not** established:

{chr(10).join("- " + n for n in ai["whatIsNotEstablished"])}

{ai["notUnsupported"]}

## Difference classification

When a pair does become available, differences are typed per spec v3 section 51
and only promoted to `BugCandidate` under the section 52 conditions: scope
Exact, a strong identity match, and evidence the concept matters. Everything
else stays a `Difference`.

{_table(["Difference type", "Count this run"], [
 ["MissingInAiExport", len(missing)],
 ["ExtraInAiExport", len(extra)],
 ["ValueMismatch", 0],
 ["TypeMismatch", 0],
 ["RepresentationDifference",
  len([dd for c in x.comparisons for dd in c["differences"]
       if dd["differenceType"] == "RepresentationDifference"])],
])}

{"All counts are zero because no AiExport artifact was supplied." if not x.ai_artifacts else ""}
""")


# --- reanalysis ------------------------------------------------------------

def _reanalysis(x, d):
    live = x.live_profile
    exact = [c for c in x.comparisons
             if c["scope"]["level"] == "Exact"]
    not_same_build = [c for c in exact
                      if not (c["scope"].get("temporal") or {}).get("sameBuild")]
    if not x.ai_artifacts:
        next_artifact = (
            "1. **A same-scope golden pair** (spec v3 sections 78-79): one "
            "small but feature-complete system exported twice from the same "
            "build at the same time, once legacy and once AiExport, with a "
            "`pairs.json` naming the selection. The comparison pipeline in "
            "`tools/` is built and tested; it needs only the pair.\n"
            "2. **An `AiChangeBatch` document**, to settle whether the AI "
            "write path can consume an AiExport projection.\n"
            "3. **Decompiled `Barsa.Meta.DataExchange.dll`**, specifically "
            "`NewImportManager.Import`.")
    elif not_same_build:
        c = not_same_build[0]
        t = c["scope"].get("temporal") or {}
        next_artifact = (
            "A pair now exists and was compared: `%s` against `%s`, scope "
            "**Exact**. What it cannot settle is timing.\n\n"
            "1. **A same-build golden pair.** The current Exact pair was taken "
            "from different builds (legacy core %s on %s; AiExport producer "
            "%s), months apart. Every bug candidate it produces is therefore "
            "held as unconfirmed, because an object missing from the newer "
            "artifact may simply have been deleted in between. Re-exporting "
            "the same selection twice, back to back, on one build would "
            "convert those candidates into findings or clear them.\n"
            "2. **An `AiChangeBatch` document**, to settle whether the AI "
            "write path can consume an AiExport projection. This is now the "
            "largest open question about the AI side.\n"
            "3. **An AiExport containing a workflow and a business rule.** The "
            "profile has record types and serializers for both; no supplied "
            "artifact exercises them.\n"
            "4. **Decompiled `Barsa.Meta.DataExchange.dll`**, specifically "
            "`NewImportManager.Import`, which remains the biggest legacy-side "
            "Unknown and is obfuscated."
            % (c["pair"]["legacy"], c["pair"]["aiExport"],
               t.get("legacyCoreVersion"),
               (t.get("legacyExportTime") or "?")[:10],
               t.get("aiProducerVersion")))
    else:
        next_artifact = (
            "1. **An `AiChangeBatch` document**, to settle whether the AI "
            "write path can consume an AiExport projection.\n"
            "2. **An AiExport containing a workflow and a business rule.**\n"
            "3. **Decompiled `Barsa.Meta.DataExchange.dll`**.")
    sem_types = next((r["typesCount"] for r in x.assemblies.values()
                      if r["assemblyName"] == "Barsa.Meta.SemanticExchange"),
                     "?")
    _write(d, "REANALYSIS-REPORT.md", f"""# Reanalysis report

{BANNER}
Spec v3 sections 55-58 and 96. This run re-derived the data-exchange findings
from the binaries rather than patching the previous pack. The earlier
conclusions are treated as hypotheses to re-test, including the ones that were
right.

## Previously believed

1. Barsa has **one** export format: GZip + BinaryFormatter + DataSet.
2. `Barsa.Meta.DataExchange.dll` is the data-exchange subsystem, and it is
   obfuscated, so its internals are largely unknowable.
3. `BixHelper.ExportJson` exists but its output shape is **Unknown** for want of
   a JSON sample.
4. `met_Report.ReportData` and `MET_TYPEVIEWENTITY.TypeViewBlob` are opaque
   blobs with no identified deserializer.
5. Forms and workflows are **Unknown**: no supplied sample contains them.
6. Import atomicity, duplicate policy and version gating are **Unknown**.

## New evidence

1. **`Barsa.Meta.SemanticExchange.dll`** — {sem_types} types,
   **not obfuscated**. It declares its types in the `Barsa.Meta.DataExchange`
   namespace while being a separate assembly, and the dependency runs
   DataExchange -> SemanticExchange. A namespace-scoped search misses it
   entirely, which is how the first pass missed it.
2. **The embedded AI export profile.** Four manifest resources in that
   assembly, two of them full {live.raw_size if live else 0}-byte rule documents
   at profileVersion 14 and 15. The profile declares
   {len(live.record_types) if live else 0} record types,
   {len(live.serialized_types) if live else 0} serialized types,
   {len(live.enums) if live else 0} enums and
   {len(live.binary_decoders) if live else 0} binary decoders. This is the
   authoritative AiExport specification, and it is better evidence than a
   sample: a sample shows one system, the profile states the rules.
3. **`Barsa.Ai.Host.exe`** — an HTTP surface (`AiHttpServer`) over the semantic
   engine, with handlers for plan, apply, lint, snapshot-diff and knowledge
   read/write.
4. **Enum member lists**, read from the Field and Constant tables, which a
   method-level scan cannot see. These settle several questions outright.
5. **MemberRef evidence** for the cross-assembly hand-off, which survives the
   delegate indirection that hides it from the call graph.

## Changed conclusions

| Was | Now | Confidence |
|---|---|---|
| One export format | **Two families**: `Barsa.LegacyMetaExport` and `Barsa.AiExport`, plus a third document type, `AiChangeBatch`, on the write side | CrossVerified |
| DataExchange is the subsystem | DataExchange is the **legacy half and the facade**; SemanticExchange is the AiExport half | Verified |
| `ExportJson` output Unknown | Fully described from the writer plus the profile: root `tree` / `manifest` / `unmappedRecords`, per-node inline-or-file output, declared ZIP folder layout | Verified |
| `ReportData` / `TypeViewBlob` opaque | The profile **names decoders** for both (`SerializeReportData`, `SerializeTypeView`). Their output shape is still Unknown | Verified that decoders exist |
| Workflows Unknown | The profile has record types for `Barsa.Workflow.WorkflowDef`, `ActivityDef`, `ChoiceDef`, `WorkflowActorDef`, `WorkflowVariableDef`, and a `WorkflowDiagramSimple` decoder. The format **supports** workflows; the supplied samples merely do not contain any | Verified |
| Business rules Unknown | `Barsa.Meta.BRRule` is a serialized type with a `business-rule` serializer, and `AiBusinessRuleChangeProvider` exists | Verified |
| Atomicity Unknown | Unknown **for legacy**; for the AI write path, **not atomic** — `AiBatchStatus.PartiallySucceeded` and `AiBatchErrorPolicy.ContinueIndependent` | Verified (AI path) |
| Duplicate policy Unknown | Unknown **for legacy**; the AI path models it as `AiChangeOperation` = Create / Update / Delete with per-command `Conflict` status | Verified (AI path) |
| Version gating Unknown | Unknown **for legacy**; the AI path hard-gates on `profileVersion` 15 at six sites | Verified (AI path) |
| Diff states Unknown | `CompareChangeTypeEnum` = NoChange, Edited, New, Deleted | Verified |

## Still valid

Re-tested and unchanged:

- The legacy container is GZip + BinaryFormatter + `System.Data.DataSet`, with
  `SerializationHelper2` as writer and reader. **CrossVerified.**
- `BixHelper.Export` / `BixHelper.Import` are a symmetric legacy pair, and
  `BixHelper.Clone` chains them with `ImportOptions.IsClone`. **CrossVerified.**
- `$IdEmbeddingFields` carries per-column remap instructions consumed by
  `FixIdForImport`. **CrossVerified.** The profile corroborates it from the
  other side: `JsonExportDocumentBuilder` reads the same control tables.
- `NewImportManager.GetImportData` returns the export tree's own
  `IActiveDataSource`, which `ImportTreeForm` renders against the live database.
  **Verified**, and now with the state enum named.
- The legacy stage order inside `NewImportManager.Import`. **Observed.**

## Invalidated

- **"All exports in `source/` are legacy."** Still true of the two artifacts
  actually present, but it was stated as a property of Barsa. It is not.
- **"`Barsa.Meta.DataExchange` is the data-exchange subsystem."** Incomplete.
- **"`System.Export` / `System.Import` capabilities."** Replaced with
  format-aware ids (`DataExchange.Legacy.Export`,
  `DataExchange.AiExport.Export`, `DataExchange.AiExport.ApplyChangeBatch`),
  because a generic `System.Export` cannot say which of two formats it means.
- **"Forms and workflows are Unknown."** Mis-scoped. Not observed in the
  supplied samples is not the same as not supported — the exact error spec v3
  section 91 warns about.

## Unknown

Carried forward, with what would settle each:

{_table(["Question", "What would settle it"], [
 ["Legacy import atomicity and rollback", "decompiled `NewImportManager.Import`, or SQL capture against a scratch database"],
 ["Legacy duplicate policy", "import the same package twice and diff"],
 ["Legacy `Core Version` enforcement", "import a package whose core version differs"],
 ["The output shape of each named binary decoder", "run a decoder, or decompile `JsonExportBinarySerializerRegistry`"],
 ["Whether an AiExport projection can be fed to `ApplyPlan` unchanged", "an AiChangeBatch sample, or the `AiChangePlanner.Build` input contract"],
 ["Which option produced each AiExport variant in the wild", "an AiExport artifact in `source/`, with the call that made it"],
 ["Semantic selector uniqueness scope", "decompiled `SemanticSelectorCodec.Parse`, or artifacts to compare selectors across"],
 ["How `profileVersion` is expected to evolve", "a v16 profile, or the team's own answer"],
])}

## Recommended next artifact

{next_artifact}

Note on what is **not** needed: more DLLs. The current set was sufficient to
derive the entire AiExport specification, because Barsa ships it inside the
binary.

## Method note

The previous pack is not patched; it is superseded. The delta above is against
the committed v2 output, so `git log -- dist/` is the audit trail. Assembly
inventory was re-read rather than reused, since this run also needed resources
and enum constants the earlier pass did not extract.
""")


# --- indexes and scenarios -------------------------------------------------

def _v3_indexes(x, d):
    _write(d, "index/export-formats.json", _j({
        "schemaVersion": "3.0",
        "families": [
            {
                "logicalFormat": LEGACY_LABEL,
                "physicalFormats": ["GZip"],
                "variants": ["Legacy.DataSet.BinaryFormatter"],
                "serializer": "System.Runtime.Serialization BinaryFormatter",
                "payloadType": "System.Data.DataSet",
                "producer": "Barsa.Meta.DataExchange",
                "writer": "SerializationHelper2.BinarySerializeToFile",
                "reader": "SerializationHelper2.DeserializeDataSetFromFile",
                "confidence": "CrossVerified",
            },
            {
                "logicalFormat": AI_LABEL,
                "physicalFormats": ["PlainJson", "ZIP"],
                "variants": ["AiExport.SingleJson", "AiExport.ZipJsonPackage",
                             "AiExport.MultiProjectionPackage"],
                "serializer": "Newtonsoft.Json",
                "payloadType": "tree + manifest",
                "producer": "Barsa.Meta.SemanticExchange",
                "writer": "BixJsonExportManager.SaveSelectedJson",
                "reader": None,
                "profileVersion": 15,
                "confidence": "Verified",
            },
            {
                "logicalFormat": "Barsa.AiChangeBatch",
                "physicalFormats": ["PlainJson"],
                "variants": ["AiChangeBatch"],
                "serializer": ("Newtonsoft.Json with "
                               "CamelCasePropertyNamesContractResolver and a "
                               "camelCase StringEnumConverter"),
                "payloadType": "AiChangeBatch",
                "producer": "external (an agent or tool)",
                "writer": None,
                "reader": "BixWriteHelper.ParseBatch",
                "profileVersion": 15,
                "objectTypes": list(__import__(
                    "barsa_extractor.change_batch",
                    fromlist=["change_batch"]).OBJECT_TYPES),
                "operations": list(__import__(
                    "barsa_extractor.change_batch",
                    fromlist=["change_batch"]).OPERATIONS),
                "forbiddenRuntimeKeys": list(__import__(
                    "barsa_extractor.change_batch",
                    fromlist=["change_batch"]).FORBIDDEN_RUNTIME_KEYS),
                "schema": "models/ai-change-batch.schema.json",
                "linter": "tools/lint_change_batch.py",
                "confidence": "Verified",
            },
        ],
        "apiFormatMap": x.api_formats,
        "variantSwitch": x.variant_switch,
        "profileVersion": x.profile_version,
        "aiImportVerdict": x.ai_import,
        "diffStates": x.diff_states,
        "atomicity": x.atomicity,
        "systemCodeRoute": getattr(x, "system_code", None),
        "detected": [
            {k: v for k, v in r.items() if k not in ("entries",)}
            for r in x.formats
        ],
    }))

    tables = []
    for p in x.packages:
        for t, info in sorted(p.tables.items()):
            tables.append({
                "artifact": p.path.split("/")[-1],
                "table": t,
                "isControlTable": info["isControl"],
                "columns": info["columns"],
                "rows": p.row_counts.get(t, 0),
            })
    _write(d, "index/legacy-dataset-tables.json", _jl(tables))

    live = x.live_profile
    _write(d, "index/ai-export-properties.json", _j({
        "schemaVersion": "3.0",
        "source": ("embedded resource in Barsa.Meta.SemanticExchange, read "
                   "without executing Barsa code"),
        "profileVersion": live.profile_version if live else None,
        "engine": live.engine if live else None,
        "packaging": live.packaging_rules() if live else None,
        "recordTypes": live.record_type_rows() if live else [],
        "legacyTableMap": live.legacy_table_map() if live else {},
        "binaryDecoders": live.binary_decoders if live else {},
        "decoderTargets": live.decoder_targets() if live else [],
        "serializedTypes": (sorted(live.serialized_types) if live else []),
        "enums": live.enums if live else {},
        "answerEnums": x.answer_enums,
        "observedInArtifacts": [a.summary() for a in x.ai_artifacts],
    }))

    _write(d, "index/normalized-model.json", _j({
        "schemaVersion": "3.0",
        "collections": x.normalized,
        "reconstructionOrder": x.reconstruction_order,
        "legacyNormalized": [
            {"source": e["_source"], "availability": e["_availability"],
             "counts": {k: (len(v) if isinstance(v, list) else None)
                        for k, v in e.items() if not k.startswith("_")
                        and k != "schemaVersion" and k != "extensions"}}
            for e in x.normalized_legacy],
        "aiNormalized": [
            {"source": e["_source"], "availability": e["_availability"],
             "counts": {k: (len(v) if isinstance(v, list) else None)
                        for k, v in e.items() if not k.startswith("_")
                        and k != "schemaVersion" and k != "extensions"}}
            for e in x.normalized_ai],
    }))

    os.makedirs(os.path.join(d, "models", "normalized-samples"), exist_ok=True)
    for env in x.normalized_legacy:
        name = env["_source"]["file"].replace(".metaexport", "")
        _write(d, "models/normalized-samples/legacy-%s.json" % name,
               _j(_trim_env(env)))
    for env in x.normalized_ai:
        name = os.path.splitext(env["_source"]["file"])[0]
        _write(d, "models/normalized-samples/ai-%s.json" % name,
               _j(_trim_env(env)))

    # Samples above remain short for review. The canonical index below is
    # generated from the full in-memory envelopes, before sample trimming.
    systems = system_index.build(x.normalized_legacy, x.normalized_ai)
    _write(d, "index/systems/manifest.json", _j({
        "schemaVersion": "1.0", "systemIds": sorted(systems),
        "indexPath": "index/systems/<system-id>/semantic.json",
    }))
    for sid, index in sorted(systems.items()):
        _write(d, "index/systems/%s/semantic.json" % sid, _j(index))


def _trim_env(env, per_collection=25):
    """Keep sample documents reviewable: a slice per collection, counts kept."""
    out = {}
    for k, v in env.items():
        if isinstance(v, list) and len(v) > per_collection:
            out[k] = v[:per_collection]
            out["_truncated_" + k] = {"shown": per_collection,
                                      "total": len(v)}
        else:
            out[k] = v
    return out


def _v3_scenarios(x, d):
    ds = x.diff_states
    _write(d, "scenarios/preview-import-diff.md", f"""# Scenario: preview an import as a diff

{BANNER}
Spec v3 section 22.

## Why this matters

A legacy package can be inspected and compared against the live system before
anything is written. The mechanism is neat: the importer hands back the **same
interface the export tree consumes**.

## Flow

```mermaid
sequenceDiagram
  participant UI as ApplicationImportForm
  participant BH as BixHelper
  participant IM as NewImportManager
  participant DB as DbDataSource
  participant TF as ImportTreeForm

  UI->>BH: ExtractData(ImportOptions)
  BH->>IM: GetImportData(options)
  IM-->>BH: IActiveDataSource over the package
  UI->>DB: GetCurrentDb()
  UI->>TF: new ImportTreeForm(packageSource, currentDb)
  TF->>TF: ImportTreeControl.RefreshContent(...)
  TF->>TF: GetChangeIcon(CompareChangeTypeEnum) per node
```

`btnImportTest_Click` is the entry point; `btnImport_Click` is the one that
commits.

## States shown

{_table(["State", "Value"],
        [[f"`{m['name']}`", m["value"]] for m in (ds["members"] or [])])
 if ds["members"] else "_Enum unavailable._"}

Rendered by `{ds["renderedBy"]}`.

**Confidence: {ds["confidence"]}** — read from the Field and Constant metadata
tables.

{ds["note"]}

## Filtering

`ImportTreeControl.JustShowChanges` and `SomeNodeHasChange(TreeNodesCollection)`
let the operator collapse the tree to only what differs.

## What this does not establish

Whether the operator can **deselect** nodes in the preview and import a subset.
The control exposes no such API in its metadata, so **Unknown**.
""")

    ai = x.ai_import
    _write(d, "scenarios/export-system-ai-json.md", f"""# Scenario: export a system as AiExport JSON

{BANNER}
## Preconditions

- A logged-in session with a live database connection.
- An `ObjectReferenceSelection` from the export tree — the same selection object
  the legacy export uses.
- The embedded profile at `profileVersion` 15.

## Input

```
BixHelper.ExportJson(ObjectReferenceSelection, string path,
                     BixJsonExportSelection, bool, bool) : bool
BixHelper.ExportJson(ObjectReferenceSelection, string path,
                     BixJsonExportMode, bool, bool) : bool
BixHelper.ExportInitialJson(ObjectReferenceSelection, string, bool, bool) : bool
```

## Flow

```mermaid
sequenceDiagram
  participant UI as ApplicationExportForm
  participant BH as BixHelper
  participant NEM as NewExportManager
  participant CTX as SemanticExportContext
  participant MGR as BixJsonExportManager
  participant DOC as JsonExportDocumentBuilder
  participant PW as JsonExportPackageWriter

  UI->>BH: ExportJson(selection, path, selectionFlags, ...)
  BH->>NEM: Export(progress, selection, callback)
  NEM-->>BH: ExportSaveContext{{DataSet, ExportFilePath}}
  BH->>CTX: new SemanticExportContext{{DataSet, ExportFilePath}}
  BH->>MGR: SaveSelectedJson(context, bool, bool)
  MGR->>DOC: BuildInitialDocument()
  DOC->>DOC: apply profile rules per record type and field
  MGR->>PW: Save(document, path, options)
  PW->>PW: WriteManifest / WriteTree / ExternalizeLargeCodeValues
  PW->>PW: CreatePortableZipFromDirectory, when the path is a .zip
```

The UI entry point is `ApplicationExportForm.btnExport_Click`, which calls
`BixHelper.ExportJson` when the JSON checkbox is set and `BixHelper.Export`
otherwise — and rejects an empty type selection with
`'حداقل یک نوع خروجی JSON باید انتخاب شود.'` ("at least one JSON output type
must be selected"), which is the `BixJsonExportSelection` flags enum surfacing in
the UI.

## Side effects

Writes a JSON document, or a directory that is then zipped. No database write.

## Failure modes

- `'Export dataset is empty.'` and `'Export file path is empty.'`
- `'Semantic runtime export accepts only profileVersion=15.'`
- `'No JSON export files were created.'`
- A binary column with no decoder is dropped; a decode failure becomes an
  error marker in the output rather than failing the export
  (`engine.binary.onDecodeError = error-marker`).

## Confidence

**Verified** for the API surface, the pipeline and the profile rules.

{"**Unknown** for the resulting bytes: no AiExport artifact was supplied." if not x.ai_artifacts else "**Verified** for the resulting bytes as well: " + str(len(x.ai_artifacts)) + " artifact(s) were parsed, and the root shape, manifest keys, bracketed folder layout and per-node inline-or-file split all match what the writer and the profile predict."}
""")

    _write(d, "scenarios/import-system-ai-json.md", f"""# Scenario: write changes back through the AI path

{BANNER}
> This is deliberately **not** called "import a system as AiExport JSON". The AI
> side has a write path, but it is not the inverse of the export.

## The verdict

{ai["answer"]}

## What exists

```
BixWriteHelper.ValidateBatch(string)                    // structural lint
BixWriteHelper.ParseBatch(string)      : AiChangeBatch
BixWriteHelper.BuildPlan(AiChangeBatch): AiChangePlan
BixWriteHelper.ApplyPlan(AiChangePlan) : AiApplyResult
BixWriteHelper.SerializePlan(AiChangePlan)   : string
BixWriteHelper.SerializeResult(AiApplyResult): string
```

Exposed over HTTP by `Barsa.Ai.Host.AiHttpServer`: `HandleLint`, `HandlePlan`,
`HandleApply`.

## Flow

```mermaid
sequenceDiagram
  participant C as Caller (agent or tool)
  participant WH as BixWriteHelper
  participant PL as AiChangePlanner
  participant EX as AiBatchExecutor
  participant PR as Ai*ChangeProvider
  participant VF as AiRuntimeVerifier

  C->>WH: ValidateBatch(json)
  C->>WH: ParseBatch(json) -> AiChangeBatch
  C->>WH: BuildPlan(batch)
  WH->>PL: Build(batch)
  PL-->>WH: AiChangePlan + AiPlanDiagnostic[]
  C->>WH: ApplyPlan(plan)
  WH->>EX: Apply(plan)
  EX->>PR: per-object Create / Update / Delete
  EX->>VF: FinalReadBackAndVerify(plan)
  EX-->>C: AiApplyResult + AiBatchStatus
```

## Change providers

{len(ai["whatExists"]["providers"])} providers, one per concept:

{chr(10).join("- `%s`" % p for p in ai["whatExists"]["providers"])}

That list is itself a coverage statement: it names what the AI write path can
actually create, update and delete.

## Operations and outcomes

{_table(["Enum", "Members"], [
 ["`AiChangeOperation`", ", ".join("`%s`" % m["name"] for m in x.answer_enums.get("Barsa.Meta.DataExchange.AiChangeOperation", {}).get("members", []))],
 ["`AiBatchStatus`", ", ".join("`%s`" % m["name"] for m in x.answer_enums.get("Barsa.Meta.DataExchange.AiBatchStatus", {}).get("members", []))],
 ["`AiBatchErrorPolicy`", ", ".join("`%s`" % m["name"] for m in x.answer_enums.get("Barsa.Meta.DataExchange.AiBatchErrorPolicy", {}).get("members", []))],
 ["`AiCommandStatus`", ", ".join("`%s`" % m["name"] for m in x.answer_enums.get("Barsa.Meta.DataExchange.AiCommandStatus", {}).get("members", []))],
 ["`AiSemanticReferenceLifecycle`", ", ".join("`%s`" % m["name"] for m in x.answer_enums.get("Barsa.Meta.DataExchange.AiSemanticReferenceLifecycle", {}).get("members", []))],
])}

## Not atomic

`AiBatchStatus` includes `PartiallySucceeded` and `AiBatchErrorPolicy` offers
`ContinueIndependent` alongside `StopBatch`. A batch is therefore **explicitly
permitted to half apply**, and the caller chooses which behaviour it wants.
**Confidence: Verified** — this is an enum member list, not an inference.

Contrast the legacy path, where atomicity remains Unknown.

## Reference resolution

References are resolved against the target at apply time rather than remapped
afterwards: `AiSemanticReferenceResolver`, `AiSemanticReferenceContract`,
`AiPlanReferenceBinding`, and `AiDeferredBindingEntry` for references that
cannot resolve yet. `AiSemanticReferenceLifecycle` orders the work into
`StructuralRequired`, `PostCreateConfig` and `FinalWiring` — which is the AI
path's answer to the problem `$IdEmbeddingFields` solves on the legacy side.

## What is not established

{chr(10).join("- " + n for n in ai["whatIsNotEstablished"])}

{ai["notUnsupported"]}
""")

    _write(d, "scenarios/compare-legacy-ai-export.md", f"""# Scenario: compare a legacy export with an AiExport

{BANNER}
Spec v3 sections 39-54. This scenario is **implemented and tested but not
exercised**, because `source/` holds no AiExport artifact.

## The rule that governs it

Two exports are compared in full only when their selection scope is equivalent.
Equal filenames prove nothing — the specification's own example is that
"Push Notification" and "Push Notification + الگو + پورتال" may not share a
scope.

## Pipeline

```
extract selection roots      legacy: $RootSelection
                             AiExport: top-level tree nodes
            |
            v
normalize semantic identity  selector > id > dbName > name > caption
            |
            v
compare selected object sets
            |
            v
scope-equivalence level      Exact | Partial | Candidate | Different | Unknown
            |
            v
only then compare content    Exact -> full; Partial -> intersection only;
                             Candidate or Unknown -> no percentage at all
```

## Identity strength

{_table(["Key", "Match strength", "Why"], [
 ["`selector`", "ExactIdentity", "the AiExport semantic identity, produced by SemanticSelectorCodec"],
 ["`id`", "ExactIdentity", "the database id, carried by both formats"],
 ["`dbName`", "StrongMatch", "the physical table or column name"],
 ["`name`", "StrongMatch", "the record name"],
 ["`caption`", "WeakMatch", "display text; spec section 48 calls this a weak key on its own"],
])}

A `WeakMatch` never drives a bug assertion.

## Bug candidate conditions

All five must hold, per spec section 52:

1. scope is equivalent;
2. the semantic match is strong;
3. the legacy representation is valid;
4. the importer shows the concept actually matters;
5. the difference is not merely representational.

Otherwise the finding is a `Difference`, not a bug.

## The trap this pipeline avoids

The profile sets `omitNull` and `omitDefault` to true. A property absent from
AiExport may therefore be null, or equal to its default, or genuinely not
projected. A naive diff would report thousands of false `MissingInAiExport`
findings. The comparison treats absence as ambiguous and records why, rather
than counting it as loss.

## Current state

{"No pair exists. `comparison/scope-equivalence.json` records that, and no compatibility percentage is produced." if not x.comparisons else "%d pair(s) assessed; see `comparison/`." % len(x.comparisons)}

To exercise it, supply a golden pair as described in `MISSING-INPUTS.md`.
""")


def _match_report(x, d):
    """Spec v3 sections 48-52: per-collection matching and bug classification."""
    sc = getattr(x, "system_code", None)

    bug_rows = []
    for c in x.comparisons:
        for dd in c["differences"]:
            if dd["verdict"].startswith("BugCandidate"):
                bug_rows.append([
                    c["pair"]["legacy"][:28], dd["concept"],
                    json.dumps(dd["legacy"] or dd["aiExport"],
                               ensure_ascii=False),
                    dd["verdict"]])

    match_rows = []
    for c in x.comparisons:
        for label, info in sorted((c.get("comparedConcepts") or {}).items()):
            if not isinstance(info, dict):
                continue
            match_rows.append([
                c["pair"]["legacy"][:24], c["scope"]["level"], label,
                info["legacyCount"], info["aiCount"], info["matched"],
                ", ".join("%s=%d" % (k, v)
                          for k, v in sorted(info["byKey"].items()))])

    bug_note = ""
    if bug_rows:
        bug_note = (
            "### Reading these\n\n"
            "Every candidate above is marked unconfirmed because the paired "
            "artifacts are not from one build. Scope equivalence proves the "
            "same objects were *selected*; it says nothing about the system "
            "being unchanged between two exports taken months apart. A "
            "same-build golden pair would settle each one.\n")

    if sc and sc.get("systemLevelObservations"):
        obs_table = _table(
            ["Artifact", "Variant", "Caption", "CodeLayer", "Target is the system"],
            [[o["artifact"][:26], o["variant"].replace("AiExport.", ""),
              (o["caption"] or "")[:24], o["codeLayer"], _yn(o["targetIsSystem"])]
             for o in sc["systemLevelObservations"]])
        per_sys = _table(
            ["System id", "In AiExport scope", "Legacy code rows",
             "AiExport code rows", "Agrees"],
            [[p["systemId"], _yn(p["systemInAiScope"]), p["legacyCodeRows"],
              p["aiCodeRows"],
              "-" if p["agrees"] is None else _yn(p["agrees"])]
             for p in sc.get("perSystem", [])])
        # Two variables separate the agreeing pair from the disagreeing one,
        # and the supplied artifacts vary both at once.
        rows = []
        for c in x.comparisons:
            t = c["scope"].get("temporal") or {}
            art = next((a for a in x.ai_artifacts
                        if a.path.endswith(c["pair"]["aiExport"])), None)
            rows.append([
                c["pair"]["legacy"][:24],
                (art.variant.replace("AiExport.", "") if art else "?"),
                "%s" % t.get("approxMonthsApart"),
                c["scope"]["level"],
            ])
        confound = "\n".join([
            "#### Why the supplied pair cannot settle it", "",
            _table(["Pair (legacy)", "AiExport variant",
                    "Months apart", "Scope"], rows), "",
            "The pair that **agrees** is the single-document one, taken three "
            "days apart. The pair that **disagrees** is the ZIP one, taken "
            "five months apart. So variant and elapsed time differ together, "
            "and nothing in these artifacts separates them.",
            "",
            "Stated plainly: this is weaker evidence for a ZIP-variant defect "
            "than it first looks. The simpler reading is that the two code "
            "records were deleted during those five months. Both readings "
            "remain open, and a same-build pair of **both variants** from one "
            "selection decides between them in one step.",
        ])
        agree = sc.get("inScopeAgreements") or []
        disagree = sc.get("inScopeDisagreements") or []
        verdict_lines = []
        for p in agree:
            verdict_lines.append(
                "- System `%s`: %d legacy row(s), %d in the AiExport. "
                "**Agrees.** Its system-level code was projected in full."
                % (p["systemId"], p["legacyCodeRows"], p["aiCodeRows"]))
        for p in disagree:
            verdict_lines.append(
                "- System `%s`: %d legacy row(s), %d in the AiExport. "
                "**Disagrees** -- ids %s are unaccounted for."
                % (p["systemId"], p["legacyCodeRows"], p["aiCodeRows"],
                   ", ".join("`%s`" % i for i in p["legacyCodeIds"])))
        miss_table = "\n".join([
            "Only systems present on both sides are evidence: a system outside "
            "the AiExport's selection is expected to contribute nothing.", "",
            per_sys, "",
            "\n".join(verdict_lines) if verdict_lines
            else "_No system was in scope on both sides._",
        ])
        gap_section = "\n".join([
            "**" + sc["answer"] + "**", "",
            "### Observed in an artifact", "", obs_table, "",
            "### Per-system accounting", "", miss_table, "",
            "### Correction", "",
            sc["correctsEarlierReading"], "",
            "### What follows", "",
            "The two barcode rows carry `CodeLayer` 2 and 11, which the "
            "profile's own enum names `Bl` and `Web2Ui` -- the same two layers "
            "as the system-level codes that *are* present in the Push "
            "Notification projection. They were exportable in principle.",
            "", confound, "",
        ])
    else:
        gap_section = ("_No system-level code was observed in any supplied "
                       "artifact, so this question is Unknown._")

    repr_table = _table(
        ["Concept", "Legacy form", "AiExport form", "Verdict"], [
            ["Navigation", "`MET_FOLDER` rows with a `Path` column",
             ("directory structure: a folder is a directory, a report "
              "placement is a JSON file inside it"),
             "RepresentationDifference"],
            ["Field-level code",
             "`MET_METACODE` rows keyed by `TargetObjectId`",
             ("inline `formula.code` on the owning field, per the profile's "
              "`code-file-if-large` transform"),
             "RepresentationDifference"],
            ["Relation fields",
             "`MET_FIELDDEF` rows with `relationType` set",
             "`relation` records nested inside the entity",
             "RepresentationDifference"],
        ])

    _write(d, "comparison/match-report.md", f"""# Match report

{BANNER}
Spec v3 sections 48-52. Per-collection matching for every assessed pair, with
the key each match was made on.

Matching runs in passes, strongest key first, and the passes are global: every
pair agreeing on `selector` or `id` is matched before a weaker key is
consulted. A single-pass loop lets a weak key consume a node that had an exact
identity match with a different node, which silently reports a present object
as missing.

`dbName` is never a bare key. A field's dbName is `F1`, `F2`, `F3` within its
own entity and repeats across every other entity, so it is only used scoped to
the owning record.

{_table(["Pair (legacy)", "Scope", "Collection", "Legacy", "AiExport",
         "Matched", "By key"], match_rows)
 if match_rows else "_No pair assessed._"}

## Collections compared as a union

Legacy `MET_FIELDDEF` holds plain fields **and** relation fields in one table,
while AiExport splits them into `field` and `relation` record types. Compared
separately, every relation field reads as missing on one side and extra on the
other. They are therefore compared as a union, which is why the row above is
labelled "fields (incl. relation fields)".

## Bug candidates

A difference is promoted per spec v3 section 52 only when scope is Exact, the
object was looked for by a decisive key the other side also carries, and the
concept matters. An absent object has no match strength of its own, so what
gets checked is whether it was searchable at all.

{_table(["Pair", "Concept", "Object", "Verdict"], bug_rows)
 if bug_rows else "_None._"}

{bug_note}
## System-level code: the one real candidate

{gap_section}

## Representation differences that are not losses

Two collections look absent on the AiExport side until the package layout is
read properly, and this extractor now reads both.

{repr_table}

Matching navigation needs one more thing: Arabic and Persian letter forms are
used interchangeably in this data. The profile itself maps both `فرآيند` and
`فرآیند` to one folder. Names are folded before comparison, or the same folder
reads as two objects.

## Variant consistency

Spec v3 section 86 asks whether both AiExport variants normalize identically.
**They do not, for navigation.** The single-document variant emits
`navigationGroup`, `navigationPage` and `navigationReport` records; the ZIP
variant encodes the same information as directory structure and emits no
navigation records at all. A consumer of AiExport has to handle both.

## Manifest consistency

The two variants also differ in their manifest. The ZIP package's
`manifest.json` carries `producer`, `producerVersion` and `buildId`; the single
document's `$.manifest` carries only `format` and `profileVersion`. So
`JsonExportPackageWriter.AddProducerIdentity` is reached on one path and not the
other. Spec v3 section 85 would class this as a `PackageManifestMismatch`
candidate.
""")


def _change_batch(x, d):
    """Spec v3 section 14: the AiExport write path's input contract."""
    from . import change_batch as cb

    contract = getattr(x, "semantic_contract", None)
    if contract:
        _write(d, "index/semantic-contract.json", _j(contract))
    _write(d, "models/ai-change-batch.schema.json", _j(cb.json_schema()))
    _write(d, "models/sample-ai-change-batch.json", _j(cb.example()))

    contract = _table(
        ["CLR type", "Role", "Properties (camelCase in JSON)"],
        [[f"`{r['type']}`", r["role"],
          ", ".join("`%s`" % p for p in r["properties"])]
         for r in cb.contract_rows()])

    rules = _table(["Rule", "What the binary says"], [
        ["`profileVersion` must be 15",
         "Runtime accepts only explicit profileVersion=15 input."],
        ["no `externalDataMappings` at the root",
         "Semantic v15 authored package root must not contain legacy "
         "externalDataMappings."],
        ["`policy.errorPolicy` may only be `continueIndependent`",
         "Semantic v15 supports only ContinueIndependent; StopBatch is not an "
         "executable authored policy."],
        ["`changes[]` required and non-empty",
         "AiChangeBatch must contain changes[]."],
        ["no null or non-object entries in `changes[]`",
         "changes[] cannot contain null/non-object values at index N."],
        ["`commandId` unique", "Duplicate commandId: X"],
        ["`tempId` only on a `create`",
         "Semantic v15 tempId can only be declared by create commands: X"],
        ["`tempId` declared at most once",
         "Duplicate Semantic v15 tempId declaration: X"],
        ["a `tempId` reference must resolve in the same batch",
         "Semantic v15 tempId reference is not declared in this logical batch "
         "at PATH: X."],
        ["no runtime identity anywhere",
         "Semantic v15 forbids Runtime authority 'KEY' at PATH."],
        ["`selector` must be a string",
         "Semantic selector property must be a string at PATH."],
        ["`selector` must parse",
         "Semantic selector property is not valid selector syntax at PATH."],
    ])

    _write(d, "formats/ai-change-batch.md", f"""# AiChangeBatch

{BANNER}
**Logical format:** `Barsa.AiChangeBatch` · **profileVersion:** 15 ·
**Confidence: Verified** for shape and rules

This is the document the AI write path consumes. It is **not** an AiExport
projection: `BixWriteHelper.ParseBatch` takes a list of create / update /
delete commands, not a tree of records. That asymmetry is the main thing to
understand about writing to Barsa through this path.

No `AiChangeBatch` artifact was supplied, so everything below is read from
`Barsa.Meta.SemanticExchange` — which is **not obfuscated**, so the property
names, enum members and validation messages are the real ones rather than
reconstructions.

## Entry points

```
BixWriteHelper.ValidateBatch(string)                     // structural lint
BixWriteHelper.ParseBatch(string)       : AiChangeBatch
BixWriteHelper.BuildPlan(AiChangeBatch) : AiChangePlan
BixWriteHelper.ApplyPlan(AiChangePlan)  : AiApplyResult
```

Over HTTP, via `Barsa.Ai.Host.AiHttpServer`: `HandleLint`, `HandlePlan`,
`HandleApply`.

## JSON conventions

`BixWriteHelper.CreateJsonSettings` installs a
`CamelCasePropertyNamesContractResolver` and a `StringEnumConverter` with
`CamelCaseText` set. So every property is camelCase and every enum value is a
camelCase **string**, not a number: `"create"`, not `0`.

## Shape

{contract}

## Document

```json
{{
  "profileVersion": 15,
  "policy": {{ "errorPolicy": "continueIndependent", "ignoreUnsupported": false }},
  "assetRoot": null,
  "changes": [
    {{
      "commandId": "c1-create-entity",
      "operation": "create",
      "objectType": "entity",
      "tempId": "tmpGate",
      "parent": {{ "objectType": "system", "selector": "#بارکد" }},
      "properties": {{ "caption": "گیت" }}
    }}
  ]
}}
```

A complete, rule-clean example is in `models/sample-ai-change-batch.json`, and
the schema in `models/ai-change-batch.schema.json`.

## objectType

One value per registered provider, taken from each `Ai*ChangeProvider`'s
`CanHandle`:

{", ".join("`%s`" % t for t in cb.OBJECT_TYPES)}

Plus `AiGenericChangeProvider`, which matches no literal and acts as the
fallback. The planner also matches some of these case-insensitively.

**These are the same names AiExport uses for `$type`.** The export projection
and the write path share one object vocabulary, even though their document
shapes differ. That is the strongest available signal that the two are meant to
work together, and it is a fact about the vocabulary, not a demonstrated
round-trip.

## Identity: three ways, one forbidden

{_table(["Mechanism", "Use", "Status"], [
 ["`selector`", "point at something that already exists, by semantic name",
  "Required form for existing objects"],
 ["`tempId`", "point at something created earlier in the same batch",
  "Declared on a create, referenced anywhere"],
 ["`name` / `caption`", "present on AiObjectReference",
  "Weak; the planner's own diagnostics treat selectors as the authority"],
 ["`id`, `rowId`, `sourceId`, `runtimeId`, `dependencyKey`",
  "raw runtime identity", "**Forbidden in an authored batch**"],
])}

The forbidden set is the linter's own static list. The error code is
`runtimeAuthorityForbiddenV15`, with a sibling `dependencyKeyForbiddenV15` and
`legacyReferenceAuthorityForbiddenV15`.

This is the sharpest contrast with the legacy path. Legacy carries raw numeric
ids and remaps them after the fact, driven by `$IdEmbeddingFields`. An authored
change batch is **forbidden** from carrying them, and resolves selectors against
the target at apply time instead.

## Validation rules

Every rule below is a literal in `SemanticV15Linter`:

{rules}

`tools/lint_change_batch.py` implements all of them, so a batch can be checked
before it is sent:

```bash
python3 tools/lint_change_batch.py batch.json
python3 tools/lint_change_batch.py --example > batch.json
python3 tools/lint_change_batch.py --schema
```

It is a convenience, not a substitute. Selector resolution and target
inspection need a live system.

## Error codes

From `AiChangePlanner`, `AiPatchHelper` and `AiProviderValidation`:

{", ".join("`%s`" % c for c in cb.ERROR_CODES)}

`AiPlanDiagnostic` carries one of these in `errorCode`, alongside `commandId`,
`objectType`, `operation`, `path` and `message`.

## What a plan tells you before you apply

`BuildPlan` returns an `AiChangePlan` whose `summary` is an `AiPlanSummary`
with, among others: `canApplyAny`, `canApplyAll`, `canApplyCleanly`,
`hasUnsupported`, `hasBatchFatalError`, `hasCommandLocalErrors`, and per-concept
counts (`entityCount`, `fieldCount`, `relationCount`, `viewCount`,
`reportCount`, `folderCount`, `workflowCount`).

So the write path is a **plan-then-apply** design: a caller can see exactly what
would happen, and whether it would happen cleanly, before committing.

## Not atomic, by design

`AiBatchStatus` includes `PartiallySucceeded`, and the authored policy is forced
to `ContinueIndependent` — `StopBatch` exists in the enum but the linter refuses
it. A batch is therefore **expected** to half-apply when a command fails.

`AiApplyResult` is built for that: `mutationApplied`, `partialMutation`,
`needsReconcile`, `verificationSucceeded`, plus `succeededCount`,
`failedCount`, `skippedCount`, `applyFailedCount`,
`verificationFailedCount` and `skippedDependencyCount`. `AiCommandResult` adds
`phase`, `failureClass`, `mutationStage`, `reconcileSucceeded` and
`reconcileMessage` per command.

`temporaryIds` on the result maps each `tempId` to the real id it became, which
is how a caller learns what it created.

## Still unknown

{_table(["Question", "What would settle it"], [
 ["Can an AiExport projection be converted into a batch?",
  "No code path was found doing it. A real AiChangeBatch artifact, or the "
  "tool that authors them, would settle whether this is intended."],
 ["What `properties` are valid per objectType?",
  "The planner raises `unsupportedProperty` for unknown ones, so the set is "
  "enforced somewhere. The embedded export profile's record-type field lists "
  "are the best available approximation, and are not proven to be the same set."],
 ["What `assetRoot` expects on disk",
  "Error codes name `assets/`, `sha256` and `mediaType`, so assets are "
  "content-addressed. The layout was not established."],
 ["Whether `ignoreUnsupported` changes the outcome or only the reporting",
  "Runtime observation, or decompiled AiBatchExecutor."],
])}
""")


def _golden_pair(x, d):
    """Spec v3 sections 78-79: how to produce a pair that settles things."""
    pairs = []
    for c in x.comparisons:
        t = c["scope"].get("temporal") or {}
        pairs.append([
            c["pair"]["legacy"][:30], c["pair"]["aiExport"][:28],
            c["scope"]["level"], _yn(t.get("sameBuild")),
            t.get("legacyCoreVersion") or "?",
            t.get("aiProducerVersion") or "absent"])

    held = []
    for c in x.comparisons:
        for dd in c["differences"]:
            if dd["verdict"].startswith("BugCandidate"):
                held.append([c["pair"]["legacy"][:24], dd["concept"],
                             json.dumps(dd["legacy"] or dd["aiExport"],
                                        ensure_ascii=False)[:60]])

    template = _j([{
        "pairId": "golden-001",
        "barsaVersion": "4.1.203.0",
        "selection": ["<the object titles ticked in the export tree>"],
        "legacy": "exports/<name>.metaexport",
        "aiExport": "exports/<name>.zip",
        "scope": "exact",
        "note": ("Both exports taken from one build, back to back, with the "
                 "same tree selection and no edits in between."),
    }])
    _write(d, "comparison/pairs.template.json", template)

    _write(d, "comparison/golden-pair-protocol.md", f"""# Golden pair protocol

{BANNER}
Spec v3 sections 78-79. A golden pair is two exports of **one selection**, from
**one build**, taken **back to back**. It is the artifact that converts held bug
candidates into findings or clears them.

## Why the current pair is not enough

{_table(["Legacy", "AiExport", "Scope", "Same build", "Legacy core", "AiExport producer"], pairs)
 if pairs else "_No pair supplied._"}

Scope equivalence proves the same objects were **selected**. It says nothing
about the system being unchanged between the two exports. The barcode pair is
scope-Exact and still cannot settle a difference, because the two artifacts are
from different builds months apart: anything missing from the newer one may have
been deleted in between rather than dropped by the exporter.

## Findings currently held for exactly this reason

{_table(["Pair", "Concept", "Object"], held) if held else "_None._"}

## The protocol

Both exports come from the same UI, so this is a short sequence. The point is
that nothing changes between steps 3 and 5.

1. **Pick a small but feature-complete system.** Two or three entities,
   primitive fields, one single relation, one list relation, a view, a report,
   a navigation folder, a business rule, a parameter. If the install has a
   workflow and an outgoing web service, include one of each — the profile has
   record types for both and no supplied artifact exercises them.
2. **Note the build.** `Barsa.Meta.SemanticExchange` and
   `Barsa.Meta.DataExchange` file versions, and the `Core Version` the legacy
   header will carry. They should agree; if they do not, say so in the pair
   manifest.
3. **Make no edits from here until step 5 is done.** This is the whole point.
4. **Export legacy.** The export tree, tick exactly the chosen roots, then
   export without the JSON option. Keep the selection visible or write it down
   — it becomes `selection` in the manifest.
5. **Export AiExport, same selection.** Re-open the export form, tick the
   **same** roots, and this time set the JSON option. Produce both variants if
   the UI allows it: a plain `.json` path and a `.zip` path. Two AiExport
   artifacts from one selection also settle the variant-consistency question in
   spec v3 section 86, which the current samples answer only partially.
6. **Drop the files in `exports/`** (or `source/exports/`; the extractor scans
   both and classifies by content, so neither the folder nor the extension
   matters).
7. **Write `exports/pairs.json`.** Template: `comparison/pairs.template.json`.
   The declaration is recorded but never trusted on its own — the structural
   check still runs, and a declared `exact` that the structure contradicts is
   reported as a conflict.
8. **Re-run `python3 tools/extract.py`.** `comparison/match-report.md` will then
   either promote the held candidates to confirmed findings or clear them.

## What the pair will settle

{_table(["Question", "How the pair answers it"], [
 ["Are the two system-level MetaCode rows dropped by the exporter, or were they deleted?",
  "If a same-build legacy export still has them and the same-build AiExport does not, the exporter drops them. If neither has them, they were deleted."],
 ["Does the ZIP variant emit a system `[كد]` folder at all?",
  "A system with code, exported to both variants, shows it directly."],
 ["Do both AiExport variants normalize to the same model?",
  "Section 86 asks this. Navigation is already known to differ; a same-selection pair of variants shows whether anything else does."],
 ["Is a compatibility percentage trustworthy?",
  "Only a same-build Exact pair makes the number mean format fidelity rather than drift."],
 ["Which concepts does AiExport not project at all?",
  "A feature-complete system distinguishes 'not projected' from 'not present in this system', which the current samples cannot."],
])}

## The one thing to avoid

Do not reconstruct a pair from two exports taken at different times because the
names match. That is exactly what the current samples are, and it is why two
findings are stuck. Filename candidacy is recorded as `pairedBy: "filename"`
and never as proven scope.
""")


def _semantic_contract_doc(x, d):
    """The per-objectType property contract (user request 1)."""
    c = getattr(x, "semantic_contract", None)
    if not c:
        _write(d, "formats/semantic-write-contract.md",
               "# Semantic write contract\n\n"
               "_Barsa.Meta.SemanticExchange was not available._\n")
        return

    obj_rows = [[f"`{o['objectType']}`",
                 ", ".join("`%s`" % s for s in o["supportedOperations"]) or "—",
                 o["structuralOrder"], _yn(o["hasOrderingSemantics"]),
                 o["applyClass"], o["identitySemantics"]]
                for o in c["objectContracts"]]

    sections = []
    for object_type in sorted(c["propertyContracts"],
                              key=lambda k: (
                                  next((o["structuralOrder"]
                                        for o in c["objectContracts"]
                                        if o["objectType"] == k), 999), k)):
        rows = c["propertyContracts"][object_type]
        writable = [r for r in rows if r["classification"] == "Writable"]
        other = [r for r in rows if r["classification"] != "Writable"]
        base = [r for r in writable if not r["subtypes"]]
        by_sub = {}
        for r in writable:
            for s in r["subtypes"]:
                by_sub.setdefault(s, []).append(r)

        part = ["### `%s`" % object_type, ""]
        part.append("%d property contracts: %d writable, %d not."
                    % (len(rows), len(writable), len(other)))
        part.append("")
        if base:
            part.append("**Writable on any subtype**")
            part.append("")
            part.append(_table(
                ["Property", "Kind", "Create", "Update", "Reference target",
                 "Writer"],
                [[f"`{r['property']}`", r["kind"] or "—",
                  _yn(r["writableOnCreate"]), _yn(r["writableOnUpdate"]),
                  f"`{r['referenceTargetType']}`"
                  if r["referenceTargetType"] else "—",
                  f"`{r['writer']}`" if r["writer"] else "—"]
                 for r in base]))
            part.append("")
        if by_sub:
            part.append("**Writable only on a subtype**")
            part.append("")
            part.append(_table(
                ["Subtype", "Properties"],
                [[f"`{s}`",
                  ", ".join("`%s`" % r["property"] for r in sorted(
                      v, key=lambda r: r["property"] or ""))]
                 for s, v in sorted(by_sub.items())]))
            part.append("")
        if other:
            part.append("**Not authorable**")
            part.append("")
            part.append(_table(
                ["Property", "Classification", "Kind", "Runtime source"],
                [[f"`{r['property']}`", r["classification"], r["kind"] or "—",
                  r["runtimeSource"] or "—"] for r in other]))
            part.append("")
        sections.append("\n".join(part))

    _write(d, "formats/semantic-write-contract.md", f"""# Semantic write contract

{BANNER}
**Confidence: Verified.** Recovered from `SemanticContractRegistry` in
`Barsa.Meta.SemanticExchange`, which is not obfuscated.

This answers, per objectType: which properties exist, what kind each is,
whether it is writable on create, on update, or not at all, and which runtime
member does the writing.

## How this was recovered

The contract is not a data file. `SemanticContractRegistry` builds it at
type-init time: its static constructor registers one object contract per
objectType through `Obj(...)`, and `BuildProperties` registers every property
through `Writable(...)`, `Reference(...)`, `ReadOnly(...)`, `Derived(...)`,
`ReconstructionOnly(...)` and `RawJson(...)`.

Both methods are straight-line sequences of calls whose arguments are all
compile-time constants, so `tools/barsa_extractor/il_eval.py` recovers the table
by walking the opcode stream with a symbolic stack. Parameter names come from
the Param metadata table, which matters: `Reference` takes its source and
writer **before** its target type, and reading the signature the other way
round would have mislabelled every reference property.

{_table(["Metric", "Value"], [
 ["Object types", c["counts"]["objectTypes"]],
 ["Property contract rows", c["counts"]["propertyRows"]],
 ["Rows that could not be bound to an objectType", c["counts"]["unbound"]],
])}

## Object contracts

{_table(["objectType", "Operations", "Structural order", "Ordering semantics",
         "Apply class", "Identity"], obj_rows)}

`structuralOrder` is what `AiChangePlanner.SortByDependencies` and
`AiApplyLifecyclePolicy.StructuralOrder` use, so it is the order a batch's
commands are actually applied in when nothing else forces a different one:
systems and entities first, then fields and relations, then views and reports,
then folders, then workflows and dynamic commands, then constraints and rules,
with dynamic object data last.

`applyClass` separates `Hardcoded` metamodel objects from `Dynamic` ones; only
`dynamicObject` is Dynamic.

## Classification, and what "authorable" means

{_table(["Classification", "Meaning for an authored batch"], [
 ["`Writable`", "may appear in `properties`, subject to the create/update flags"],
 ["`ReadOnly`", "never authorable; present so a projection can carry it"],
 ["`Derived`", "computed by Barsa; never authorable"],
 ["`ReconstructionOnly`",
  "carried by an export so a system can be rebuilt, but not accepted from an "
  "authored batch. `orderNumber` is the one to watch: it appears in every "
  "AiExport field record and is **not** authorable."],
])}

The kinds come from `SemanticPropertyKind`: `Scalar`, `Enum`, `Reference`,
`RawJson`, `Embedded`, `Collection`, `Ordering`, `Logic`, `Other`.

## Required versus optional

The registry does **not** carry a required flag. Requiredness is enforced by
the providers, through `AiChangeProviderBase.ResolveRequired(reference, context,
name)`, which throws when a reference a provider needs cannot be resolved. So:

- **Verified:** which properties are *allowed*, per objectType and operation.
- **Unknown from the registry:** which are *required*. That lives in each
  provider's `Validate` and `Apply`, as control flow this extractor did not
  reconstruct.

`tools/lint_change_batch.py` therefore reports an unknown property as
`unsupportedProperty`, matching the planner's own code, and says nothing about
missing ones.

## Per objectType

{chr(10).join(sections)}

## Machine-readable

`index/semantic-contract.json` carries all of the above, including aliases,
subtype lists and phase-3 dependencies.

## Limits

{c["limits"]}
""")


def _write_pipeline_doc(x, d):
    """The end-to-end semantic write pipeline (user request 2)."""
    from . import write_pipeline as wp
    asm = (getattr(x, "exchange_asms", {}) or {}).get(
        "Barsa.Meta.SemanticExchange")
    if asm is None:
        _write(d, "scenarios/semantic-write-pipeline.md",
               "# Semantic write pipeline\n\n"
               "_Barsa.Meta.SemanticExchange was not available._\n")
        return
    p = wp.summary(asm)
    _write(d, "index/write-pipeline.json", _j(p))

    stage_table = _table(
        ["Stage", "Entry point", "Produces"],
        [[s["stage"], f"`{s['entryPoint']}`", f"`{s['produces']}`"]
         for s in p["stages"]])

    prov_table = _table(
        ["Provider", "objectType", "Barsa types touched", "Persists via"],
        [[f"`{r['provider']}`",
          ", ".join("`%s`" % o for o in r["objectTypes"]) or "—",
          r["coreCallCount"],
          (", ".join("`ActiveObject.%s`" % x.split("::")[1]
                     for x in r["persistenceCalls"])
           or ", ".join("`%s`" % x for x in r["persistsViaBaseHelpers"])
           or "**no write traced**")]
         for r in p["providerMutations"] if r["objectTypes"] or r["writes"]])

    _write(d, "scenarios/semantic-write-pipeline.md", f"""# Semantic write pipeline

{BANNER}
**Confidence: Observed.** Every stage is a resolved call edge in
`Barsa.Meta.SemanticExchange`, which is not obfuscated, so the names are real.
Order is the order the calls appear in each method body. Branch conditions were
not reconstructed, so *which* stages run for a given command is Unknown except
where a guard is visible as a property read or a literal.

## The six stages

{stage_table}

```mermaid
graph TD
  J["AiChangeBatch JSON"] --> L["1 ValidateBatch<br/>SemanticV15Linter"]
  L --> P["2 ParseBatch"]
  P --> PL["3 BuildPlan<br/>AiChangePlanner"]
  PL --> SUM["AiChangePlan + AiPlanSummary<br/>(nothing written yet)"]
  SUM --> AP["4 ApplyPlan<br/>AiBatchExecutor"]
  AP --> PR["5 provider.Apply"]
  PR --> AO["Barsa.Spl.ActiveObject<br/>Create / Update / Delete / CRUD"]
  AO --> DB[("database")]
  AP --> V["6 FinalReadBackAndVerify<br/>AiRuntimeVerifier"]
  V --> DB
  V --> R["AiApplyResult + AiBatchStatus"]
```

Note the shape: **plan and apply are separate calls**. A caller can build a
plan, read `AiPlanSummary.canApplyCleanly`, and decide — nothing is written
until `ApplyPlan`.

## Stage 3: planning, in body order

{_table(["Step", "What it does"],
        [[f"`{s['step']}`" if "." in s["step"] else s["step"], s["what"]]
         for s in p["planSteps"]])}

## Stage 4: applying, in body order

{_table(["Step", "What it does"],
        [[f"`{s['step']}`" if "." in s["step"] else s["step"], s["what"]]
         for s in p["applySteps"]])}

Two guards are worth calling out. The profileVersion gate is applied **again**
to the plan, so a plan built elsewhere cannot smuggle a non-v15 command past
it. And `PreflightConflicts` rechecks the fingerprint each provider recorded at
plan time, failing with *"Target changed between plan and apply."* — so a plan
is not blindly replayable against a system that moved underneath it.

## The deferral model

A reference that cannot resolve yet is not an error; it is deferred.

{_table(["Phase", "Name", "Meaning"],
        [[ph["value"], f"`{ph['name']}`", m] for ph, m in zip(
            p["lifecycle"]["phases"],
            ["what must exist before anything else can point at it",
             "configuration applied once the object exists",
             "wiring that can only be done when every object in the batch exists"])])}

`{p["lifecycle"]["deferralDecision"]}` decides per property, classifying it as
one of: {", ".join("`%s`" % k for k in p["lifecycle"]["deferredKinds"])}.

{p["lifecycle"]["placeholder"]}

Deferred work becomes an `{p["lifecycle"]["stageType"]}` carrying
{", ".join("`%s`" % s for s in p["lifecycle"]["stageProperties"])}, and
`AiBatchExecutor.OrderPhase3Stages` then `ExecuteInternalStages` run the final
wiring pass after every command has been applied.

{p["lifecycle"]["subtypeResolution"]}

## Stage 5: what actually mutates

{prov_table}

**Persistence base:** {p["persistenceBase"]}

{p["persistenceNote"]}

{"**No write traced for:** " + ", ".join("`%s`" % n for n in p["providersWithNoTracedWrite"]) + ". `AiGenericChangeProvider` is the fallback that matches no objectType literal, so having no write of its own is expected. For `AiDynamicObjectChangeProvider` the write was not located, which is consistent with its `applyClass` being `Dynamic` -- it writes instance rows rather than metamodel objects -- but the path is **Unknown**." if p["providersWithNoTracedWrite"] else ""}

## Stage 6: verification is real

`AiRuntimeVerifier` has a `Verify*` per objectType — `VerifySystem`,
`VerifyEntity`, `VerifyField`, `VerifyView`, `VerifyReport`, `VerifyFolder`,
`VerifyRule`, `VerifyWorkflow`, `VerifyDynamicCommand`, `VerifyDynamicObject` —
plus `VerifyFieldSiblingRelativeOrder` and `VerifyFolderSiblingRelativeOrder`.

It reads each written object back out of the database and compares it against
what was asked for, canonicalizing both sides first (`CanonicalizeViewLayoutForVerify`,
`CanonicalizeConditionForVerify`, `NormalizeSemanticScalar`,
`TryCanonicalSemanticDate`, and `ImagePixelsEqual` for image payloads). A
mismatch becomes `AiCommandStatus.VerificationFailed` and
`ClassifyVerificationFailure` labels it.

So the pipeline does not trust its own writes — which is the strongest
indication that half-application is an expected outcome rather than an edge
case.

## What this means for a caller

{_table(["If you want", "Do this"], [
 ["to check a batch without a server",
  "`tools/lint_change_batch.py batch.json`"],
 ["to know what would happen",
  "`BuildPlan`, then read `AiPlanSummary.canApplyAny` / `canApplyAll` / `canApplyCleanly`"],
 ["to know what did happen",
  "`AiApplyResult.status`, then per-command `AiCommandResult.status`, `phase`, `failureClass` and `mutationStage`"],
 ["the real ids of what you created",
  "`AiApplyResult.temporaryIds`, which maps each tempId to its new id"],
 ["to know whether a half-applied command was repaired",
  "`needsReconcile`, `reconcileSucceeded` and `reconcileMessage`"],
 ["to know whether Barsa agrees it worked",
  "`verificationSucceeded`, and `runtimeReadBack` for what it found"],
])}

## Limits

{p["limits"]}
""")
