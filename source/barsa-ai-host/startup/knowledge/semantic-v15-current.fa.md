# KM — SystemBuilder Semantic v15

## Semantic v15 — Apply Lifecycle v217 (Authoritative)

- Phase classification از `SemanticContractRegistry.ApplyClass/StructuralOrder` می‌آید، نه `objectType==System` heuristic. objectهای دارای Core metadata provider/persistence اختصاصی (System/Entity/Field/Relation/View/Report/Folder/Workflow/Command/Rule) Hardcoded/Phase 1 هستند؛ `dynamicObject` یعنی Core `MetaObject` row و در Phase 2 است.
- Phase 2 از `dynamicObject` با Core `MetaObject` CRUD پشتیبانی می‌کند: `parent`=Entity و `properties.values` map از Semantic Field selector به value. Metadata/Data reference architecture جدا ساخته نشده و همه relation valueها همان `#` هستند.
- Deferred reference slotهای مستقیم در Phase 1/2 واقعاً Runtime placeholder=`-1` می‌گیرند؛ Ledger علاوه بر مقدار اصلی، `PlaceholderApplied` و dependencyهای Phase 3 را ثبت می‌کند. Structural-identity referenceهایی که Core برای ساخت shell الزاماً نیاز دارد (مثل relation.target) استثنای creation identity هستند، نه deferred reference.
- Phase 3 با dependency graph قراردادی topological اجرا می‌شود و از ترتیب JSON مستقل است؛ نمونه: `report.condition` بعد از `report.parameters` و grouping/sorting بعد از columns. cycle فقط diagnostic می‌دهد و fallback deterministic دارد.
- Deferral از Contract kind/reference lifecycle/value shape استنتاج می‌شود، نه executor property-name allowlist. Complex details، logic، reference و selector-bearing values late-bound هستند.
- Apply در سه Phase اجرا می‌شود: Phase 1 = Hardcoded basic CRUD، Phase 2 = Dynamic objects/data basic CRUD، Phase 3 = consume Deferred Ledger و تکمیل Reference/Logic/Dependent details.
- تنها reference model همان `#Key` / `#[Target]Key` است؛ metadata/data resolver split و `externalData` ممنوع است.
- Text Boundary برای تمام strings بدون استثنا مرکزی است: Semantic=`ی/ک`، Runtime/DB=`ي/ك`.
- Validation و command Verify فقط diagnostic هستند؛ فقط failure واقعی Runtime/Provider/DB Apply error است.
- معیار نهایی reconstruction فقط Fresh Semantic Export(Target) → Canonical Semantic Compare → Reference Semantic است؛ Full فقط developer troubleshooting است.
- Semantic objectهای اصلی self-describing هستند و `$type` canonical انگلیسی دارند (`system/entity/field/relation/view/report/workflow`؛ Navigation JSON در صورت وجود `navigation*`). `$type` فقط object kind است؛ Compose ownership و Navigation placement مستقل‌اند. AiChange همچنان از `objectType` envelope برای dispatch استفاده می‌کند.
- Contract revision: `v15-qtr-v217`.


### `$type` object discriminator

Export جدید روی objectهای اصلی `$type` می‌نویسد تا JSON مستقل از filename/path self-describing باشد. canonical values: `system`, `entity`, `field`, `relation`, `view`, `report`, `workflow`. Field/Relation با `fieldType` subtype خود را نگه می‌دارند. `$type` هیچ ownership/Compose یا Navigation placementی را تعیین نمی‌کند و جای `objectType` در AiChange را نمی‌گیرد.

## Semantic v15 — Contract consolidation v202 (Historical; superseded by v205)

این بخش وضعیت جاری را supersede می‌کند؛ بخش‌های نسخه‌ای قدیمی‌تر فقط Historical هستند.

- `#Key` و `#[Target]Key` تنها مدل canonical برای semantic FK/reference هستند. Data Row و Metadata Object representation جدا ندارند.
- Target ابتدا از Property/FieldInfo/FieldType/`SemanticResolutionContext` استنتاج می‌شود؛ Target داخل selector فقط وقتی لازم است که Context آن را تعیین نکند.
- Dynamic Row با همان Semantic resolver و `TypeDef.GetDefaultFieldOrFirst()` resolve می‌شود. Runtime ID، `sourceRowId` و `dependencyKey` semantic authority نیستند.
- `externalData` یک Semantic v15 reference kind نیست و `externalDataMappings` فقط legacy authored input ممنوع است.
- `0 match` یعنی `UnresolvedSemanticReference`. Writer فقط اگر FieldInfo/SystemBuilder یک empty/sentinel واقعی را مجاز بداند همان مقدار type-aware را می‌نویسد؛ در غیر این صورت خطای command-local می‌دهد. fake row ساخته نمی‌شود.
- Text boundary مرکزی است: Semantic/Application از `ی/ک` و DB/provider payload از `ي/ك` استفاده می‌کند. Plan و Apply از یک Provider payload policy عبور می‌کنند؛ per-feature Unicode normalization ممنوع است.
- Report Parameter: `input` و `notAutoRemove` در صورت absence برابر `false` هستند. `currentUser` یک context parameter است، نه ordinary input parameter.
- Report scalar conditionهای Source-certified فعلی: `equal`, `notEqual`, `greaterThan`, `lessThan`, `greaterThanOrEqual`, `lessThanOrEqual` و برای String/RichString نیز `contains`, `doesNotContain`, `startsWith`, `doesNotStartWith`. operator ناشناخته explicit Unsupported است.
- Formula activation authority فقط FormulaClass/HasFormula است؛ stale AutoCalc MetaCode Formula فعال ایجاد نمی‌کند.
- Navigation order با relative sibling sequence مقایسه می‌شود، نه raw numeric order.
- Runtime fingerprint از binary واقعی Host/DataExchange/Barsa.Meta و `socContractRevision=v15-qtr-v202`, profile 15 و build identity ساخته می‌شود؛ `updateId` hard-coded authority نیست.
## وضعیت مرجع Semantic v15 — shape/export v164 + Runtime reconstruction v174+
### تاریخ دانش: 2026-09-24
### کاربرد: ادامه گفتگو + Knowledge برای Barsa.Ai.Host + مرجع Implementor/Reviewer

