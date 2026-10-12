# Recipes

> **Source:** dist/index/semantic-contract.json (validated against) · dist/index/write-pipeline.json
> **dist commit:** 79df8282d328dd5b18ff6dbcaa105d6e18ffdf79
> **compiled:** 2026-10-12 · **scope:** system=1011413550000000100

Complete `AiChangeBatch` documents for the common report tasks. Every one below was validated during the build by `barsa_extractor.change_batch.lint` -- the same code path `tools/lint_change_batch.py` runs, against the contract in `dist/index/semantic-contract.json`. The build fails on any error or warning, so a recipe in this file linted clean at compile time.

Scope: system `1011413550000000100`. Placeholders are bound to this system's real selectors where dist/ supplies them.

## Bound selectors

The placeholders below were replaced with real selectors from this scope:

| placeholder | bound to |
|---|---|
| `#<entity>` | `#BarcodeReader` |
| `#<existing-report>` | `#BarcodeReaders` |
| `#<field2>` | `#Camera` |
| `#<field>` | `#Value` |
| `#<system>` | `#بارکد` |
| `#<view>` | `#نمای 1` |

Notes on binding:

- Folder selectors are not bound: the observed navigation paths are identities for retrieval, but the SemanticRules resolver has no folder selector case. A path cannot be used as a batch selector.

## R1 — A list report on an existing entity

The smallest useful report: pick an entity, pick columns, done.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r1-create-report",
      "operation": "create",
      "objectType": "report",
      "parent": {
        "objectType": "entity",
        "selector": "#BarcodeReader"
      },
      "properties": {
        "name": "Gate list",
        "reportType": "list",
        "columns": [
          {
            "field": "#Value",
            "alias": "Title"
          },
          {
            "field": "#Camera",
            "alias": "Notes"
          }
        ],
        "condition": {
          "all": []
        },
        "immediateExecute": true
      }
    }
  ]
}
```

Why it looks like this:

- The target entity is set by `parent`, not by a property. `entity` is ReadOnly on a report, so this is the only way to say which entity the report runs over -- and it cannot be changed afterwards.
- `reportType` uses the AiExport vocabulary (`list`), not the CLR enum member (`ViewResults`). The mapping between them is Inferred; see REPORT-TYPES.md.
- `condition: {"all": []}` is an empty condition. `all` and `any` line up with CombinationOperator. The comparison operator vocabulary is Unknown, so no filled condition is shown.

Lint: 0 error(s), 0 warning(s).

## R2 — A list report, delivered with its navigation

A report nobody can navigate to is invisible. This builds the placement path with it, in one wave.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r2-create-report",
      "operation": "create",
      "objectType": "report",
      "tempId": "tmpReport",
      "parent": {
        "objectType": "entity",
        "selector": "#BarcodeReader"
      },
      "properties": {
        "name": "Gate list",
        "reportType": "list",
        "columns": [
          {
            "field": "#Value",
            "alias": "Title"
          }
        ],
        "condition": {
          "all": []
        }
      }
    },
    {
      "commandId": "r2-create-page",
      "operation": "create",
      "objectType": "folder",
      "tempId": "tmpPage",
      "parent": {
        "objectType": "system",
        "selector": "#بارکد"
      },
      "properties": {
        "name": "Gate",
        "kind": "page",
        "order": 1
      }
    },
    {
      "commandId": "r2-create-group",
      "operation": "create",
      "objectType": "folder",
      "tempId": "tmpGroup",
      "parent": {
        "objectType": "folder",
        "tempId": "tmpPage"
      },
      "properties": {
        "name": "Gate lists",
        "kind": "group",
        "order": 1
      }
    },
    {
      "commandId": "r2-place-report",
      "operation": "create",
      "objectType": "folder",
      "parent": {
        "objectType": "folder",
        "tempId": "tmpGroup"
      },
      "properties": {
        "name": "Gate list",
        "kind": "report",
        "report": {
          "objectType": "report",
          "tempId": "tmpReport"
        },
        "order": 1
      }
    }
  ]
}
```

Why it looks like this:

- The canonical path is System -> Page -> Group -> Report placement, and the Host's folder reference states it. Page and Group are both FolderType.ReportFolder at runtime; the hierarchy carries the semantics, not the runtime type.
- One wave, not four. The planner collects tempIds from `target`, `parent` and recursively from `properties`, so every dependency here is expressible with a temporary reference. Split a batch only when the contract needs a persisted id read back.
- A same-batch reference carries both `objectType` and `tempId`. A bare `{"tempId": ...}` is not the documented shape.
- `kind` is a create-only enum; its values are documented. See common/PLACEMENT.md.
- Page and Group names come from the requirement. The Host does not invent them, so these two are the rows to edit.
- Reuse before you create: if a suitable Page or Group already exists, placing under it needs a folder selector, which this pack still cannot supply. See MISSING-FROM-DIST.md.

