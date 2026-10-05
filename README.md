# Barsa Knowledge Extractor

Turns the Barsa binaries and export packages in `source/` into an
evidence-based, machine-readable knowledge layer in `dist/`.

The governing rule: **no fact without evidence**. Anything that could not be
proven from the supplied inputs is marked `Unknown` rather than guessed, and
"not observed in these samples" is never written as "unsupported".

Barsa has **two export format families**, and the extractor keeps them apart:

| Family | Physical | Produced by | Read back by |
|---|---|---|---|
| `Barsa.LegacyMetaExport` | GZip → BinaryFormatter → `DataSet` | `Barsa.Meta.DataExchange` | `NewImportManager.Import` (symmetric) |
| `Barsa.AiExport` | JSON document, or ZIP of JSON | `Barsa.Meta.SemanticExchange` | `BixWriteHelper.ApplyPlan` (change batches, not symmetric) |

Both share one collection engine, so AiExport is a *projection* of the same
`DataSet` the legacy export writes.

## Layout

```
source/   inputs: Barsa DLLs/EXEs, configs, .metaexport packages, resources
tools/    the extractor (pure Python, standard library only)
dist/     the generated knowledge pack
specs/    the master specifications this implements (v2 and v3)
```

## Running it

```bash
python3 tools/extract.py
```

Roughly three minutes over the current `source/`. Exits non-zero if a final
validation check fails. Options: `--source DIR`, `--dist DIR`, `--quiet`.

No third-party packages, and no .NET runtime, mono or decompiler is required —
the extractor parses ECMA-335 metadata itself.

## What it reads

| Phase | Input | Output |
|---|---|---|
| 1–3 | every file under `source/` | assembly, type and method inventory |
| 4–5 | IL opcode streams | call graph, string literals, SQL, config call sites |
| 6 | `*.metaexport` | legacy package structure, schema, row counts |
| 6b | every candidate artifact | content-based physical/logical format detection |
| 7 | embedded resources + enums | the AiExport profile, API→format map, version gates |
| 8 | both families | normalized model per artifact, scope equivalence, comparison |
| 9 | all of the above | cross-source validation and conflict detection |
| 10–12 | cross-validated facts | reconstruction order, format-aware capabilities |
| 13–14 | everything | `dist/` plus a validation pass |

## Start here in `dist/`

- `README.md` — headline findings and reading order
- `REANALYSIS-REPORT.md` — what changed from the previous pass, and why
- `ARCHITECTURE.md` — the layer map
- `formats/format-detection.md` — telling the two families apart
- `formats/ai-export.md` — the JSON family and its embedded profile
- `comparison/legacy-vs-ai-export.md` — how the two relate
- `formats/legacy-metaexport.md` — the legacy on-disk container
- `scenarios/import-system-legacy.md` — how a system is rebuilt from a package
- `evidence/cross-validation.md` — what two or more independent sources confirm
- `CONFIDENCE-REPORT.md` — how far to trust each area, and why
- `RUNTIME-GAPS.md` / `MISSING-INPUTS.md` — what is still unproven

## Safety

Per the spec's static-analysis rules, the extractor never executes Barsa code,
calls a constructor, connects to a database or imports a sample. It also never
deserializes a package — `BinaryFormatter` input is untrusted, so the embedded
schema and diffgram are read straight out of the byte stream. Embedded profile
resources are likewise read as bytes, not loaded as assemblies. Credential-shaped
strings and sensitive-looking columns are redacted before they reach `dist/`.

## Confidence levels

```
CrossVerified > Verified > Observed > Inferred > Unknown
```

A consumer must not complete anything marked `Unknown`.