Technical contract برای Read/Write/Verify: `dataexchange/13-semantic-v15-reference.fa.md`

> این فایل Source of Truth دانشی جاری برای Semantic v15 است.
> اگر سند یا Prompt قدیمی با این فایل تعارض دارد، این فایل مقدم است مگر اینکه Source code واقعی SystemBuilder خلاف آن را ثابت کند.
> Implementor نباید در موارد بسته‌شده fallback یا قرارداد جدید اختراع کند. در تعارض قطعی با Source باید `STOP/GAP` گزارش شود.

---

# 1. وضعیت جاری در یک نگاه

## نسخه

```text
Semantic profileVersion = 15
v14 = historical / frozen
Semantic shape/export baseline = update-v164
Runtime reconstruction/apply implementation = update-v174+
```

## وضعیت ارزیابی

```text
Code review                 = GO
Real Full/Semantic Export   = GO
Static regression contract  = present
Real Apply on clean Target  = هنوز انجام نشده
Re-export + Semantic Compare= هنوز انجام نشده
```

بنابراین:

> `v164` از نظر Code + Real Export پذیرفته شده است.  
> مرحله باقی‌مانده برای certification نهایی، اجرای واقعی:
>
> `Export → Apply روی Target → Re-export → Semantic Compare`
>
> است.

## Audit واقعی آخرین Export

روی فایل:

```text
تست فرم، تست فيلد، تست گزارش (05-07-02 21;38).zip
```

بررسی شد:

```text
Semantic JSON files                         = 654
Navigation report placements                = 495
Report placements missing report selector   = 0
nested {objectType,selector} semantic refs   = 0
page:n/group:n/placement:n/report:n refs     = 0
parentRef leakage                           = 0
numeric field references found              = 0
known Report child collections with id leak = 0
```

دو blocker نسخه v163 در v164 بسته شدند:

1. Navigation Report placement دیگر `report` selector را از دست نمی‌دهد.
2. BusinessRule condition دیگر Field Runtime ID خام صادر نمی‌کند.

---

# 2. هدف اصلی Semantic v15

هدف ساخت یک representation است که:

- برای AI قابل فهم باشد؛
- به Local Runtime ID وابسته نباشد؛
- بتواند SystemBuilder system را روی Target دیگری بازسازی/اصلاح کند؛
- تا حد قراردادهای پشتیبانی‌شده Round-trip شود؛
- از semantics واقعی Source استفاده کند و behavior حدسی نسازد.

سه مفهوم باید جدا بمانند:

```text
Semantic Identity
= این Object از نظر معنایی چیست؟

Semantic Reference
= این Property به کدام Object معنایی اشاره می‌کند؟

Runtime / Technical Identity
= این Object در DB/Runtime با چه ID فنی ذخیره شده؟
```

در v15:

```text
Semantic Identity / Reference
→ authority برای Semantic Export/Apply

Runtime ID
→ implementation detail
→ semantic authority نیست
```

---

# 3. اصل معماری مرکزی

در DataExchange یک framework مرکزی Semantic داشته باشیم؛ نه دو hierarchy جدا برای Metadata و Data.

مفاهیم اصلی:

```text
SemanticRules
SemanticResolutionContext
SemanticSelectorCodec
SemanticFieldValueConverterRegistry
SemanticValueResolver
```

Metadata در SystemBuilder خودش data-like است؛ بنابراین MetadataResolver و DataResolver مستقل، abstraction مطلوب این پروژه نیست.

Core SystemBuilder FieldInfo/FieldType برای Semantic layer تغییر نکند.

---

# 4. Semantic Context

Semantic Context از execution/batch state جدا است.

حداقل contextهای مفهومی:

```text
System
TypeDef / Entity
ActiveField
FieldType
```

قاعده:

```text
Push context
→ process children/value
→ Pop context
```

Owner TypeDef با Target/Value TypeDef یکی نیست.

برای Report:

```text
Report child context ← Report.TypeDefId
```

`Report.SystemId` design information است، نه driver context و نه جزو Report PK.

---

# 5. Semantic Selector

همه Semantic Referenceها با `#` شروع می‌شوند.

فرم پایه:

```text
#Key
#[Target]Key
#Part1|Part2|Part3
#[TargetPart1|TargetPart2]KeyPart1|KeyPart2
```

مثال:

```text
#پرسنل
#ویرایش پرسنل
#پرسنل|ویرایش پرسنل
#[شهر]تهران
#[منابع انسانی|پرسنل]12345
#[@SplUser]admin
```

Context می‌تواند prefix را حذف کند:

```text
Full:
#منابع انسانی|پرسنل|ویرایش پرسنل

System context:
#پرسنل|ویرایش پرسنل

Entity context:
#ویرایش پرسنل
```

نباید identity را بیش از حد به «path» در برابر «composite key» تقسیم مفهومی کنیم؛ resolver هر object type اجزای selector را تفسیر می‌کند.

---

# 6. Escaping

Contract پایه:

```text
\|  literal pipe
\[  literal [
\]  literal ]
\@  literal leading @ when local
\\  literal backslash
\#  literal # inside selector
```

Leading hash precedence:

```text
#ABC    → selector Key=ABC
##ABC   → literal text #ABC
###ABC  → selector Key=#ABC
####ABC → literal text ##ABC
```

این precedence قبل از generic selector parsing اعمال شود.

## Local index namespace

برای local structural fallback:

```text
~<digits>
```

namespace رزروشده است.

مثلاً:

```text
#~2
```

یعنی local fallback index.

اگر natural key واقعی به شکل `~2` باشد، باید به صورت literal escape/encode شود و با generated index اشتباه نشود.

---

# 7. Reference JSON Shape

وقتی Property نوع target را می‌گوید، wrapper اضافی ممنوع است.

غلط:

```json
"field": {
  "objectType": "field",
  "selector": "#عنوان"
}
```

درست:

```json
"field": "#عنوان"
```

همین قاعده:

```json
"entity": "#پرسنل"
"report": "#گزارش پرسنل"
"view": "#نمای اصلی"
"systemId": "#منابع انسانی"
"target": "#شهر"
```

`selector` یک Property معمولی semantic reference نیست؛ خود string `#...` selector است.

## Heterogeneous collection

وقتی type از Property قابل تعیین نیست:

```json
"selectedRules": [
  "#[businessRule]کنترل مبلغ",
  "#[uniqueConstraint]عدم تکرار کد"
]
```

Target clause معتبر است.

---

# 8. Report identity

Semantic PK گزارش:

```text
ReportName
```

Source fact:

```csharp
ReportBusinessLogic.LoadListByName(name)
```

lookup نام را استفاده می‌کند.

Duplicate behavior طبق contract قبلی:

```text
0 match → Unresolved
1 match → Resolved
>1      → ResolvedWithAmbiguity + Warning + First Match
```

`>1` Round-trip certified نیست.

## Report.SystemId

این property semantic design information است:

```json
"systemId": "#منابع انسانی"
```

اما:

```text
جزو Report PK نیست
resolution را تغییر نمی‌دهد
child context را تعیین نمی‌کند
```

---

# 9. Workflow identity

Source API:

```csharp
WorkflowDef.LoadByTitle(systemName, workflowName)
```

Semantic identity:

```text
SystemName + WorkflowDef.Title
```

---

# 10. Global Entity

فعلاً فقط Entity global concept رسمی دارد.

مثال:

```text
#@SplUser
```

Registry می‌تواند constraint داشته باشد:

```text
@SplUser
→ EntityName = SplUser
→ SystemName = Meta01
```

Resolve باید live باشد؛ preload/cache object نباید semantic authority شود.

---

# 11. Dynamic Row identity

برای Dynamic Row فقط:

```csharp
typeDef.GetDefaultFieldOrFirst()
```

به‌عنوان key field استفاده می‌شود.

این fallback عمومی برای:

```text
Report
Field
Entity
Rule
...
```

نیست.

Supported اولیه:

- scalar-like FieldInfoهایی که converter صریح دارند؛
- calculated stored field وقتی stored value موجود است.

اگر default key field از نوع `SingleRelation` باشد:

```text
Unsupported + Warning
```

و traversal حدسی انجام نشود.

Null key:

```text
Unsupported/Unresolved + Warning
```

Empty string فقط وقتی converter همان FieldInfo آن را مجاز می‌داند.

---

# 12. Relation semantics

هر دو جهت لازم است:

```text
Runtime Row → Semantic Selector
Semantic Selector → Target Runtime Row
```

Standard relation:

```text
#تهران
```

General Relation که target از Field معلوم نیست:

```text
#[شهر]تهران
```

Cross-system:

```text
#[منابع انسانی|پرسنل]12345
```

Global:

```text
#[@SplUser]admin
```

Semantic layer از Report single-column override قدیمی UI برای relation identity استفاده نمی‌کند.

Target key از Target TypeDef و `GetDefaultFieldOrFirst()` می‌آید.

---

# 13. User / CreatorUser

Target از field semantics معلوم است (`SplUser`).

پس value فقط:

```json
"value": "#admin"
```

باشد؛ type/target اضافی تکرار نشود.

---

# 14. FieldItem traversal

FieldItem با Semantic identity path یکی نیست.

Source model:

```csharp
FieldItem
{
    FieldDefEx FieldDefEx;
    FieldItem ParentItem;
    ...
}
```

FieldItem می‌تواند semantics traversal مثل relation/reverse/join/aggregate داشته باشد.

بنابراین این کار غلط است:

```text
FieldItem chain
→ #A|B|C
```

Canonical:

Direct field:

```json
"field": "#عنوان"
```

Chain:

```json
"field": {
  "items": [
    "#استان",
    "#شهر",
    "#عنوان"
  ]
}
```

اگر segment semantics اضافه دارد، همان segment object باشد و فقط propertyهای Source-confirmed حفظ شوند.

`path` shape قدیمی DataExchange canonical نیست.

---

# 15. SelfFieldDefEx

Self یک Field واقعی با Runtime ID نیست.

Condition:

```json
{
  "field": {
    "self": true
  },
  "operator": "equal",
  "parameter": "#{خود}"
}
```

Parameter definition:

```json
{
  "name": "{خود}",
  "self": true
}
```

`name="{خود}"` به تنهایی marker semantic نیست؛ Implementor نباید از اسم Self را حدس بزند.

Self داخل chain:

```json
"field": {
  "items": [
    "#رابطه عکس",
    {
      "self": true
    }
  ]
}
```

ممنوع:

```text
field = 0
Runtime ID placeholder
```

---

# 16. Report Parameter

Reference مستقیم:

```json
"parameter": "#تاریخ"
```

Source فعلی Name uniqueness را enforce می‌کند:

```text
Name non-empty
Name unique inside Report
```

پس:

```text
Parameter local key = Name

empty     → Error
duplicate → Error
```

برای Parameter `~index` fallback نداریم.

این تصمیم جایگزین proposal قبلی `~index` برای Parameter شده است.

---

# 17. Report Column identity

Column یک local child همان Report است.

Source Runtime ID حذف می‌شود.

Local key priority:

```text
1. explicit Alias اگر usable باشد
2. semantic caption/display متناظر ستون
3. اگر خالی/duplicate بود → ~index
```

تکرار Caption/Alias در عمل نادر و غالباً اشتباه طراحی است، اما Source آن را قطعی منع نمی‌کند؛ به همین دلیل fallback محدود index حفظ شده است.

مثال:

```json
"columns": [
  { "alias": "ردیف", "caption": "ردیف" },
  { "caption": "مبلغ" },
  { "caption": "مبلغ" }
]
```

refs:

```text
#ردیف
#~1
#~2
```

