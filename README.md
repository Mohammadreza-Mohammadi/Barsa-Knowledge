# Barsa Knowledge Extractor

Turns the Barsa binaries and export packages in `source/` into an
evidence-based, machine-readable knowledge layer in `dist/`.

The governing rule: **no fact without evidence**. Anything that could not be
proven from the supplied inputs is marked `Unknown` rather than guessed.

## Layout

```
source/   inputs: Barsa DLLs/EXEs, configs, .metaexport packages, resources
tools/    the extractor (pure Python, standard library only)
dist/     the generated knowledge pack
specs/    the master specification this implements
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
| 6–8 | `*.metaexport` | package structure, table/column schema, row counts |
| 9 | all of the above | cross-source validation and conflict detection |
| 10–12 | cross-validated facts | normalized system model, capabilities, scenarios |
| 13–14 | everything | `dist/` plus a validation pass |

## Start here in `dist/`

- `README.md` — headline findings and reading order
- `ARCHITECTURE.md` — the layer map
- `formats/export-package.md` — the on-disk package format
- `scenarios/import-system.md` — how a system is rebuilt from a package
- `evidence/cross-validation.md` — what two or more independent sources confirm
- `CONFIDENCE-REPORT.md` — how far to trust each area, and why
- `RUNTIME-GAPS.md` / `MISSING-INPUTS.md` — what is still unproven

## Safety

Per the spec's static-analysis rules, the extractor never executes Barsa code,
calls a constructor, connects to a database or imports a sample. It also never
deserializes a package — `BinaryFormatter` input is untrusted, so the embedded
schema and diffgram are read straight out of the byte stream. Credential-shaped
strings and sensitive-looking columns are redacted before they reach `dist/`.

## Confidence levels

```
CrossVerified > Verified > Observed > Inferred > Unknown
```

A consumer must not complete anything marked `Unknown`.
