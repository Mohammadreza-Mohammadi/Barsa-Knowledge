# مرجع Report / Column / Condition / Folder برای AI

این سند از Source واقعی `Barsa.Meta` و `Barsa.Meta.Ui.Win` استخراج شده است. هدف، قرارداد semantic قابل استفاده برای Inspect/Change/Plan/Apply/Verify است؛ نه dump کردن `ReportData` یا payloadهای داخلی Designer.

## Scope

تمام `ReportData.ReportTypeEnum`ها در مدل پایه حضور دارند:

| semantic type | Runtime enum | وضعیت فعلی |
|---|---|---|
| `list` | `ViewResults` | common + design settings |
| `statistics` | `Statistics` | base lifecycle؛ design اختصاصی deferred |
| `tree` | `TreeView` | common + tree settings |
| `matrix` | `MatrixView` | common + matrix settings |
| `calendar` | `CalendarView` | common + calendar settings |
| `print` | `PrintView` | base lifecycle؛ template/design deferred |
| `heterogeneousTree` | `HetrogeniousTree` | common settings |
| `heterogeneousTreeNonGraphical` | `HetrogeniousTree_NoneGraphical` | common settings |
| `gantt` | `GauntView` | common settings؛ type-specific extra payload فقط با Source جدا |
| `form` | `FormView` | common settings |
| `forum` | `ForumView` | common + forum settings |
| `dashboard` | `Dashboard` | base lifecycle؛ dashboard design deferred |

قاعده: وجود یک نوع در Scope به معنی مجاز بودن dump/write payload اختصاصی آن نیست. Statistical/Dashboard/Print قابل تشخیص و lifecycle پایه/common دارند، اما designer-specific settings آنها همچنان deferred است.

## Lifecycle رسمی Report

Report object مستقل است و Parent semantic آن Entity است.

Create رسمی از constructor Runtime انجام می‌شود:

```text
new Report(name, typeDef, false, systemId)
→ semantic patch
→ PrepareForUpdate()
→ Create()
```

Update:

```text
load Report
→ semantic patch
→ Report.Update()
```

`Update()` مسیر `PrepareForUpdate()` را اجرا می‌کند. Prepare شامل FixId/MetaCode و آماده‌سازی Column/Condition/Group/FormatCondition و ReportData serialized blob است. AI این blob را contract نمی‌داند.

Delete از `Report.Delete()` است.

## Report Create — write contract

مالک Report در Create از **`parent` با `objectType:"entity"`** تعیین می‌شود. Provider همان Entity را resolve می‌کند و `new Report(name, typeDef, false, typeDef.SystemId)` می‌سازد. `properties.name` نیز برای Create اجباری است.

`entity` و `system` که در **Semantic read-back** Report دیده می‌شوند derived information هستند: `entity` از `Report.TypeDefId` و `system` از `Report.SystemId` serialize می‌شوند. این دو عضو `AiReportModel.KnownReportProperties` نیستند و نباید در `properties` یک Report Create/Update نوشته شوند. Provider برای property ناشناخته Plan را unsupported می‌کند؛ Runtime نباید برای پذیرش payload غلط permissive شود.

شکل حداقلی Create:

```json
{
  "operation":"create",
  "objectType":"report",
  "tempId":"listReport",
  "parent":{"objectType":"entity","tempId":"entity1"},
  "properties":{
    "name":"فهرست",
    "reportType":"list",
    "columns":[]
  }
}
```

Propertyهای قابل patch همان فهرست **Common report settings / `KnownReportProperties`** این سند هستند؛ مشاهده یک property در Semantic read shape به‌تنهایی writeability آن را ثابت نمی‌کند. validation shape/field paths در Plan انجام می‌شود و اگر temp reference وجود داشته باشد validation وابسته پس از resolve در Apply تکرار می‌شود.

## Semantic Report

نمونه فشرده:

```json
{
  "objectType":"report",
  "name":"فهرست فاکتورها",
  "reportType":"list",
  "entity":{"objectType":"entity","id":100},
  "system":{"objectType":"system","id":10},
  "columns":[...],
  "condition":{...},
  "sorting":[...],
  "sqlGrouping":[...],
  "gridGrouping":[...],
  "parameters":[...],
  "joinAliases":[...],
  "formatConditions":[...]
}
```

Read-back و Verify از Semantic shape استفاده می‌کنند، اما Write یک **patch subset** از `KnownReportProperties` است و read-only/derived propertyهای Semantic را نمی‌پذیرد. Verifier فقط propertyهای درخواست‌شده‌ی همان patch را مقایسه می‌کند.

در Verify، تفاوت‌های persistence-only نباید false-negative بسازند:
- `ComplexCondition/SingleCondition.id` هویت داخلی Runtime است و در مقایسه semantic نادیده گرفته می‌شود.
- wrapper پیش‌فرض `all` با یک child می‌تواند با همان leaf معادل شود.
- Reference پارامتر شرط می‌تواند در Action با `name` یا `id` بیاید؛ Verifier نام Parameter همان Report را قبل از مقایسه به Runtime id آن normalize می‌کند.

## `preserveUserViewState` exact write contract

`preserveUserViewState` یک **string enum** است، نه boolean/number/array. Provider authority همان `ReportData.PreserveUserViewStateEnum` است؛ فقط نام واقعی enum به‌صورت case-insensitive پذیرفته می‌شود و numeric string/ordinal مثل `"1"` معتبر نیست. read-back نام enum را camelCase می‌کند؛ canonical token همان نام واقعی Runtime enum با camelCase است.

Source bundle این repository declaration خود `ReportData.PreserveUserViewStateEnum` را حمل نمی‌کند، پس DX فهرست نام‌ها را حدس یا hardcode نمی‌کند. برای جلوگیری از ambiguity عملی، Plan validation در `AiReportModel` روی token نامعتبر، **allowed values واقعی همان deployment** را با `Enum.GetNames(typeof(ReportData.PreserveUserViewStateEnum))` و camelCase در diagnostic برمی‌گرداند. numeric ordinal یا boolean contract نیست.

## Common report settings

Propertyهای Designer-backed زیر در contract semantic جاری هستند:

- `name`, `description`, `sharedScope`, `reportType`
- `columns`, `condition`, `sorting`, `sqlGrouping`, `gridGrouping`
- `parameters`, `joinAliases`, `formatConditions`
- `ignoreColumns`
- `extraQueryTemplate`, `alternateRootTable`, `rootTableAlias`
- `ignoreAdvancedSecurityCondition`, `useAdvancedAccess`
- `preserveUserViewState`
- `showWpfChart`
- `allowView`
- `parameterEntity`
- `alternateRowMode`
- `gridShowSelectionChecks`
- `logExecutions`
- `hideToolbar`, `hideRowIcon`
- `typeView`, `listEditView`
- `customSql`, `oracleHint`, `additionalWhere`
- `isDistinct`, `includeDeleted`
- `showRecordSignFormatting`
- `pagingType`, `pageSize`
- `gridLines`, `gridViewStyle`, `gridHideLines`, `gridCustomKey`
- `freeColumnSizing`, `useSummaryRow`, `top`
- `allowRemove`, `allowEdit`, `allowAddToList`, `allowRemoveFromList`, `allowAddNew`
- `showRowNumber`, `allowInlineEdit`, `autoInlineEdit`
- `hideHeader`, `disableColumnHeaders`, `allowGridColumnSort`
- `insideViewHeight`, `insideViewActive`, `insideViewRelatedField`
- `selfReferencingField`
- `treeAutoOpenLevels`, `dontUseChildParentReport`, `useHierarchyConditionForRoot`, `treeCondition`
- `commandDisplayMode`
- `previewState`, `showPreviewField`, `previewField`
- `parameterPanelHeight`
- `parameterLayout` (`mode`, `columns`, `autoHeight`, `showSearch`)
- `subReports`
- `immediateExecute`
- `alternateEditObjectColumn`
- `disableOptimizeForDisplay`, `dontExecuteCount`
- type-specific common sections: `matrix`, `calendar`, `forum`

