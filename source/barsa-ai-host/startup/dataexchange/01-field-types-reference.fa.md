# مرجع پایدار انواع Field در SystemBuilder

> وضعیت: مرجع Source-study برای AI/Codex و توسعه `Barsa.Meta.DataExchange`  
> مبنا: `FieldInfo` runtime source + Windows Designer (`FieldInfo.ui`) + نمونه‌های واقعی Export و semantic export جاری.  
> هدف: در گفتگوها و تغییرات بعدی برای شناخت Fieldها نیازی به بازخوانی Sourceهای اصلی نباشد؛ فقط اگر رفتار جدید/متناقض در Runtime دیده شد Source دوباره بررسی شود.

## 1. قواعد پایه

Field در Runtime از `FieldDef + FieldInfoBase` تشکیل می‌شود. `FieldDef` هویت/مالک/نام DB/ترتیب را نگه می‌دارد و `FieldInfo` نوع و رفتار را تعیین می‌کند.

مدل AI از این پس Designer-oriented است:

```json
{
  "id": 123,
  "caption": "عنوان",
  "dbName": "F1",
  "orderNumber": 1,
  "fieldType": "string",
  "maximumLength": 200,
  "isMandatory": true
}
```

قاعده‌ها:

- `fieldType` نام semantic است، نه نام کلاس Runtime.
- Propertyهای داخلی، capabilityها و مقدارهای مشتق‌شده در Export AI حذف می‌شوند.
- Propertyهای Designer فقط وقتی معنی دارند Serialize می‌شوند.
- Defaultهای قطعی و بدون اطلاعات حذف می‌شوند.
- Reference عمومی به شکل `{objectType,id,caption}` ارائه می‌شود. در contract جاری، Entity شناخته‌شده `SplUser` علاوه بر آن `name` پایدار (`SplUser`/`SplUsers`) می‌گیرد تا Writer/Verifier بتوانند بدون تثبیت Runtime ID آن را در System `Meta01` resolve کنند؛ این رفتار special-case عمومی برای Entityهای دیگر نیست.
- Runtime class همچنان مرجع اجرای واقعی است ولی Codex نباید برای ساخت معمولی نام کلاس Runtime را تولید کند.
- Read/Export، Semantic Change و Runtime verification باید همین نام‌های semantic را استفاده کنند.

## 2. موارد خارج از Scope فعلی

این موارد فعلاً عمداً از Field contract این مرحله حذف شده‌اند و نباید برایشان Write تولید شود:

- `CategoryInfo`
- `FindContactCommandInfo`
- `InterfaceInfo`
- `ConvertCommandInfo`
- `DialCommandInfo`

وجود یک مقدار در `FieldInfoTypeEnum` به معنی فعال/قابل‌ساخت بودن در Designer نیست.

## 3. وضعیت پشتیبانی جاری

در contract جاری مجموعاً **47 semantic field type** از Runtime/Designer شناخته و Serialize می‌شوند. پنج نوع حذف‌شده‌ی مالک (`CategoryInfo`, `FindContactCommandInfo`, `InterfaceInfo`, `ConvertCommandInfo`, `DialCommandInfo`) عمداً `unsupported` هستند.

معنی وضعیت Write:
- `create/update/delete`: Writer و semantic Runtime verify برای propertyهای تعریف‌شده فعال است.
- `update/delete؛ create lifecycle`: خود Type در Runtime قابل تغییر/حذف است ولی Create مستقیم عمومی مجاز نیست، چون Designer آن را محصول یک جریان دیگر می‌سازد.
- `existing update/delete؛ create inactive`: Source/UI وجود دارد ولی registration فعلی Runtime فعال نیست؛ Create مستقیم نمی‌شود.
- `linked read-only`: خود Field writable است، ولی metadata فرعی مرتبط API mutation امن/صریح در Sourceهای بررسی‌شده ندارد.

