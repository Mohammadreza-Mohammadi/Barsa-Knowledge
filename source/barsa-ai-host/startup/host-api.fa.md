# Barsa.Ai.Host API

## Apply v206 — contract-classified three-phase lifecycle and final Semantic certification

`POST /plan` validation diagnostics are non-blocking; a structurally parsed plan is stored and can enter Apply.

`POST /apply` body:

```json
{
  "planId": "...",
  "referenceSemanticFile": "optional/path/to/reference-semantic.zip"
}
```

Apply runs contract-classified Phase 1/2/3 with an internal Deferred Ledger. Core metadata provider objects are Phase 1; authored `dynamicObject`/`MetaObject` rows are Phase 2. Phase 3 is property-contract dependency-ordered and does not use JSON property order. Deferred direct-reference slots are persisted as Runtime `-1` placeholders before final binding. Validation and command Verify are diagnostic-only. If `referenceSemanticFile` is supplied, the Host performs a Fresh Semantic Export for affected Systems and returns `semanticCertification`; Full Structured is not used.


Base URL پیش‌فرض:

```text
http://127.0.0.1:17840
```

JSON request/response = UTF-8.

## GET /health

وضعیت Host و Runtime identity را می‌دهد؛ از جمله workspace/database/connection identity و وضعیت Metadata Package Watcher/Chat Bridge.

## GET /systems

لیست lightweight Systemها را با `id`, `name`, `caption`, `isInactive` می‌دهد. Host قبل از پاسخ Metadata cache محلی را refresh می‌کند تا state جاری Runtime دیده شود.

## POST /pull

سه mode ورودی دارد و فقط یکی باید در هر request استفاده شود. Systemهای مشخص:

```json
{ "systemIds": [123, 456] }
```

Selection File موجود، یا descriptor AI-facing برای partial Semantic pull:

```json
{
  "targets": [
    { "targetType": "entity", "targetId": 123 }
  ]
}
```

در v96، `/pull.targets` فقط `system` و `entity` را end-to-end می‌پذیرد. `targetType` به table/type آزاد تبدیل نمی‌شود؛ همان mapping ثابت target knowledge استفاده و وجود object واقعی کنترل می‌شود. Entity selection از همان selection موجود و projection-root اصلاح‌شده v92 استفاده می‌کند؛ System والد می‌تواند فقط برای context/semanticId خوانده شود و مجبور نیست وارد خروجی شود. `systemIds` و SelectionFile موجود بدون تغییر باقی‌اند. قبل از Export، cache رسمی Metadata refresh می‌شود. خروجی semantic تازه برای Inspect/Workspace استفاده می‌شود.

## POST /snapshot

قرارداد diagnostic snapshot فعلاً همان `systemIds` یا `selectionFile` قبلی است و `targets` را نمی‌پذیرد. Snapshot در `host/snapshots/` دو projection ساختاری `full/` و `semantic/` از یک BIX capture داخلی می‌سازد؛ DataSet و جدول‌های `$...` artifact خروجی نیستند. این endpoint جزو normal Verify نیست.

## POST /snapshot-diff

```json
{"beforeFile":"...","afterFile":"..."}
```

Full Structured diff و Semantic diff را برمی‌گرداند و فقط coverage-gap candidate را گزارش می‌کند؛ Full delta را حدسی به semantic property تبدیل نمی‌کند.

## POST /lint

Body = `AiChangeBatch`. این endpoint هیچ Runtime resolution یا mutation انجام نمی‌دهد و فقط authored Semantic v15 payload را با همان structural linter و `SemanticSelectorCodec` مسیر Plan validate می‌کند. Package Builder پیش از ساخت ZIP از همین endpoint استفاده می‌کند تا duplicate `commandId`، dependency cycle، selector grammar، root `externalDataMappings` و Runtime-authority leakage با contract واحد reject شوند.

## POST /plan

Body = `AiChangeBatch`.

```text
Semantic Change
→ provider validation/resolution
→ plan
```

`BuildPlan` Mutation ندارد. قرارداد پیش‌فرض `POST /plan` همان Full serialized Plan قبلی است. فقط Package Bridge برای transport ایمن Plan بزرگ، `POST /plan?compact=true` را درخواست می‌کند؛ پاسخ compact شامل `planId`, `isValid`, همان `summary` camelCase تولیدشده توسط serializer اصلی Plan، `diagnostics` و `fullPlan.file` است. بنابراین client قدیمی Full Plan را از دست نمی‌دهد و diagnostics Package Bridge نیز به حمل Full Plan بزرگ وابسته نیست.

