# قابلیت‌های پیش‌فرض Dynamic Command

## وضعیت

- نوع: Host Built-in Capability Knowledge
- membership فقط از آخرین Excel `تعریف دستور پویا`
- raw code فقط evidence است.
- Runtime IDs authority نیستند.
- identity اصلی semantic است.

---

## Definition registration resolution

Dynamic Command Change همان Definition خوانای واقعی را حمل می‌کند:

```json
{
  "definition": "نمایش پیغام"
}
```

Plan از relation metadata `دستور پويا.تعريف دستور → TargetTypeId` family واقعی Definition را به‌دست می‌آورد و Central Infrastructure Registration Resolver عنوان `definition` را در Default String Field همان family به Runtime Id تبدیل و cache می‌کند. `فرم ويرايش` همان registration، Settings TypeDef را تعیین می‌کند. Apply فقط binding resolved را مصرف می‌کند و Definition را دوباره search نمی‌کند.

- Runtime ID در Knowledge/Change hard-code نمی‌شود.
- GlobalId در این مسیر استفاده نمی‌شود.
- symbolic capability key جداگانه ساخته نمی‌شود.
- Caption برای lookup record داخل family صحیح استفاده می‌شود، اما behavior discriminator Writer نیست.

# 1. مدل

```text
Dynamic Command Definition = reusable capability registration
Dynamic Command = usage
Settings object = usage configuration
```

Wiring observed:

```text
MetaCommand / supported parent
-> Dynamic Command usage
   -> Definition
   -> Settings object
```

---

# 2. Selection boundary

Dynamic Command برای behavior command/UI/metadata است.

اگر outcome یک Workflow step است، ابتدا Workflow mechanism بررسی شود.

اگر outcome navigation ثابت بدون action اجرایی است، navigation/page wiring عادی ترجیح دارد.

---

# 3. Catalog فعلی

## اجرای گزارش

Purpose:
باز/اجرای Report انتخاب‌شده.

Settings Entity:
`دستور-اجرای گزارش`

Semantic parameters:
- `انتخاب گزارش`
- `اجرا در فرم مستقل`

Behavior:
در Win/Web گزارش را resolve و نمایش می‌دهد؛ می‌تواند popup یا container اصلی باشد.

Use when:
command باید Report مشخصی را نمایش/اجرا کند.

Do not use when:
هدف چاپ، Excel export یا dispatch یک MetaCommand است.

---

## اجرای دستور

Purpose:
dispatch/reuse کردن یک `MetaCommand` موجود.

Settings Entity:
`دستور-اجرای دستور`

Parameter:
- `انتخاب دستور` -> MetaCommand

Use when:
behavior مطلوب از قبل به‌صورت Command canonical موجود است.

Do not use when:
می‌خواهیم behavior جدیدی را پشت یک Command دیگر پنهان کنیم.

---

## اجرای فرآیند

Purpose:
شروع یک Workflow Definition از UI command context.

Settings Entity:
`دستور-اجرای فرآیند`

Semantic parameter:
- `فرآیند` -> Workflow Definition

Sample note:
در sample مقدار `فرآیند` خالی بود چون هنوز Workflow ساخته نشده بود؛ این نقص sample است، نه schema.

Use when:
action UI باید یک Workflow مشخص را start کند.

---

## نمایش پیغام

Purpose:
محاسبه و نمایش پیام به User.

Settings Entity:
`دستور-نمایش پیغام`

Parameter:
- `فرمول` / expression تولید message

Use when:
command فقط باید message محاسبه‌شده نشان دهد.

Do not use when:
validation باید operation را enforce/block کند؛ message جای Rule/Validation نیست.

---

## چاپ

Purpose:
چاپ یا preview یک Report با استفاده از parent object به‌عنوان parameter context.

Settings Entity:
`دستور-چاپ`

Semantic parameters:
- `گزارش` -> Report
- `پیشنمایش` -> bool

Use when:
command باید print/preview report انجام دهد.

Do not use when:
فقط نمایش گزارش یا export لازم است.

---

## اجرای کد منطق کاری

Purpose:
اجرای logic کدنویسی‌شده روی parent object.

Settings Entity:
`دستور-اجرای کد منطق کاری`

Parameter:
- `کد`

Rule:
code fallback است.