| fieldType | Runtime | دسته | Write | نکته ساخت |
|---|---|---|---|---|
| `string` | `StringInfo` | Simple | create/update/delete | `AddField(StringInfo)` |
| `int` | `IntInfo(Long)` | Simple | create/update/delete | `NumberType=Long` صریح |
| `float` | `IntInfo(Float)` | Simple | create/update/delete | `NumberType=Float` صریح |
| `decimal` | `IntInfo(Decimal)` | Simple | create/update/delete | `NumberType=Decimal` صریح |
| `money` | `CurrencyInfo` | Simple | create/update/delete | `CurrencyInfo` |
| `bool` | `BoolInfo` | Simple | create/update/delete | `BoolInfo` |
| `date` | `DateInfo` | Simple | create/update/delete | date/datetime یک Runtime type |
| `enum` | `EnumInfo` | Simple | create/update/delete | values semantic |
| `timeSpan` | `TimeSpanInfo` | Simple | create/update/delete | invariant TimeSpan |
| `longText` | `RichStringInfo` | Advanced | create/update/delete | `isMandatory` capability ندارد |
| `binary` | `BinaryInfo` | Advanced | create/update/delete | bool-specialized |
| `code` | `CodeInfo` | Advanced | create/update/delete | resolverها semantic SingleValueDefinition |
| `color` | `ColorInfo` | Advanced | create/update/delete | تنظیم اختصاصی اصلی ندارد |
| `gauge` | `GaugeInfo` | Other | create/update/delete | formula/no-column semantics Runtime |
| `workCenter` | `WorkCenterInfo` | Advanced | create/update/delete | WorkCenter selector |
| `referenceField` | `ReferenceFieldInfo` | Advanced | create/update/delete | `targetField` در Create الزامی |
| `recordSign` | `RecordSignInfo` | Advanced | create/update/delete | selectedFields refs |
| `reminder` | `ReminderInfo` | Advanced | existing update/delete؛ create inactive | registration در MetaService بررسی‌شده commented است |
| `sequence` | `SequenceInfo` | Advanced | create/update/delete | در Create `formula` الزامی |
| `rowNumber` | `RowNumberInfo` | Other | create/update/delete | singleton؛ Field معمولی است، نه AddAdvancedField |
| `file` | `FileInfo` | File | create/update/delete | composed file object |
| `pictureFile` | `PictureFileInfo` | File | create/update/delete | File + picture settings |
| `wordFile` | `WordFileInfo` | File | create/update/delete | File + Word settings |
| `pictures` | `PicturesInfo` | File | create/update/delete | collection/groups |
| `picture` | `SinglePictureInfo` | File | create/update/delete | image payload semantic |
| `icon` | `IconInfo` | File | create/update/delete | FileKey مشتق‌شده و write نمی‌شود |
| `command` | `CommandInfo` | Command | create/update/delete | linked `dynamicCommands` read-only |
| `refreshCommand` | `RefreshFieldCommandInfo` | Command | create/update/delete | + fields refs |
| `wordReportCommand` | `WordReportCommandInfo` | Command | create/update/delete | + report/file |
| `searchCommand` | `SearchCommandInfo` | Command | create/update/delete | command common settings |
| `creatorUser` | `CreatorUserInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>`؛ dbName Runtime-owned |
| `creationDate` | `CreationDateInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>` |
| `lastUpdateDate` | `LastUpdateDateInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>` |
| `history` | `HistoryInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>` |
| `isDeleted` | `IsDeletedInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>` |
| `order` | `OrderInfo` | Automatic | create/update/delete | رسمی `AddAdvancedField<T>` |
| `customField` | `CustomFieldInfo` | Dynamic | create/update/delete | definition/settings driven؛ arbitrary settings schema عمومی نیست |
| `singleRelation` | `MetaObjectInfo` | Relation | create/update/delete | رسمی `AddSingleRelationInfo` |
| `user` | `UserInfo` | Relation | create/update/delete | target داخلی نوع User است |
| `listRelation` | `RelationInfo` | Relation | create/update/delete | رسمی `AddRelationListField` + RelationDef semantic |
| `reverseListRelation` | `RelationInfoReverse` | Relation | create/update/delete | Create نیازمند `relationDefinitionId` |
| `reverseSingleListRelation` | `RelationInfoSingleReverse` | Relation | create/update/delete | Create نیازمند `destinationField` |
| `reverseSingleRelation` | `ReverseMetaObjectInfo` | Relation | create/update/delete | destination باید one-to-one باشد |
| `hierarchical` | `HierarchicalInfo` | Relation | create/update/delete | hookهای Runtime/FieldDef حفظ می‌شوند |
| `inheritance` | `InheritanceInfo` | Relation | create/update/delete | target یا parent one-to-one relation |
| `inheritanceChild` | `InheritanceChildInfo` | Automatic/Relation | update/delete؛ create lifecycle | Create مستقیم ممنوع؛ محصول inheritance flow |
| `reportRelation` | `ReportInfo` | Relation | create/update/delete | Create نیازمند `reportId` |

