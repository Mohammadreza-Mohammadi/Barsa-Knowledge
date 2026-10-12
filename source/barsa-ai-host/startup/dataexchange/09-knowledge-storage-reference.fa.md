# HK / KM Storage — DataExchange Technical Reference

این سند مرجع فنی storage/lifecycle دو Entity موجود دانش است که `BixKnowledgeHelper` مصرف می‌کند. این قرارداد مدل DB تازه نمی‌سازد و تولید محتوای KM را انجام نمی‌دهد.

## مدل موجود

دو TypeDef موجود در `Meta02` استفاده می‌شوند:

### دانش انسانی

Fieldهای واقعی:

- `نوع شيء مرتبط` / `RelatedObjectTypeDefId`
- `شناسه شيء مرتبط` / `RelatedObjectId`
- `محتوا` / `Content`

`Content` متن انسانی و منبع اصلی همان HK است.

### دانش ai

همان سه Field بالا به‌علاوه:

- `معتبر است` / `IsValid`

`Content` JSON cache تولیدشده توسط AI است. `IsValid=false` یعنی برای مصرف جاری معتبر نیست؛ Content قبلی حذف نمی‌شود و می‌تواند ورودی regeneration باشد.

`SystemId` جداگانه وجود ندارد. اگر Target خود System باشد، TypeDef/ID همان System به‌عنوان target ثبت می‌شود.

## Target mapping

AI-facing `targetType + targetId` فقط alias امن روی همان pair واقعی storage است. allow-list ثابت:

```text
system
entity
field
view
report
workflow
```

مالک فنی mapping، `BixKnowledgeHelper` است. برای metadata targetها، `RelatedObjectTypeDefId` از **registry واقعی EorgType** همان table resolve می‌شود؛ lookup مستقیم `met_TypeDef.DbName` authority نیست، چون static metadata typeهایی مانند `TypeViewEntity` از آن مسیر الزاماً discover نمی‌شوند.

مسیر canonical Source:

```text
targetType
→ SupportedTargetTypes[targetType] = metadata table
→ EorgType.GetLocalIdByTableName(table)
→ TypeDefCacheNew.GetTypeDefIdByLocalId(localId)
→ TypeDef.GetById(typeDefId) / DbName consistency check
→ RelatedObjectTypeDefId = resolved Meta TypeDef id
RelatedObjectId = targetId
```

جدول mapping ثابت:

| targetType | metadata table / EorgType registration | storage identity |
|---|---|---|
| `system` | `met_MetaSystem` | resolved TypeDef of registered table + System id |
| `entity` | `met_TypeDef` | resolved TypeDef of registered table + Entity(TypeDef) id |
| `field` | `met_FieldDef` | resolved TypeDef of registered table + FieldDef id |
| `view` | `met_TypeViewEntity` | resolved TypeDef of registered table + TypeViewEntity id |
| `report` | `met_Report` | resolved TypeDef of registered table + Report id |
| `workflow` | `wfl_WorkflowDef` | resolved TypeDef of registered table + WorkflowDef id |

این table nameها از allow-list `SupportedTargetTypes` می‌آیند؛ numeric TypeDef ID hardcode نمی‌شود. registration static targetها در Source upgrade registry `spl_EorgType` موجود است. resolver runtime table را از allow-list می‌گیرد، `EorgType` را authority registration می‌داند، `TypeDefCacheNew` را fast path مصرف می‌کند و اگر descriptor static در cache حاضر نباشد همان `LocalId` ثبت‌شده را در `TypeDef.GetAll(true)` با **match همزمان LocalId + DbName** به‌صورت unique resolve می‌کند. `ResolveKnowledgeTarget(targetType,targetId)` علاوه بر mapping، وجود object واقعی را در table resolved کنترل می‌کند و بدون mutation قابل استفاده است. numeric TypeDef id در این مسیر hardcode نمی‌شود.

### Resolver diagnostics

`ResolveKnowledgeTargetTypeDefId` failure را stage-aware گزارش می‌کند تا defectهای deployment/registry با invalid target مخلوط نشوند:

```text
EorgType registry
→ TypeDefCacheNew fast path
→ TypeDef.GetAll(true) registered-descriptor fallback
→ unique LocalId + DbName verification
```

`failureStage`های resolver این Source: `targetRegistry`, `targetTypeDefLookup`, `targetTypeDefAmbiguous`, `targetTypeDefVerification`, `targetIdentity`. پیام generic `Metadata TypeDef for targetType '...' was not found.` مرحله واقعی failure را پنهان می‌کند. **cache-only resolution برای static Meta01 descriptorها مانند View contract کافی نیست**؛ resolver باید همان Eorg registration را با fallback مستقل از cache resolve کند و numeric mapping ساختگی نسازد. اگر Runtime پس از deploy همچنان diagnostic قدیمی یا behavior cache-only را نشان دهد، assembly لودشده نیز باید audit شود.

pair فنی `relatedObjectTypeDefId + relatedObjectId` برای compatibility باقی است؛ اگر typed و compatibility representation همزمان داده شوند باید دقیقاً همان Target را نشان دهند. caller اجازه تعیین table/DbName/type دلخواه ندارد.

## Storage availability

