# Snapshot technical reference

## Scope

`BixSnapshotManager` روی همان `ExportSaveContext.DataSet` که BIX Export تولید کرده کار می‌کند، اما DataSet فقط capture داخلی است و داخل Snapshot ذخیره نمی‌شود. این قابلیت Provider/Planner/Runtime Verify جدید نیست.

## Package v2

```text
snapshot.zip
  manifest.json
  full/
    ... structured JSON package ...
  semantic/
    ... semantic JSON package ...
```

هیچ table dump یا `bix-dataset.bin` در artifact وجود ندارد. جدول‌های `$...` فقط در memory برای reconstruction استفاده می‌شوند.

برای ساخت package، projectionهای Full و Semantic به‌صورت ZIP تولید و entryهای آنها مستقیماً داخل Snapshot نهایی merge می‌شوند. Snapshot دیگر projection ZIP را روی filesystem extract نمی‌کند؛ بنابراین hierarchy عمیق داخلی به محدودیت legacy `MAX_PATH` مرحله Snapshot برخورد نمی‌کند و extract/re-zip اضافه نیز انجام نمی‌شود.


## قاعده نام و طول مسیر فیزیکی

نام/Caption منطقی objectها داخل JSON هرگز به‌خاطر محدودیت filesystem کوتاه نمی‌شود. کوتاه‌سازی فقط روی نام فیزیکی directory/file داخل package اعمال می‌شود.

قاعده جاری:

```text
Max physical segment       = 60 chars
Max artifact relative path = 170 chars

1. ابتدا هر segment مستقل حداکثر 60 کاراکتر می‌شود.
2. اگر کل مسیر به سقف نزدیک شد، basename فایل leaf قبل از folderهای بالاتر کوتاه‌تر می‌شود.
3. اگر hierarchy هنوز طولانی باشد، segmentهای عمیق مسیر از انتها به سمت بالا با بودجه باقی‌مانده کوتاه می‌شوند؛ بخش‌های بالاتر تا حد ممکن خوانا می‌مانند.
4. کوتاه‌سازی deterministic است: readable-prefix + "~" + stable short hash.
5. uniqueness suffix نیز داخل همان budget طول قرار می‌گیرد.
```

مثال:

```text
گزارش جامع وضعیت درخواست خرید شعب و واحدها برای دوره بسیار طولانی سال مالی ۱۴۰۵
→
گزارش جامع وضعیت درخواست خرید شعب و واحدها برای دور~3AE4012A
```

برای کاهش طول absolute path هنگام materialization، staging موقت نیز در مسیر کوتاه `%TEMP%\bx\<short-id>` ساخته می‌شود. این staging implementation detail است و داخل artifact دیده نمی‌شود.

این قاعده برای هر دو projection Semantic و Full Structured مشترک است تا path یک object بین modeها تا حد ممکن پایدار بماند. کوتاه‌شدن نام فیزیکی نباید به تغییر object identity، caption/name داخل JSON یا semantics منجر شود.

## Full Structured

`BixJsonExportManager.SaveFullStructuredJson` همان `JsonExportDocumentBuilder` و `JsonExportPackageWriter` را reuse می‌کند تا hierarchy، ownership، composition و folder structure مشابه JSON Export باقی بماند.

تفاوت با Semantic:

- normalizationهای Semantic مخصوص Field/Report/Folder اجرا نمی‌شوند؛
- `outputName`های صرفاً semantic روی columnها و objectهای decoded اعمال نمی‌شوند و نام source/persisted حفظ می‌شود؛
- اگر یک alias فقط duplicate یک property واقعی باشد و مقدار خام دو طرف دقیقاً برابر باشد، alias تکراری حذف می‌شود؛ اگر مقادیر متفاوت باشند هر دو حفظ می‌شوند؛
- enum scalarها به نام semantic تبدیل نمی‌شوند؛
- decoderهای FieldInfo/ReportData/TypeView و BusinessRule در Full از readable/source-oriented serialization استفاده می‌کنند، نه serializer خلاصه‌شده AI؛
- transform/enum renameهای مخصوص Semantic روی objectهای decoded در Full اعمال نمی‌شوند؛
- defaultهای persisted فقط به دلیل default بودن حذف نمی‌شوند؛
- payload باینری معناداری که decoder ندارد به‌صورت marker شامل `length/sha256` نگه داشته می‌شود تا تغییر آن پنهان نشود؛ raw bytes در Snapshot dump نمی‌شود؛
- Folder واقعی تا آخرین سطح حفظ می‌شود و داخل هر directory واقعی Folder فایل `[پوشه].json` properties همان Folder را نگه می‌دارد؛ این قاعده شامل Root Folder واقعی سیستم در `[پوشه اصلی]/[پوشه].json` نیز هست؛ در Full، Report/Command زیر Folder نهایی داخل همان Folder باقی می‌ماند؛
- Parent/child اصلی از graph واقعی `spl_ObjectReference` می‌آید. nodeهای واقعی ObjectReference-backed در Full مستقل materialize می‌شوند؛ relation payloadها داخل owner می‌مانند. بنابراین profile Semantic (`inline/auto`) حق ندارد یک child واقعی مثل Report زیر Folder را در Full داخل parent پنهان کند؛
- object identity برای nodeهای ObjectReference-backed همان `id` سراسری است. اگر یک Report هم از ownership Folder و هم از navigation relation مثل `MetaReport` reachable باشد فقط یک‌بار materialize می‌شود؛
- داده‌های dynamic/basic-info که ExportData براساس data-relationهای ObjectReference داخل جدول واقعی TypeDef fetch می‌کند و structure node مستقل ندارند، زیر owner TypeDef در `DataRecords[]` قرار می‌گیرند؛ rowهایی که خودشان structure object بوده و قبلاً materialize شده‌اند دوباره اضافه نمی‌شوند؛
- رکورد auxiliary شناخته‌شده با relation واقعی DB/Source به owner وصل می‌شود و نباید صرفاً چون node مستقل `$Selection` ندارد unmapped بماند:
  - `Spl_TrusteeAccess.OBJECTID -> owner.id` و رکوردها زیر `TrusteeAccess[]` قرار می‌گیرند؛
  - `MET_RELATION.SourceId -> owner.id` و relationها زیر `Relations[]` قرار می‌گیرند؛ `SourceId` داخل child تکرار نمی‌شود؛
  - `m02_GridSettings.ReportId -> Report.id` و تنظیمات زیر `ListSettings[]` قرار می‌گیرند؛
  - `SHR_FILEATTACHMENTOBJECT.OBJECTID -> owner.id` و `FILEATTACHMENTID -> SHR_FILEATTACHMENT.ID` است؛ association و Attachment زیر `Attachments[]` owner قرار می‌گیرند. `OBJECTID2` حفظ می‌شود چون مشخص‌کننده field/relation واقعی attachment است؛ owner/file IDs تکراری با nesting حذف می‌شوند؛
- `unmappedRecords.json` فقط safety-net توسعه است. رکوردی که owner/relation آن هنوز شناخته نشده آنجا می‌ماند؛ در Snapshot سالم این فایل ideally وجود ندارد یا بسیار کوچک است؛
- noiseهای runtime شناخته‌شده Ruleها (`RuleList[*].Sequence` و `DeepHashCodeForCallCache`) از Full حذف می‌شوند؛ این حذف به Sequenceهای business مستقل تعمیم داده نمی‌شود؛
- null، back-reference/cache/resolved، media/runtime payload و duplicateهای صریح حذف می‌شوند؛ `omit`های صرفاً Semantic به‌تنهایی باعث حذف داده از Full نمی‌شوند؛
- Full و Semantic هر دو Reportهایی را که در BIX/ObjectReference حضور دارند از همان capture materialize می‌کنند. اگر Runtime enumeration Reportی را پیدا کند که واقعاً از BIX representation جا افتاده است، fallback فقط همان Reportهای missing را اضافه می‌کند؛ در Full fallback با readable Full serialization و در Semantic با serializer canonical Report انجام می‌شود. Full نباید از Semantic از نظر objectهای meaningful ناقص‌تر باشد.

هدف Full Structured «raw database» یا «CLR object graph» نیست؛ هدف بیشترین اطلاعات مفید و قابل‌فهم از capture با کمترین semantic rewriting است.

## Parent/Child و انتخاب داده در BIX

مبنای tree و export، FK خام جدول‌ها نیست. SystemBuilder ابتدا graph `spl_ObjectReference` را نگه می‌دارد:

- برای objectهای static، parent از `GetParentObject()` و child relationها از `GetChildRelations()` استخراج می‌شوند؛
- `EorgChildRelationToObject` child object واقعی می‌سازد؛
- `EorgChildRelationToData` یک data-relation می‌سازد؛
- برای dynamic structure، `StructureEntitySettings` parent و relation fieldها را تعیین می‌کند؛
- Security نیز با relationهای `Structure_SecurityAccess` / `Data_SecurityAccess` وارد همین graph می‌شود؛
- BasicInfo، attachment، picture و data relationهای دیگر نیز از همین selection/filter mechanism عبور می‌کنند.

`Query_FillSelectionExpanded` انتخاب را با `ParentId` روی `spl_ObjectReference` recursively expand می‌کند و category/filter تعیین می‌کند چه relationهایی وارد شوند. سپس `ExportData` از data-relationهای انتخاب‌شده استفاده می‌کند تا payload واقعی جدول‌هایی مثل `Spl_TrusteeAccess` یا جدول داده TypeDef را fetch کند.

قاعده Full Structured:

```text
ObjectReference object node -> object مستقل در package
ObjectReference data relation -> payload متصل به owner
explicit auxiliary FK/owner   -> payload متصل به owner
unknown payload/ownership     -> unmappedRecords safety-net
```

پس `$Selection` و سایر `$...` tableها فقط implementation input برای reconstruction هستند و خودشان خروجی Full نیستند.

### Partial projection و parent خارج از selection

وجود parent در `$Selection` شرط materialize شدن object انتخاب‌شده نیست. اگر یک object معتبر انتخاب شده ولی parent ساختاری آن (برای مثال System یک Entity) عمداً در selection حضور ندارد، آن object در projection به‌عنوان root همان selection materialize می‌شود. Parent فقط در صورت نیاز برای context/path/`semanticId` resolve می‌شود و نباید صرفاً برای کامل‌کردن tree وارد package شود.

برای Entity partial export، Semantic همان Entity boundary و childهای انتخاب‌شده را با همان serializer/profile Export کامل می‌سازد؛ در صورت resolve شدن System context، مسیر conventional `System/[موجوديت]/Entity/...` حفظ می‌شود ولی `system.json` ساخته نمی‌شود. نبود parent انتخاب‌شده به‌تنهایی mapping gap نیست و Entity/Field شناخته‌شده را نباید به `unmappedRecords` بفرستد. Export کامل System که parentهای tree در selection حضور دارند از همان مسیر قبلی materialize می‌شود.

## Semantic

Semantic projection همان `BixJsonExportManager.SaveInitialJson` جاری است؛ Snapshot variant مستقل برای Semantic ساخته نمی‌شود. Folder انتهایی که صرفاً container یک Report/Command است flatten می‌شود تا navigation structure بدون معنای مستقل وارد مدل semantic نشود؛ Full همان Folder واقعی را نگه می‌دارد. Attachment metadata در Semantic قابل نگهداری است، اما فقط ستون `SHR_FILEATTACHMENT.CONTENT` حذف می‌شود؛ سایر فیلدهای Attachment مانند نام، پسوند، اندازه، مسیر، نوع و توضیح حفظ می‌شوند.

Reportهایی که از BIX/ObjectReference در Entity/Folder یا relation واقعی دیگری already represented هستند دوباره با `Report.LoadBySystemId` serialize/materialize نمی‌شوند. Runtime report enumeration فقط fallback برای Reportهایی است که واقعاً در BIX selection representation ندارند. این قاعده هم duplication `[گزارش]` را حذف می‌کند و هم second-pass serialization غیرضروری را در Semantic Export کم می‌کند.

### Semantic identity و reference خوانا

در Semantic، `id` فنی همچنان حفظ می‌شود و برای `System / Entity / Field / View / Report` یک `semanticId` رشته‌ای deterministic نیز اضافه می‌شود. این مقدار نشانی معنایی **وضعیت فعلی** است و شناسه تاریخی پایدار یا جایگزین Runtime ID نیست. شکل جاری آن از segmentهای خوانا ساخته می‌شود، برای مثال:

```text
system:فروش/entity:مشتری/field:عنوان
system:فروش/entity:مشتری/view:نمای اصلی
system:فروش/report:فهرست مشتریان
report:گزارش عمومی
```