### metadataهای مرتبط ولی خارج از mutation عمومی Field

- `logic`: MetaCodeهای child فیلد؛ در Export semantic می‌شوند، raw `كد` حذف می‌شود.
- `dynamicCommands`: metadata مرتبط با Command Field؛ در Export خوانا می‌شود ولی setter امن در Sourceهای فعلی در دسترس نیست، پس mutation آن حدسی نیست.
- `jsonProperty`: مقدار raw و opaque از Runtime `JsonProperty`؛ بدون parse/تبدیل، در Export/Apply/Read-back حفظ می‌شود.
- `customField` settings: `definitionId/settingsId` قابل انتخاب است؛ schema داخلی settings وابسته به Custom Field Definition است و با reflection عمومی Patch نمی‌شود.


## 4. Common Designer properties

این propertyها در `FieldDefCreateForm`/FieldInfo capability model دیده می‌شوند. وجود property در JSON به معنی تنظیم صریح است.

| property | معنی | مقدار | محدودیت |
|---|---|---|---|
| `caption` | عنوان Field | string | در Entity باید یکتا باشد |
| `dbName` | نام ستون/شناسه DB | string | اختیاری؛ باید code-name، غیررزرو و در Entity یکتا باشد؛ برای AddAdvancedFieldهای Automatic قابل override نیست |
| `orderNumber` | ترتیب Field | int | Export/read؛ patch مستقیم فعال نیست. Planner ترتیب sibling Createهای مستقل را حفظ می‌کند و dependency واقعی می‌تواند ترتیب را محدود کند؛ Formula به‌تنهایی Field را پشت siblingهای بعدی نمی‌برد. |
| `isMandatory` | اجباری بودن | bool | فقط اگر `SupportsIsMandatory` |
| `isUnique` | یکتا | bool | فقط اگر `SupportsIsUnique` |
| `hasEncryption` | رمزنگاری | bool | فقط اگر `SupportsEncryption` |
| `isReadOnly` | فقط‌خواندنی در UI/metadata | bool | capability عمومی |
| `isLeftToRight` | نمایش LTR | bool | برای متن/کد/شناسه‌های لاتین مفید |
| `doNotUpdateInDb` | عدم update مستقیم DB توسط Field | bool | Advanced؛ فقط با نیاز روشن |
| `useFullTextIndex` | Full-text index | bool | Designer برای String؛ برای سایر typeها نگذار |
| `icon` | آیکون Field | string یا `{base64}` | binary payload در read-back به `{configured:true}` خلاصه می‌شود |
| `formula` | Formula semantic | object/null | `type=code` write-enabled؛ execution flags و edit settings semantic هستند؛ raw XML/serialized object ممنوع |
| `defaultValue` | مقدار پیش‌فرض semantic | scalar یا object/null | `constantValue` و `code` write-enabled؛ Report-backed فعلاً فقط read/configured تا Contract semantic مستقل |

Capabilityها مثل `SupportsIsMandatory`, `FormulaIsSupported`, `IsColumn`, `HasReport` در JSON semantic خروجی نمی‌آیند؛ اینها implementation/capability هستند نه تنظیم کاربر.

## 5. Scalar types

### 5.1 `string` — `StringInfo`

Designer properties:

| property | معنی |
|---|---|
| `maximumLength` | حداکثر طول؛ `-1` در برخی مسیرها به معنی متن بلند/نامحدود runtime است |
| `minimumLength` | حداقل طول |
| `nullText` | متن/نمایش مقدار null |
| `isPassword` | نمایش password |
| `useAutoComplete` | فعال‌سازی autocomplete |
| `autoCompleteReportId` | Report مورد استفاده autocomplete |
| `useFullTextIndex` | full-text indexing |
| `isMultiline` | چندخطی |
| `isTranslatable` | قابلیت ترجمه |
| `onlyAcceptCurrentCulture` | محدود به culture جاری |
| `regularExpression` | regex validation |
| `allowedStringChars` | محدودیت کاراکترهای مجاز |
| `templateDefinitionId` | template definition مرتبط |

نمونه:

```json
{
  "caption": "کد ملی",
  "fieldType": "string",
  "maximumLength": 10,
  "isMandatory": true,
  "isLeftToRight": true,
  "regularExpression": "..."
}
```