### چیزهایی که عمداً semantic نیستند

- cached/resolved/effective variants
- `GridCustomization`/chart customization binary state
- `ParameterLayoutXml`
- raw GZip ReportData
- raw `ExtraData`/`ExtraData1` فقط برای پر کردن Gap
- deep Statistical/Dashboard/Print design payload

`ParameterDesign.Height` و intent فشرده `parameterLayout` semantic هستند؛ `ParameterLayoutXml` implementation detail است.

## Column

Column semantic:

```json
{
  "id":501,
  "field":{
    "field":{"objectType":"field","id":101}
  },
  "alias":"کد",
  "enabled":true,
  "visible":true,
  "width":120,
  "fixedWidth":false,
  "wordWrap":false,
  "tooltip":"...",
  "joinForCaption":true,
  "customSqlAlias":"...",
  "customCode":"...",
  "customSql":"..."
}
```

Column می‌تواند به‌جای Field ساده، `cases`/AdvancedFormula داشته باشد. این مدل از CaseList واقعی Source استخراج می‌شود؛ raw MetaCode dump نمی‌شود.

## Field path / relation traversal

`FieldItem` path recursive است. هر node شامل Field و در صورت نیاز parent relation path است.

نمونه مفهومی:

```json
{
  "field":{"objectType":"field","id":priceFieldId},
  "parent":{
    "field":{"objectType":"field","id":productRelationId},
    "relationDirection":"direct"
  }
}
```

`relationDirection` از Runtime Direct/Reverse استخراج می‌شود. `joinAlias` نیز در FieldItem قابل reference است.

AI نباید SQL join حدسی بسازد وقتی FieldItem path رسمی کافی است.

## Sorting

```json
{
  "field":{...FieldItem...},
  "direction":"asc"
}
```

قرارداد canonical read/write برای `sorting.direction` فقط `asc` و `desc` است. serializer رسمی `AiReportModel` نیز فقط همین دو مقدار را در read-back تولید می‌کند؛ Change باید از ابتدا یکی از همین valueها را بنویسد تا Verify با representation canonical مقایسه شود. alias دیگری جزو قرارداد Agent-facing نیست.

## Grouping

دو مفهوم جدا هستند:

### `sqlGrouping`

معادل `ReportData.Grouping` و تولیدکننده SQL `GROUP BY` است. فقط وقتی query از نظر SQL معتبر است استفاده شود. Writer canonical نام `sqlGrouping` را تولید می‌کند.

### `gridGrouping`

گروه‌بندی نمایشی Grid است و SQL query را به `GROUP BY` تبدیل نمی‌کند. برای list/report معمول که فقط نمایش گروه‌شده می‌خواهد از این مسیر استفاده کن.

Plan ناسازگاری روشن `sqlGrouping` با ستون‌های SELECT غیرaggregate را قبل Apply رد می‌کند.

## Parameters

پارامتر Report:

```json
{
  "id":601,
  "name":"customerId",
  "caption":"مشتری",
  "value":null,
  "field":{"objectType":"field","id":101},
  "external":true,
  "input":true,
  "fromParent":false,
  "ignoreReport":false,
  "mandatory":true,
  "notAutoRemove":false,
  "behindReport":{"objectType":"report","id":700},
  "sourceOperator":"equal",
  "code":"..."
}
```

نام پارامتر در یک Report باید یکتا باشد.

### External parameter و parent-context در Query Formula

Source جاری دو رفتار دقیق را روشن می‌کند:

- `ReportData.AddCustomAskParameter(...)` پارامتر تازه را با `IsInput=true` و `NotAutoRemove=true` می‌سازد. `AddExternalParameter(...)` سپس همان Parameter را به `IsInput=false`, `IsExternal=true`, `Caption=name` تبدیل می‌کند؛ بنابراین external parameter ساخته‌شده از این helper به‌طور طبیعی `NotAutoRemove=true` را نیز حفظ می‌کند.
- اجرای query-backed Formula قبل از ساخت single-valued query، `ReportData.SetParameterValuesByParentObject(parentObject)` را فراخوانی می‌کند. برای Parameter با `IsExternal=true`: اگر `Name == "Id"` باشد مقدار `parentObject.Id` تزریق می‌شود؛ در غیر این صورت Runtime Field والد را با Caption برابر `parameter.Name` پیدا می‌کند و مقدار همان Field را می‌گذارد.

DataExchange Semantic v15 برای Parameterها `input=false` و `notAutoRemove=false` را default می‌کند؛ فقط input واقعی باید صریحاً `input=true` داشته باشد. `currentUser` یک context parameter با `input=false` است و نباید مانند ordinary input parameter تفسیر شود.

### Runtime default parameters از FieldInfo

همه Parameterها Asked/Input نیستند. بعضی FieldInfoها Parameterهای native دارند که مقدارشان هنگام اجرای Condition توسط Runtime resolve می‌شود. در این حالت AI باید **نام native Parameter** را نگه دارد و مقدار dynamic را به constant/code تبدیل نکند.

نمونه برای Field تاریخ/زمان:

```json
{
  "parameters":[
    {"name":"امسال","caption":"امسال","input":false,"external":false,"fromParent":false,"mandatory":false,"notAutoRemove":false}
  ],
  "condition":{
    "field":123,
    "operator":"equal",
    "parameter":"امسال",
    "nullBehavior":"dontIgnore"
  }
}
```

در این مدل خود Parameter لازم نیست value ثابت داشته باشد؛ FieldInfo شرط (`DateInfo` یا subtype سازگار آن) نام `امسال` را در Runtime به بازه سال جاری resolve می‌کند.

Parameterهای Source-confirmed `DateInfo`:

```text
اکنون
امروز
اين هفته
اين ماه
امسال
ديروز
هفته پيش
ماه پيش
سال پيش
فردا
هفته بعد
ماه بعد
سال بعد
```

برای Field نوع `UserInfo` نیز Parameter native زیر موجود است:

```text
كاربر جاري → Util.CurrentUserId
```

قاعده عمومی: default parameter فقط وقتی native محسوب می‌شود که FieldInfo/Runtime Source آن را تعریف کرده باشد. از روی نام مشابه Parameter جدید اختراع نکن.

## Asked parameter panel — `parameterLayout` contract

Source جاری `AiReportModel` intent فشرده زیر را برای layout پارامترهای input می‌پذیرد:

```json
"parameterLayout": {
  "mode": "compact",
  "columns": 2,
  "autoHeight": true,
  "showSearch": true
}
```

### Defaults و validation

- `mode` در نبود مقدار = `compact`. مقدار مجاز فقط `compact` یا `default` است.
- `columns` در `compact` در نبود مقدار = `2` و باید در بازه `1..4` باشد.
- `showSearch` در نبود مقدار = `true`.
- `autoHeight` در write در نبود مقدار = `true`. اگر `false` باشد Writer ارتفاع موجود `ParameterDesign.Height` را تغییر نمی‌دهد.
- `mode:"default"`، `ParameterLayoutXml` را `null` می‌کند. اگر `autoHeight` غایب/true باشد، Height با همان محاسبه compact ولی با `columns=1` و Search visible محاسبه می‌شود.

### Geometry compact که adapter تولید می‌کند

فقط input Parameterهایی که `FieldDef` دارند در grid compact قرار می‌گیرند. Source فعلی constants زیر را explicit می‌کند:

- root width = `743`
- content width = `723`
- row height = `24`
- Root padding = `9,9,9,9`
- هر Parameter item padding = `2,2,2,2`
- Parameter item `MinSize = 78 x 24` و `MaxSize = 0 x 24`
- `$Search` width = `723`; visible size = `723 x 28`; hidden size = `723 x 25`; `MinSize = 164 x 28`; `MaxSize = 204 x 34`

