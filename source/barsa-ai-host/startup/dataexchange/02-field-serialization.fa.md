# Field Serialization — Current Semantic Contract

- Verify unresolved substitution: still-unresolved selector + FieldInfo-approved runtime-safe value => NonCertified warning، نه semantic mismatch.

## هدف

Field برای AI به شکل semantic و Designer-oriented Serialize می‌شود؛ object graph داخلی `FieldInfo`/`Settings` contract AI نیست. همان shape برای Read/Write/Verify استفاده می‌شود.

## شکل پایه

```json
{
  "$type": "field",
  "id": 1068313510000000201,
  "caption": "عنوان",
  "dbName": "F1",
  "orderNumber": 1,
  "fieldType": "string",
  "maximumLength": 200
}
```

ترتیب canonical propertyهای اول:
1. `$type` — discriminator خواندنی object (`field` یا `relation`)
2. `id`
3. `caption`
4. `dbName`
5. `orderNumber`
6. `fieldType`
7. تنظیمات non-default/type-specific
8. relation/code/report child data موجود در profile

## موارد حذف‌شده

از Field JSON حذف می‌شوند:
- `$caption`
- `typeDefId` چون Field داخل Entity قرار دارد
- `fieldInfoType`
- `relationType` خام FieldDef
- wrapper `Settings`
- `$serializedType`
- capability/derived props مثل `HasFormula`, `HasReport`, `IsColumn`, `MaxNumericDotPlace`, `HasNumericDotPlace`
- binary payloadها
- `IconInfo.FileKey` چون derived است.

## Semantic object discriminator

`$type` بخشی از Semantic v15 است و برای Field/Relation حذف نمی‌شود:

```json
{"$type":"field","fieldType":"string","caption":"عنوان"}
```

```json
{"$type":"relation","fieldType":"singleRelation","caption":"مشتری","target":"#مشتری"}
```

`$type` فقط **نوع Semantic object** را مشخص می‌کند. مالکیت Compose از relation واقعی مدل و placement از Navigation می‌آید؛ `$type` هیچ‌کدام را تعیین نمی‌کند. مقدار `fieldType` همچنان subtype Runtime/Designer است. در AiChange نیز `objectType` envelope authority dispatch است و `$type` داخل `properties` author نمی‌شود.

## Flattening

`Settings` با Decoder `FieldInfo` خوانده می‌شود اما خروجی Decoder مستقیماً در top-level Field merge می‌شود:

نمونه internal input که contract AI نیست:
```json
{
  "fieldInfoType":"StringInfo",
  "Settings":{"$serializedType":"Barsa.Meta.StringInfo","MaximumLength":200,"IsMandatory":false}
}
```

خروجی semantic:
```json
{"fieldType":"string","maximumLength":200}
```

## Default omission

قاعده:
- مقدار default قطعی که اطلاعات طراحی ندارد حذف شود.
- false/zero را فقط وقتی حذف می‌کنیم که واقعاً default همان property باشد.
- reference با id=0 حذف شود.
- object configured/binary به `{configured:true}` خلاصه شود.

این قاعده به‌خصوص باعث می‌شود JSON فیلدهای ساده کوتاه بماند.

## Semantic mapping

- `StringInfo` -> `string`
- `IntInfo(Long)` -> `int`
- `IntInfo(Float)` -> `float`
- `IntInfo(Decimal)` -> `decimal`
- `CurrencyInfo` -> `money`
- `BoolInfo` -> `bool`
- `DateInfo` -> `date`
- `EnumInfo` -> `enum`
- `TimeSpanInfo` -> `timeSpan`
- `RichStringInfo` -> `longText`
- `MetaObjectInfo` -> `singleRelation`
- `RelationInfo` -> `listRelation`
- سایر mappingهای فنی FieldInfo/Designer/Create-Update در `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/01-field-types-reference.fa.md`.

Most-specific subclass باید قبل از base class تشخیص داده شود.

## Reference shape

```json
{
  "objectType": "entity",
  "id": 123,
  "caption": "مشتری"
}
```

برای Field:
```json
{"objectType":"field","id":456,"caption":"عنوان"}
```

Caption convenience است؛ identity عمومی بر اساس id است.

استثنای جاری برای Entity شناخته‌شده کاربر: وقتی target واقعی `SplUser`/`SplUsers` است، serializer علاوه بر `id/caption` یک `name` پایدار می‌دهد:

```json
{"objectType":"entity","id":123,"caption":"کاربر","name":"SplUser"}
```