### 5.2 `int`, `float`, `decimal` — `IntInfo`

Runtime enum `NumberType`:
- `Float = 0`
- `Long = 1`
- `Decimal = 2`

در AI JSON خود `NumberType` نمایش داده نمی‌شود؛ `fieldType` semantic آن را تعیین می‌کند.

Designer properties:
- `numericDotPlace`: تعداد اعشار؛ برای `float/decimal`
- `totalDigits`: precision کلی؛ مخصوصاً `decimal`
- `showNumericSeparator`: جداکننده هزارگان
- `minValue`, `maxValue`: دامنه

**نکته مهم:** `TypeDef.AddIntField()` یک `IntInfo` با default `NumberType=Float` می‌سازد؛ بنابراین Writer برای semantic `int/float/decimal` مقدار `NumberType` را صریحاً به‌ترتیب `Long/Float/Decimal` تنظیم می‌کند.

### 5.3 `money` — `CurrencyInfo`

علاوه بر numeric settings:

`displayUnit`:
- `riyal`
- `thousandRiyal`
- `millionRiyal`
- `dalor` (نام legacy Runtime)
- `toman`
- `pound`
- `euro`
- `dinar`

مثال:
```json
{"caption":"مبلغ","fieldType":"money","displayUnit":"toman","showNumericSeparator":true}
```

### 5.4 `bool` — `BoolInfo`

`viewType`:
- `default`
- `checkBox`
- `comboBox`
- `radioBox`

Properties:
- `showCheckInGrid`
- `trueDisplay`
- `falseDisplay`
- `trueImage` / `falseImage` در Export فقط `{configured:true}`؛ binary payload وارد JSON AI نمی‌شود.

Default captionهای runtime معمولاً `درست`/`نادرست` هستند و در صورت default حذف می‌شوند.

### 5.5 `date` — `DateInfo`

`calendarType`:
- `default`
- `hijriShamsi`
- `gregorian`

Properties:
- `dateFormat`
- `timeFormat`
- `relativeFormat`

`DateInfo` هم تاریخ و هم date-time را پوشش می‌دهد؛ semantic type جداگانه `datetime` در Runtime لازم نیست.

#### پارامترهای پیش‌فرض Runtime برای تاریخ/زمان

`DateInfo.GetDefaultParameters()` مجموعه‌ای از Parameterهای native را برای Condition/Report در اختیار Runtime می‌گذارد. اینها مقدار ثابت ذخیره‌شده نیستند؛ مقدار در زمان اجرا از خود `DateInfo.GetParameterValue()` محاسبه می‌شود و calendar همان FieldInfo در DateRange مؤثر است. نام‌ها contract واقعی Runtime هستند:

| نام Parameter | مقدار Runtime |
| --- | --- |
| `اکنون` | `Util.Now` |
| `امروز` | بازه روز جاری |
| `اين هفته` | `DateRangeType.ThisWeek` |
| `اين ماه` | `DateRangeType.ThisMonth` |
| `امسال` | `DateRangeType.ThisYear` |
| `ديروز` | `DateRangeType.Yesterday` |
| `هفته پيش` | `DateRangeType.PrevWeek` |
| `ماه پيش` | `DateRangeType.PrevMonth` |
| `سال پيش` | `DateRangeType.PrevYear` |
| `فردا` | `DateRangeType.Tommorrow` |
| `هفته بعد` | `DateRangeType.NextWeek` |
| `ماه بعد` | `DateRangeType.NextMonth` |
| `سال بعد` | `DateRangeType.NextYear` |

در semantic Report، استفاده از این Parameterها با **همین نام Runtime** و `input:false` مجاز است؛ لازم نیست مقدار تاریخ یا DateRange را AI محاسبه/ثابت کند. FieldInfo شرط تعیین می‌کند Parameter چگونه resolve شود. نمونه canonical در مرجع Report آمده است.

#### پارامتر پیش‌فرض Runtime برای کاربر

`UserInfo` از hook رسمی Runtime یک Parameter با نام دقیق `كاربر جاري` اضافه می‌کند. `UserInfo.GetParameterValueStatic()` آن را به `Util.CurrentUserId` resolve می‌کند. بنابراین برای شرط‌های مبتنی بر Field نوع User، «کاربر جاری» باید با همین Parameter native مدل شود و AI نباید شناسه کاربر جاری را در زمان طراحی hard-code کند.