ارتفاع compact از فرمول زیر می‌آید:

```text
rows = ceil(inputParameterCount / columns)
height = 18 + rows * 24 + (showSearch ? 28 : 0)
height = max(showSearch ? 46 : 34, height)
```

`18` همان padding بالا+پایین Root (`9 + 9`) است و سهم Search در حالت visible برابر `28` است. مثال Source — چهار Parameter / دو ستون / Search visible → `94px`.

### Flat / RTL materialization

- layout compact **flat** است: Parameterها مستقیم زیر `Root` قرار می‌گیرند و adapter برای ستون‌ها `LayoutGroup` مصنوعی تولید نمی‌کند.
- پنل RTL پر می‌شود: `parameterIndex=0` در ستون راست قرار می‌گیرد، سپس indexها به چپ حرکت می‌کنند و بعد به row بعد می‌روند.
- `$Search` هیچ‌گاه از XML حذف نمی‌شود. `showSearch=true` → `ParentName=Root`; `showSearch=false` → `ParentName=Customization`.
- مختصات column از تقسیم صحیح `contentWidth=723` محاسبه می‌شوند: `x = 723 * visualColumn / columns` و width از اختلاف boundary فعلی/بعدی می‌آید.

### Encoding `Location` / `Size`

`Location` و `Size` با `EncodeLayoutComponent` به‌شکل length-prefixed نوشته می‌شوند:

```text
@<decimal-value-length>,<Name>=<decimal-value>
```

مثال: `X=361` → `@3,X=361` و `Y=24` → `@2,Y=24`. Point از `X+Y` و Size از `Width+Height` با همین encoding ساخته می‌شود.

### Read-back boundary

Semantic read-back فقط layoutهایی را normalize می‌کند که XML آنها marker خود adapter یعنی `BarsaAiCompactParameterLayout:<columns>` را داشته باشد. layoutهای hand-designed DevExpress بدون این marker opaque/local باقی می‌مانند و `parameterLayout` semantic از آنها ساخته نمی‌شود.

برای layout markerدار، read-back `mode:"compact"`، columns marker، `showSearch` از `ParentName` آیتم `$Search` و در Source فعلی `autoHeight:true` را برمی‌گرداند. در نتیجه `autoHeight:false` یک write-time instruction برای حفظ Height است و read-back فعلی آن را به‌صورت flag پایدار round-trip نمی‌کند.

این geometry/encoding contract مربوط به adapter جاری است؛ color/theme/appearance خارج از evidence فعلی است و flag حدسی نباید اضافه شود.

## JoinAlias

```json
{
  "id":701,
  "name":"customerJoin",
  "field":{...FieldItem...},
  "entity":{"objectType":"entity","id":100}
}
```

## Condition

machine-level Condition contract مشترک Report/BusinessRule در `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md` تعریف شده است. Working Knowledge فقط design/usage guidance را نگه می‌دارد.

Report root `condition` یک `ComplexCondition` است. `treeCondition` نیز همان contract را reuse می‌کند.

## Format Conditions

فقط local `GridFormatConditionList` serialize می‌شود؛ `_Resolved` مجاز نیست چون effective/computed state را با local definition مخلوط می‌کند.

```json
{
  "id":801,
  "condition":{...ComplexCondition...},
  "style":{
    "cssClass":"...",
    "column":{"id":501},
    "foreColor":"#...",
    "backColor":"#...",
    "bold":"true",
    "italic":"false",
    "strikeout":"default"
  }
}
```

TriStateها semantic `true/false/default` هستند.

## Matrix

در `reportType=matrix`، Source common properties زیر را روشن می‌کند:

- horizontal column
- vertical column
- value column
- horizontal report
- vertical report

اینها semantic reference هستند. هر payload آماری خارج از این common contract بعداً تکمیل می‌شود.

## Calendar

`calendar` شامل Field referenceهای زیر است:

- name
- description
- startDate
- endDate
- ownerId
- hasReminder
- imageType
- color
- groupColorField
- ownerReport

## Forum