## شرط اعتبار `~index`

Canonical `columns[]` order باید در:

```text
Export → Apply → Re-export
```

پایدار باشد.

اگر ترتیب بدون semantic reason تغییر کرد و refs جابه‌جا شدند:

```text
STOP / GAP
```

Runtime ID fallback ساخته نشود.

---

# 18. Matrix و Report-local refs

Runtime child object/raw ID نباید صادر شود.

مثال نهایی:

```json
"matrix": {
  "horizontalColumn": "#ردیف",
  "verticalColumn": "#ستون",
  "valueColumn": "#مقدار"
}
```

یا:

```json
"valueColumn": "#~2"
```

همین برای:

```text
alternateEditObjectColumn
```

و سایر refs محلی Source-confirmed.

---

# 19. Report child Runtime IDs

Source IDs نباید روی Target assign شوند.

حداقل:

```text
columns
groups
parameters
joinAliases
conditions
formatConditions
structural children
```

قاعده:

```text
Export source child id → omit
Apply source child id  → never assign
```

آخرین export v164 برای collectionهای شناخته‌شده بالا ID leakage نداشت.

---

# 20. BusinessRule / UniqueConstraint

Definition discriminator:

```json
"type": "businessRule"
```

یا:

```json
"type": "uniqueConstraint"
```

نه:

```json
"objectType": "businessRule"
```

`type` چون definition heterogeneous است معتبر است.

Computed/display `Title` semantic identity نیست و صادر نشود.

---

# 21. Rule semantic key

Scope:

```text
Owner Entity + Rule subtype
```

اگر Caption:

```text
non-empty + unique
```

باشد:

```json
{
  "type": "businessRule",
  "caption": "کنترل مبلغ"
}
```

Ref:

```text
#[businessRule]کنترل مبلغ
```

اگر Caption خالی یا duplicate باشد:

```json
{
  "type": "businessRule",
  "key": "~583921"
}
```

یا:

```json
{
  "type": "businessRule",
  "caption": "کنترل مبلغ",
  "key": "~247105"
}
```

در duplicate set همه اعضا fallback key بگیرند.

---

# 22. Rule fallback hash و GlobalId

در قرارداد جاری پروژه:

```csharp
EorgGlobalIdHelper.GenerateGlobalId(rule.Id)
```

Global identity معتبر/unique SystemBuilder محسوب می‌شود.

ساختار مفهومی:

```text
CenterGlobalId + TypeGlobalId + Sequence
```

Fallback Rule از GlobalId مشتق می‌شود، نه از local Runtime ID خام.

Algorithm:

```text
globalId
→ SHA-256 UTF-8 deterministic
→ decimal digit stream
→ first 6 digits
→ "~" + digits
```

مثال:

```text
~094159
```

در collision:

```text
6 digits → 8 → 10 → ...
```

تا در scope Rule unique شود.

با Caption واقعی نیز collision check شود.

ممنوع:

```csharp
string.GetHashCode()
```

چون transport-stable نیست.

این fallback **Universal UID نیست** و مجوز استفاده GlobalId در همه semantic references نیست.

---

# 23. Rule internal references

Field reference داخل BusinessRule باید semantic باشد:

```json
"field": "#متن"
```

نه:

```json
"field": 1077313510000000311
```

در v164 blocker قبلی raw numeric Field در Rule condition بسته شده است.

---

# 24. Code / SQL / Formula

MetaCode envelope فنی و noise اضافی حذف شود.

وقتی Property semantics را تعیین می‌کند:

```json
"code": "return value;"
"sql": "select ..."
```

و metadataهایی مثل:

```text
id
address
addressInTarget
layer
location
parameterTypeDefId
```

نباید صرفاً به دلیل internal MetaCode model نشت کنند.

## Formula nuance

Formula را کورکورانه به string تبدیل نکنیم اگر Source semantics واقعی دیگری مثل:

```text
executionTime
type / formula kind
```

لازم دارد.

آخرین audit نشان داد Formula در بعضی موارد structured object باقی مانده است. این به‌خودی‌خود bug نیست.

قاعده:

> noise implementation metadata حذف شود، ولی semantics واقعی Formula حفظ شود.

---

# 25. Picture Group

Source fact:

```csharp
PicturesInfo.GroupItem.Id == PicturesInfo.GroupItem.Value
```

Legacy DataConvert Group را بر اساس `Name` match می‌کند.

Semantic:

```json
"groups": [
  {
    "name": "لیست تصاویر-چپ به راست1"
  }
]
```

Source `id/value` حذف شوند.

Identity:

در Field context:

```text
#گروه1
```

در Entity context:

```text
#فیلد تصاویر|گروه1
```

Validation:

```text
Name empty     → Error
Name duplicate → Error
```

هیچ:

```text
Runtime ID
hash
index
```

fallback وجود ندارد.

---

# 26. SystemItemGroup

Synthetic:

```text
group:n
```

حذف شده است.

Semantic definition:

```json
"systemItemGroups": [
  {
    "caption": "فیلد متنی"
  }
]
```

Reference:

```json
"systemItemGroup": "#فیلد متنی"
```

empty/duplicate:

```text
explicit ambiguity/error
```

نه ordinal/Runtime ID fallback.

---

# 27. Navigation — Source-confirmed model

Synthetic navigation IDs حذف شوند:

```text
page:n
group:n
placement:n
report:n
parentRef
```

Hierarchy از nesting می‌آید.

## نکته Source بسیار مهم

در Source فعلی v164، placement target اثبات‌شده فقط:

```text
Report
```

است.

کد validation فعلی نیز `folder.kind` را به:

```text
page
group
report
```

محدود می‌کند و صریحاً می‌گوید View/Entity placement identity هنوز Source-proven نیست.

پس Implementor نباید صرفاً از روی قیاس:

```text
view placement
entity placement
```

را اضافه کند.

اگر بعداً Source واقعی چنین targetی را ثابت کرد، contract توسعه می‌یابد.

---

# 28. Navigation Page / Group identity

برای containers:

```text
Page  → Name within Parent
Group → Name within Parent
```

Duplicate Name در داده واقعی ممکن است رخ دهد و معمولاً خطای طراحی است.

Rule:

```text
0 match → Create
1 match → Update
>1 match → Ambiguity/Error
```

نه First Match و نه Runtime-ID fallback.

---

# 29. Navigation Report Placement identity

نکته قطعی پروژه:

> نام NavItem برای Report مستقل از Report name نیست؛ این نام‌ها sync می‌شوند و عملاً یک نام را منعکس می‌کنند.

پس `NavItem.Name` یک identity دوم جداگانه نیست.

Semantic:

```json
{
  "kind": "report",
  "report": "#گزارش پرسنل"
}
```

Local identity در Parent:

```text
kind=report + target Report semantic identity
```

در Apply:

```text
Parent مشخص
→ Report selector resolve
→ existing placement با همان Parent + Report target پیدا شود
```

Duplicate identical report placement زیر یک Parent:

```text
Error/Ambiguity
```

ordinal/Runtime ID fallback ساخته نشود.

---

# 30. Navigation Apply behavior

Navigation blind subtree rebuild نیست.

قاعده:

```text
1. Parent scope را مشخص کن.
2. Page/Group را با Name در Parent match کن.
3. Report placement را با Report target در Parent match کن.
4. 1 match → Update
5. 0 match → Create
6. >1 → Error/Ambiguity
7. omitted existing node → خودکار Delete نکن
```

Delete باید explicit باشد.

## Bug بسته‌شده v164

در v163:

```text
WrapScalarReference(report)
→ semantic JObject
→ RemoveZeroReference()
→ JObject اشتباهاً zero دیده می‌شد
→ report property حذف می‌شد
```

در v164 `RemoveZeroReference` فقط numeric zero را حذف می‌کند.

نتیجه واقعی:

```text
495 / 495 report placements
→ report selector present
```

---

# 31. Universal UID / Rename

فعلاً `$uid` عمومی به Semantic objectها اضافه نمی‌شود.

علت:

در SystemBuilder بسیاری از objects UniqueName immutable ندارند و Caption/Name ممکن است تغییر کنند؛ UID در آینده احتمالاً برای rename-aware reconciliation مفید خواهد بود.

اما در مرحله فعلی عمداً سه مفهوم را مخلوط نمی‌کنیم:

```text
Semantic identity
Semantic reference
Reconciliation identity
```

Contract جاری:

```text
Semantic key تغییر کند
→ Object جدید ممکن است ساخته شود
→ old Object implicit delete نمی‌شود
```

پس v15 فعلی:

```text
Rename-aware synchronization = NOT GUARANTEED
```

این limitation پذیرفته‌شده است.

بعداً اگر UID اضافه شد:

```text
$uid = reconciliation-only
```

و نباید به Semantic Selector تبدیل شود.

---

# 32. Unresolved Semantic Reference verification

`sourceRowId` و `dependencyKey` در Contract فعال وجود ندارند؛ authored Runtime authority همچنان توسط linter رد می‌شود.

برای selectorی که 0-match دارد:

```text
Expected selector
→ resolve again during Verify
→ still Unresolved
→ actual == FieldInfo-approved unresolved/empty value
→ `VerificationNonCertified` warning / non-blocking match
```

این rule فقط وقتی معتبر است که همان `FieldInfo` runtime-safe unresolved value را Source-certify کند؛ اگر selector اکنون resolve شود یا actual با safe value برابر نباشد، mismatch واقعی است. Field default و relation-backed Report condition/parameter از همین policy استفاده می‌کنند.

---

# 33. FieldInfo-driven invariant converters

CLR type نباید converter را تعیین کند.

Contract:

```csharp
public interface ISemanticFieldValueConverter
{
    string ToSemanticValue(object value, FieldInfoBase fieldInfo);
    object FromSemanticValue(string value, FieldInfoBase fieldInfo);
}
```

برای هر FieldInfo:

```text
1. Source FieldInfo class را پیدا کن.
2. value↔text behavior واقعی را بخوان.
3. deterministic pure semantics را استخراج کن.
4. DB/code/expression/side-effect/UI-only behavior را جدا کن.
5. invariant behavior را در DataExchange پیاده کن.
6. bidirectional tests.
7. اگر safe semantics ثابت نشد → Unsupported + Warning.
```

`GetCaptionFromValue/GetValueFromCaption` نباید کورکورانه runtime dependency شود.

Date/Enum support در v159+ اضافه شده است.

---

# 34. absent / null / empty / unsupported

این چهار حالت متفاوت‌اند:

```text
absent      = valid omission
null        = explicit null
""          = real empty string
unsupported = conversion/contract gap + warning/error
```

Unsupported نباید silently absent شود.

---

# 35. Comparison Operators

فقط semantics Source-confirmed پیاده شود.

Known operator families:

```text
equal
notEqual
gt / lt
contains
isNull
between
inList
...
```

نباید فرض شود RHS همه مثل `equal` است.

`contains` برای String/RichString در Source فعلی Source-certified است؛ operator/shapeهای دیگر فقط با evidence صریح اضافه می‌شوند.

---

# 36. Persian/Arabic Text Boundary

DB:

```text
Arabic ي / ك
```

Application/Semantic:

```text
Persian ی / ک
```

Wrappers:

```csharp
ToDatabaseText(...)    => FixFarsiText()
ToApplicationText(...) => FixFarsiTextReverse(...)
```

Contract فعلی برای همه strings است، حتی:

```text
Code
Expression
SQL
Regex
URL
opaque textual payload
```

برای executable/opaque strings behavioral test لازم است.

Normalization collision:

```text
Warning + First Match + non-certified
```

---

# 37. Partial Mutation / Reconcile

Final rule:

```text
Failure without mutation
→ Fail
→ block dependents
→ proven-independent branches may continue

Failure with partial mutation
→ PartialMutation = true
→ affected branch blocked
→ NeedsReconcile

Shared/unknown effect
→ Immediate Reconcile

Otherwise
→ aggregated Final Read-back / Reconcile
```