Writer و Runtime verifier این Reference نام‌محور را در System `Meta01` resolve می‌کنند تا Action مرجع مجبور به کپی Runtime ID نباشد. این special-case تا وقتی System مالک بخشی از generic Entity Reference نشده، فقط برای همین Entity شناخته‌شده است.

`additionalTargets`:
```json
[
  {"objectType":"entity","id":123,"caption":"A"},
  {"objectType":"entity","id":456,"caption":"B","reportId":789}
]
```

## Enum

```json
{
  "fieldType":"enum",
  "values":[
    {"value":0,"caption":"فعال"},
    {"value":1,"caption":"غیرفعال","disabled":true}
  ]
}
```

Default `enumType=single`, `viewType=comboBox`, `iconDisplayType=noImage` در صورت default حذف می‌شوند.

## Number

NumberType داخلی مستقیم contract نیست. شکل semantic:

```json
{"fieldType":"int"}
```

یا:

```json
{"fieldType":"decimal","numericDotPlace":2,"totalDigits":18}
```

`TypeDef.AddIntField()` در Runtime یک `IntInfo` با default `NumberType=Float` می‌سازد؛ Writer برای semantic `int/float/decimal` نوع عدد را صریح تنظیم می‌کند.

## Relation

### Change ownership — non-ambiguous

`fieldType` در Semantic نوع metadata را بیان می‌کند، اما **`objectType` Change انتخاب Provider را تعیین می‌کند**:

- Fieldهای scalar/non-relation با `objectType:"field"` ساخته/ویرایش می‌شوند.
- همه‌ی relation semantic typeهای write-enabled (`singleRelation`, `listRelation`, ... مطابق DX01) با `objectType:"relation"` ساخته/ویرایش می‌شوند و نوع دقیق Relation در `properties.fieldType` می‌آید.
- ارسال `objectType:"field"` همراه `fieldType:"singleRelation"`/`"listRelation"` contract غلط است؛ Planner آن را auto-rewrite نمی‌کند و باید `wrongObjectType` گزارش کند.
- `relationKind` compatibility قدیمی Provider است و representation canonical Agent-facing نیست؛ Change جدید باید `properties.fieldType` را بفرستد.

یک Create کامل `singleRelation` در همان logical Change با Entityهای تازه:

```json
{
  "changes": [
    {
      "commandId":"create-system",
      "operation":"create",
      "objectType":"system",
      "tempId":"sys",
      "properties":{"caption":"نمونه"}
    },
    {
      "commandId":"create-a",
      "operation":"create",
      "objectType":"entity",
      "tempId":"entity-a",
      "parent":{"objectType":"system","tempId":"sys"},
      "properties":{"caption":"A"}
    },
    {
      "commandId":"create-b",
      "operation":"create",
      "objectType":"entity",
      "tempId":"entity-b",
      "parent":{"objectType":"system","tempId":"sys"},
      "properties":{"caption":"B"}
    },
    {
      "commandId":"create-a-to-b",
      "operation":"create",
      "objectType":"relation",
      "tempId":"a-to-b",
      "parent":{"objectType":"entity","tempId":"entity-a"},
      "properties":{
        "caption":"B",
        "fieldType":"singleRelation",
        "target":{"objectType":"entity","tempId":"entity-b"}
      }
    }
  ]
}
```

این dependencyها با `tempId` همان Batch قابل مرتب‌سازی‌اند؛ گرفتن ID واقعی A/B به‌تنهایی wave boundary نیست. Apply `singleRelation` از Provider تخصصی Relation به مسیر رسمی `TypeDef.AddSingleRelationInfo` می‌رود.

شکل Semantic/read-back همان Relation:

Single:
```json
{
  "fieldType":"singleRelation",
  "target":{"objectType":"entity","id":100,"caption":"مشتری"},
  "isMandatory":true
}
```

List:
```json
{
  "fieldType":"listRelation",
  "target":{"objectType":"entity","id":200,"caption":"اقلام"},
  "relationType":"composition",
  "max":20
}
```

Create canonical `listRelation` نیز `objectType:"relation"` و `properties.fieldType:"listRelation"` دارد و Provider آن را از مسیر رسمی `TypeDef.AddRelationListField` اجرا می‌کند.

`RelationDef` فنی به شکل object dump جداگانه برای AI تکرار نمی‌شود؛ propertyهای Designer-facing آن در Field semantic ادغام می‌شوند. Child relationهای legacy profile فقط وقتی هنوز اطلاعاتی خارج از canonical model دارند باقی می‌مانند و باید در مراحل بعدی حذف/ادغام شوند.

## Formula/defaultValue