Lint: 0 error(s), 0 warning(s).

## R3 — Change the columns of an existing report

The most common edit.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r3-update-columns",
      "operation": "update",
      "objectType": "report",
      "target": {
        "objectType": "report",
        "selector": "#BarcodeReaders"
      },
      "properties": {
        "columns": [
          {
            "field": "#Value",
            "alias": "Title"
          },
          {
            "field": "#Camera",
            "alias": "Notes"
          }
        ]
      }
    }
  ]
}
```

Why it looks like this:

- `columns` is writable on update, so the whole column list is replaced. There is no evidence in dist/ of a per-column patch, so replacing the list is the only form shown.
- The report is addressed by `target`, by selector. `entity` and `system` cannot appear here: both are ReadOnly.

Lint: 0 error(s), 0 warning(s).

## R4 — Delete a report

Included because `report` supports Delete and the shape differs.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r4-delete-report",
      "operation": "delete",
      "objectType": "report",
      "target": {
        "objectType": "report",
        "selector": "#BarcodeReaders"
      }
    }
  ]
}
```

Why it looks like this:

- A delete carries no `properties`. `report` lists Delete among its supported operations, so the operation is available; what it does to the report's placement rows is Unknown.

Lint: 0 error(s), 0 warning(s).

## R5 — A form report over a view

The second reportType actually observed in an artifact.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r5-create-form-report",
      "operation": "create",
      "objectType": "report",
      "parent": {
        "objectType": "entity",
        "selector": "#BarcodeReader"
      },
      "properties": {
        "name": "Gate form",
        "reportType": "form",
        "typeView": "#نمای 1",
        "condition": {
          "all": []
        }
      }
    }
  ]
}
```

Why it looks like this:

- `reportType: "form"` and a `typeView` selector is the shape the Push Notification artifact shows.
- `typeView` is writable on create and update, and takes a view selector.

Lint: 0 error(s), 0 warning(s).

## R6 — A read-only list report with paging

Shows the permission and paging groups, which are where most of the 80 properties live.

```json
{
  "profileVersion": 15,
  "policy": {
    "errorPolicy": "continueIndependent",
    "ignoreUnsupported": false
  },
  "changes": [
    {
      "commandId": "r6-create-readonly-report",
      "operation": "create",
      "objectType": "report",
      "parent": {
        "objectType": "entity",
        "selector": "#BarcodeReader"
      },
      "properties": {
        "name": "Gate list, read only",
        "reportType": "list",
        "columns": [
          {
            "field": "#Value",
            "alias": "Title"
          }
        ],
        "condition": {
          "all": []
        },
        "allowView": true,
        "allowEdit": false,
        "allowAddNew": false,
        "allowRemove": false,
        "allowGridColumnSort": true,
        "pagingType": "Automatic",
        "pageSize": 50,
        "showRowNumber": true
      }
    }
  ]
}
```

Why it looks like this:

- Every property here is writable on both create and update, so the same body works as an update with `target` instead of `parent`.
- `pagingType` takes a ReportPagingType member; see `index/report-enums.json`.

Lint: 0 error(s), 0 warning(s).

## What happens to a batch after you send it

| stage | entry point | produces |
|---|---|---|
| 1. Structural lint | `BixWriteHelper.ValidateBatch(string)` | a throw, or nothing |
| 2. Parse | `BixWriteHelper.ParseBatch(string)` | AiChangeBatch |
| 3. Plan | `BixWriteHelper.BuildPlan(AiChangeBatch)` | AiChangePlan + AiPlanSummary + AiPlanDiagnostic[] |
| 4. Apply | `BixWriteHelper.ApplyPlan(AiChangePlan)` | AiApplyResult + AiCommandResult[] + AiBatchStatus |
| 5. Mutate | `IAiChangeProvider.Apply(AiSemanticChange, AiBatchExecutionContext)` | AiProviderApplyResult carrying the new RealId |
| 6. Verify | `AiRuntimeVerifier.FinalReadBackAndVerify(plan, result)` | AiRuntimeObject[] on AiApplyResult.RuntimeReadBack, plus per-command VerificationSucceeded |

The pipeline is a change-plan executor, not an importer, and it is deliberately non-atomic: commands that fail are reported per-command and the rest proceed. A batch is therefore not a transaction -- keep batches small enough that partial application is recoverable by hand.
