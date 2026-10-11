# Placement in the navigator

> **Source:** dist/index/semantic-contract.json → objectContracts, propertyContracts.folder · dist/index/ai-export-properties.json → enums.Barsa.Meta.FolderType
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

A report nobody can navigate to is invisible. Creating the report is half the job; the other half is a placement row in the navigator.

## The two folder rows involved

| FolderType | member | meaning here |
|---|---|---|
| 0 | `MainRoot` | the navigator root |
| 3 | `ReportRoot` | the root of the report tree |
| 9 | `Report` | a placement of one report |
| 12 | `ReportFolder` | the container folder |

Use the member name, not the number. Both are in dist/ and the name is harder to get wrong.

## Order inside the batch is Verified

`report` has structuralOrder 120 and `folder` has 130, so the report is created first and the folder refers to it. The planner sorts by dependency regardless, but writing the commands in this order matches what it will do.

## What may be written on a folder

| property | classification | kind | on create | on update | runtime source |
|---|---|---|---|---|---|
| `$type` | ReadOnly | Enum | no | no | `AiSemanticV15ExportPostProcessor semantic object discriminator` |
| `entity` | Writable | Reference | yes | yes | `Folder.ContainingTypeDefId` |
| `icon` | Writable | Scalar | yes | yes | `Folder.FolderIcon` |
| `kind` | Writable | Enum | yes | no | `Folder semantic kind` |
| `name` | Writable | Scalar | yes | yes | `Folder.Name` |
| `order` | Writable | Ordering | yes | yes | `Folder.OrderNo` |
| `report` | Writable | Reference | yes | yes | `Folder.ReportId` |

`report` is a Reference to a report, and `order` carries ordering semantics, so sibling order is writable.

`kind` is an Enum, writable on create only, and its value vocabulary is **Unknown**: no dist/ document lists the strings the semantic side uses for a folder kind. The recipes omit it. If the server requires it, it has to come from outside this pack.

## The two-command recipe

`common/RECIPES.md` recipe R2. One caution carried from there: the parent folder is named by a selector. Observed exports carry navigation paths but no folder selectors, and the inspected SemanticRules resolver has no folder case. See `MISSING-FROM-DIST.md`.
