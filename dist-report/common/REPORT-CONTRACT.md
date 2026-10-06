# Report write contract

> **Source:** dist/index/semantic-contract.json → propertyContracts.report
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

What may be written on a report object in an `AiChangeBatch`, taken from the write contract the Barsa binary builds at type-init. Classification, create and update flags are **Verified**; the grouping into sections is **Inferred** by this compiler and is the only thing here that dist/ does not state.

## The object

|  | value |
|---|---|
| objectType | `report` |
| supported operations | Create, Update, Delete |
| structural order | 120 |
| identity | `Report.Id under entity` |
| ordering semantics | no |
| runtime adapter | `report:semantic` |
| apply class | Hardcoded |
| confidence | Verified |

`structuralOrder` is what decides command order inside a batch: a report (120) is created before a folder (130) that points at it, and after the entity (100) and fields (110) it reads.

## Writable properties, grouped

80 named writable properties, in 15 groups. Every one is in exactly one group; the build fails otherwise.

The contract carries 81 writable rows in total. The extra one has no property name at all -- it is the `RawJson` contract, which covers a raw payload rather than a named property, so there is nothing to group. It is described in `LIMITS.md`.

### identity

What the report is called and where it belongs.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `name` | unstated | yes | yes |  |
| `description` | unstated | yes | yes |  |
| `systemId` | unstated | yes | yes |  |

### shape

Which kind of report this is, and what it renders over.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `reportType` | unstated | yes | yes |  |
| `typeView` | unstated | yes | yes |  |
| `parameterEntity` | unstated | yes | yes |  |

### data

Where the rows come from.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `columns` | unstated | yes | yes |  |
| `customSql` | unstated | yes | yes |  |
| `additionalWhere` | unstated | yes | yes |  |
| `extraQueryTemplate` | unstated | yes | yes |  |
| `alternateRootTable` | unstated | yes | yes |  |
| `rootTableAlias` | unstated | yes | yes |  |
| `joinAliases` | unstated | yes | yes |  |
| `isDistinct` | unstated | yes | yes |  |
| `top` | unstated | yes | yes |  |
| `includeDeleted` | unstated | yes | yes |  |
| `oracleHint` | unstated | yes | yes |  |
| `ignoreColumns` | unstated | yes | yes |  |

### filtering

Which rows survive.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `condition` | unstated | yes | yes |  |
| `treeCondition` | unstated | yes | yes |  |
| `useHierarchyConditionForRoot` | unstated | yes | yes |  |
| `ignoreAdvancedSecurityCondition` | unstated | yes | yes |  |

### shaping

How rows are ordered, grouped and aggregated.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `sorting` | unstated | yes | yes |  |
| `grouping` | unstated | yes | yes |  |
| `sqlGrouping` | unstated | yes | yes |  |
| `matrix` | unstated | yes | yes |  |
| `useSummaryRow` | unstated | yes | yes |  |

### presentation

How the result looks.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `gridViewStyle` | unstated | yes | yes |  |
| `gridLines` | unstated | yes | yes |  |
| `gridHideLines` | unstated | yes | yes |  |
| `gridGrouping` | unstated | yes | yes |  |
| `gridShowGroupBox` | unstated | yes | yes |  |
| `gridShowSelectionChecks` | unstated | yes | yes |  |
| `gridCustomKey` | unstated | yes | yes |  |
| `gridHideColumnsWhenGrouped` | unstated | yes | yes |  |
| `freeColumnSizing` | unstated | yes | yes |  |
| `alternateRowMode` | unstated | yes | yes |  |
| `disableColumnHeaders` | unstated | yes | yes |  |
| `hideHeader` | unstated | yes | yes |  |
| `hideRowIcon` | unstated | yes | yes |  |
| `hideToolbar` | unstated | yes | yes |  |
| `showRowNumber` | unstated | yes | yes |  |
| `calendar` | unstated | yes | yes |  |
| `formatConditions` | unstated | yes | yes |  |
| `showRecordSignFormatting` | unstated | yes | yes |  |
| `showWpfChart` | unstated | yes | yes |  |

### paging

How many rows at a time.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `pagingType` | unstated | yes | yes |  |
| `pageSize` | unstated | yes | yes |  |
| `dontExecuteCount` | unstated | yes | yes |  |

### permissions

