# Barsa report designer pack

> **Source:** dist/, compiled by tools/report_compiler.py
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

A small pack about one task: **building and understanding a report in Barsa**. It is compiled from the general knowledge pack in `dist/` and contains nothing else -- no Barsa architecture, no format archaeology, no assembly inventory.

Two kinds of consumer are intended:

- **Authoring** — produce an `AiChangeBatch` that creates or changes a report, and have it accepted. Start at `common/RECIPES.md`.
- **Comprehension** — explain an existing report, or say why something cannot be changed. Start at `common/REPORT-CONTRACT.md` and `common/LIMITS.md`.

## The rule this pack is built on

No fact without evidence. Anything that could not be shown from `dist/` is marked **Unknown**, and a consumer must not fill an Unknown with a plausible value. *Not observed* is never written as *unsupported*.

```text
CrossVerified > Verified > Observed > Inferred > Unknown
```

Exactly two things in this pack are **Inferred**, both this compiler's own additions: the grouping of the writable properties, and the report type × property affinity. Everything else carries the confidence its `dist/` source carried.

## Reading order

| file | what it answers |
|---|---|
| `common/REPORT-CONTRACT.md` | what may be written on a report, on create and on update |
| `common/LIMITS.md` | what cannot be written, and what is not known -- read this second |
| `common/RECIPES.md` | complete batches for the common tasks, lint-clean at build time |
| `common/REPORT-TYPES.md` | the two report-type vocabularies, and why they must not be conflated |
| `common/COLUMNS-AND-FIELDS.md` | what can be a column |
| `common/CONDITIONS.md` | how filtering is shaped, and why a non-empty condition cannot be authored |
| `common/PARAMETERS.md` | why parameters are not authorable |
| `common/PLACEMENT.md` | how a report becomes visible |
| `common/SELECTORS.md` | how objects are named, and the letter trap |
| `PROVENANCE.md` | where each part came from |
| `MISSING-FROM-DIST.md` | what the Extractor would have to add next, and why it matters |

## Six things this pack can answer

1. *Can I create a list report?* Yes — `common/RECIPES.md` R1, with 80 writable properties documented in `common/REPORT-CONTRACT.md`.
2. *Can I change which entity a report runs over?* No. `entity` is ReadOnly; it is fixed by the create command's `parent`. `common/LIMITS.md`.
3. *Which fields can be columns on this entity?* In a system-scoped pack, search the full `dist/` system index with `tools/report_retrieve.py`; whether a given field *type* may be a column is Unknown.
4. *What order do commands go in?* `report` is structuralOrder 120 and `folder` is 130, so the report is created before the folder that points at it. `common/PLACEMENT.md`.
5. *What do you not know?* `MISSING-FROM-DIST.md`, and the Unknown section of `common/LIMITS.md`. The short list: condition operators, parameter semantics, panel layout, the type × property matrix.
6. *What is the exact selector for a field?* `systems/<id>/index/selectors.json` — copy the string, do not retype it.

## Scope

This pack was compiled at scope `system=1011413550000000100`.

It carries the entity model for system `1011413550000000100`.

The full canonical index is `dist/index/systems/1011413550000000100/semantic.json`. Retrieve a bounded field candidate set with `python tools/report_retrieve.py --system 1011413550000000100 --kind field --query <name-or-id>`. Search results retain provenance; check the owning entity before using a selector.

## Staleness

`PROVENANCE.md` lists every input with its hash. `python3 tools/report_compiler.py --check` compares them against `dist/` as it is now and exits non-zero if the pack is stale.