**لیست capability/provider در این فایل نگهداری نمی‌شود.** مرجع جاری:

```text
knowledge/support-matrix.fa.md
```

برای shape دقیق Change از Feature doc/Deep مرتبط استفاده کن؛ property یا provider حدسی نساز.

## POST /apply

```json
{ "planId": "..." }
```

فقط Plan از قبل ساخته‌شده همان Runtime process اجرا می‌شود. Result شامل status، command results، temporary IDs، affected systems و Runtime read-back/verification است.

در Semantic v15/v202، command result می‌تواند `failureClass` داشته باشد. Verify از classificationهای `mutationMissing`, `semanticMismatch`, `readBackProjectionMissing`, `physicalVerificationMismatch`, `normalizationMismatch` استفاده می‌کند. 0-match برای هر semantic selector یک `UnresolvedSemanticReference` است؛ اگر FieldInfo runtime-safe empty/sentinel واقعی را مجاز بداند Apply با Warning/NonCertified ادامه می‌دهد وگرنه همان command خطا می‌گیرد. Host/Agent نباید row ساختگی یا Runtime ID تزریق کند.

پس از success/partial فقط affected systemها refresh می‌شوند.

## GET /apply-status?planId=<id>

برای reconciliation بعد از قطع client استفاده می‌شود. stateهای اصلی:

```text
ready
applying
applied
faulted
unknown
```

اگر اجرای قبلی قابل اثبات نباشد state=`unknown` است و Apply مجدد خودکار ممنوع است.

## Human Knowledge / AI Knowledge

این APIها مستقیماً دو Entity موجود Meta02 را می‌خوانند/می‌نویسند و به Export کامل System وابسته نیستند. persistence همان DbName واقعی Fieldهاست. برای **AI Knowledge lifecycle** ورودی ترجیحی AI-facing برابر `targetType + targetId` است؛ Host descriptor را از طریق `BixKnowledgeHelper` resolve/validate می‌کند و caller نمی‌تواند table/type دلخواه بدهد.

exact `targetType → RelatedObjectTypeDefId/RelatedObjectId` mapping و Source owner آن فقط در `Barsa.Meta.SemanticExchange/Docs/AI/09-knowledge-storage-reference.fa.md` تعریف می‌شود. Host این mapping را دوباره تعریف نمی‌کند. pair فنی قدیمی برای compatibility همچنان پذیرفته می‌شود؛ اگر caller هر دو شکل را هم‌زمان بدهد باید دقیقاً به یک Target اشاره کنند، وگرنه request رد می‌شود.

Availability و target-resolution دو failure class جدا هستند:

- اگر Entity storage رسمی `Meta02 / دانش ai` در deployment وجود نداشته باشد، endpointهای AI Knowledge پاسخ HTTP `503` با `status=unavailable` و `failureStage=knowledgeStorage` می‌دهند. این یعنی capability storage در آن deployment unavailable است، نه اینکه System delivery شکست خورده باشد.
- check availability پیش از target mapping برای همه routeهای `/ai-knowledge*` اجرا می‌شود؛ بنابراین storage غایب با target-resolution defect اشتباه نمی‌شود.
- اگر storage موجود است ولی mapping یک Knowledge Target از registry/type cache/load/verification fail شود، پاسخ `status=failed` است و `failureStage` مرحله resolver را مشخص می‌کند (`targetRegistry`, `targetTypeDefLookup`, `targetTypeDefAmbiguous`, `targetTypeDefVerification`, `targetIdentity`). target از contract حذف نمی‌شود.

Runtime resolver `BixKnowledgeHelper` داخل assembly **`Barsa.Meta.DataExchange.dll`** است. Host project این assembly را از `Build/LocalExecution/Barsa.Meta.DataExchange.dll` reference می‌کند، نه project-reference؛ بنابراین تغییر resolver فقط با build/deploy همان DataExchange assembly و restart process مصرف‌کننده اثر می‌کند.

### GET /human-knowledge

```text
/human-knowledge?relatedObjectTypeDefId=<MetaTypeDefId>&relatedObjectId=<objectId>
```

### POST /human-knowledge

```json
{
  "id": 0,
  "relatedObjectTypeDefId": 123,
  "relatedObjectId": 456,
  "content": "متن دانش انسانی"
}
```

`id` صفر یا حذف‌شده از request یعنی Create و مقدار مثبت یعنی Update همان رکورد.