Formula/default value به‌صورت semantic Serialize می‌شوند؛ object graph داخلی contract نیست.

Formulaهای write-enabled فعلی:
- `code`
- `query` / aggregate-on-report با Report reference و aggregation رسمی

DefaultValueهای write-enabled عمومی:
- `constantValue`
- `code`

Report-backed DefaultValue بدون contract semantic مستقل نباید حدس زده شود.

اگر metadata پیکربندی شده ولی contract خواندنی کامل ندارد، فقط `{configured:true}` برگردانده شود و mutation حدسی فعال نشود.

## Contract boundary

Serialization profile جاری `profileVersion=14` است. Consumer نباید به `Settings/fieldInfoType/$serializedType` یا childهای raw `FieldInfo/RelationDef` وابسته باشد.

Workspace structure، System/Entity layout و physical folder structure بخشی از این Field contract نیستند؛ representation Field semantic است.

## Canonical child metadata

Field علاوه بر `FieldInfo` می‌تواند metadata child داشته باشد. Contract semantic آنها را raw نگه نمی‌دارد:

- child `رابطه`/`RelationDef` حذف می‌شود؛ اطلاعات لازم در `fieldType=listRelation/...` و propertyهای semantic relation ادغام شده است.
- child `كد`/`کد`/`MetaCode` به `logic[]` تبدیل می‌شود. هر item در حد موجود بودن شامل `id`, `caption`, `address`, `addressInTarget`, `layer`, `language`, `location`, `code`, `parameterTypeDefId` است. Enumهای layer/language/location نام semantic دارند، نه عدد خام.
- child `دستور پويا` به `dynamicCommands[]` تبدیل می‌شود. این metadata linked برای inspect صادر می‌شود؛ mutation عمومی Field برای آن فعال نیست.
- child `JsonProperty` به canonical raw `jsonProperty` منتقل می‌شود؛ مقدار parse یا به flagهای UI تبدیل نمی‌شود و null/empty/raw text حفظ می‌شود.

مثال:

```json
{
  "id": 123,
  "caption": "عملیات",
  "dbName": "F8",
  "orderNumber": 8,
  "fieldType": "command",
  "displayType": "button",
  "executeTarget": ["singleObject", "contextMenu"],
  "logic": [
    {"id":456,"layer":"bl","language":"cSharp","location":"systemCode","code":"..."}
  ],
  "dynamicCommands": [ ... ],
  "jsonProperty": "WordEditor:true"
}
```

## Flags

هر enum دارای `[Flags]` به شکل **array نام‌های camelCase** Serialize می‌شود، نه رشته comma-separated و نه عدد:

```json
"executionTime": ["afterCreate", "afterUpdate", "afterFormLoad"]
```

همین شکل در Write پذیرفته و در Verify به‌صورت set مقایسه می‌شود.

## Read = Write = Verify

Semantic JSON فقط خروجی خواندنی نیست. Propertyهای write-enabled همان نام و shape را در Semantic Change استفاده می‌کنند. Runtime verifier پس از Apply دوباره `AiFieldTypeModel` را اجرا می‌کند و فقط propertyهای درخواست‌شده را به‌صورت semantic مقایسه می‌کند؛ objectها subset و referenceها با id/tempId resolve می‌شوند.

استثناهای linked metadata: `logic` و `dynamicCommands` در universal Field patch قرار ندارند مگر provider رسمی مستقلی برای mutation آنها اضافه شود؛ `jsonProperty` raw مستقیماً پشتیبانی می‌شود.


## Reflective serializer safety

در serializerهای generic/reflection-based، member دارای `[Obsolete]` باید **قبل از خواندن getter/value** skip شود.

قاعده attribute-based است؛ legacy memberها را با blacklist نامی مثل `ChoiceDefList` مدیریت نکن. بعضی compatibility getterهای obsolete رفتار Runtime دارند و صرف خواندن آنها می‌تواند Export را خراب کند.

Source فعلی همین قاعده را برای property و field در `BixJsonExportManager` اعمال می‌کند.

## Formula `executionTime` write boundary

`executionTime` یک property سطح Field نیست. exact writable path فقط داخل replacement object فرمول است:

```json
{
  "formula": {
    "type": "code",
    "code": "...",
    "executionTime": ["afterCreate", "afterUpdate"]
  }
}
```