`AiRuntimeVerifier.FinalReadBackAndVerify` مبنا است و failed partial mutations نیز باید وارد read-back شوند.

---

# 38. Validation philosophy

Semantic layer نباید خطاهای design را مخفی کند.

Default philosophy:

```text
unique natural semantic identity → resolve
local structural fallback proven safe → use limited fallback
ambiguous/error design → explicit Error/Gap
Runtime-ID fallback → ممنوع مگر contract صریح آینده
```

مثال‌ها:

```text
Parameter duplicate Name     → Error
Picture Group duplicate Name → Error
Nav Page/Group duplicate Name→ Error
Duplicate Report placement   → Error
SystemItemGroup ambiguous    → Error
Column duplicate key         → limited ~index fallback
```

---

# 39. وضعیت v164 — موارد بسته‌شده

در کد/Export فعلی موارد زیر بسته شده‌اند:

```text
context-relative selectors
Date/Enum semantic converters
raw id-only ghost Field references
nested semantic wrapper cleanup
FieldItem items representation
Self condition
Self parameter marker
Parameter uniqueness/no-index rule
Column local selector + ~index support
Matrix/local column refs
Report child source-ID assignment removal
Rule type discriminator
Rule GlobalId decimal hash fallback
Rule internal field semantic refs
Picture Group name-based semantics
SystemItemGroup semantic selector
Navigation nested representation
Navigation synthetic ref removal
Navigation Report placement target selector
Navigation non-destructive matching
MetaCode noise reduction
```

---

# 40. Known Gaps / Not Yet Certified

این موارد نباید در Task بعدی بی‌دلیل دوباره redesign شوند:

1. `contains` برای String/RichString Source-certified است؛ operator/shapeهای خارج از فهرست جاری explicit Unsupported هستند.
2. Report Parameter با `FieldInfo == null` → Invalid/Unsupported.
3. Report duplicate ambiguity طبق contract قبلی non-certified است.
4. Persian/Arabic normalization ambiguity non-certified است.
5. Universal UID / rename-aware reconciliation deferred است.
6. View/Entity Navigation placement فعلاً Source-confirmed نیست.
7. `~index` Column path در آخرین real export احتمالاً به‌دلیل نبود duplicate Column واقعی exercise نشده؛ regression code وجود دارد ولی integration round-trip هنوز لازم است.
8. Apply → Re-export روی clean Target هنوز اجرا نشده است.

---

# 41. تنها مرحله مهم بعدی

قبل از redesign جدید، اول integration certification انجام شود:

```text
1. Source system Export Full + Semantic
2. Apply Semantic روی Target مناسب/clean
3. Final Read-back
4. Re-export Semantic از Target
5. Semantic Compare
6. classify differences:
   - expected target-generated runtime differences
   - normalization differences
   - semantic loss
   - ordering instability
   - unresolved/unsupported
```

تمرکز خاص Compare:

```text
Rule fallback keys
Report parameters
Report column order / ~index
Matrix refs
Self
FieldItem chains
Picture Groups
SystemItemGroups
Navigation pages/groups/report placements
Code/SQL/Formula
Relations / GeneralRelation
```

اگر difference مربوط به local Runtime ID باشد ولی Semantic برابر است:

```text
not a failure
```

اگر Semantic selector/key/structure تغییر کرده باشد:

```text
failure or explicit known gap
```

---

# 42. فایل‌های کلیدی Implementation

در baseline `update-v164`:

```text
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticSelectorCodec.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticFieldValueConverterRegistry.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticResolutionContext.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticRules.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticTextBoundary.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/AiSemanticV15ExportPostProcessor.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Export/SemanticValueResolver.cs
Barsa.Meta.SemanticExchange/Helper/Bix/AiReportModel.cs
Barsa.Meta.SemanticExchange/Helper/Bix/AiViewRuleModel.cs
Barsa.Meta.SemanticExchange/Helper/Bix/BixJsonExportManager.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiChangeProviders.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiReportChangeProvider.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiViewRuleChangeProvider.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiFieldWriteModel.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiRuntimeVerifier.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiChangePlanner.cs
Barsa.Meta.SemanticExchange/Helper/Bix/Write/AiBatchExecutor.cs
```

Regression coverage:

تست‌های فعال Source-only با نام‌های عمومی نگهداری می‌شوند و نام/نسخهٔ فایل تست authority قرارداد نیست.

---

# 43. Decision History — تصمیم‌های superseded

این موارد دیگر مبنای پیاده‌سازی نیستند:

```text
Separate MetadataResolver/DataResolver
→ superseded by one central Semantic framework

FieldItem as #A|B|C identity path
→ rejected; traversal uses items

Self inferred from "{خود}"
→ rejected; explicit self:true

Parameter ~index fallback
→ rejected; Name must be unique/non-empty

Rule index fallback
→ rejected; use Caption or GlobalId-derived hash

Picture Group ID/value
→ rejected; use Name, invalid duplicate/empty

SystemItemGroup group:n
→ rejected; semantic Caption selector

Navigation page:n/group:n/placement:n/parentRef
→ rejected; nested structure

Blind Navigation subtree rebuild
→ rejected; non-destructive semantic matching

NavItem name as independent Report placement identity
→ rejected; Report name/NavItem name sync; placement identity derives from target Report

Universal $uid now
→ deferred, not part of v15 current model
```

---

# 44. Instructions for Host / Future Chat

وقتی این KM در Host قرار گرفت:

1. این فایل را current Semantic v15 knowledge baseline بدان.
2. از v14 یا promptهای قدیمی contract را بازسازی نکن.
3. برای decisionهای بسته‌شده دوباره سؤال طراحی مطرح نکن مگر Source contradiction واقعی پیدا شود.
4. Source code واقعی SystemBuilder authority رفتار است.
5. اگر Source behavior ثابت نیست:
   ```text
   Gap/Unsupported
   ```
   بهتر از heuristic است.
