# Caseهایی که Reviewer باید بسنجد

| Case | چه چیزی | پایهٔ داوری |
|---|---|---|
| T-1 | یک فرمان، `create` روی `report` | `changes` طولش ۱ است |
| T-2 | موجودیت هدف از `parent` می‌آید، نه از property | `changes[0].parent.selector == "#BarcodeReader"` و هیچ `properties.entity` نیست |
| T-3 | نام دقیقاً «بارکدخوان‌های فعال» | `changes[0].properties.name` |
| T-4 | دو ستون، به ترتیب مقدار بارکد سپس دوربین | `changes[0].properties.columns` |
| T-5 | شرط خالی | `condition == {"all": []}` |
| T-6 | اجرای خودکار | `immediateExecute == true` |
| T-7 | نوع گزارش در واژگان AiExport | `reportType == "list"` |
| T-8 | هیچ property ای بیرون نیاز نوشته نشده | فهرست کلیدهای `properties` |

## ردیف‌های regression

این‌ها را در `evidence.additionalChecks` ثبت کن، نه در `testCoverage`:

- هر پنج گیت Manager پاس شده‌اند (`verify.json`)
- selector `#Camera` که نوع فیلدش `command` است، در index همین scope وجود دارد
  — یعنی ارجاع resolve می‌شود. اینکه چنین فیلدی *باید* ستون شود Unknown است و
  ردیف ریسک جداگانه دارد.
