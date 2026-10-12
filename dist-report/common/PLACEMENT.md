# Placement in the navigator

> **Source:** dist/index/semantic-contract.json → objectContracts, propertyContracts.folder · dist/index/ai-export-properties.json → enums.Barsa.Meta.FolderType
> **dist commit:** 79df8282d328dd5b18ff6dbcaa105d6e18ffdf79
> **compiled:** 2026-10-12 · **scope:** system=1011413550000000100

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

`kind` is an Enum, writable on create only. The Host's own folder reference names its values, so it is authorable: `page`, `group`, `report`, and nothing else.

**Confidence: Documented** -- the vendor stating the contract, not this compiler inferring it from a binary. Source: `barsa-ai-host/startup/dataexchange/05-report-folder-reference.fa.md`.

It says nothing about *where* the folder goes: reusing an existing parent still needs a selector the resolver does not have. See `MISSING-FROM-DIST.md`.

## The recipe

`common/RECIPES.md` recipe R2 builds the whole path in one wave.
