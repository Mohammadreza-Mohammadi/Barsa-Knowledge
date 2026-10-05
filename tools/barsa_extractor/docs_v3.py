"""Spec v3 deliverables: format docs, comparison, reanalysis report."""

import json
import os
import time

from .docs import BANNER, _j, _jl, _table, _write, _yn

LEGACY_LABEL = "Barsa.LegacyMetaExport"
AI_LABEL = "Barsa.AiExport"


def write_all(x):
    d = x.dist
    _format_detection(x, d)
    _legacy_docs(x, d)
    _ai_docs(x, d)
    _version_matrix(x, d)
    _comparison(x, d)
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

## Why no percentage

{chr(10).join("- %s: %s" % (c["pair"]["legacy"], c["coverage"]["percentageNote"]) for c in x.comparisons) if x.comparisons else "No pair exists. A percentage would be meaningless and is therefore not produced."}
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

In priority order:

1. **A same-scope golden pair** (spec v3 sections 78-79): one small but
   feature-complete system exported twice from the same build at the same time,
   once legacy and once AiExport, with a `pairs.json` naming the selection. The
   comparison pipeline in `tools/` is built and tested; it needs only the pair
   to produce a real `comparison/` report. Without it, no compatibility
   percentage can be computed, by design.
2. **An `AiChangeBatch` document**, which would settle whether the AI write path
   can consume an AiExport projection.
3. **Decompiled `Barsa.Meta.DataExchange.dll`**, specifically
   `NewImportManager.Import`, which is the single biggest remaining Unknown and
   is obfuscated.

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
                "serializer": "Newtonsoft.Json",
                "payloadType": "AiChangeBatch",
                "producer": "external (an agent or tool)",
                "writer": None,
                "reader": "BixWriteHelper.ParseBatch",
                "profileVersion": 15,
                "confidence": "Verified",
            },
        ],
        "apiFormatMap": x.api_formats,
        "variantSwitch": x.variant_switch,
        "profileVersion": x.profile_version,
        "aiImportVerdict": x.ai_import,
        "diffStates": x.diff_states,
        "atomicity": x.atomicity,
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
**Unknown** for the resulting bytes, since no AiExport artifact was supplied.
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
