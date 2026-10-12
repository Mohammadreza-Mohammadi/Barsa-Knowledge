# مرجع View و Layout برای AI/Codex

این سند مرجع پایدار حاصل بررسی `TypeViewEntity/TypeView/FieldView`، Windows Designer، `MetaLayoutControl`، `LayoutParser94/LayoutMaker94` و نمونه‌های واقعی Layout است. در گفتگوهای بعدی این سند مرجع مدل View/Layout است؛ Source فقط هنگام تناقض Runtime یا قابلیت خارج از این قرارداد دوباره خوانده شود.

## اصل محوری: Local Source-of-Truth، نه Effective State

`TypeViewEntity` بخش‌های زیر را می‌تواند از Parent View یا Default Edit View resolve کند:

- `FieldListSettings`
- `LayoutSettings`
- `FormSettings`
- `SelectedRuleList`

AI فقط **local/explicit state** را Serialize و mutate می‌کند. Effective/resolved state تعریف قابل ویرایش View نیست و نباید در Export تکرار شود.

### Hint عمومی برای موارد مشابه

هرجا Runtime/Designer مفهومی از نوع `inherited / computed / resolved / effective` دارد:

1. local/explicit source-of-truth را Serialize/Write کن؛
2. منبع inheritance/reference را جدا نشان بده؛
3. effective state را برای تعریف قابل ویرایش copy نکن؛
4. computed/read-only property را Write-enabled فرض نکن؛
5. implementation detail را فقط در adapter/generation نگه دار، مگر اینکه مالک صریحاً خلاف آن را بخواهد.

این قاعده مخصوص View نیست و برای مدل‌های مشابه آینده نیز اعمال می‌شود.

## Patch semantics

- property غایب: no-change
- `fields:null`: local FieldListSettings حذف → inherit
- `layout:null`: local LayoutSettings حذف → inherit
- `formSettings:null`: local FormSettings حذف → inherit
- `selectedRules:null`: local SelectedRuleList حذف → inherit
- `selectedRules:[]`: local override صریح با «هیچ Rule»؛ inherit نیست
- object/list: local override صریح

### Layout محلی پیش‌فرض

`LayoutSettings != null` با `LayoutXml` خالی در Runtime به معنی inherit نیست؛ یعنی View بخش Layout محلی دارد ولی Runtime چیدمان پیش‌فرض را Restore می‌کند. قرارداد Semantic:

```json
{"layout":{"mode":"default"}}
```

بنابراین:

- `layout:null` = inherit
- `layout:{"mode":"default"}` = local default layout
- `layout:{...tree...}` = local semantic layout

## قرارداد View

`objectType = "view"` و Parent Change همیشه Entity مالک است.

```json
{
  "operation":"create",
  "objectType":"view",
  "tempId":"mainView",
  "parent":{"objectType":"entity","id":100},
  "properties":{
    "name":"نمای اصلی",
    "inheritsFrom":null,
    "fields":null,
    "layout":{"mode":"default"},
    "formSettings":null,
    "selectedRules":[]
  }
}
```

Propertyها:

| Property | معنی |
|---|---|
| `name` | نام View؛ در Entity یکتا |
| `inheritsFrom` | View پایه صریح از **همان Entity**؛ `null` یعنی ParentId=0 |
| `relatedParentView` | View متناظر در Entity والد inheritance؛ فقط وقتی Entity inheritance parent دارد |
| `fields` | Field settings محلی؛ null=inherit |
| `layout` | Layout محلی semantic؛ null=inherit |
| `formSettings` | Form settings محلی؛ null=inherit |
| `selectedRules` | Rule/UniqueConstraintهای local؛ null=inherit، []=none |

قواعد Designer:

- Default Edit View setting مستقلی روی TypeDef است؛ Create View آن را خودکار تغییر نمی‌دهد.
- Default Edit View نمی‌تواند از View دیگری inherit کند.
- `inheritsFrom` فقط View همان Entity است.
- `relatedParentView` فقط View متعلق به `InheritanceParentInfo.TargetTypeId` است.

## Operational wiring: Primary / Default Edit View

ساختن یک View به‌تنهایی آن را View اصلی Entity نمی‌کند. Source `AiEntityChangeProvider` setting رسمی `TypeDef.SettingsObject.DefaultEditViewId` را از طریق **Entity update** expose می‌کند. representation canonical AI-facing برابر `properties.defaultEditView` است:

```json
{
  "operation":"update",
  "objectType":"entity",
  "target":{"objectType":"entity","tempId":"customerEntity"},
  "properties":{
    "defaultEditView":{"objectType":"view","tempId":"mainView"}
  }
}
```

قواعد exact Source:

- `defaultEditView` فقط reference معنایی می‌پذیرد: View همان batch با `tempId` یا View persisted با selector canonical `#...`. Runtime ID در SOC ممنوع است؛ `null` setting را clear می‌کند.
- `tempId` از همان `AiBatchExecutionContext` resolve می‌شود؛ بنابراین `Entity create → View create → Entity update(defaultEditView)` می‌تواند در **همان logical Change batch** باشد. گرفتن real ID برای این wiring لازم نیست.
- View باید متعلق به همان Entity باشد.
- View انتخاب‌شده برای Default Edit View نباید از View دیگری inherit کند (`ParentId=0`).
- Create View هیچ auto-wiring انجام نمی‌دهد. فقط Viewی که Design آن را Primary/Main Edit View تعیین کرده باید صریح wire شود؛ Secondary View خودکار Default نمی‌شود.
- Runtime verifier مقدار `TypeDef.SettingsObject.DefaultEditViewId` را read-back و با requested `defaultEditView` مقایسه می‌کند؛ Verify نباید صرف وجود View را proof این wiring بداند.

در executable Semantic v15 فقط `defaultEditView` property canonical و authorable است. Aliasهای legacy `defaultView`، `defaultEditViewId` و `defaultViewId` ورودی canonical نیستند و در Lint/Plan رد می‌شوند؛ هیچ‌کدام مسیر validation جدا یا Runtime-ID fallback ندارند.

## Field settings داخل View

```json
{
  "fields": {
    "tabOrderByFieldOrder": true,
    "items": [
      {
        "field":{"objectType":"field","id":101},
        "visible":true,
        "editable":true,
        "mandatory":false,
        "prominent":false,
        "reportView":{"objectType":"report","id":201},
        "tabOrder":1
      }
    ]
  }
}
```

وقتی `fields` object ارسال می‌شود، Writer همان رفتار Designer را مبنا می‌گیرد: ابتدا `FieldListSettings.CreateFieldListSettings(owner)` کل Fieldهای Entity را با Defaultهای Designer می‌سازد و سپس `items` فقط overrideهای صریح روی آن لیست کامل‌اند. بنابراین کل section یک **local replacement** است، ولی لازم نیست AI همه Fieldها را در `items` تکرار کند.

قواعد:

- هر Field باید متعلق به همان Entity باشد.
- Field تکراری در `items` مجاز نیست.
- `visible/editable/mandatory/prominent` nullable هستند؛ `null` با false متفاوت است.
- `reportView` با setter رسمی `FieldView.ReportView` اعمال می‌شود؛ `ReportViewId` read-only است.
- `tabOrderByFieldOrder=true` باعث `SetTabOrders()` روی local list می‌شود.

## Form settings

Propertyهای Semantic/Designer-visible:

- `changeOrderByEnter`
- `isResizable`
- `useToolboxTitlebar`
- `showToolbar`
- `showSendMail`
- `showRefTree`
- `showSaveButton`
- `showLabelsColored`
- `hideControlBordersWhenReadonly`
- `showColonInLabels`
- `dontShowInWorkflow`
- `showParentFormInInheritance`

`MinimumSize` وجود دارد اما pixel/geometry است و عمداً جزو AI contract نیست.

## Layout Semantic

Runtime Windows از DevExpress XML استفاده می‌کند؛ XML/coordinate/size/serializer metadata زبان AI نیست.

نمونه:

```json
{
  "type":"group",
  "direction":"vertical",
  "children":[
    {"type":"field","field":{"objectType":"field","id":101}},
    {
      "type":"group",
      "caption":"مشخصات",
      "direction":"horizontal",
      "children":[
        {"type":"field","field":{"objectType":"field","id":102}},
        {"type":"field","field":{"objectType":"field","id":103}}
      ]
    },
    {
      "type":"tabs",
      "selected":"اسناد",
      "tabs":[
        {"type":"tab","caption":"اسناد","children":[{"type":"field","field":{"objectType":"field","id":104}}]},
        {"type":"tab","caption":"توضیحات","children":[{"type":"field","field":{"objectType":"field","id":105}}]}
      ]
    }
  ]
}
```

Nodeها:

- `group`: `caption`, `direction=vertical|horizontal`, `border`, `expanded`, `children`
- `field`: `field`, `caption`, `labelVisible`, `textLocation=default|left|right|top|bottom`
- `tabs`: `caption`, `selected`, `tabs`
- `tab`: `caption`, `children`
- `space`
- `label`: `caption`
- `separator`
- `splitter`: `direction=vertical|horizontal`

قواعد:

- root semantic layout یک container مصنوعی Runtime است. `caption` روی **root group** جزو round-trip contract نیست و نباید نوشته شود؛ Writer/Plan آن را reject می‌کند. `caption` فقط برای nested groupهای واقعی مجاز است و همان‌ها در read-back حفظ می‌شوند.
- Field reference باید به Field همان Entity resolve شود. reference canonical می‌تواند `id` یا، داخل همان `AiChangeBatch`، `tempId` همان Field باشد؛ execution context بعد از dependency resolution آن را به Runtime Field واقعی resolve می‌کند. بنابراین ساخت Field و View layout وابسته می‌تواند یک logical Change wave بماند.
- یک Field در یک semantic layout فقط یک بار می‌آید؛ XML Runtime از `DbName` به‌عنوان ControlName استفاده می‌کند.
- raw XML، `Location`, `Size`, pixel و propertyهای DevExpress در Change پذیرفته نمی‌شوند.

### Generation boundary

Adapter داخلی از semantic tree XML حداقلی و deterministic می‌سازد. برای سازگاری Runtime مجبور است `Location/Size/TextLocation` و ساختار flat DevExpress را تولید کند؛ این داده‌ها فقط generation detail هستند و source-of-truth AI نیستند.

این نمونه رسمی Rule عمومی «Generation detail is not AI contract» است.

## Serialization profile (`profileVersion=14`)

```json
{
  "id":123,
  "semanticId":"system:فروش/entity:مشتری/view:نمای اصلی",
  "name":"نمای اصلی",
  "inheritsFrom":{
    "objectType":"view",
    "id":120,
    "semanticId":"system:فروش/entity:مشتری/view:نمای پایه"
  },
  "definition":{
    "fields":{...},
    "layout":{...},
    "formSettings":{...},
    "selectedRules":[...]
  }
}
```

Entity مالک از nesting Semantic معلوم است و reference تکراری آن در خود View حذف می‌شود. `inheritsFrom` حذف نمی‌شود چون همان `ParentId` و یک رابطه معنایی واقعی به View دیگر است. فقط sectionهای local داخل `definition` می‌آیند. `_Resolved`, Parent object dump، raw `TypeViewBlob` و effective values حذف‌اند.

`selectedRules` می‌تواند هم `businessRule` و هم `uniqueConstraint` reference باشد و هر reference باید متعلق به RuleList همان Entity باشد.

## Runtime Verify

پس از Apply، View با `TypeViewEntity.LoadById` دوباره خوانده و local TypeView به همان Semantic model Serialize می‌شود. فقط patch درخواست‌شده مقایسه می‌شود؛ absent property no-change باقی می‌ماند. چون root group مصنوعی است، Semantic canonical آن `caption` ندارد؛ Agent باید از ابتدا root بدون caption بسازد، نه اینکه Verify درخواست non-canonical را نادیده بگیرد.

## Field lookup در Layout parser/serializer

برای resolve کردن Field از `TypeDef.FieldDefList` در مسیرهای Layout، collection را قبل از LINQ materialize کن:

```csharp
var field = typeDef.FieldDefList
    .ToArray<FieldDef>()
    .FirstOrDefault(x => string.Equals(x.DbName, dbName, StringComparison.OrdinalIgnoreCase));
```

این الگوی compatibility در Source فعلی `BixJsonExportManager` و `AiViewRuleModel` استفاده شده است. تا وقتی API واقعی `FieldDefList` تغییر نکرده، lookup مستقیم LINQ روی collection را جایگزین آن نکن.

## profile v14 — unresolved layout nodes

در Semantic projection، layout nodeای که به Field موجود همان Entity resolve نشود drop می‌شود. این filter عمومی است و بر ID/dbName خاص hard-code نشده است. Full Structured raw layout را برای diagnosis نگه می‌دارد.

## v177 Layout authority

`AiSemanticLayoutModel` authority مشترک مسیر Semantic Layout است: authored SOC → generated Runtime XML و Runtime XML → canonical SOC projection/Verify. `textLocation=top|right|...` باید Save/Reload/Read-back را round-trip کند و special-case ignore نمی‌شود.

