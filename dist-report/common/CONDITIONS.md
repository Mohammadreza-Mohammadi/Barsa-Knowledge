# Conditions

> **Source:** dist/formats/ai-export-single-json.md → Observed paths · dist/index/ai-export-properties.json → enums · dist/index/semantic-contract.json → propertyContracts.report
> **dist commit:** 79df8282d328dd5b18ff6dbcaa105d6e18ffdf79
> **compiled:** 2026-10-12 · **scope:** system=1011413550000000100

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

## The operator values

The profile's `Barsa.Meta.ComparisonOperator` has 1 member: `AdvancedTextSearch2` -- far too few for a condition engine that also carries `nullBehavior` and multi-field clauses. The real vocabulary is elsewhere, and where it is settles below.

The Host's own reference document names them, so this is no longer a guess. 18 operators:

`none`, `equal`, `notEqual`, `greaterThan`, `lessThan`, `greaterThanOrEqual`, `lessThanOrEqual`, `contains`, `doesNotContain`, `startsWith`, `doesNotStartWith`, `isNull`, `isNotNull`, `between`, `inList`, `notInList`, `advancedTextSearch`, `advancedTextSearch2`.

`nullBehavior` takes `ignoreCondition`, `checkNullValue`, `dontIgnore`, and nothing else.

**Confidence: Documented.** This is the vendor stating the contract, not this compiler inferring it from a binary -- a different kind of evidence from everything else in this pack, and recorded as such. Source: `barsa-ai-host/startup/dataexchange/10-condition-reference.fa.md`.

One thing the document says that a reader must not miss: it names `DoseNotContain` as an internal typo that does **not** enter the AI contract. A name appearing in that document is not automatically a value you may write; only the list above is.

A clause may also carry `value`, `parameter`, `nullBehavior`, `customSql`, `enabled`, `ignoreCase` and `autoSetInNew`. Groups nest: a member of `all` may itself be an `all`/`any`.

## treeCondition

A separate writable property, for the hierarchy side of a tree report. Its value shape is **Unknown** -- no artifact carries one. `useHierarchyConditionForRoot` decides whether it also applies to root rows.

## Ordering inside the batch

The contract records `condition` as depending on `parameters`: a clause may reference a parameter, so parameters are applied first. `sorting` likewise depends on `columns`.