وجود contract Knowledge به معنی وجود Entityهای storage در هر deployment نیست. availability واقعی AI Knowledge با وجود TypeDef `Meta02 / دانش ai` تعیین می‌شود. `BixKnowledgeHelper.EnsureAiKnowledgeStorageAvailable()` فقط این storage capability را بدون mutation کنترل می‌کند. نبود آن `AiKnowledgeStorageUnavailableException` است و با `target mapping` defect یکی نیست.

- storage missing → capability `unavailable`؛ این وضعیت به‌تنهایی delivery موفق Metadata/System را باطل نمی‌کند.
- storage موجود ولی target mapping/identity fail → Integration defect همان target؛ Knowledge maintenance `incomplete` است و target مهم از design/selection حذف نمی‌شود.

Host می‌تواند `unavailable` را برای KM lifecycle surface کند؛ exact Agent orchestration و اینکه System delivery چگونه جدا از KM status گزارش می‌شود در AR01/SK10 است.

## Read / Write

HK و AI Knowledge مستقیم از همین Entityهای موجود با lifecycle رسمی `MetaObject` خوانده/نوشته می‌شوند و به Export کامل System وابسته نیستند.

Semantic composition فقط HK را روی Target مربوط نمایش می‌دهد؛ KM به Semantic inject نمی‌شود. شکل/serialization خود Semantic در مرجع Snapshot/Semantic این component مستند است.

## AI Knowledge lifecycle

عملیات storage موجود:

```text
Read current valid
Read previous invalid
Create
Update
Invalidate
Delete
```

قرارداد transition عادی:

```text
current
→ invalidate همان current
→ previous-invalid همان row
→ incremental/full regeneration بیرون Host/DataExchange
→ update همان row به Content جدید و valid
```

- regeneration عادی برای Target موجود row جدید نمی‌سازد و همان current/previous row را reuse می‌کند.
- `Invalidate` فقط validity را تغییر می‌دهد و Content را حفظ می‌کند؛ خودش regeneration انجام نمی‌دهد.
- `previous-invalid` صرفاً با `MAX(Id)` حدس زده نمی‌شود.
- process correlation آخرین row واقعاً invalidated را برای همان Target نگه می‌دارد.
- اگر correlation قابل اتکا نباشد و legacy duplicateهای invalid مانع تشخیص previous واقعی باشند، `AiKnowledgeAmbiguityException`/وضعیت `ambiguous` با candidate IDها برگردانده می‌شود؛ caller باید Full Generate fallback کند و یک candidate را حدس نزند.
- Delete صریح است و می‌تواند target descriptor را فقط به‌عنوان guard تطبیق رکورد مصرف کند.

## KM content boundary

`BixKnowledgeHelper.WriteAiKnowledge` برای `Content` فقط `JToken.Parse` انجام می‌دهد و سپس **همان string ورودی** را در Field موجود ذخیره می‌کند؛ Storage آن را minify/re-serialize نمی‌کند. بنابراین whitespace از نظر semantic JSON بی‌اهمیت است ولی representation persisted همان متنی است که به endpoint رسیده است. DB/KM schema برای formatting تغییر نمی‌کند.

ساخت/به‌روزرسانی متن KM مسئول AI Skill است، نه `BixKnowledgeHelper`. در EM01، Package Bridge می‌تواند قبل از route به endpoint موجود، JSON معتبر KM را parse و با indentation canonical بازنویسی کند تا single/batch persistence human-readable باشد؛ این normalization transport boundary است و storage semantics/lifecycle را تغییر نمی‌دهد. قرارداد AI-facing KM v1 و Full/Incremental strategy در:

`source:Meta/Core/Barsa.Ai.Host/Docs/AI/agent/skills.fa.md`

Host فقط transport/endpoint orchestration را ارائه می‌کند؛ request/response جاری در:

`source:Meta/Core/Barsa.Ai.Host/Startup/host-api.fa.md`

## Build / deployment boundary

`BixKnowledgeHelper` داخل **`Barsa.Meta.DataExchange.dll`** compile می‌شود. Source audit projectها نشان می‌دهد `Barsa.Ai.Host.csproj` به `Barsa.Meta.DataExchange.csproj` project-reference ندارد؛ Host به binary موجود در:

```text
Build\LocalExecution\Barsa.Meta.DataExchange.dll
```

reference می‌دهد. بنابراین تغییر resolver در `BixKnowledgeHelper.cs` فقط با rebuild Host فعال نمی‌شود. برای اثر Runtime باید `Barsa.Meta.DataExchange/Barsa.Meta.DataExchange.csproj` build شود، DLL حاصل در deployment/`Build\LocalExecution` مورد استفاده Host قرار گیرد و process Host با همان assembly جدید restart/redeploy شود. اگر Host source جدید ولی DataExchange binary قدیمی باشد، behavior قدیمی resolver کاملاً ممکن است باقی بماند.

build/release procedure عمومی owner Host است؛ این بخش فقط assembly ownership فنی mapping را ثبت می‌کند.

## خارج از این contract

- automatic invalidation after Apply
- automatic regeneration داخل Storage/DataExchange (AR01/SK10 می‌تواند بعد از delivery آن را orchestrate کند)
- final `km/` file generation
- question-generation algorithm

این موارد از storage lifecycle موجود نتیجه‌گیری یا به آن اضافه نمی‌شوند.