What a viewer may do with a row.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `allowView` | unstated | yes | yes |  |
| `allowEdit` | unstated | yes | yes |  |
| `allowAddNew` | unstated | yes | yes |  |
| `allowRemove` | unstated | yes | yes |  |
| `allowInlineEdit` | unstated | yes | yes |  |
| `autoInlineEdit` | unstated | yes | yes |  |
| `allowAddToList` | unstated | yes | yes |  |
| `allowRemoveFromList` | unstated | yes | yes |  |
| `allowGridColumnSort` | unstated | yes | yes |  |
| `useAdvancedAccess` | unstated | yes | yes |  |

### preview

The preview pane.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `previewField` | unstated | yes | yes |  |
| `showPreviewField` | unstated | yes | yes |  |
| `previewState` | unstated | yes | yes |  |

### insideView

The report embedded inside another form.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `insideViewActive` | unstated | yes | yes |  |
| `insideViewHeight` | unstated | yes | yes |  |
| `insideViewRelatedField` | unstated | yes | yes |  |
| `listEditView` | unstated | yes | yes |  |

### behaviour

Runtime behaviour that is not presentation.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `immediateExecute` | unstated | yes | yes |  |
| `sharedScope` | unstated | yes | yes |  |
| `logExecutions` | unstated | yes | yes |  |
| `preserveUserViewState` | unstated | yes | yes |  |
| `disableOptimizeForDisplay` | unstated | yes | yes |  |
| `dontUseChildParentReport` | unstated | yes | yes |  |
| `selfReferencingField` | unstated | yes | yes |  |

### tree

Tree-shaped reports.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `treeAutoOpenLevels` | unstated | yes | yes |  |

### parameters

Operator-supplied parameters.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `parameters` | unstated | yes | yes |  |
| `parameterPanelHeight` | unstated | yes | yes |  |

### composition

Reports built from other reports.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `subReports` | unstated | yes | yes |  |

### other

No grouping could be justified from the name alone.

| property | kind | on create | on update | reference to |
|---|---|---|---|---|
| `forum` | unstated | yes | yes |  |
| `commandDisplayMode` | unstated | yes | yes |  |
| `alternateEditObjectColumn` | unstated | yes | yes |  |

## Properties whose value kind the contract does not state

80 of the writable properties were registered through `RegisterWritableSet`, which records the name but no value kind. For these the contract proves *that* they may be written, not *what* a valid value looks like. See `report-shapes.json` for the ones an artifact happens to show, and `MISSING-FROM-DIST.md` for the rest.

`additionalWhere`, `allowAddNew`, `allowAddToList`, `allowEdit`, `allowGridColumnSort`, `allowInlineEdit`, `allowRemove`, `allowRemoveFromList`, `allowView`, `alternateEditObjectColumn`, `alternateRootTable`, `alternateRowMode`, `autoInlineEdit`, `calendar`, `columns`, `commandDisplayMode`, `condition`, `customSql`, `description`, `disableColumnHeaders`, `disableOptimizeForDisplay`, `dontExecuteCount`, `dontUseChildParentReport`, `extraQueryTemplate`, `formatConditions`, `forum`, `freeColumnSizing`, `gridCustomKey`, `gridGrouping`, `gridHideColumnsWhenGrouped`, `gridHideLines`, `gridLines`, `gridShowGroupBox`, `gridShowSelectionChecks`, `gridViewStyle`, `grouping`, `hideHeader`, `hideRowIcon`, `hideToolbar`, `ignoreAdvancedSecurityCondition`, `ignoreColumns`, `immediateExecute`, `includeDeleted`, `insideViewActive`, `insideViewHeight`, `insideViewRelatedField`, `isDistinct`, `joinAliases`, `listEditView`, `logExecutions`, `matrix`, `name`, `oracleHint`, `pageSize`, `pagingType`, `parameterEntity`, `parameterPanelHeight`, `parameters`, `preserveUserViewState`, `previewField`, `previewState`, `reportType`, `rootTableAlias`, `selfReferencingField`, `sharedScope`, `showPreviewField`, `showRecordSignFormatting`, `showRowNumber`, `showWpfChart`, `sorting`, `sqlGrouping`, `subReports`, `systemId`, `top`, `treeAutoOpenLevels`, `treeCondition`, `typeView`, `useAdvancedAccess`, `useHierarchyConditionForRoot`, `useSummaryRow`

## Writer

Every writable property above is applied by `AiReportModel.ApplyReportPatch`.