### 5.6 `enum` — `EnumInfo`

`enumType`:
- `single`
- `multiSelection`

`viewType`:
- `comboBox`
- `radioButton`

`iconDisplayType`:
- `noImage`
- `image`
- `imageAndText`

Canonical values:
```json
"values": [
  {"value": 0, "caption": "فعال"},
  {"value": 1, "caption": "غیرفعال", "disabled": true}
]
```

Write شکل کوتاه را هم می‌پذیرد:
```json
"values": ["فعال", "غیرفعال"]
```
در شکل کوتاه value از 0 به ترتیب تولید می‌شود.

### 5.7 `timeSpan` — `TimeSpanInfo`

`format`:
- `hourMin`
- `hourMinLong`
- `dayHourMin`
- `dayHourMinLong`

Properties:
- `minValue`, `maxValue`: TimeSpan با invariant `.NET "c"` مثل `1.13:25:00`
- `numericDotPlace`
- `showNullText`

Regex/maskهای داخلی Runtime Serialize نمی‌شوند.

### 5.8 `longText` — `RichStringInfo`

`richInfoType`:
- `richTextFormat`
- `html` (default رایج)

Supports encryption؛ `isMandatory` را Runtime پشتیبانی نمی‌کند.

## 6. File/media

### `file` — `FileInfo`

Properties:
- `acceptableFileExtensions`: رشته محدودیت extension مطابق Designer
- `maxFileSizeKb`
- `maxTotalFileSizeKb`
- `maxFileCount`
- `setTextContent`
- `supportSourceControl`
- `checkOutDefaultPathCode`
- `showFileExtension`
- `isMultiSelect`
- `viewType`: `linearListBox`, `fileViewerControl`, `singleFileControl`

`FileInfo` composed object است؛ ستون ساده file-content در Entity نیست.

### `pictureFile` — `PictureFileInfo`
همه `file` settings +:
- `sizeMode`: `normal`, `stretchImage`, `autoSize`, `centerImage`
- `nullImage`: در Export فقط `{configured:true}`
- `showBarsaImageLibrary`

### `wordFile` — `WordFileInfo`
همه `file` settings +:
- `hideSelectFields`
- `fieldSelectTargetType`: reference به Entity

### `pictures` — `PicturesInfo`
- `maxPictureCount`
- `maxFileSizeKb`
- `maxTotalFileSizeKb`
- `groups`: collection نام/مقدار/اشتراک

### `picture` — `SinglePictureInfo`
- `sizeMode`: `normal`, `stretchImage`, `autoSize`, `centerImage`
- `image`: فقط وضعیت configured؛ binary در AI JSON نمی‌آید.

### `icon` — `IconInfo`
Designer setting اختصاصی مهمی ندارد. `FileKey` از FieldDefId مشتق می‌شود و **نباید** به‌عنوان property کاربر Serialize/Write شود.

## 7. Advanced types

### `binary` — `BinaryInfo`
specialization از Bool:
- bool view/display settings در صورت non-default
- `controlManageCode`
Default display semantics: `دارای مقدار` / `بدون مقدار`.

### `code` — `CodeInfo`
Properties:
- `codeType`
- `codeLayer`
- `codeLanguage` (default `cSharp`)
- `codeTemplate`
- `isMinimized`
- `isWordWrap`
- `helperTypeDefResolver`
- `helperDescriptionResolver`

دو resolver آخر `SingleValueDefinition` هستند و semantic Serialize می‌شوند. Writer برای `constantValue` و `code` از SingleValueDefinition صریح استفاده می‌کند؛ Report-backed value-definition بدون Contract semantic مستقل پذیرفته نمی‌شود.

### `color` — `ColorInfo`
نوع numeric/UI رنگ؛ Designer تنظیم type-specific مهمی ندارد.

### `gauge` — `GaugeInfo`
Properties:
- `gaugeType`: `type1`, `type2`, `type3`
- `direction`: `incrementing`, `decrementing`
- `labelPosition`: `center`, `bottom`, `hide`
- `showNumber`
- `numericDotPlace`
- `minValue`, `maxValue`
- `minValue2`, `maxValue2`

Runtime defaults:
- min=-100
- max=100
- min2=-60
- max2=60
- gaugeType=Type2
Gauge formula-backed و `DonotUseDbColumn=true` است.

