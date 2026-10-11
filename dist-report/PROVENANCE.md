# Provenance

> **Source:** every input listed below
> **dist commit:** 79df8282d328dd5b18ff6dbcaa105d6e18ffdf79
> **compiled:** 2026-10-11 · **scope:** system=1011413550000000100

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
| `dist/index/systems/1001513550000000100/semantic.json` | d7bdfae8b936ce28… |
| `dist/index/systems/1008513550000000101/semantic.json` | feca26339b65e748… |
| `dist/index/systems/1011413550000000100/semantic.json` | f883280905007ab3… |
| `dist/index/systems/1013413550000000100/semantic.json` | f123ee25148c9f9d… |
| `dist/index/systems/1013413550000010104/semantic.json` | 3ebb481da0996db8… |
| `dist/index/systems/1043513550000000145/semantic.json` | 294375703cc52560… |
| `dist/index/systems/1101513550000000103/semantic.json` | 629b40698ed8b1f7… |
| `dist/index/systems/1101513550000000106/semantic.json` | c463e1edcf519911… |
| `dist/index/systems/7097413550000000101/semantic.json` | 9f62b35900963058… |
| `dist/index/systems/manifest.json` | ea0ba27043f8b64c… |
| `dist/index/write-pipeline.json` | 0faa6654189bfb4c… |
| `dist/models/ai-change-batch.schema.json` | c7b68f8c8db02efc… |
| `dist/models/normalized-samples/ai-Push Notification (05-07-11 20;08).json` | 0079a82d49c65e58… |
| `dist/models/normalized-samples/ai-باركد (05-07-11 20;08).json` | 325e2a3e679f04e3… |
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
