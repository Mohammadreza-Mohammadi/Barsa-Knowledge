# Provenance

> **Source:** every input listed below
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

Every input this pack was compiled from, with the hash it had at compile time. If a hash no longer matches, the pack is stale: `python3 tools/report_compiler.py --check` says so and exits non-zero.

## Inputs

| dist/ file | sha256 |
|---|---|
| `dist/formats/ai-export-single-json.md` | c7ef01aa9aff19ea… |
| `dist/formats/report-format.md` | 79002ce206fd9862… |
| `dist/index/ai-export-properties.json` | 15f3d6565cf58250… |
| `dist/index/export-formats.json` | 22f7339d7a1892cc… |
| `dist/index/knowledge-index.json` | a427b37b4d4bc0d7… |
| `dist/index/semantic-contract.json` | fd55f87a4f4c5f46… |
| `dist/index/systems/1001513550000000100/semantic.json` | 65ee8e2fbfb1ec48… |
| `dist/index/systems/1008513550000000101/semantic.json` | c3b392e07c1f09f0… |
| `dist/index/systems/1011413550000000100/semantic.json` | ef92fef073014d01… |
| `dist/index/systems/1013413550000000100/semantic.json` | 4f317a895fa6ff20… |
| `dist/index/systems/1013413550000010104/semantic.json` | ae253875325d50b8… |
| `dist/index/systems/1043513550000000145/semantic.json` | db601604dd3e6b41… |
| `dist/index/systems/1101513550000000103/semantic.json` | dfeba77694d5a4b0… |
| `dist/index/systems/1101513550000000106/semantic.json` | f5bb2185d2058991… |
| `dist/index/systems/7097413550000000101/semantic.json` | 99d7088ba60d5abb… |
| `dist/index/systems/manifest.json` | 6561e802e134c458… |
| `dist/index/write-pipeline.json` | ffd258a7743d5ff2… |
| `dist/models/ai-change-batch.schema.json` | d20383c250b9600c… |
| `dist/models/normalized-samples\ai-Push Notification (05-07-11 20;08).json` | 203a915d663f23f4… |
| `dist/models/normalized-samples\ai-باركد (05-07-11 20;08).json` | b7df9bd940c2ab3c… |
| `dist/models/normalized-samples\legacy-NewMeta01.json` | 37bf50789ad0bbc8… |
| `dist/models/normalized-samples\legacy-NewMeta02.json` | e298370b00e706ab… |
| `dist/models/normalized-samples\legacy-Push Notification، الگو، پورتال برسانوين‌راي (05-07-08 13;42).json` | 08f8b28e249668a5… |
| `dist/models/normalized-samples\legacy-باركد (05-02-02 11;14).json` | a41887d5954fe686… |

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