`forum` شامل:

- titleField
- descriptionField
- timeField
- ownerIdField

## Tree / hierarchy

Common tree settings:

- `selfReferencingField`
- `treeAutoOpenLevels`
- `dontUseChildParentReport`
- `useHierarchyConditionForRoot`
- `treeCondition`

این‌ها از Designer واقعی آمده‌اند؛ effective child-parent resolution serialize نمی‌شود.

## Union / SubReports

Designer `ReportData.SubReports` را به‌عنوان composition report IDs نگه می‌دارد. Semantic:

```json
"subReports":[
  {"objectType":"report","id":1001},
  {"objectType":"report","id":1002}
]
```

این بخش برای Union/composition common پشتیبانی می‌شود. Aggregate design اختصاصی همچنان deferred است.

## Report formula columns

Source `FormulaParser` برای **Report column formulas** syntaxهای caption-based را پشتیبانی می‌کند، از جمله:

- `{Field Caption}`
- `{Relation Caption}.{Field Caption}`
- operator/aggregate روی relation path

این syntax مخصوص مسیر Report Formula Parser است. از آن برای `Field.formula.code` نتیجه‌گیری نکن؛ Field Formula از compiler مسیر Field/Designer استفاده می‌کند.

## Folder / Navigation

Report placement object مستقل است و Report داخل Folder JSON embed نمی‌شود. ساختار canonical Navigation گزارش:

```text
System Root
└─ Page
   └─ Group
      └─ Report
```

Semantic:
- Page: `kind:"page"` و parent System
- Group: `kind:"group"` و parent Page
- Report placement: `kind:"report"` و parent Group + report reference

Page و Group در Runtime هر دو `FolderType.ReportFolder` هستند و hierarchy معنای semantic آنها را تعیین می‌کند. Report leaf `FolderType.Report` است.

Lifecycle:
- create: `Folder.GetNew(...)` + `Create()`
- move: `Folder.Move(source,destinationParent)`
- update/delete: lifecycle خود Folder
- System parent به `MetaSystem.RootFolderId` resolve می‌شود.
- affected System از `Folder.GetRelatedSystemId()` گرفته می‌شود.
- پس از AI-created Root/Page/Group/Report Folder فقط `ReportService.ViewContent` برای `Barsa.Spl.BasicInfo.User.AdminUserGlobalId` روی همان `met_folder` تکمیل می‌شود؛ permission موازی روی Report/Entity ساخته نمی‌شود.

### User-facing delivery و same-wave dependency

Report metadata و navigation دو object/lifecycle جدا هستند. برای Report helper/internal، Folder placement لازم نیست. برای Report **user-facing**، وجود metadata به‌تنهایی delivery کامل نیست: قبل از Change باید همین exact contract مصرف شود و placement موجود مناسب reuse یا کوچک‌ترین structure طراحی‌شده‌ی `System → Page → Group → Report placement` نیز در outcome باشد. نام Page/Group از Requirement/Design می‌آید؛ Host آنها را خودکار اختراع نمی‌کند. Report placement باید با `properties.report` به همان Report موردنظر اشاره کند.

Planner `tempId`ها را از `target`، `parent` و به‌صورت recursive از `properties` جمع می‌کند. بنابراین **پیش‌فرض یک logical Change wave** است وقتی dependencyها با reference موقت قابل بیان‌اند: Page parent=System، Group parent=`page tempId` و Report placement parent=`group tempId` با `properties.report={objectType:"report",tempId:"report tempId"}`. Report column/FieldItem نیز reference موقت Field همان Batch را deferred-validate و در Apply resolve می‌کند. Apply پس از resolve dependency همان objectهای ساخته‌شده را مصرف می‌کند؛ گرفتن real id به‌تنهایی دلیل Change دوم نیست. Wave فقط وقتی شکسته می‌شود که contract واقعاً persisted id/read-back مرحله قبل را لازم داشته باشد یا ambiguity/runtime evidence تصمیم بعدی را تعیین کند.

