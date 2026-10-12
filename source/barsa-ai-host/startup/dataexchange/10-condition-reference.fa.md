# Condition — DataExchange Technical Contract

`ComplexCondition` و `SingleCondition` مدل Runtime هستند؛ این سند مالک machine-level Condition contract مشترک Report و BusinessRule است. design/usage guidance در `source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/deep/conditions.md` قرار دارد.

## Canonical syntax

### Leaf

```json
{"field":110,"operator":"greaterThan","value":0}
```

Shape نوع را مشخص می‌کند؛ default noise نوشته نمی‌شود:

```text
type="condition"
valueType="constant"
enabled=true
ignoreCase=false
autoSetInNew=false
customCodeExecutePerRow=false
```

non-defaultها فقط در صورت نیاز صریح نوشته می‌شوند.

### AND / OR

```json
{"all":[
  {"field":110,"operator":"greaterThan","value":0},
  {"field":111,"operator":"equal","value":"A"}
]}
```

```json
{"any":[
  {"field":111,"operator":"equal","value":"A"},
  {"field":111,"operator":"equal","value":"B"}
]}
```

nesting recursive است. root `all` تک‌فرزندی default می‌تواند در Export به leaf collapse شود؛ Writer هنگام Apply آن را به `ComplexCondition(All)` موردنیاز Runtime تبدیل می‌کند. definition محلی serialize می‌شود؛ resolved/effective tree جداگانه تولید نمی‌شود.

### Report Parameter

```json
{"field":110,"operator":"equal","parameter":501}
```

Parameter reference فقط وقتی معتبر است که در parameter list همان Report resolve شود؛ id یا name پایدار قابل استفاده است. BusinessRule Designer parameter list گزارش ندارد، پس Rule condition نباید Report Parameter بسازد.

Report Parameter می‌تواند runtime-supplied و `input:false` باشد. اگر FieldInfo شرط default parameter native دارد، name همان contract است؛ مثلاً `امسال` برای DateInfo یا `كاربر جاري` برای UserInfo. مقدار dynamic را AI hard-code نکند. فهرست دقیق native parameterها در `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/01-field-types-reference.fa.md` است.

## Backward compatibility

Reader شکل legacy `type/group/conditions/valueType` و typed Field reference را می‌پذیرد، ولی Export و Documentation فقط shape compact را canonical می‌دانند.

## Field reference / relation path

Field مستقیم:

```json
{"field":110}
```

Relation traversal:

```json
{"field":{"path":[111,100]}}
```

`path` از Entity اصلی به leaf می‌رود. relation path را با SQL دستی جایگزین نکن. `parent/target` عمومی Change همچنان typed reference است چون polymorphic است.

## Comparison operators

`none`, `equal`, `notEqual`, `greaterThan`, `lessThan`, `greaterThanOrEqual`,
`lessThanOrEqual`, `contains`, `doesNotContain`, `startsWith`, `doesNotStartWith`,
`isNull`, `isNotNull`, `between`, `inList`, `notInList`,
`advancedTextSearch`, `advancedTextSearch2`.

نام‌ها normalization semantic enum Runtime هستند؛ typo داخلی مثل `DoseNotContain` وارد contract AI نمی‌شود.

## Null / Date behavior

`nullBehavior` فقط از این values استفاده می‌کند:

`ignoreCondition | checkNullValue | dontIgnore`

numeric enum مجاز نیست.

`dateComparisonMode` از `DateTimeComparisonMode` واقعی Runtime می‌آید و فقط enumهای شناخته‌شده Source پذیرفته می‌شوند.

## Optional advanced properties

فقط با Requirement واقعی:

- `enabled:false`
- `ignoreCase:true`
- `autoSetInNew:true`
- `nullBehavior`
- `dateComparisonMode`
- `predefinedConditionId`
- `serviceAccessConditionId`
- `entity`
- `customSql`
- `customCode`
- `customCodeExecutePerRow:true`

شرط ساده را بی‌دلیل به CustomSql/Code تبدیل نکن.

## BusinessRule branches

بدون شرط:

```json
{"events":[...],"actions":[...]}
```

شرط‌دار:

```json
{
  "events":[...],
  "branches":[
    {"condition":{"field":110,"operator":"greaterThan","value":0},"actions":[...]},
    {"else":true,"actions":[...]}
  ]
}
```

قواعد Source-derived:

- branch شرط‌دار = `BRExpressionCondition.Condition : ComplexCondition`.
- else = `BRElseCondition`.
- چند expression branch مجاز است.
- حداکثر یک Else؛ Else بدون expression branch قبلی معتبر نیست.
- رسیدن به Else semantic است؛ branchهای بعد از Else اجرا نمی‌شوند. AI Else را canonical در انتها تولید کند، ولی read-back legacy صرفاً به‌خاطر Else میانی invalid اعلام نشود.
- هر branch action list خودش را دارد.
- Rule Designer همان Condition editor را با Entity مالک Rule باز می‌کند.
- `actions` top-level فقط برای Rule بدون Condition است؛ Rule شرط‌دار از `branches` استفاده می‌کند.

## عدم حدس

- «تعداد باید مثبت باشد» می‌تواند با `lessThanOrEqual 0` و action مناسب مدل شود، اگر event requirement روشن باشد.
- predicateهایی مثل cardinality/aggregate روی list فقط وقتی ساخته شوند که operator/FieldItem واقعی آن در Source روشن باشد؛ از Condition عمومی قابلیت aggregate حدس نزن.

## Ownership links

- BusinessRule container/persistence: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/04-business-rules-constraints.fa.md`
- Report container/parameter/FieldItem: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/05-report-folder-reference.fa.md`
- design/usage guidance only: `source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/deep/conditions.md`

## profile v14 — Report parameter/data constants

Report parameter local identity = `Parameter.Name` (در scope همان Report). Export جدید condition را به‌صورت `{parameter:{name:"..."}}` می‌دهد؛ reader برای backward compatibility id قدیمی را می‌خواند ولی serializer جدید raw parameter id تولید نمی‌کند.

اگر constant مربوط به MetaObject/User row باشد، raw row id صادر نمی‌شود؛ external data dependency Designer-readable + explicit deployment mapping استفاده می‌شود. unresolved mapping قبل از Apply Plan را invalid می‌کند.