Resolver مشترک ابتدا cache همان Export را با کلید `objectType + id` بررسی می‌کند، سپس داده‌های Load‌شده در `ExportSaveContext.DataSet` و در نهایت scalar lookup سبک DB را. lookup ناموفق نیز cache می‌شود و برای resolve کردن `semanticId` نباید full object load انجام شود. در segment عنوان، delimiterهای `\`، `/` و `:` با backslash escape می‌شوند تا parsing مسیر deterministic و بدون ابهام بماند.

Referenceهای قابل resolve برای پنج نوع بالا `id + semanticId` را نگه می‌دارند؛ وقتی `semanticId` موجود است `caption` تکراری داخل Reference حذف می‌شود. Runtime `id` هرگز حذف نمی‌شود.

فقط parent ساختاری تکراری حذف می‌شود: `Entity.systemId` و reference موجودیت مالک در `View` در Semantic تولید نمی‌شوند. `View.ParentId` که به‌صورت `inheritsFrom` نمایش داده می‌شود و `Report.entity` رابطه معنایی واقعی‌اند و باقی می‌مانند.

`$caption` وقتی object یک عنوان طبیعی مثل `name/caption/Caption` دارد از Semantic حذف می‌شود؛ packaging caption می‌تواند کوتاه‌شده یا format متفاوت همان عنوان باشد و برای نام فایل جداگانه حفظ می‌شود. `$type` برعکس، discriminator رسمی Semantic object است و روی objectهای اصلی حفظ می‌شود: `system`, `entity`, `field`, `relation`, `view`, `report`, `workflow`. اگر Navigation node به‌صورت JSON object باقی بماند از `navigationPage`, `navigationGroup`, `navigationReport`, `navigationRoot` استفاده می‌شود؛ directory-only placement نیازی به JSON type جدا ندارد. `$type` ownership/compose/placement را تعیین نمی‌کند. `$serializedType` فقط وقتی حذف می‌شود که container نوع را قطعی کند (فعلاً `MetaSystemSettings` زیر System و `TypeDefSettings` زیر Entity)؛ در payloadهای polymorphic مثل FieldInfo/Workflow type marker فنی داخلی مستقل از `$type` Semantic است.

Referenceهای عددی فقط وقتی نوع آنها از Source/contract روشن و `semanticId` قابل resolve باشد به `id + semanticId` تبدیل می‌شوند؛ در غیر این صورت shape فنی قبلی حفظ می‌شود. در Report این قاعده FieldItemهای ستون/Sorting/Grouping/Condition و pathهای Field را نیز پوشش می‌دهد. default omission همچنان type-specific است: Column (`enabled=true`, `visible=true`, `fixedWidth=false`, `wordWrap=false`)، Parameter flagهای boolean پیش‌فرض، Group `enabled=true` و `SingleCondition.customCodeExecutePerRow=true` طبق Source/Profile از Semantic حذف می‌شوند. `sorting.direction` و سایر مقدارهای معنایی غیرپیش‌فرض حفظ می‌شوند. serializer مشترک `AiReportModel` که Provider/Verify نیز از آن استفاده می‌کنند تغییر نمی‌کند و Full Structured تحت این pass قرار نمی‌گیرد.

### Human Knowledge composition

Semantic Export، HK را از Entity موجود `Meta02 / دانش انساني` با Fieldهای واقعی `نوع شيء مرتبط / شناسه شيء مرتبط / محتوا` می‌خواند. برای Targetهای مجاز System / Entity / Field / View / Report / Workflow، دانش مرتبط داخل همان object compose می‌شود؛ این lookup به انتخاب شدن Entityهای دانش یا Export کامل System وابسته نیست.

خواندن HK در Semantic به‌صورت batch و scoped به همان Export است: ابتدا Targetهای حاضر در projection جمع می‌شوند، نوع‌های واقعی آنها resolve می‌شوند و HK با یک batch read خوانده می‌شود؛ سپس index موقت با کلید `(RelatedObjectTypeDefId, RelatedObjectId)` ساخته می‌شود. Compose هر object فقط از همین index می‌خواند و Query جداگانه اجرا نمی‌کند. نبود Entity دانش، نبود HK، یا نبود HK برای یک Target باعث fail شدن Export یا serialize شدن property خالی نمی‌شود. cache سراسری/ماندگار برای رکوردهای HK وجود ندارد.

Shape فشرده جاری داخل Target:

```json
{
  "humanKnowledge": [
    { "id": 123, "content": "متن ثبت‌شده انسان" }
  ]
}
```

Target داخل entry تکرار نمی‌شود چون ownership از object میزبان روشن است. اگر زیرساخت/Entity دانش در یک DB موجود نباشد، composition نباید Metadata Export را fail کند. این pass فقط Semantic است؛ Full Structured/Lossless، Plan/Apply و Writer تغییری ندارند. `AiKnowledge` در این مرحله داخل Semantic compose نمی‌شود.

## Semantic-only package shape و archive portability

`SaveSelectedJson` برای backward compatibility، وقتی فقط Semantic انتخاب شده باشد همان single-projection package را نگه می‌دارد: `manifest.json` و Semantic payload در **root ZIP** هستند. فقط وقتی Semantic و Full هم‌زمان انتخاب شوند projectionها زیر `semantic/` و `full/` قرار می‌گیرند. بنابراین consumer نباید وجود directory `semantic/` را برای هر Semantic-only Export شرط بداند؛ contract مصرف‌کننده باید manifest/shape معتبر را تشخیص دهد.

نام entryهای Barsa AI Export باید مستقل از OS و همیشه با `/` materialize شود. این فقط archive naming است و filesystem path واقعی staging را تغییر نمی‌دهد.

## Report placement در Semantic materialization

Runtime object مستقلی به نام «فایل Report» وجود ندارد. Report metadata همان `Report` است و navigation یک `Folder` با `FolderType.Report`/`ReportId` جداگانه است (قرارداد write در DX05).

در Semantic Export، **محل فیزیکی هر object از direct compose/owner واقعی خودش می‌آید و ownership هرگز از ancestor به‌صورت transitive ارث نمی‌رسد**. اگر Report/View یا هر object مستقل مستقیماً compose یک Entity باشد، در boundary همان Entity materialize می‌شود؛ اگر direct owner آن Field، Relation، View یا object دیگری باشد، نباید صرفاً به دلیل قرارگرفتن آن owner زیر Entity به پوشه Entity promote شود و در representation همان direct owner باقی می‌ماند. Navigation نیز دقیقاً همین قاعده را دارد: Folder/Page/Group فقط placement owner خود را نمایش می‌دهد و ownership اصلی object را عوض نمی‌کند. `[گزارش]` در ریشه فقط fallback برای Reportی است که هیچ direct ownership/materialization route و هیچ placement مؤثر دیگری ندارد. Page/Groupهای Semantic فقط با hierarchy پوشه نمایش داده می‌شوند و فایل `[navigation].json` تولید نمی‌کنند، چون آن فایل semantic design payload مستقلی ندارد. این قاعده type-specific نیست و برای تمام objectهاست: **direct owner determines placement; ancestor does not promote descendants**.

## Diff

`CompareSnapshots` فایل‌های `full/` و `semantic/` را جداگانه مقایسه می‌کند.

- JSON با diff ساختاری property/item مقایسه می‌شود.
- آرایه‌های object دارای `id` با `id` match می‌شوند تا reorder noise تولید نکند.
- فایل‌های non-JSON با hash مقایسه می‌شوند.
- برای JSON fileAdded/fileRemoved علاوه بر hash، محتوای محدودشده نیز در detail قرار می‌گیرد تا object جدید/حذف‌شده بدون بازکردن ZIP قابل بررسی باشد.
- جزئیات محدود می‌شوند ولی `changeCount` کل delta را نگه می‌دارد.

قاعده Gap:

```text
Full Structured delta > 0
Semantic delta == 0
→ candidateCoverageGap
```

اگر هر دو تغییر دارند، نتیجه `requiresReview` است و mapping حدسی ساخته نمی‌شود.

## انتخاب representation در JSON Export UI

قابلیت `خروجی JSON` در `ApplicationExportForm` همچنان diagnostic/developer-facing است و فقط وقتی فرم با `Ctrl` باز شود یا روی `DebugPc` اجرا شود visible است:

```csharp
GeneralHelper.ControlKeyIsDown || DebugHelper.IsDebugPc
```

وقتی `خروجی JSON` فعال باشد، representationها **انتخاب‌های مستقل** هستند و ComboBox تک‌انتخابی نیستند:

- `Semantic`: قابل انتخاب/عدم انتخاب.
- `Full`: قابل انتخاب/عدم انتخاب.
- `Knowledge`: از نظر contract رزرو شده، فعلاً در UI دیده می‌شود ولی disabled است چون implementation ندارد.

حداقل یکی از `Semantic` یا `Full` باید انتخاب شود. اگر فقط یکی انتخاب شود، shape قدیمی همان projection حفظ می‌شود. اگر هر دو انتخاب شوند، یک BIX capture انجام می‌شود و یک package با دو directory تولید می‌شود:

```text
manifest.json
semantic/
full/
```

این رفتار از `BixJsonExportSelection` استفاده می‌کند. `ExportInitialJson(...)` برای backward compatibility معادل Semantic باقی می‌ماند. بعداً Knowledge باید به همین selection contract اضافه شود، نه با مسیر Export موازی.

## Meta01 ComplexCondition binary

`m01_MetaCondition.Condition$BINARY` payload فنی ناشناخته نیست. این ستون companion مربوط به `BinaryInfo` است و مقدار واقعی `ComplexCondition` را با `SerializationUtil.BinarySerializeToByteArray` بدون compression نگه می‌دارد. قرارداد خواندن همان `BinaryInfo.GetBinaryData(..., true)` / `LoadSerializedObjectFromDb` است.

در JSON Export:

- decoder table/column ثبت‌شده برای `m01_MetaCondition.Condition$BINARY` باید حتی اگر profile نتوانست rule نوع nested object را resolve کند اعمال شود؛
- Semantic پس از deserialize از representation فشرده و canonical شرط (`leaf / all / any`) استفاده می‌کند؛
- Full Structured خود `ComplexCondition` خوانا و کم‌پردازش‌شده را نگه می‌دارد؛ hash-only برای این ستون Gap محسوب می‌شود؛
- اگر deserialize شکست بخورد، رفتار عمومی decode-error marker اعمال می‌شود و blob به‌عنوان داده موفق silently حذف نمی‌شود.


### Auxiliary ownership scope

در Full Structured، رکوردهای auxiliary فقط وقتی جزو representation سیستم هستند که owner آنها در tree انتخاب‌شده وجود داشته باشد. قراردادهای فعلی: `MET_RELATION.SourceId`، `Spl_TrusteeAccess.OBJECTID`، `SHR_FILEATTACHMENTOBJECT.OBJECTID` و `m02_GridSettings.ReportId`. اگر owner معتبر است ولی خارج از selection قرار دارد، رکورد out-of-scope است و نباید وارد `unmappedRecords` شود. `unmappedRecords` فقط برای ownership واقعاً unresolved/unsupported باقی می‌ماند.

Auxiliary payload متصل به owner، از جمله TrusteeAccess/Relations/Attachments/ListSettings/DataRecords، بخشی از فایل خود owner است و نباید در سطح System به فایل مستقل `[TrusteeAccess].json` یا مشابه تبدیل شود. شناسه owner فقط پس از attachment موفق از payload حذف می‌شود؛ در diagnostic unresolved باید شناسه owner حفظ شود.

## Semantic profile v14 round-trip boundary

Semantic = Designer-facing projection، نه کوچک‌شده‌ی Full. package writer image/icon payloadهای Semantic را قبل از materialization به `assets/<sha256>.png` تبدیل می‌کند و JSON فقط asset reference نگه می‌دارد. Root navigation خودکار materialize نمی‌شود. Re-export/Runtime acceptance باید جدا از static Source validation گزارش شود.

## Producer identity diagnostic

برای اینکه Re-export بتواند دقیقاً اثبات کند کدام DataExchange binary خروجی را ساخته است، manifest هر projection و snapshot outer manifest این فیلدها را دارد:

```json
{
  "producer":"Barsa.Meta.DataExchange",
  "producerVersion":"<assembly-version>",
  "buildId":"<module-MVID>"
}
```

`producerVersion` ممکن است بین buildهای یک release ثابت بماند؛ `buildId` (MVID) شناسه diagnostic build واقعی است و برای اثبات loaded binary استفاده می‌شود، نه design identity.