### `workCenter` — `WorkCenterInfo`
- `startWorkCenter`
- `showPositions`
- `cannotSelectOrganizationUnit`

### `referenceField` — `ReferenceFieldInfo`
- `targetField`: Field reference
- `isConditional` (default true)
- `operator`: `ComparisonOperator` name
نوع DB از target field مشتق می‌شود.

### `recordSign` — `RecordSignInfo`
- `salt`
- `selectedFields`: array of Field refs
- `isChained`

### `reminder` — `ReminderInfo`
- `remindTimeFormula`
- `remindUserIdFormula`
- `remindDescriptionFormula`
- `remindSmsFormula`
- `remindEmailFormula`
- `enableAdvanceReminders`
- `enableMediaSelect`
- `enableSelectBeforeInterval`

### `sequence` — `SequenceInfo`
شماره خودکار؛ subclass StringInfo ولی `FormulaIsRequired=true`. `FormulaIsRequired=true` است؛ Create فقط وقتی `formula` semantic معتبر داده شود مجاز است.

## 8. Relations

### 8.1 `singleRelation` — `MetaObjectInfo`

Canonical:
```json
{
  "fieldType": "singleRelation",
  "target": {"objectType":"entity","id":123,"caption":"مشتری"}
}
```

Designer settings:
- `target`
- `isOneToOne`
- `isComposed`
- `relationViewType`: `default`, `simpleList`, `reportView`, `selectionList`, `radioBox`
- `reportId`
- `typeViewId`
- `showInSubForm`
- `showNewButton`
- `hideCombo`
- `fillBeforeDropDown`
- `viewRelatedFormType`: `show`, `showReadOnly`, `hide`
- `previewDependsOnField`
- `passParentForm`: `disabled`, `always`, `enabled_Conditional`
- `showImageInGrid`
- `generalViewName`
- `preventRemovePrimaryTarget`
- `additionalTargets`: array of entity refs + optional `reportId`


### 8.2 `listRelation` — `RelationInfo`

Create رسمی:
`TypeDef.AddRelationListField(caption, targetTypeDef)`

Properties:
- `target`
- `relationDefinitionId` (read identity)
- `relationViewType`: `selectionList`, `checkedList`, `checkedCombo`, `linearListBox`, `popupForm`
- `reportId`
- `reloadListOnDropDown`
- `isSymmetric`
- `relationType`: semantic `aggregation` یا `composition` (`Aggrigation` نام legacy enum)
- `relationName`
- `max`
- `additionalTargets`
- `associativeClass`:
  - `enabled`
  - `entity`
  - `sourceField`
  - `targetField`

Create/Update/Delete همه propertyهای فهرست‌شده، شامل `additionalTargets` و `associativeClass`، را از provider تخصصی Relation اعمال و semantic verify می‌کند.

### Reverse/hierarchy/inheritance

`reverseListRelation`, `reverseSingleListRelation`, `reverseSingleRelation`, `hierarchical` و `inheritance` Create/Update/Delete تخصصی دارند. `inheritanceChild` فقط Update/Delete دارد و Create مستقیم آن ممنوع است چون Automatic و محصول جریان inheritance است.

- reverse fields به destination/original field وابسته‌اند.
- hierarchical دارای report/view settings و maintenance عملیات path است.
- inheritance دارای parentField/baseOnParentRelation و view/map settings است.
اینها از provider تخصصی Relation استفاده می‌کنند؛ lifecycle هر subtype حفظ می‌شود.

## 9. Commands

Command Field داده نیست. Common settings:
- `menuName`
- `displayType`: `toolbar`, `button`
- `executeTarget` (flags): form/singleObject, listObject, contextMenu
- `disableWhenReadonly`
- `hideWhenDisabled`
- list state flags: always/single/multi

Subtypeهای باقی‌مانده در Scope:
- `command`
- `refreshCommand` (`fields`)
- `wordReportCommand` (`reportType`, `reportId`, `wordReportFile`)
- `searchCommand`

خود Command Fieldها Create/Update/Delete می‌شوند. تنظیمات common و subtypeها write-enabled هستند؛ `dynamicCommands` child metadata فقط read/inspect است چون setter رسمی امن آن در Sourceهای بررسی‌شده موجود نیست.

## 10. Automatic fields

