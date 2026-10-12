# مرجع Business Rule و Unique Constraint برای AI/Codex

این سند مرجع جاری حاصل بررسی `BRRule`, `BRUniqueConstraint`, Event/Action classes، `ComplexCondition` و Windows Designer است. BusinessRule همان Condition model canonical مشترک با Report را reuse می‌کند؛ raw internal dump مجاز نیست.

## Unique Constraint

`objectType = "uniqueConstraint"` و Parent همیشه Entity مالک است.

```json
{
  "caption":"عدم تکرار کد",
  "fields":[101],
  "errorMessage":"کد تکراری است",
  "isDefault":true,
  "isDisabled":false
}
```

قواعد:

- Create حداقل یک Field می‌خواهد.
- هر Field باید DB-backed و متعلق به همان Entity باشد.
- Field تکراری مجاز نیست.
- `caption`, `errorMessage`, `isDefault`, `isDisabled` Designer-visible و Write-enabled هستند.
- `Description` در Runtime class وجود دارد ولی در Designer بررسی‌شده تنظیم نمی‌شود؛ وارد Write contract نشده است.
- Create/Update/Delete از `TypeDef.SettingsObject.RuleList` و مسیر save رسمی TypeDef استفاده می‌کند.

## Business Rule

`objectType = "businessRule"` و Parent Entity الزامی است.

Write-enabled top-level properties:

- `caption`
- `isDefault`
- `isDisabled`
- `events`
- `actions` — فقط برای Rule بدون Condition
- `branches` — برای Rule شرط‌دار

`BRRule.Description` در Runtime class موجود است، اما Windows Designer بررسی‌شده آن را برای Rule root expose نمی‌کند. اگر مقدار legacy موجود باشد ممکن است در Read برای diagnostics دیده شود، ولی **Write-enabled نیست**.

## Events

Form:

```json
{"type":"form","event":"beforeLayoutCreated"}
{"type":"form","event":"dataPopulated"}
{"type":"form","event":"beforeSave"}
{"type":"form","event":"beforeActivityDone"}
```

Field:

```json
{"type":"field","event":"valueChanged","field":101}
```

Field event values:

- `valueChangedOnly`
- `valueChanged`

Field event reference باید Field همان Entity مالک Rule باشد.

## Actions

### Field action

Field action در Runtime می‌تواند دو نوع target داشته باشد:

1. Field واقعی (`FieldDefId`)
2. Caption یک Layout item/group (`ItemCaption`)؛ این target Field نیست.

Semantic contract:

```json
{
  "type":"field",
  "fields":[101],
  "layoutCaptions":["گروه مشخصات"],
  "editable":false,
  "visible":true,
  "mandatory":true,
  "colored":true,
  "enabled":true,
  "removeValue":false
}
```

حداقل یکی از `fields` یا `layoutCaptions` باید target داشته باشد. Fieldها باید متعلق به Entity Rule باشند. target تکراری مجاز نیست.

Windows Designer `IsReadOnly` نگه می‌دارد ولی AI از `editable` استفاده می‌کند تا معنی طبیعی باشد.

### Show message

```json
{
  "type":"showMessage",
  "messageType":"information",
  "position":"popup",
  "evaluate":"text",
  "message":"اطلاعات کامل نیست"
}
```

- `messageType`: `information | error | okCancel`
- `position`: `popup | infoBar`
- `evaluate`: `text | code`
- اگر `evaluate=code` باشد property `code` استفاده می‌شود.

### Apply View

```json
{"type":"applyView","view":201}
```

View target باید View همان Entity مالک Rule باشد.

### Code

```json
{"type":"code","code":"..."}
```

### Reverse

```json
{"type":"reverse"}
```

## Condition / Branches

Condition machine-level contract مشترک Report/BusinessRule در `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md` است. `BRExpressionCondition.Condition` همان `ComplexCondition` و Rule Designer همان editor را با Entity مالک و بدون Report parameter list استفاده می‌کند.

Rule بدون شرط همان `actions` top-level را دارد. Rule شرط‌دار از `branches` استفاده می‌کند:

```json
{
  "caption":"کنترل تعداد",
  "events":[{"type":"field","event":"valueChanged","field":101}],
  "branches":[
    {
      "condition":{"field":101,"operator":"lessThanOrEqual","value":0},
      "actions":[{"type":"showMessage","messageType":"error","position":"popup","evaluate":"text","message":"تعداد باید مثبت باشد"}]
    },
    {"else":true,"actions":[]}
  ]
}
```

قواعد:
- چند condition branch مجاز است.
- حداکثر یک `else`. AI به‌صورت canonical آن را آخر تولید کند؛ اگر legacy Runtime آن را وسط نگه داشته باشد، branchهای بعد از Else semantic اجرا نمی‌شوند.
- `else` بدون expression branch قبلی ممنوع.
- `actions` و `branches` هم‌زمان در یک patch مجاز نیستند.
- update `branches` کل branch structure را جایگزین می‌کند؛ actionهای هر branch همراه آن می‌آیند.
- parameter-backed Condition در BusinessRule پشتیبانی نمی‌شود چون Rule Designer parameter list گزارش ندارد.
- Conditionهایی که capability آنها از Source روشن نیست (مثلاً cardinality/aggregate شرط list) حدس زده نمی‌شوند.

## Selected Rules در View

`TypeView.SelectedRuleList` می‌تواند ID هر دو نوع زیر از RuleList همان Entity را داشته باشد:

- `businessRule`
- `uniqueConstraint`

Serializer نوع واقعی را در reference مشخص می‌کند و Writer membership را validate می‌کند.

## اصل عدم حدس

اگر Source بررسی‌شده behavior/lifecycle را روشن نمی‌کند:

1. Write فعال نشود؛
2. raw internal object برای پرکردن خلأ Serialize نشود؛
3. Gap مستند شود؛
4. فقط پس از Source/Runtime verification تکمیل شود.


## Persistence contract

`BusinessRule` و `UniqueConstraint` داخل `TypeDef.SettingsObject.RuleList` نگهداری می‌شوند.

نکته Runtime مهم: تغییر collection داخلی `RuleList` الزاماً خود `TypeDef` را dirty نمی‌کند. بنابراین `TypeDef.CRUD()` که به object state وابسته است مسیر قابل اتکای settings-only mutation نیست.

مسیر رسمی استخراج‌شده از Source —

1. mutate `TypeDef.SettingsObject.RuleList`
2. `TypeDef.Update()` به‌صورت صریح
3. `TypeDefCacheNew.Reload(typeDef)` برای read-back واقعی DB/cache replacement
4. verify وجود/عدم وجود Rule با `Id` داخل همان `RuleList`

Provider جاری همین مسیر را برای Create/Update/Delete Rule و UniqueConstraint استفاده می‌کند.

`selectedRules` فقط مجاز است به Rule/Constraint موجود در `RuleList` همان Entity اشاره کند. Rule id برگشتی command به‌تنهایی اثبات persistence نیست؛ read-back از RuleList معیار نهایی است.
