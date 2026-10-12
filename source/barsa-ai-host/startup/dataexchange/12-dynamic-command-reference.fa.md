# Dynamic Command Writer — DataExchange Exact Contract (v130)

این سند contract فنی create/read-back **Dynamic Command usage** را تعریف می‌کند. capability membership از Host Infrastructure Capability Knowledge می‌آید؛ Writer catalog جدید crawl نمی‌کند و `تعريف دستور پويا` registration جدید نمی‌سازد.

## Object graph

```text
MetaCommand
→ دستور پويا [usage]
   ├─ تعريف دستور → existing Dynamic Command Definition registration
   ├─ تنظيمات → usage-specific Settings MetaObject
   └─ پدر → MetaCommand
```

Runtime numeric IDهای fixture portable نیستند. `definition` همان registration caption خوانای Knowledge است. Plan از relation metadata `دستور پويا.تعريف دستور → TargetTypeId` family واقعی deployment را پیدا می‌کند و Central Resolver با Default String Field + DB lookup محدود + `FixFarsiText` آن را به Runtime ID resolve/cache می‌کند؛ سپس Settings Entity واقعی از `فرم ويرايش` همان registration می‌آید. Apply همین immutable resolved set را مصرف می‌کند و Definition را دوباره search نمی‌کند. Runtime ID و GlobalId در Knowledge/Change ذخیره نمی‌شوند.

## Semantic Change

`objectType:"dynamicCommand"`, create-only در v130.

### Parent System — create MetaCommand + usage

```json
{
  "operation":"create",
  "objectType":"dynamicCommand",
  "tempId":"show-message",
  "parent":{"objectType":"system","tempId":"sys"},
  "properties":{
    "name":"نمایش پیام ثبت",
  "definition":"نمایش پیغام",
    "parameters":{"فرمول":"return \"ثبت شد\";"}
  }
}
```

اگر Parent `system` باشد `properties.name` caption Parent MetaCommand است و Writer همان Parent را می‌سازد.

### Existing MetaCommand parent

```json
{
  "operation":"create",
  "objectType":"dynamicCommand",
  "parent":{"objectType":"metaCommand","id":123},
  "properties":{
    "definition":"اجرای کد منطق کاری",
    "parameters":{"کد":"return 0;"}
  }
}
```

## Generic supported usage pattern

برای Definition انتخاب‌شده توسط Agent از Capability Knowledge:

```text
resolve existing Definition registration by semantic caption
→ Definition.فرم ويرايش → Settings TypeDef
→ create usage-specific Settings object of that TypeDef
→ set requested Settings parameters (scalar or typed references)
→ create دستور پويا usage
→ usage.تعريف دستور = registration.Id
→ usage.تنظيمات = settings.Id
→ usage.پدر = parent MetaCommand.Id
→ persist
→ read-back verify Definition + Settings Entity + parameters + parent
```

این support generic در **write mechanism** است؛ selection/membership همچنان از catalog Host می‌آید و Writer Definitionهای business را crawl نمی‌کند.

## نمونه‌های پوشش‌داده‌شده

### نمایش پیغام

```json
{
  "definition":"نمایش پیغام",
  "parameters":{"فرمول":"return \"ثبت شد\";"}
}
```

برای این Definition، `فرمول` non-empty در validation الزامی است.

### اجرای کد منطق کاری

```json
{
  "definition":"اجرای کد منطق کاری",
  "parameters":{"کد":"return 0;"}
}
```

برای این Definition، `کد` non-empty در validation الزامی است.

### اجرای فرآیند

```json
{
  "definition":"اجرای فرآیند",
  "parameters":{
    "فرآیند":{"objectType":"workflow","tempId":"workflow-to-start"}
  }
}
```

Relation parameterها با typed reference / tempId targeted resolve می‌شوند؛ numeric ID نمونه hard-code نمی‌شود. اگر Settings Entity یک context field اضافی مثل `زیرسیستم` داشته باشد فقط وقتی Design/Capability contract آن را نیاز دارد ارسال می‌شود؛ omission به‌معنی ساخت مقدار حدسی نیست.

همین mechanism برای سایر Definitionهای catalog که `فرم ويرايش` معتبر دارند و پارامترهایشان در Capability Knowledge مشخص است قابل استفاده است، مانند اجرای گزارش، اجرای دستور، چاپ و UI-code commandها.

## Verify

Verifier usage را از `realId/tempId` read-back می‌کند و حداقل این موارد را مقایسه می‌کند:

- usage metadata type = `دستور پويا`؛
- Definition caption = requested semantic definition؛
- Settings TypeDef = `Definition.فرم ويرايش`؛
- تمام parameterهای درخواست‌شده، شامل typed references، با read-back match باشند؛
- parent MetaCommand واقعی وجود داشته باشد؛
- Parent System/MetaCommand wiring با request match باشد.

## UI attachment boundary

این contract فقط object graph `MetaCommand + Dynamic Command Usage + Settings` را می‌سازد. اتصال MetaCommand به Command Field/View/UI surface contract دیگری است. اگر Source/DX جدا برای آن attachment وجود نداشته باشد Writer format حدسی نمی‌سازد؛ Usage/Settings ساخته‌شده همچنان capability مستقل supported است و UI attachment به‌صورت `blocked/unverified` در outcome می‌ماند.

## v130 regression fixtures


وجود fixture یا parse موفق JSON به‌تنهایی Runtime PASS نیست.