Regular Designer tree انواع `Automatic` را از selector معمول Field حذف می‌کند. از جمله:
- `creatorUser`
- `creationDate`
- `lastUpdateDate`
- `history`
- `isDeleted`
- `rowNumber`
- `order`

`creatorUser/creationDate/lastUpdateDate/history/isDeleted/order` از مسیر رسمی `TypeDef.AddAdvancedField<T>()` ساخته می‌شوند و `dbName` آنها Runtime-owned است. `rowNumber` برخلاف این گروه Field معمولی و singleton است. `inheritanceChild` از جریان inheritance ایجاد می‌شود و direct Create ندارد.

## 11. قواعد Runtime verification

- `fieldType` از `AiFieldTypeModel.GetSemanticType()` خوانده می‌شود.
- برای `IntInfo`: Long=>`int`, Float=>`float`, Decimal=>`decimal`.
- relation list ستون DB ندارد؛ verifier نباید نبودن column را failure بگیرد.
- relation single معمولاً column دارد.
- Runtime read-back propertyهای semantic serializer را برمی‌گرداند، نه `fieldInfoType`.
- Write fieldType existing قابل تغییر نیست.
- Propertyهای write-enabled همان patch semantic درخواست‌شده را با read-back مقایسه می‌کنند. linked metadataهای `dynamicCommands` و custom settings schema بدون API رسمی mutation نمی‌شوند؛ `jsonProperty` raw طبق contract خودش قابل round-trip است.

## 12. زمانی که Source باید دوباره خوانده شود

فقط در این حالت‌ها:
1. رفتار Runtime با این مرجع تناقض واقعی نشان دهد.
2. نوع/persisted property جدیدی به Designer اضافه شده باشد.
3. Runtime lifecycle یک Type با این مرجع تناقض نشان دهد.
4. بخواهیم linked metadataهایی مثل DynamicCommand/JsonProperty یا Report-backed SingleValueDefinition را write-enable کنیم که setter رسمی آنها در Sourceهای فعلی تثبیت نشده است.

## profile v14 — portable Designer state for field types

این contract برای Semantic round-trip است و Runtime ID را identity طراحی نمی‌داند:

- `picture.image`، `pictureFile.nullImage`، Bool/Binary images و Enum/Pictures item icon در Semantic package به asset reference تبدیل می‌شوند: `{asset, sha256, mediaType}`. payload خام فقط در مرحله staging موقت است و داخل JSON نهایی base64 بزرگ باقی نمی‌ماند.
- `pictures.groups[]` فقط meaning طراحی (`value/caption/icon`) را نگه می‌دارد؛ runtime `id` حذف می‌شود.
- `workCenter.startWorkCenter` و technical IsDeleted rendering flags semantic-essential نیستند.
- `file.checkOutDefaultPathCode` فقط وقتی `supportSourceControl=true` معنی دارد.
- SingleRelation/User default record از raw row id استفاده نمی‌کند؛ contract مشترک external data dependency در `dataexchange/07-ai-change-runtime-reference.fa.md` است.

## Re-export fix v149 — remaining Field gaps

- `timeSpan.minValue/maxValue`: reader باید most-derived property را بخواند؛ `TimeSpanInfo` این دو property را با `new` روی base number properties پنهان می‌کند و reflection ساده‌ی `GetProperty` مجاز نیست silently آنها را حذف کند.
- `hierarchical.viewRelatedFormType`: مقدار `hide` یک state صریح Designer است و default-omission نمی‌شود.
- `listRelation.relationType`: از `RelationHelper.GetRelationType(RelationInfo)` به `composition|aggregation` project می‌شود؛ وجود lazy `RelationDef` شرط export نیست.
- `pictures.maxPictureCount`: persisted `null` در legacy Designer برای این control به effective value `100` نمایش داده می‌شود؛ Full و Semantic باید همین effective Designer state را صریح حمل کنند.
- Enum item iconهای provider-backed مثل `Barsa2:...` قبل از Semantic materialization با `MetaHelper.GetBitmap(...,16)` resolve و به portable asset تبدیل می‌شوند. unresolved configured icon باید export را fail-closed کند، نه اینکه provider-local string را portable فرض کند.

## v177 reportRelation write projection

برای `reportRelation`: `reportId` یک Semantic Report reference قابل author است؛ `target` derived از Report است و write-input لازم نیست؛ `orderNumber` raw patch نیست و فقط relative sibling order در collection واقعی همه `FieldDef`های همان Entity را بیان می‌کند.

