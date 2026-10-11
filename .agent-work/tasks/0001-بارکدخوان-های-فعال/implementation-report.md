# چه چیزی ساخته شد

یک فرمان، دقیقاً همان نقشه. `change-batch.json` یک فرمان `create` روی
`objectType: report` دارد با `parent` روی `#BarcodeReader`.

## از کجا آمد هر مقدار

| کلید | مقدار | منبع |
|---|---|---|
| `parent.selector` | `#BarcodeReader` | کپی از `selectors.json` |
| `columns[0].field` | `#Value` | کپی از `selectors.json` |
| `columns[1].field` | `#Camera` | کپی از `selectors.json` |
| `name` | «بارکدخوان‌های فعال» | AC-2، عیناً از نیاز |
| `reportType` | `list` | واژگان AiExport، `REPORT-TYPES.md` |
| `condition` | `{"all": []}` | AC-4؛ شرط غیرخالی قابل نوشتن نیست |
| `immediateExecute` | `true` | AC-5 |

هیچ selectorی تایپ نشد. هر سه از `selectors.json` کپی شدند، به‌خاطر درهم‌بودن
شکل‌های `ي`/`ی` در این داده‌ها.

## چه چیزی نوشته نشد و چرا

- `parameters` — شکلش Unknown است، گیت `unknowns` ردش می‌کند، و نیاز هم نخواسته.
- `pagingType`, `allowEdit`, `typeView`, … — در نیاز نیست. هر property اضافه یک
  تصمیم اعلام‌نشده است.
- فرمان `folder` برای جای‌گذاری — نقشه (R-2) توضیح داده: `dist/` هیچ selector
  پوشه‌ای ندارد.

## خودسنجی قبل از تحویل

`python3 tools/manager.py verify 0001` اجرا شد و هر پنج گیت پاس شدند؛ همان را
Manager مستقل دوباره اجرا می‌کند و حرف این فایل در آن تصمیم نقشی ندارد.