6. Runtime ID را Semantic key/ref نکن.
7. GlobalId-derived hash فقط Rule fallback فعلی است و به Universal UID تعمیم داده نشود.
8. Navigation target فعلی فقط Report است تا Source چیز دیگری را اثبات کند.
9. Rename limitation را Known Limitation بدان، نه bug فوری.
10. اولویت بعدی پروژه integration round-trip است، نه redesign contract.

---

# 45. Definition of Current Success

وضعیت فعلی را می‌توان این‌گونه خلاصه کرد:

```text
Semantic v15 contract        = substantially closed
v164 code implementation     = accepted
real export shape            = accepted
major runtime-id leakage     = closed for audited paths
navigation report refs       = fixed
rule condition field refs    = fixed

remaining certification:
real Apply → Re-export → Semantic Compare
```

تا قبل از نتیجه این integration test، معماری جدیدی مثل Universal UID اضافه نشود مگر failure واقعی ضرورت آن را نشان دهد.

---

# 46. Runtime Reconstruction / Apply — Final v10 sync (update-v171)

این بخش وضعیت اجرایی قدیمی‌تر v164/v166 در انتهای سند را برای Runtime Apply supersede می‌کند؛ Semantic shape اصلی بازطراحی نشده است.

1. Runtime ID خارج از canonical Semantic v15 است. same-batch=`tempId`؛ cross-wave=persisted object با selector/context.
2. Plan/Apply/Verify یک resolution contract دارند و context معنایی per-command تازه است.
3. Plan→Apply binding فقط execution evidence است؛ target متفاوت/unresolved در Apply => `Conflict`.
4. ambiguity عمومی: first match + Warning + non-certified؛ blocking عمومی ساخته نشود.
5. `dbName`: preserve اگر آزاد؛ collision => deterministic remap + explicit evidence + Warning + continue. فقط mismatch دارای evidence قابل تحمل است.
6. structured metadata مانند View/Layout باید remap-aware باشد؛ SQL/Code/Expression blind rewrite ممنوع و احتمال dependency فقط Warning است.
7. Host/Package Bridge با `canApplyAny` اجازه ContinueIndependent می‌دهد؛ `canApplyAll/canApplyCleanly` نشان‌دهنده clean-all است، نه gate برای هر Apply.
8. image SHA transport-only است؛ semantic equality decoded pixels است.
9. assetها از package transport و `assetRoot` واقعی می‌آیند؛ Agent آن را حدس نمی‌زند.
10. Runtime Certification تا full real round-trip همچنان Pending است.


---

# 47. Runtime Reconstruction focused follow-up — update-v173

`v173` فقط دو blocker باقی‌مانده بعد از v172 را می‌بندد و معماری v10 را تغییر نمی‌دهد:

1. Package lint قبل از ZIP از همان Runtime linter/`SemanticSelectorCodec` استفاده می‌کند و duplicate `commandId`، dependency cycle، selector grammar، legacy root `externalDataMappings` و Runtime authority را reject می‌کند.
2. `DbNameRemap` بعد از persistence به identity canonical همان object finalize می‌شود؛ کلید matching/dedup نهایی `OwnerSemanticIdentity + ObjectSemanticIdentity + SourceDbName` است و `AiApplyResult.DbNameRemaps` فقط از registry finalized execution ساخته می‌شود.
3. Verify فقط exact scoped remap را tolerate می‌کند؛ mapping یک owner/object به owner/object دیگر سرایت نمی‌کند.
4. Runtime/full round-trip certification تا Build/Deploy/Full Reconstruction واقعی همچنان Pending است.

# 48. Final DbNameRemap canonical identity closure — update-v174

`update-v174` is a direct delta on the applied `update-v172` baseline and includes the unapplied v173 focused fixes. DbNameRemap artifact identities are full/context-independent semantic selectors. Runtime IDs may be used to locate runtime objects while constructing the selector but are never part of the semantic remap key. Matching/dedup/Verify/Final Compare use canonical OwnerSemanticIdentity + ObjectSemanticIdentity + SourceDbName. Cross-system same-name objects therefore remain independent. Runtime Certification remains Pending until the full real reconstruction round-trip passes.

---

# 49. Runtime Reconstruction focused follow-up — update-v175

این Delta فقط failureهای واقعی Runtime بعد از v174 را می‌بندد و Semantic v15/v10 را redesign نمی‌کند.

1. `runCodeAtStartup` و `iconName` در System export/write/read-back/verify متقارن هستند.
2. Report `FieldItem` یک contract object-specific دارد: Field reference مستقیم، `self` و `items`؛ Snapshot خام جای Write payload را نمی‌گیرد.
3. View layout field reference از resolver مشترک استفاده می‌کند؛ same-wave=`tempId` و persisted/cross-wave=selector/context.
4. `reportId` و `typeViewId` در authored v15 Runtime integer نیستند؛ semantic reference هستند و Writer پس از Resolve Runtime ID داخلی را می‌سازد.
5. `referenceField.operator` canonical scalar است، مانند `"equal"`؛ array آزمایشی قدیمی compatibility ندارد.
6. Plan/Apply binding بر authority معنایی selector/tempId تکیه دارد؛ materialization طبیعی same-batch از context صفر به Runtime ID conflict نیست. تغییر واقعی target همچنان conflict است.
7. Enum + dependent formula در همان Apply با materialization/reload موجود تکمیل می‌شود؛ wave جدید فقط برای ID ساخته نمی‌شود.
8. Verify semantic equality را از representation/physical mismatch جدا می‌کند؛ failure classها: `mutationMissing`, `semanticMismatch`, `readBackProjectionMissing`, `physicalVerificationMismatch`, `normalizationMismatch`.
9. Navigation capability موجود است: Page=`folder kind=page`، Group=`folder kind=group`، Report Placement=`folder kind=report`؛ Root Folder را Runtime/System می‌سازد و Agent نباید create کند.
10. application-data row گمشده همان `UnresolvedSemanticReference` است؛ اگر FieldInfo empty/sentinel واقعی را مجاز بداند type-aware ادامه می‌یابد وگرنه command-local fail می‌شود. fake row ساخته نمی‌شود.
11. Runtime ID در v15 Agent-facing authority نیست؛ `sessionReferenceMap` فقط execution/diagnostic evidence است.

