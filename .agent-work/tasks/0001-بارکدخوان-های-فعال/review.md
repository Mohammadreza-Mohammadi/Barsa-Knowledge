# داوری — task 0001

تصمیم: **approved**.

`verify.json` که Manager مستقل ساخته، هر پنج گیت را پاس اعلام کرده. ستون‌های
زیر از خودِ `change-batch.json` نقل شده‌اند، نه از `implementation-report.md`.

## Acceptance Criteria

| AC | verdict | basis |
|---|---|---|
| AC-1 | pass | `changes[0].parent` = `{objectType: entity, selector: "#BarcodeReader"}`؛ و `properties` هیچ کلید `entity` یا `system` ندارد |
| AC-2 | pass | `changes[0].properties.name` = «بارکدخوان‌های فعال» |
| AC-3 | pass | `columns[0].field` = `#Value`، `columns[1].field` = `#Camera` — به همین ترتیب |
| AC-4 | pass | `properties.condition` = `{"all": []}` |
| AC-5 | pass | `properties.immediateExecute` = `true` |
| AC-6 | pass | `properties.reportType` = `"list"` |

## Caseهای tests.md

| Case | verdict | basis |
|---|---|---|
| T-1 | pass | `changes` طولش ۱ است |
| T-2 | pass | همان basis AC-1 |
| T-3 | pass | همان basis AC-2 |
| T-4 | pass | همان basis AC-3 |
| T-5 | pass | همان basis AC-4 |
| T-6 | pass | همان basis AC-5 |
| T-7 | pass | همان basis AC-6 |
| T-8 | pass | کلیدهای `properties` دقیقاً: name, reportType, columns, condition, immediateExecute — پنج کلید، هیچ‌کدام بیرون نیاز |

## بررسی‌های اضافه

| check | verdict | basis |
|---|---|---|
| پنج گیت Manager | pass | `verify.json` → `summary.passed: true` |
| resolve شدن `#Camera` | pass | در `selectors.json` همین scope هست، `fieldType: command` |
| ریسک R-1 باز است | partial | اینکه ستون روی فیلد `command` پذیرفته می‌شود Unknown است. این در گیت apply-approval کار انسان است، نه چیزی که داوری بتواند ببندد |
| جای‌گذاری در navigator | partial | عمداً انجام نشده (R-2)؛ با AC تضاد ندارد چون هیچ AC آن را نخواسته |

## چرا approved و نه rejected

هر شش AC با شاهد عینی برآورده شده‌اند و هیچ گیتی رد نشده. دو ردیف `partial`
بالا محدودیت‌های اعلام‌شدهٔ بستهٔ دانش‌اند، نه نقص اجرا — و هیچ‌کدام یک AC را
نقض نمی‌کنند. اگر کاربر جای‌گذاری در منو را لازم داشته باشد، آن یک نیاز تازه
است با یک selector پوشه که انسان می‌دهد.
