# نقشهٔ پیاده‌سازی

## یک فرمان، نه بیشتر

این نیاز با **یک** فرمان `create` روی `objectType: report` تمام می‌شود. هیچ
فرمان دومی لازم نیست، و عمداً هم اضافه نمی‌شود:

- جای‌گذاری در navigator (یک `folder` با `report`) **داخل این تسک نیست**، چون
  `dist-report/MISSING-FROM-DIST.md` بند ۱ می‌گوید در `dist/` هیچ selector
  پوشه‌ای وجود ندارد. بدون selector والد، آن فرمان قابل نوشتن نیست و گیت
  `selectors` آن را رد می‌کند. این یک تصمیم است، نه فراموشی: اگر کاربر
  جای‌گذاری بخواهد، یک تسک جدا با selector پوشه که انسان می‌دهد.

## شیء هدف و selectorها

از `systems/1011413550000000100/index/selectors.json` کپی شده‌اند، تایپ نشده‌اند:

| نقش در نیاز | selector | نوع فیلد |
|---|---|---|
| موجودیت هدف | `#BarcodeReader` | entity، dbName `dyn_244` |
| ستون «مقدار بارکد» | `#Value` | string |
| ستون «دوربین» | `#Camera` | command |

نکتهٔ `#Camera`: نوع فیلدش `command` است، نه یک فیلد دادهٔ ساده. بستهٔ دانش
(`COLUMNS-AND-FIELDS.md`) می‌گوید **اینکه کدام نوع فیلد می‌تواند ستون شود
Unknown است** — پس این ردیف یک ریسک شناخته‌شده است، در `risks.md` ثبت شده، و
`tests.md` آن را به‌عنوان یک Case جدا می‌سنجد. حذفش هم نمی‌کنیم: کاربر صریح
«دوربین» را خواست و «Unknown» دلیل حذف نیست، همان‌طور که دلیل حدس هم نیست.

## خودِ فرمان

```text
operation : create
objectType: report
parent    : { objectType: entity, selector: "#BarcodeReader" }
properties:
  name             : "بارکدخوان‌های فعال"
  reportType       : "list"
  columns          : [ {field:"#Value", alias:"مقدار بارکد"},
                       {field:"#Camera", alias:"دوربین"} ]
  condition        : { all: [] }
  immediateExecute : true
```

چرا هر کدام:

- `parent` و نه یک property: `entity` روی گزارش **ReadOnly** است
  (`LIMITS.md`). موجودیت هدف فقط در زمان create و فقط از `parent` می‌آید، و
  بعداً هم با update عوض نمی‌شود. این مستقیماً AC-1 است.
- `reportType: "list"` — واژگان AiExport، نه نام عضو enum. نگاشت `list` به
  `ViewResults` در بسته **Inferred** است؛ ولی آنچه یک batch می‌نویسد همین
  رشتهٔ معنایی است، پس این انتخاب به آن نگاشت وابسته نیست.
- `condition: {all: []}` — شرط خالی، AC-4. غیرخالی نمی‌نویسیم: واژگان عملگر
  Unknown است.
- `immediateExecute: true` — AC-5.
- `columns` به همین ترتیب — AC-3. ترتیب آرایه همان ترتیب ستون‌هاست.

## چه چیزی عمداً نوشته نمی‌شود

`parameters`، `parameterEntity`، `pagingType`، `allow*`، `typeView`. هیچ‌کدام
در نیاز نیست و هر property اضافه یک تصمیم اعلام‌نشده است.

## scope

```text
entity:#BarcodeReader          خواندنی، والد فرمان
report:#بارکدخوان‌های فعال      شیئی که ساخته می‌شود
```

باریک‌ترین مجموعهٔ لازم. `report:*` نوشته نشده چون کل گزارش‌های سیستم را قفل
می‌کرد.
