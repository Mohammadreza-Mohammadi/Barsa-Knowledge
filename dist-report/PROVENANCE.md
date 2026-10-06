# Provenance

> **Source:** every input listed below
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

Every input this pack was compiled from, with the hash it had at compile time. If a hash no longer matches, the pack is stale: `python3 tools/report_compiler.py --check` says so and exits non-zero.

## Inputs

| dist/ file | sha256 |
|---|---|
| `dist/formats/ai-export-single-json.md` | c0233374247334c2… |
| `dist/formats/report-format.md` | a0b59d6ccafe395a… |
| `dist/index/ai-export-properties.json` | 15f3d6565cf58250… |
| `dist/index/export-formats.json` | 22f7339d7a1892cc… |
| `dist/index/knowledge-index.json` | a427b37b4d4bc0d7… |
| `dist/index/semantic-contract.json` | 6de61fdc7bc6f2d6… |
| `dist/index/write-pipeline.json` | 0faa6654189bfb4c… |
| `dist/models/ai-change-batch.schema.json` | c7b68f8c8db02efc… |
| `dist/models/normalized-samples/ai-Push Notification (05-07-11 20;08).json` | 86b11dab1a61db9d… |
| `dist/models/normalized-samples/ai-باركد (05-07-11 20;08).json` | c7432f1c67207b53… |
| `dist/models/normalized-samples/legacy-NewMeta01.json` | b3350b5061ece933… |
| `dist/models/normalized-samples/legacy-NewMeta02.json` | d73d9b90dac4683c… |
| `dist/models/normalized-samples/legacy-Push Notification، الگو، پورتال برسانوين‌راي (05-07-08 13;42).json` | 52a481bc56b805a3… |
| `dist/models/normalized-samples/legacy-باركد (05-02-02 11;14).json` | a8358e1149645cf9… |

## Which part of the pack came from where

| pack file | dist/ source | what the Extractor read it from |
|---|---|---|
| `common/REPORT-CONTRACT.md`, `common/index/report-contract.json` | `index/semantic-contract.json` | SemanticContractRegistry type-init, by constant IL evaluation |
| `common/LIMITS.md` | `index/semantic-contract.json` | the same, ReadOnly rows |
| `common/REPORT-TYPES.md`, `common/index/report-types.json` | `index/ai-export-properties.json`, `models/normalized-samples/` | the embedded AI export profile resource, and the supplied artifacts |
| `common/index/report-enums.json` | `index/ai-export-properties.json` | enum members from the profile resource |
| `common/COLUMNS-AND-FIELDS.md`, `common/CONDITIONS.md`, `common/PARAMETERS.md`, `common/index/report-shapes.json` | `formats/ai-export-single-json.md` | a walk over the supplied AiExport artifacts, recording keys and types |
| `common/index/field-types.json` | `index/semantic-contract.json` | propertyContracts.field |
| `common/PLACEMENT.md` | `index/semantic-contract.json`, `index/ai-export-properties.json` | objectContracts and the FolderType enum |
| `common/RECIPES.md`, `common/index/recipes.json` | `index/semantic-contract.json`, `index/write-pipeline.json` | written by this compiler, validated against the contract |
| `systems/*/` | `models/normalized-samples/` | the supplied legacy and AiExport artifacts, normalized |

## What this pack adds that dist/ does not state

Two things, both marked **Inferred** wherever they appear:

1. the grouping of the writable properties into sections (`common/REPORT-CONTRACT.md`)
2. the report type × property affinity, and the AiExport ↔ CLR report type mapping (`common/REPORT-TYPES.md`)

Everything else carries the confidence its dist/ source carried. The build checks this: a fact whose provenance is a dist/ file may not be published at a higher confidence than the source states.