### AI Knowledge / KM v1

`دانش ai.Content` همان JSON Cache موجود است و مدل DB تغییر نکرده است. قرارداد اولیه محتوای KM:

```json
{
  "summary": "...",
  "keyPoints": ["..."],
  "drillDown": [
    {
      "targetType": "entity",
      "targetId": 123,
      "semanticId": "system:Meta02/entity:Person",
      "reason": "..."
    }
  ]
}
```

در هر drill-down، `targetType + targetId` لازم است تا AI بتواند Child KM/Semantic را مستقیم بخواند. `semanticId` هرجا مدل Semantic فعلی آن را دارد ثبت می‌شود؛ برای Workflow در v1 اجباری نیست. بخش خالی (`summary` خالی، `keyPoints` خالی یا `drillDown` خالی) توسط AI Skill Serialize نشود. Host فقط JSON بودن Content را کنترل و همان متن را ذخیره می‌کند؛ تولید summary/keyPoints/drillDown یا تصمیم Full/Incremental داخل Host انجام نمی‌شود.

`IsValid=true` یعنی KM برای مصرف جاری معتبر است. `IsValid=false` یعنی KM جاری نیست، اما Content حذف نمی‌شود و باید برای incremental regeneration قابل Read باقی بماند.

### GET /ai-knowledge

```text
/ai-knowledge?targetType=entity&targetId=<objectId>
```

شکل فنی قدیمی `relatedObjectTypeDefId + relatedObjectId` نیز برای compatibility پذیرفته می‌شود. به‌صورت پیش‌فرض فقط `IsValid=true` برمی‌گردد. `includeInvalid=true` همه رکوردهای Target را برای diagnostics/lifecycle برمی‌گرداند.

### GET /ai-knowledge/current

```text
/ai-knowledge/current?targetType=system&targetId=<systemId>
```

شکل فنی قدیمی نیز پذیرفته می‌شود. جدیدترین رکورد `IsValid=true` همان Target را در `knowledge` برمی‌گرداند؛ اگر current KM وجود نداشته باشد `knowledge=null` است.

### GET /ai-knowledge/previous-invalid

```text
/ai-knowledge/previous-invalid?targetType=entity&targetId=<objectId>
```

شکل فنی قدیمی نیز پذیرفته می‌شود. بعد از `Invalidate`، همان rowای که پیش از آن `current` بوده به‌عنوان `previous-invalid` برگردانده می‌شود؛ انتخاب صرفاً با `MAX(Id)` انجام نمی‌شود. اگر correlation lifecycle در Host در دسترس نباشد و فقط یک invalid برای Target وجود داشته باشد همان رکورد امن است؛ اگر چند invalid legacy وجود داشته باشد پاسخ HTTP `409` با `status=ambiguous`، `candidateIds` و یک `reuseId` برمی‌گردد. در حالت ambiguous هیچ candidate Content برای Incremental مصرف نشود و AI باید Full Generate کند.

### POST /ai-knowledge

```json
{
  "id": 0,
  "targetType": "entity",
  "targetId": 456,
  "content": "{\"summary\":\"...\"}",
  "isValid": true
}
```

`id>0` یعنی Update صریح همان row. اگر `id` صفر/حذف‌شده باشد، Host فقط وقتی Target هیچ row قبلی ندارد Create می‌کند؛ برای Target موجود، row جاری یا `previous-invalid` قابل‌تشخیص را reuse می‌کند تا regeneration عادی duplicate نسازد. اگر چند invalid legacy وجود داشته باشد و previous واقعی correlate نشده باشد، پاسخ `409 ambiguous` است؛ برای Full Generate می‌توان `reuseId` اعلام‌شده را فقط به‌عنوان storage row با `id=<reuseId>` update کرد و Content قبلی آن را مبنای Incremental قرار نداد. pair قدیمی `relatedObjectTypeDefId + relatedObjectId` همچنان پذیرفته می‌شود. `content` باید JSON معتبر باشد؛ storage همان source text را حفظ می‌کند و public endpoint آن را minify/reformat نمی‌کند. در EM01، Package `km-save` قبل از route همین Content را parse و با indentation canonical serialize می‌کند، بنابراین single/batch Package save متن human-readable ذخیره می‌کند بدون تغییر schema/lifecycle. پاسخ موفق فیلد `created` را نیز برمی‌گرداند. AI Skill پس از Full Generate یا Incremental Update نتیجه قابل مصرف را با `isValid=true` ذخیره می‌کند.

