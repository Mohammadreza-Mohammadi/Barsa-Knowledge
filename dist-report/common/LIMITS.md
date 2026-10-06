# Limits

> **Source:** dist/index/semantic-contract.json → propertyContracts.report · dist/formats/ai-export-single-json.md → Observed paths
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

What cannot be written, and what is not known. This is the most important file in the pack: a consumer that treats one of these as writable will produce a batch that fails, and one that fills an Unknown with a plausible value will produce a batch that is wrong without failing.

## Not writable at all

| property | classification | kind | declared reason |
|---|---|---|---|
| `$type` | ReadOnly | Enum | `AiSemanticV15ExportPostProcessor semantic object discriminator` |
| `entity` | ReadOnly | Reference | `Report.TypeDefId` |
| `parameterLayout` | ReadOnly | Embedded | `Report parameter XML layout is out of Semantic v15 reconstruction scope in v190` |
| `system` | ReadOnly | Reference | `Report.SystemId` |

Read these as written. Three consequences matter:

1. **The target entity of a report cannot be changed.** `entity` is ReadOnly, so there is no update that moves a report to another entity. It is fixed at create time, and it comes from the command's `parent`, not from a property. Changing it means deleting the report and creating another.
2. **The owning system cannot be changed either.** `system` is ReadOnly for the same reason, and reads from `Report.SystemId`.
3. **The parameter panel layout cannot be reconstructed.** The contract's own words: *"Report parameter XML layout is out of Semantic v15 reconstruction scope in v190"*. This is a declared limitation, not an inference, and not a gap in this pack.

## The unnamed contract

- factory `RawJson`, kind `RawJson`: The RawJson factory takes no property name, so this contract covers a raw JSON payload rather than a named property. Runtime source: `Report.JsonProperty`.

## Writable, but never observed

68 of the writable properties appear in no supplied artifact. That is **not** evidence against them: the exporter omits a property sitting at its default, and the two supplied systems exercise a narrow slice of the designer. It does mean this pack can show no example of their value shape.

`additionalWhere`, `allowAddNew`, `allowAddToList`, `allowEdit`, `allowGridColumnSort`, `allowInlineEdit`, `allowRemove`, `allowRemoveFromList`, `allowView`, `alternateEditObjectColumn`, `alternateRootTable`, `alternateRowMode`, `autoInlineEdit`, `calendar`, `commandDisplayMode`, `customSql`, `description`, `disableColumnHeaders`, `disableOptimizeForDisplay`, `dontExecuteCount`, `dontUseChildParentReport`, `extraQueryTemplate`, `formatConditions`, `forum`, `freeColumnSizing`, `gridCustomKey`, `gridGrouping`, `gridHideColumnsWhenGrouped`, `gridHideLines`, `gridLines`, `gridShowGroupBox`, `gridViewStyle`, `grouping`, `hideHeader`, `hideRowIcon`, `hideToolbar`, `ignoreAdvancedSecurityCondition`, `ignoreColumns`, `includeDeleted`, `insideViewActive`, `insideViewHeight`, `insideViewRelatedField`, `isDistinct`, `listEditView`, `logExecutions`, `matrix`, `oracleHint`, `pageSize`, `pagingType`, `preserveUserViewState`, `previewField`, `previewState`, `rootTableAlias`, `selfReferencingField`, `showPreviewField`, `showRecordSignFormatting`, `showRowNumber`, `showWpfChart`, `sorting`, `sqlGrouping`, `subReports`, `systemId`, `top`, `treeAutoOpenLevels`, `treeCondition`, `useAdvancedAccess`, `useHierarchyConditionForRoot`, `useSummaryRow`

## Unknowns a consumer must not fill

- the comparison operator vocabulary in a condition
- the semantics of a `parameters` entry, and the value vocabulary of its `kind` and `sourceOperator`
- the parameter panel layout (declared out of scope, above)
- which properties are meaningful for which `reportType`
- whether a column may name a field reached through a relation
- the print template format (`PrintView`); no `.mrt` sample exists

Each has a row in `MISSING-FROM-DIST.md` saying where to look.

## Not an authoring limit, but worth knowing

The write path is not a symmetric importer. An `AiChangeBatch` is a change plan executed command by command, and the pipeline is deliberately non-atomic: a partial batch leaves partial state. `errorPolicy` accepts exactly one value, `continueIndependent`.