Metadata verification هر command فقط همان object/patch را read-back می‌کند. وجود Report metadata به‌تنهایی وجود navigation را اثبات نمی‌کند؛ اگر navigation جزو Design outcome است، Folder placementها نیز باید در Change/Read-back/Verify scope باشند و completion باید به **همان Report + placement** trace شود.

## Statistical / Dashboard / Print — مرز فعلی

این سه نوع **داخل Scope هستند** ولی design-specific payloadشان در write contract عمومی فعلی نیست.

Supported now:

- reportType
- name/description و owner مشتق‌شده از parent Entity؛ `system/entity` read-only derived Semantic information هستند
- common ReportData settings که برای نوع معتبرند
- Folder placement
- Create/Update/Delete
- semantic Read-back/Verify common properties

Deferred:

- Statistics/Aggregate-specific design object
- Dashboard widget/layout/data binding design
- Print/Word template/design payload

تا Source اختصاصی هرکدام بررسی نشود، raw object/blob راه جایگزین نیست.

## Canonical FieldItem contract

Field مستقیم برای کاهش token یک reference مستقیم است:

```json
{"field":{"objectType":"field","id":101},"alias":"کد"}
```

Relation traversal معمولی با path از Entity اصلی تا leaf بیان می‌شود:

```json
{
  "field": {
    "path": [
      {"objectType":"field","id":/* relation */},
      {"objectType":"field","id":/* leaf */}
    ]
  },
  "alias":"نام مرتبط"
}
```

- Writer chain را با lifecycle/helper رسمی `FieldItem.CreateNew(parentItem, childField)` می‌سازد.
- `parentItem` property داخلی Runtime است و در سطح Column emit نمی‌شود.
- `relationDirection:"reverse"` فقط در traversal معکوس لازم است.
- `condition` singular است.
- Placement گزارش با change مستقل `objectType:"folder", kind:"report"` انجام می‌شود.
- Reader می‌تواند ورودی‌های compatibility را تحمل کند، ولی Writer فقط شکل canonical را تولید می‌کند.

## profile v14 — Report + Navigation portability

- Report condition که به Parameter وصل است، Parameter را با `name` محلی Report بیان می‌کند؛ raw Parameter id contract نهایی نیست.
- constant user/data از همان external-data dependency مشترک Field استفاده می‌کند.
- `allowInlineEdit=true` default واقعی Runtime است و در Semantic به‌عنوان noise تکرار نمی‌شود.
- `TranslationKey` serializer/runtime leak از Semantic حذف می‌شود.
- fallback Reportها همان standalone Report materialization را می‌گیرند؛ `System.MetaReport` Design object مستقل نیست.

Navigation Designer model:

```text
System
└─ Root (automatic, not a Semantic object)
   └─ Page
      └─ Group
         └─ Report placement
```

Page/Group `name + parentRef + order + icon` را در صورت meaningful نگه می‌دارند. placement `target report + parentRef + order` دارد و title/icon آن از target derivable است. Folder writer در این candidate order و Designer icon-name را write/read-back می‌کند. Access/security فقط پس از exact source-backed non-default contract باید اضافه شود؛ current default access rebuild blocker نیست.

## Re-export fix v149 — fallback Report و canonical placement

- Runtime fallback Report شیء Report واقعی است؛ `MetaReport` فقط ownership/materialization route است. fallback metadata باید selection-backed باشد تا Report در `[گزارش]` مثل سایر Reportها standalone materialize شود و `System.MetaReport` داخل design payload نماند.
- Full fallback باید `ReportData` واقعی را نیز بخواند و `{id,name}` stub نباشد.
- Navigation Page که parent آن auto Root است `parentRef:"root"` دارد؛ خود Root object همچنان در Semantic materialize نمی‌شود.
- Report placement فقط scalar `report` reference + `parentRef` + `order` (و kind/ref فنی لازم برای local navigation identity) را نگه می‌دارد. relation array حاوی Report کامل قبل از package materialization حذف می‌شود؛ title/icon placement از target Report مشتق است.

