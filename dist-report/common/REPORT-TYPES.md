# Report types

> **Source:** dist/index/ai-export-properties.json → enums · dist/models/normalized-samples/ → reports[].reportType
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

Barsa has two report-type vocabularies, and they are not the same words. Getting this wrong is the single easiest way to write a batch that is accepted and wrong.

## The CLR enum

`Barsa.Meta.ReportTypeEnum`, as the embedded export profile spells it out.

| value | member | properties whose names line up (Inferred) |
|---|---|---|
| 0 | `ViewResults` | **Unknown** |
| 1 | `Statistics` | `useSummaryRow`, `grouping`, `sqlGrouping` |
| 2 | `TreeView` | `treeCondition`, `treeAutoOpenLevels`, `useHierarchyConditionForRoot`, `selfReferencingField` |
| 3 | `MatrixView` | `matrix`, `sqlGrouping` |
| 4 | `CalendarView` | `calendar` |
| 5 | `PrintView` | **Unknown** |
| 6 | `HetrogeniousTree` | `treeCondition`, `treeAutoOpenLevels`, `useHierarchyConditionForRoot` |
| 7 | `HetrogeniousTree_NoneGraphical` | `treeCondition`, `treeAutoOpenLevels` |
| 8 | `GauntView` | **Unknown** |
| 9 | `FormView` | `typeView`, `listEditView` |
| 10 | `ForumView` | `forum` |
| 11 | `Dashboard` | `showWpfChart` |

## The AiExport vocabulary

The JSON projection writes its own `reportType` strings. Observed in the supplied artifacts: `form`, `list`.

These are what an `AiChangeBatch` carries, because the batch speaks the semantic vocabulary, not the CLR one.

## The mapping between them is Inferred

The AiExport projection writes its own reportType vocabulary, which is not the CLR enum member names. The mapping below rests on two observations and nothing else.

| AiExport value | CLR candidate | confidence | basis |
|---|---|---|---|
| `list` | `ViewResults` | Inferred | a list-shaped report in both supplied artifacts |
| `form` | `FormView` | Inferred | a report carrying typeView in the Push Notification artifact |

## Corroboration from paired artifacts

3 report ids appear on both sides -- in a legacy artifact and in an AiExport artifact. Each pairing shows the numeric ReportTypeEnum value and the AiExport string the *same report* carried:

| AiExport value | legacy enum value | reports agreeing | example ids |
|---|---|---|---|
| `list` | 0 | 3 | `1011413530000000132`, `1011413530000000133`, `1011413530000000136` |

This is stronger than name resemblance, and it is still not a promotion. Matched by report id across artifacts that are not a same-build pair. A pairing is evidence, not proof: the two sides were exported months apart, so a report could have been edited in between.

What would settle it: a **same-build pair** -- one legacy and one AiExport artifact of the same system exported from the same Barsa build minutes apart. `dist/comparison/golden-pair-protocol.md` says how to produce one. Until then the mapping stays **Inferred**.

Every CLR member not named above has no known AiExport spelling, and every AiExport value not named above is unmapped. A consumer must not derive one from the other by lowercasing a member name: `list` is not a lowercasing of `ViewResults`.

## The type × property matrix is Inferred, and thin

Name correspondence only. No dist/ document states which property applies to which report type; that lives in AiReportChangeProvider.ApplyReportPatch, which has not been decompiled.

So: for any report type, the properties named in the table above are a *guess at relevance from the name*, and every other property's relevance to that type is **Unknown**. Nothing here says a property is rejected for a type -- only that this pack cannot say it is meaningful.