پس `properties.executionTime` توسط specialized Field Provider **unsupported** است؛ شکل صحیح `properties.formula.executionTime` است. Provider همان `FormulaClass.ExecutaionTimeEnum` را authority می‌گیرد و فقط **array از نام واقعی enum، case-insensitive** را می‌پذیرد؛ numeric string/ordinal مثل `"1"` نام enum محسوب نمی‌شود. Plan پیش از Apply نام نامعتبر را با allowed values واقعی Runtime گزارش می‌کند. DX نباید alias یا property موازی در سطح Field تعریف کند. read-back نیز همین array camelCase را داخل `formula` برمی‌گرداند.

## Formula technical write/compiler contract

این بخش مالک exact machine-level contract Formula است؛ design/usage guidance در Working Knowledge باقی می‌ماند.

Canonical definitions:

```json
{"formula":{"type":"code","code":"..."}}
```

و برای query-backed Formula:

```json
{"formula":{"type":"query","report":{"objectType":"report","id":123},"aggregation":"sum"}}
```

- `aggregate` و `aggregateOnReport` alias ورودی legacy هستند؛ read-back canonical `type:"query"` است.
- `formula` replacement property است: property غایب = no-change، `formula:null` = حذف، object = replace/update definition.
- Writer Formula موجود را recreate نمی‌کند؛ identity `FormulaClass/MetaCode` را حفظ و lifecycle رسمی Designer را update می‌کند.
- Code Formula با compiler رسمی MetaCode validate می‌شود؛ Provider CLR coercion حدسی انجام نمی‌دهد.
- Field همان Entity در compiler Formula با Caption داخل `{...}` reference می‌شود؛ bare dbName/identifier contract Field reference نیست.
- Query Formula از `SingleValuedQuery` واقعی با Report reference و aggregation استفاده می‌کند. aggregationهای canonical: `count`, `sum`, `min`, `max`, `avg`, `first`, `stringConcat`, `custom`, `exists`, `notExists`. `customSql` فقط برای aggregation سفارشی است.
- Writer query Formula همان Formula object را حفظ می‌کند، `ResetCalculationFormula()` را اجرا می‌کند، سپس `FormulaType=Query` و `SingleValuedQuery={ReportId,AggreationType,CustomSql}` را روی lifecycle رسمی تنظیم می‌کند؛ recreate کردن FormulaClass ممنوع است.
- برای Formula جدید، اگر `executionTime` در patch صریح نباشد، default Designer `AfterCreate + AfterUpdate` اعمال می‌شود؛ Formula موجود execution time خود را حفظ می‌کند مگر patch صریح تغییر دهد.
- read-back Query Formula حداقل `type`, `report`, `aggregation` و در صورت وجود `customSql` را برمی‌گرداند.
- اجرای Runtime query-backed Formula قبل از ساخت single-valued query، Report helper را با parent object فعلی bind می‌کند (`SetParameterValuesByParentObject`). exact external-parameter injection و write defaults در DX05 ثبت شده‌اند؛ این bridge بخشی از contract فنی Report-backed Formula است.
- Source فعلی `FieldItemAggregateReport.AggreationTypeEnum` و writer جاری aggregationهای `count`, `sum`, `min`, `max`, `avg`, `first`, `stringConcat`, `custom`, `exists`, `notExists` را می‌شناسند. استفاده از aggregation باید با semantics Report و مورد مصرف (Formula در برابر Condition) سازگار باشد.

Batch dependency، temp reference و deferred compiler validation در DX07 تعریف شده است:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/07-ai-change-runtime-reference.fa.md`

## profile v14 — relation/data/asset projection

```text
reverseListRelation.directField
→ portable field reference
→ Writer resolves direct FieldDef
→ derives Runtime RelationDef
```

`relationDefinitionId`، `relationName` و Relation `max` در Semantic contract جدید صادر نمی‌شوند. direct `listRelation` همچنان Designer `relationType` و `additionalTargets` را در صورت non-default/meaningful نگه می‌دارد.

External record default:

```json
{
  "kind": "data",
  "target": { "semanticId": "..." },
  "caption": "readable hint",
  "selector": "#جغرافیا"
}
```

`#` همان semantic FK/reference است. Target از FieldInfo/Context تعیین می‌شود و Dynamic Row با `TypeDef.GetDefaultFieldOrFirst()` lookup می‌شود. `dependencyKey`/`sourceRowId` authority نیستند؛ 0-match=`UnresolvedSemanticReference` و unresolved behavior type-aware است.



## v202 — Universal Semantic Reference

`#Key` / `#[Target]Key` قرارداد واحد Metadata و Dynamic Row است. `externalData` kind و Metadata/Data resolver split وجود ندارد. Semantic text `ی/ک` و provider DB text `ي/ك` است و Plan/Apply از policy مرکزی مشترک عبور می‌کنند.
