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
| `Barsa.AiExport` | JSON document, or ZIP of JSON | `Barsa.Meta.SemanticExchange` | not directly; see below |
| `Barsa.AiChangeBatch` | JSON | an agent or tool, not Barsa | `BixWriteHelper.ApplyPlan` |

Both export families share one collection engine, so AiExport is a *projection*
of the same `DataSet` the legacy export writes. Writing back through the AI side
takes a third document, an `AiChangeBatch` of create/update/delete commands --
so the AI path is **not** a symmetric importer.

Validate a change batch offline before sending it. With the generated contract
present, this also checks every property against the per-objectType write
contract recovered from the binary:

```bash
python3 tools/lint_change_batch.py --example > batch.json
python3 tools/lint_change_batch.py batch.json
python3 tools/lint_change_batch.py --schema          # JSON Schema
```

## Layout

```
source/       inputs: Barsa DLLs/EXEs, configs, .metaexport packages, resources
tools/        the extractor, the report compiler and the agent protocol
dist/         the generated knowledge pack
dist-report/  the report-authoring pack, compiled from dist/
.agent-work/  the kanban: tasks, manifests, attempts, events, board
docs/         how the kanban works
specs/        the specifications this implements
```

Everything is pure Python, standard library only — no npm, no build step.

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
- `comparison/match-report.md` — what matched, what did not, and what is a bug candidate
- `comparison/golden-pair-protocol.md` — how to produce the pair that settles the open findings
- `formats/ai-change-batch.md` — the write-path document and its lint rules
- `formats/semantic-write-contract.md` — per objectType: which properties are writable, on create or update
- `scenarios/semantic-write-pipeline.md` — batch → lint → plan → apply → mutation → verify
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

## The report-authoring pack

`dist/` is about Barsa. `dist-report/` is about building one report in Barsa:
a 140 KB pack compiled out of the 58 MB one, for an agent that has to produce
an `AiChangeBatch` and get it accepted.

```bash
python3 tools/report_compiler.py --scope system=1011413550000000100
python3 tools/report_compiler.py --scope contract      # no entity model
python3 tools/report_compiler.py --check               # is the pack stale?
```

It reads `dist/` and never `source/` — the loader's allowlist is the
enforcement point. The build fails, rather than growing or softening, if the
pack goes over budget, a property escapes its one group, a recipe stops
linting clean, a confidence is promoted, a file loses its provenance header,
or the gap register comes out empty.

```
dist-report/README.md               start here
dist-report/README-FA.md            the same, in Persian, for a human
dist-report/MISSING-FROM-DIST.md    generated: every Unknown, and where to look
dist-report/common/                 the contract, scope-independent
dist-report/systems/<id>/           one system's entities, fields and selectors
```

The recipes in `common/RECIPES.md` are validated during the build by the same
linter `tools/lint_change_batch.py` runs, against the contract recovered from
the binary — so a recipe cannot drift from the contract without the build
failing.

## From a request to a change: the kanban

`dist-report/` tells an agent how to build a report. The kanban is what walks
one real need through to a verified change, with the same seven lanes, the same
state machine and the same two human gates as the BarsaAgent workflow:

```text
ورودی → طراحی → آماده → پیاده‌سازی → بازبینی → آماده اعمال → تمام
new    architecture  ready  implementing  review   approved…    integrated
```

```bash
python3 tools/manager.py init --system 1011413550000000100
python3 tools/manager.py import-issue --slug my-report --kind report.create \
    --request-file need.txt
python3 tools/manager.py run 0001        # advances to the first gate
python3 tools/kanban_server.py           # the board, at 127.0.0.1:4310
```

Implementation here produces an `AiChangeBatch`, not code, so build/lint/test
are replaced by five gates the manager runs itself: `lint` (the contract
linter, zero findings), `selectors` (every name resolves in the scope's
index), `unknowns` (nothing the knowledge pack marks Unknown may be authored),
`scope` (only objects the task holds a lock on) and `order` (structuralOrder,
parents first).

The last gate hands the batch to a human: this repository never connects to a
Barsa installation. `answer --approve` means "I applied it", and it is refused
unless the batch is still byte-for-byte the one the gate opened on.

A worked run, command by command, with the real output: `docs/kanban-walkthrough.md`. How it works: `docs/kanban.md`. Protocol state lives in `.agent-work/`.

## Specifications

| Spec | Scope | Status |
|---|---|---|
| `specs/Barsa-Knowledge-Extractor-Master-Spec.md` | v2: extract a knowledge pack from the binaries and legacy exports | implemented |
| `specs/Barsa-Knowledge-Extractor-Master-Spec-v3.md` | v3: dual export families, AiExport, scope-gated comparison | implemented |
| `specs/Barsa-Report-Designer-Knowledge-Compiler-Spec.md` | compile `dist/` down to a small report-authoring pack in `dist-report/` | implemented |

## Confidence levels

```
CrossVerified > Verified > Observed > Inferred > Unknown
```

A consumer must not complete anything marked `Unknown`.
