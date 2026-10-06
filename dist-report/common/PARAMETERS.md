# Parameters

> **Source:** dist/index/semantic-contract.json → propertyContracts.report · dist/index/write-pipeline.json · dist/formats/ai-export-single-json.md → Observed paths
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

Parameters exist, are referenced, and are not authorable from this pack. The short version:

|  | status |
|---|---|
| that a report can have parameters | **Verified** |
| that parameters are referenced and normalized on verify | **Verified** |
| the key set of a parameter entry | **Observed** |
| the semantics of those keys | **Unknown** |
| the value vocabulary of `kind` and `sourceOperator` | **Unknown** |
| the parameter panel layout | **declared out of scope** |

## Writable, per the contract

`parameters`, `parameterEntity` and `parameterPanelHeight` are writable on create and update. `parameterLayout` is ReadOnly, with the contract's declared reason: *"Report parameter XML layout is out of Semantic v15 reconstruction scope in v190"*.

## Referenced, per the pipeline

The verifier carries `BuildReportParameterIdMap` and `NormalizeReportParameterReferences`, which only make sense if parameters are referred to by identity elsewhere in the report and have to be renumbered after a write. `ReportParametersPatchMatches` then checks the result.

## The observed key set

| key | types | times seen | nullable |
|---|---|---|---|
| `parameters` | array | 7 | no |
| `parameters[*]` | object | 12 | no |
| `parameters[*].caption` | string | 12 | no |
| `parameters[*].code` | string | 2 | no |
| `parameters[*].contextValue` | string | 3 | no |
| `parameters[*].external` | boolean | 3 | no |
| `parameters[*].field` | string | 7 | no |
| `parameters[*].input` | boolean | 3 | no |
| `parameters[*].kind` | string | 3 | no |
| `parameters[*].name` | string | 12 | no |
| `parameters[*].sourceOperator` | string | 5 | no |
| `parameters[*].value` | object | 1 | no |
| `parameters[*].value.unsupported` | boolean | 1 | no |
| `parameters[*].value.warning` | string | 1 | no |
| `parameters[*].valueFieldInfoType` | number | 3 | no |

Two of those keys deserve attention: `value.unsupported` (boolean) and `value.warning` (string). The exporter itself marks a parameter value it could not represent. So some parameter values are known to be outside what the semantic projection can carry -- which means a round trip through this format is not guaranteed to preserve them.

**This key set is not a specification.** It is what two systems happened to contain. What `kind` accepts, how `sourceOperator` relates to a condition's `operator`, whether `external` and `input` are independent, and which keys are required are all **Unknown**.

**Therefore: do not author `parameters`.** Decision: parameter shape stays Unknown until an artifact or the patch writer says otherwise. Create the report without parameters and let a human add them.
