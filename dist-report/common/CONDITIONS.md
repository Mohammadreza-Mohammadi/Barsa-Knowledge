# Conditions

> **Source:** dist/formats/ai-export-single-json.md → Observed paths · dist/index/ai-export-properties.json → enums · dist/index/semantic-contract.json → propertyContracts.report
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

## How clauses combine

A condition is an object with one combining key:

```json
{
  "condition": {
    "all": []
  }
}
```

`all` and `any` line up exactly with `Barsa.Meta.CombinationOperator` (All = 0, Any = 1). Two independent sources agree, so this is **CrossVerified**.

`{"all": []}` is an empty condition: no clause, every row.

## What a clause looks like

| key | types | times seen | nullable |
|---|---|---|---|
| `condition` | object | 16 | no |
| `condition.all` | array | 16 | no |
| `condition.all[*]` | object | 16 | no |
| `condition.all[*].customSql` | string | 2 | no |
| `condition.all[*].field` | object, string | 16 | no |
| `condition.all[*].field.items` | array | 7 | no |
| `condition.all[*].field.items[*]` | string | 14 | no |
| `condition.all[*].nullBehavior` | string | 6 | no |
| `condition.all[*].operator` | string | 16 | no |
| `condition.all[*].parameter` | string | 12 | no |
| `condition.all[*].value` | null, string | 4 | yes |

So a clause carries a `field` (a selector, or an object with an `items` list when several fields are involved), an `operator`, and optionally a `value`, a `parameter` reference, a `nullBehavior`, or raw `customSql`.

These keys are **Observed** -- 16 clauses in the supplied artifacts carried them.

## But the operator values are Unknown

This is the wall. `operator` is a string in all 16 observed clauses, and dist/ records that the key exists and its type, never the strings themselves.

The profile's `Barsa.Meta.ComparisonOperator` has 1 member: `AdvancedTextSearch2`. That is far too few for a condition engine that also carries `nullBehavior` and multi-field clauses, so the real operator vocabulary is elsewhere and the profile maps only this one.

**Therefore: do not author a non-empty condition.** A clause with a guessed operator name is a batch that lints clean and does the wrong thing. Write `{"all": []}` and let a human add the condition in the designer, or supply the operator string from a source outside this pack.

## treeCondition

A separate writable property, for the hierarchy side of a tree report. Its value shape is **Unknown** -- no artifact carries one. `useHierarchyConditionForRoot` decides whether it also applies to root rows.

## Ordering inside the batch

The contract records `condition` as depending on `parameters`: a clause may reference a parameter, so parameters are applied first. `sorting` likewise depends on `columns`.