### POST /ai-knowledge/invalidate

```json
{
  "targetType": "entity",
  "targetId": 456
}
```

همان KMای که `/current` پیش از Invalidate برمی‌گرداند transition اصلی lifecycle است و `Content` آن تغییر نمی‌کند. برای پاک‌کردن legacy currentهای موازی، سایر rowهای `IsValid=true` همان Target نیز نامعتبر می‌شوند؛ Host id همان current اصلی را در process جاری correlate می‌کند تا `/previous-invalid` دقیقاً همان KM را برگرداند. این correlation ماندگار/DB history نیست. endpoint parent/child را حدس نمی‌زند، KM تولید نمی‌کند و به Apply hook نشده است؛ affected targetها را AI بعد از Read Actual Delta تعیین می‌کند.

### POST /ai-knowledge/delete

```json
{ "id": 123 }
```

`id` همچنان برای compatibility کافی است. AI می‌تواند برای guard اضافه `{ "id":123, "targetType":"entity", "targetId":456 }` بفرستد؛ Host قبل از Delete تطابق رکورد با Target را کنترل می‌کند. یک رکورد `دانش ai` را صریح حذف می‌کند. Delete بخشی از Invalidate نیست و برای regeneration لازم نیست.

### AI orchestration boundary و Semantic fallback

Host فقط endpointهای current/pull/storage را فراهم می‌کند؛ selection `drillDown` و Full/Incremental/Lazy generation authority این سند نیست و از `Docs/AI/agent/skills.fa.md` / `SK10` می‌آید. هر public `POST /ai-knowledge` همچنان فقط **یک target صریح** را ذخیره می‌کند و parent/child generation انجام نمی‌دهد. در EM01، Package Bridge می‌تواند همان endpoint single-target را برای itemهای یک `km-save` batch در یک Package processing cycle چند بار route کند؛ این رفتار public API یا storage schema را batch نمی‌کند. exact Package shape در `Docs/AI/agent/package-protocol.fa.md` و generated `chat-protocol.json` است.

Partial Semantic در Runtime جاری برای System و Entity عملیاتی است. Field/View/Report/Workflow lifecycle KM و descriptor معتبر دارند، ولی `/pull.targets` مستقیم آنها فعال نشده است؛ orchestration نباید target-semantic ساختگی برای آنها بسازد. برای Child غیر-Entity، Agent می‌تواند Semantic کامل owning System را با capability موجود System بگیرد و target دقیق را در آن locate کند؛ اگر همان System Semantic از قبل context لازم را دارد، pull دوباره لازم نیست.

Lifecycle پایه KM v1:

```text
Read current valid KM
→ Change / Apply
→ Read Actual Delta
→ Invalidate affected KM
→ Read previous invalid KM
→ اگر ambiguous بود: Full Generate و reuse یک row موجود، بدون مصرف Content مبهم
→ Incremental Update when context is sufficient
→ otherwise Full Generate
→ POST valid KM روی همان row lifecycle
```

برای parent update، AI تا حد امکان `previous invalid Parent KM + actual delta + new/current Child KM` را مصرف می‌کند و کل parent scope را دوباره نمی‌خواند. مثال پایه: `Field change → Entity KM → System KM` و `Entity change → Entity KM → System KM`.

در این مرحله فقط Target typeهای واقعی System / Entity / Field / View / Report / Workflow پذیرفته می‌شوند. AI-facing نام آنها دقیقاً `system / entity / field / view / report / workflow` است. Host آنها را به TypeDef واقعی map می‌کند؛ `relatedObjectTypeDefId` و `relatedObjectId` فقط شکل فنی/سازگار قبلی همین Target هستند و SystemId مستقل وجود ندارد.

## Metadata Package Watcher / Chat Bridge

Watcher endpoint Mutation جدیدی ایجاد نمی‌کند؛ همان `/plan`, `/apply`, `/pull` را orchestrate می‌کند.

برای Package Mode، machine-readable contract هر exchange در `chat-protocol.json` است و bootstrap اولیه از pair مستقل `<EID>-START-HERE.en.md + <EID>-upload-ai-gen.zip` استفاده می‌کند. `metadata-chat-workflow.fa.md` فقط user-flow operational mirror است. مرجع اصلی توسعه‌ای Chat Bridge در `Barsa.Ai.Host/Docs/AI/host/chat-bridge.fa.md` و مرجع اصلی Package Protocol در `Docs/AI/agent/package-protocol.fa.md` است.
