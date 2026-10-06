# Columns and fields

> **Source:** dist/formats/ai-export-single-json.md → Observed paths · dist/index/semantic-contract.json → propertyContracts.field · dist/formats/report-format.md
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

A report's columns are the part a consumer changes most, and the one the legacy export cannot see at all.

## The observed shape

```json
{
  "columns": [
    {
      "field": "#<field>",
      "alias": "Heading"
    }
  ]
}
```

| key | types | times seen | nullable |
|---|---|---|---|
| `columns` | array | 11 | no |
| `columns[*]` | object | 149 | no |
| `columns[*].alias` | string | 149 | no |
| `columns[*].field` | string | 149 | no |

`field` is a semantic selector, not an id. It resolves to a FieldDef under the report's own entity. `alias` is the column heading.

Both keys appeared in all 149 observed column rows, so neither is optional in practice -- though the contract does not mark either required.

## Replacing, not patching

`columns` is writable on create and on update, and the value is the whole list. dist/ shows no per-column patch form, so an update that changes one column sends every column.

## Where the columns live on the legacy side

They do not, in any readable form. On the legacy side a report's definition sits inside `met_Report.ReportData`, a binary blob whose decoder (`SerializeReportData`) the Extractor never ran. So a legacy `.metaexport` tells you a report exists and nothing about its columns, and only an AiExport artifact shows them.

## What can be a column

A column names a field, and this pack carries the field catalogue for the scope. Whether every field *subtype* may be a column is **Unknown**: the contract classifies field properties and says nothing about column eligibility, and no artifact in dist/ pairs a column with its field's subtype.

24 field subtypes exist, each with its own properties:

| subtype | own properties | usable as a column |
|---|---|---|
| `binary` | 7 | **Unknown** |
| `bool` | 6 | **Unknown** |
| `code` | 8 | **Unknown** |
| `command` | 8 | **Unknown** |
| `customField` | 3 | **Unknown** |
| `date` | 4 | **Unknown** |
| `enum` | 4 | **Unknown** |
| `file` | 10 | **Unknown** |
| `gauge` | 9 | **Unknown** |
| `int` | 5 | **Unknown** |
| `longText` | 1 | **Unknown** |
| `money` | 6 | **Unknown** |
| `picture` | 2 | **Unknown** |
| `pictureFile` | 3 | **Unknown** |
| `pictures` | 4 | **Unknown** |
| `recordSign` | 3 | **Unknown** |
| `referenceField` | 3 | **Unknown** |
| `refreshCommand` | 1 | **Unknown** |
| `reminder` | 8 | **Unknown** |
| `string` | 13 | **Unknown** |
| `timeSpan` | 5 | **Unknown** |
| `wordFile` | 2 | **Unknown** |
| `wordReportCommand` | 3 | **Unknown** |
| `workCenter` | 3 | **Unknown** |

A relation column -- naming a field reached through a relation rather than on the entity itself -- is **Unknown**. Whether a column may name a field reached through a relation is not stated anywhere in dist/, and no observed column does so provably. Unknown, not unsupported.