Use when:
هیچ capability declarative مناسب behavior را پوشش نمی‌دهد.

Do not use when:
Report, existing Command, navigation, workflow start یا capability تخصصی موجود است.

---

## اجرای کد واسط کاربری

Purpose:
اجرای code UI-specific برای Win/Web.

Settings Entity:
`دستور-اجرای کد واسط کاربری`

Semantic parameters:
- `کد ویندوز`
- `کد وب`

Use when:
behavior واقعاً platform-specific UI scripting لازم دارد.

---

## نمایش صفحه زیرسیستم

Purpose:
بازکردن/انتخاب یک Subsystem context به‌عنوان action.

Settings Entity:
`دستور-نمایش صفحه زیرسیستم`

Parameter:
- `زیرسیستم`

Use when:
command اجرایی باید User را به Subsystem ببرد.

Do not use when:
navigation ثابت عادی کافی است.

---

## ایجاد مشابه

Purpose:
ساخت object مشابه object جاری.

Settings Entity:
`دستور-ایجاد مشابه`

Parameter:
- `نوع` -> mode of clone/create-like

Observed behavior:
یک mode از create-like CRUD استفاده می‌کند و mode دیگر clone از DataExchange helper.

Use when:
Design صریحاً clone/create-similar action می‌خواهد.

Do not use when:
new object ساده بدون copy semantics کافی است.

---

## خروجی به Excel

Purpose:
اجرای Report با parent context و export نتیجه به فایل Excel-compatible output؛ در Win امکان open خودکار نیز دارد.

Settings Entity:
`دستور-خروجی به Excel`

Semantic parameters:
- `گزارش`
- `باز شدن خودکار فایل` (در Win)

Use when:
action صریح export report/data to Excel می‌خواهد.

Do not use when:
صرف نمایش یا چاپ report است.

---

## نمایش گزارش خارجی

Purpose:
گرفتن URL گزارش خارجی برای object جاری و بازکردن آن.

Settings Entity:
`دستور-نمایش گزارش خارجی`

Semantic parameter:
- `تعریف صفحه`

Use when:
report خارج از report renderer معمول Platform و از طریق external URL/page integration نمایش داده می‌شود.

---

## اجرای فرآیند - فرم ساده

Purpose:
شروع Workflow از parent object فعلی و استفاده از User جاری به‌عنوان starter.

Settings Entity:
`دستور-اجرای فرآیند - فرم ساده`

Semantic parameter:
- `فرآیند` -> Workflow Definition

Behavior:
parent object به‌عنوان start object استفاده می‌شود.

Use when:
روی یک form/object موجود، action باید Workflow را با همان object start کند.

Do not use when:
start object/context لازم نیست؛ آنجا `اجرای فرآیند` عمومی مناسب‌تر است.

---

# 4. Quick selection

| Need | Semantic-fit capability |
|---|---|
| show/run report | اجرای گزارش |
| dispatch existing command | اجرای دستور |
| start workflow without parent-start semantics | اجرای فرآیند |
| start workflow from current form/object | اجرای فرآیند - فرم ساده |
| show calculated message | نمایش پیغام |
| print/preview report | چاپ |
| export report/data | خروجی به Excel |
| open subsystem by action | نمایش صفحه زیرسیستم |
| clone/create-similar | ایجاد مشابه |
| external report integration | نمایش گزارش خارجی |
| custom business code | اجرای کد منطق کاری |
| custom UI code | اجرای کد واسط کاربری، فقط وقتی requirement واقعاً UI-specific code می‌خواهد |

---

# 5. ساخت Usage

```text
Need
-> select Definition semantically
-> resolve Settings Entity
-> create Dynamic Command usage
-> attach Parent
-> create Settings object
-> set semantic parameters
-> attach Settings
-> read-back / verify
```

Settings Entity و Field contract لازم‌اند چون Settings object باید واقعاً ساخته شود.

---

# 6. Identity

Knowledge باید بگوید:

```text
registry:تعریف-دستور-پویا/item:<عنوان>
system:<system>/entity:<settings-entity>
```

Runtime numeric ID فقط هنگام Build resolve می‌شود.

GlobalId در resolution این capabilityها استفاده نمی‌شود. Runtime numeric ID فقط به‌صورت targeted هنگام Plan از family + caption واقعی resolve می‌شود.