Runtime/full reconstruction certification همچنان Pending است تا Build/Deploy و Fresh Export → Generate Change → Plan → Apply → Read-back → Verify → Re-export → Semantic Compare واقعی اجرا شود.

---

## Runtime follow-up — update-v176 / SOC ↔ IOC QTR scope

- Agent فقط **SOC** را author می‌کند؛ IOC و Runtime ID فقط داخل Host/DataExchange هستند.
- Export و Apply برای QTR scope دو جهت یک mapping deterministic هستند؛ Host inference آزاد/LLM ندارد.
- dependency ساخت Child فقط به **وجود واقعی Parent** وابسته است، نه موفقیت همه‌ی post-save stageها.
- `ParentNotCreated` با `UnresolvedDependency` متفاوت است.
- command-level failure دیگر policy-based global stop ایجاد نمی‌کند؛ independent branch باید ادامه یابد.
- بعد از اولین persistence قطعی، `realId` / owner / semantic identity / mutation stage به‌صورت execution receipt حفظ و `tempId` همان batch bind می‌شود.
- partial mutation بعد از persistence، object را nonexistent نمی‌کند؛ reconcile failure محلی و `Reconstruction=Incomplete` است.
- Report FieldItem همان embedded SOC contract واحد Parser/Validator/Resolver/Writer/Verifier را استفاده می‌کند؛ direct same-wave `tempId` و persisted selector معتبرند.
- Navigation همان `folder` موجود با `kind=page|group|report` است؛ Root را Runtime می‌سازد. `order` معنای relative sibling order دارد، نه raw Runtime number.
- Layout باید از authority موجود `AiViewRuleModel` برای Read/Write/Verify استفاده کند؛ Agent XML author نمی‌کند.
- Date normalization فقط Field/Property-aware است؛ String شبیه تاریخ exact String باقی می‌ماند.
- canonical lint قبل از Package/Plan باید shapeهای قابل تشخیص محلی را با همان Provider contract رد کند.
- Historical v176 fingerprint note: superseded by v202. Current fingerprint از binary identity واقعی Host/DataExchange/Barsa.Meta، profile 15 و `socContractRevision=v15-qtr-v202` ساخته می‌شود و `updateId` hard-coded authority نیست.
- `socContractHash`, timings و failure-index در این Update P1/Deferred هستند مگر بدون بزرگ‌کردن Scope قابل تکمیل باشند.
- Runtime Golden frozen known-good SOC باید قبل از End-to-End Golden با Agent PASS شود.
- Build/Deploy/Restart و Golden واقعی فقط با evidence محیط Runtime قابل certify هستند؛ Source/package validation جای آن را نمی‌گیرد.

## v177 focused correction

- executable Semantic v15 فقط `ContinueIndependent` را می‌پذیرد؛ `StopBatch` authored reject می‌شود و command-level failure نباید `SkippedPolicy` تولید کند.
- `defaultEditView` در Planner/Resolver/Writer/Verifier از central Semantic Reference Contract استفاده می‌کند؛ same-wave=`tempId` و cross-wave=semantic selector.
- Layout `textLocation` از یک authority مشترک `AiSemanticLayoutModel` در Write و Runtime→SOC projection/Verify عبور می‌کند؛ Agent XML نمی‌سازد.
- `reportRelation` ابتدا SOC-validate و سپس به writable IOC projection تبدیل می‌شود: `reportId` semantic reference writable است، `target` از Report مشتق می‌شود، و `orderNumber` فقط relative reconstruction ordering است.
- ترتیب `orderNumber` برای FieldDef به معنی ترتیب نسبی بین همه Field/Relation siblingهای همان Entity است، نه raw numeric equality و نه فقط reportRelationها.



## v178 focused correction

- pre-resolution canonical lint selector معتبر cross-wave را به‌عنوان deferred Semantic reference عبور می‌دهد؛ Runtime binding بعد از Resolve سنجیده می‌شود.
- Entity default View در executable v15 فقط با `defaultEditView` author می‌شود؛ aliasهای legacy canonical نیستند و reject می‌شوند.
- `reportRelation.target` حتی با وجود derived بودن، اگر authored باشد قبل از projection کامل SOC-validate می‌شود؛ projection malformed input را پنهان نمی‌کند.
- FieldDef relative sibling order semantic dependency نیست و نباید DAG cycle بسازد؛ raw `orderNumber` authority نیست.
- Runtime acceptance این build تا اجرای Build/Deploy/behavioral tests و Golden واقعی `PendingRuntimeExecution` است.

## v179 focused correction

- baseline عملیاتی برای این بسته: v175؛ بسته v179 cumulative است و fixهای معتبر v176..v178 را نیز حمل می‌کند.
- Workflow nested references در pre-resolution از central Semantic reference semantics استفاده می‌کنند؛ cross-wave selector معتبر است و Runtime ID authored ممنوع می‌ماند.
- Build/Deploy/Runtime acceptance بدون اجرای واقعی `PendingRuntimeExecution` است.
- TEST-2 non-participating sibling فقط evidence/micro-test است؛ Acceptance ناقص ورودی باعث تغییر الگوریتم ordering نشده است.

## v180 — Workflow SOC/IOC reference boundary

Workflow nested typed references follow the same central Semantic v15 contract as other references:

```text
Authored SOC: same-wave=tempId, cross-wave=selector, Runtime ID forbidden.
Resolved IOC: Host-resolved Runtime object/id is valid internal execution state and is not revalidated as authored SOC.
```

Canonical cross-wave Workflow input is the selector string form. Host performs deterministic target-type-aware resolution for `variable.entity`, `activity.view`, `activity.subProcess`, `activity.itemResolveReport` and supported object-reference actor paths. Agent must not generate Runtime IDs.
