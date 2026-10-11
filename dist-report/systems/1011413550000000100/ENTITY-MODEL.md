# Entity model: system 1011413550000000100

> **Source:** dist/index/systems/1011413550000000100/semantic.json
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

Entities and fields in this system, as dist/ carries them. The selector column is the one that matters for authoring: it is what a batch uses to name the object. Copy it, do not type it -- see `../../common/SELECTORS.md` on the Arabic/Persian letter forms.

## Entities

| caption | selector | db name | in AiExport | in legacy |
|---|---|---|---|---|
| BarcodeReader | `#BarcodeReader` | `dyn_244` | yes | yes |
| بازدید گیت | `#بازدید گیت` | `dyn_246` | yes | yes |
| تنظیمات بارکدخوان | `#تنظیمات بارکدخوان` | `dyn_262` | yes | yes |
| گیت | `#گیت` | `dyn_247` | yes | yes |

## Fields

| entity | caption | selector | type | usable as a column |
|---|---|---|---|---|
| BarcodeReader | Value | `#Value` | string | yes |
| BarcodeReader | Camera | `#Camera` | command | yes |
| BarcodeReader | فرمت | `#فرمت` | enum | yes |
| بازدید گیت | بارکدخوان | `#بارکدخوان` | customField | yes |
| بازدید گیت | گيت | — none | **Unknown** | no |
| بازدید گیت | توضیحات | `#توضیحات` | string | yes |
| تنظیمات بارکدخوان | فرمت | `#فرمت` | enum | yes |
| گیت | عنوان | `#عنوان` | string | yes |

`usable as a column` means only that the field has a selector, so a batch *can* name it. Whether its type may be a column is **Unknown** -- see `../../common/COLUMNS-AND-FIELDS.md`.

A field with no selector is in the legacy export only. It exists, but nothing in this pack can refer to it.

1 of 8 fields have no known type: the legacy export hides the type inside an undecoded `FieldInfo` blob, and only an AiExport artifact states it outright.

## Reports that already exist

Useful as update or delete targets, and as examples.

| name (AiExport) | selector | reportType (AiExport) | name (legacy) | reportType (legacy enum value) |
|---|---|---|---|---|
| BarcodeReaders | `#BarcodeReaders` | list | BarcodeReaders | 0 |
| بازدید گیت ها | `#بازدید گیت ها` | list | بازديد گيت ها | 0 |
| گیت ها | `#گیت ها` | list | گيت ها | 0 |

The two name columns are not always the same string. A legacy export and an AiExport can spell the same object with different Arabic and Persian letter forms, and the selector follows the AiExport spelling. **Never build a selector from a name column** -- copy the selector itself.

The two reportType columns are two different vocabularies: a string on the AiExport side, the numeric ReportTypeEnum value on the legacy side. See `../../common/REPORT-TYPES.md`; the mapping between them is Inferred.

## Views

A `form` report names a view through `typeView`.

| name | selector |
|---|---|
| نمای 1 | `#نمای 1` |
| نمای اصلی | `#نمای اصلی` |

## Navigation folders

`path` is an observed navigation location for retrieval. It is not a supported AiChangeBatch selector.

| name | kind | path | selector |
|---|---|---|---|
| سيستم باركد | **Unknown** | -100-101-126- | unresolved |
| پايه | **Unknown** | -100-101-126-127- | unresolved |
| باركد | **Unknown** | -100-101-126-127-128- | unresolved |
| Test | **Unknown** | -100-101-126-127-141- | unresolved |
| پایه | **Unknown** | پایه | unresolved |
| Test | **Unknown** | پایه/Test | unresolved |
| بارکد | **Unknown** | پایه/بارکد | unresolved |
