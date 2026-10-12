# AI Change / Plan / Apply — DataExchange Technical Contract

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


این سند مرجع فنی عمومی `Barsa.Meta.DataExchange` برای Semantic Change، Planner، Apply و Verifier است. Host این semantics را اجرا یا بازتعریف نمی‌کند؛ فقط endpoint/orchestration را فراهم می‌کند.


## Exact Change envelope and references

`AiChangeBatch` دارای `changes[]` است. هر Change فقط یکی از `create/update/delete` است و shape machine-level `AiSemanticChange` شامل `commandId`, `operation`, `objectType`, `tempId`, `target`, `parent` و `properties` است. شناسه persisted برای update/delete داخل typed `target` می‌آید؛ `id` در root Change جایگزین `target` نیست.

Referenceهای polymorphic در Change به شکل typed reference هستند:

```json
{"objectType":"entity","id":123}
```

یا برای dependency داخل Batch:

```json
{"objectType":"entity","tempId":"customer"}
```

برای mutation روی object موجود، target نیز همین typed-reference contract را دارد:

```json
{
  "commandId":"update-report",
  "operation":"update",
  "objectType":"report",
  "target":{"objectType":"report","id":123},
  "properties":{...}
}
```

`update` همان patch semantics است. هر `update/delete` قابل‌پشتیبانی باید `target` قابل resolve با `id` واقعی یا `tempId` معتبر داشته باشد؛ target حدسی مجاز نیست. اگر object در همان Batch با `tempId` ساخته شده و اصلاح هنوز قبل از Apply همان logical Batch است، reference موقت موجود استفاده می‌شود و round-trip فقط برای گرفتن ID شکسته نمی‌شود. اگر Apply قبلی object را ساخته ولی Verify شکست خورده است، correction بعدی باید `realId` همان command، mapping `temporaryIds` یا Runtime read-back معتبر Apply result را مصرف و `target` همان object را بسازد.

استثنای Source-confirmed جاری `SplUser` می‌تواند با reference نام‌محور Entity در System `Meta01` resolve شود؛ این رفتار به Entityهای دیگر تعمیم داده نمی‌شود.

System baseline contract فعلی: Create با `caption` الزامی و `dbPrefix/defaultCodeNamespace` اختیاری؛ update/delete عمومی فعلاً Unsupported است. Entity baseline: create/update `caption`، create روی System موجود می‌تواند `systemId` داشته باشد یا Parent System استفاده کند؛ delete عمومی فعلاً Unsupported است. DataExchange در Runtime فعلی برای create Entity الزام مستقلی مبنی بر داشتن Field/Relation اعمال نمی‌کند؛ completeness طراحی Entity خارج از این machine-level contract است و در Working Knowledge به‌صورت guidance نگهداری می‌شود.

Feature-specific exact properties/writeStatus در DX01..DX05 هستند؛ envelope عمومی آنها را تکرار نمی‌کند.

### Field vs Relation provider selection

Provider از `objectType` Change انتخاب می‌شود، نه صرفاً از `properties.fieldType`:

- scalar/non-relation Field → `objectType:"field"`؛
- semantic Relation → `objectType:"relation"` و نوع دقیق در `properties.fieldType`، مثلاً `singleRelation` یا `listRelation`.

`objectType:"field" + properties.fieldType:"singleRelation/listRelation/..."` contract معتبر نیست و نباید auto-rewrite شود؛ Planner باید `errorCode=wrongObjectType`, `path=objectType` بدهد. exact Relation properties و نمونه Create در DX02 هستند. Entity Create نیز هیچ machine invariant مبنی بر همراه‌داشتن Field/Relation در همان Batch ندارد؛ اگر Design عمداً Entity خالی می‌خواهد، Planner صرفاً به این دلیل Plan را invalid نمی‌کند.

## Change Batch

Operationهای پایه فقط:

```text
create
update
delete
```

- `update` patch است؛ property غایب یعنی no-change.
- `null` فقط وقتی تغییر محسوب می‌شود که property صریحاً در patch حضور داشته باشد.
- Delete فقط operation صریح است.
- `tempId` فقط در **همان logical Change/Batch** و Execution Context آن معنا دارد و persist نمی‌شود. `temporaryIds` result برای trace/read-back همان execution است. Change بعدی object persisted را با selector/context canonical resolve می‌کند؛ Runtime ID bridge semantic نیست. Session-level cache Host فقط convenience/diagnostic است.
- dependency از parent/referenceهای موقت و dependencyهای قابل استنتاج Planner ساخته می‌شود.

`AiChangeBatch` واحد اجرای مجموعه Semantic Change است. مرز Batch نباید به‌طور پیش‌فرض per-object یا per-report باشد:

- mutationهایی که intent/contract آنها قطعی است و برای تصمیم‌گیری به Runtime read-back میانی نیاز ندارند می‌توانند در یک Batch باشند؛
- چند Report/Field/Rule یا تغییر مستقل می‌توانند در یک Batch باشند؛
- dependency قابل بیان با `tempId`/reference و قابل مرتب‌سازی توسط Planner، به‌تنهایی دلیل شکستن Batch نیست؛
- Batch وقتی شکسته می‌شود که نتیجه Runtime مرحله قبل واقعاً ورودی تصمیم بعدی است، contract هنوز نامعلوم است، diagnosis جداسازی می‌خواهد یا حجم/ناهمگونی فهم و رفع خطا را نامعقول می‌کند؛
- هدف کاهش round-trip با حفظ diagnosability است، نه ساخت بزرگ‌ترین Batch ممکن.

## Plan

`BuildPlan(batch)` باید بدون Mutation این موارد را تعیین کند:

- shape/contract validation؛
- provider resolution؛
- dependency/order؛
- warning/error/unsupported؛
- fingerprint و داده لازم برای Apply.

Validationای که فقط به‌علت `tempId` و نبود Runtime object هنوز قابل انجام نیست deferred است، نه Error. Plan آن را با contract جاری `requiresApplyValidation/deferredValidations` حمل می‌کند. command-local validation/infrastructure-preflight failure در `ContinueIndependent` کل Plan را batch-invalid نمی‌کند؛ همان command `Failed` می‌شود و dependentهایش skip می‌شوند. Global Plan invalid برای contractهای batch-fatal مثل duplicate identity/dependency cycle باقی می‌ماند. Warning advisory blocking نیست؛ Unsupported فقط وقتی `IgnoreUnsupported=false` یا strict policy آن را blocking کرده باشد Apply را globally می‌بندد.

Planner برای System Build میان nodeهای dependency-ready phase priority زیر را اعمال می‌کند و dependency topology همیشه مقدم است: `System → Structural(Entity/primitive Field/Relation) → Entity details/formula/rule/View → Workflow → Report/DynamicCommand/Folder/final wiring`.

Plan تصمیم Design نمی‌گیرد و payload معنایی جدید اختراع نمی‌کند.

Plan error diagnostics باید از همان Planner/Provider result مشتق شود؛ Host validator مستقل نمی‌سازد. برای transportهای compact، هر blocker حداقل `commandId/objectType/operation/path?/errorCode/message` دارد. `unknown tempId` باید به‌صورت قابل‌تشخیص `errorCode=unknownTempId` surface شود تا stale/foreign temp reference با contract error عمومی اشتباه نشود. Full serialized Plan می‌تواند جداگانه نگهداری شود؛ diagnostics نباید برای سالم‌ماندن JSON به حمل Full Plan وابسته باشد.

**Plan/command failure rule:** batch-fatal `plan.IsValid=false` پیش از mutation هیچ Apply ندارد و همان logical Change پس از correction دوباره Plan می‌شود. اما command-local validation/infrastructure-registration preflight failure تحت `ContinueIndependent` داخل Plan معتبر حمل می‌شود: failed node و transitive dependentهایش اجرا نمی‌شوند و proven-independentها ادامه می‌یابند. این behavior dependency-aware است و مجوز split دستی scope برای سبزکردن نتیجه نیست.


## Apply

`ApplyPlan(plan)` فقط Plan پذیرفته‌شده را اجرا می‌کند.

- default `ErrorPolicy` برای Semantic Batch، `ContinueIndependent` است. failure یک command فقط transitive dependentهای آن را متوقف می‌کند و commandهای **proven independent** ادامه می‌یابند.
- در executable Semantic v15 فقط `ContinueIndependent` معتبر است؛ authored `StopBatch` در Lint/Plan رد می‌شود. Infrastructure failure یک policy stop نیست و factual گزارش می‌شود.
- اجرای referenceهای موقت staged است: commandهای پایه ابتدا Runtime ID می‌گیرند، سپس temp referenceها resolve می‌شوند و validationهای deferred با Provider واقعی دوباره اجرا می‌شوند.
- deferred/provider/verification failure در سطح command باقی می‌ماند؛ independent commandها ادامه می‌یابند. فقط ناتوانی واقعی زیرساخت می‌تواند execution را متوقف کند.
- infrastructure-backed Workflow/Dynamic registrations قبل از mutation در Plan با Central Resolver (`family + caption → RuntimeId`) resolve/cache می‌شوند؛ Apply همان immutable resolved set را مصرف می‌کند و Writer registration rediscovery نمی‌کند.
- نتیجه per-command شامل phase/status، errors/warnings و `realId` است و mapping `temporaryIds` برای ادامه execution برگردانده می‌شود.
- mutation reporting v137 monotonic است: قبل از اولین persistence → `mutationApplied=false, partialMutation=false`؛ پس از اولین persistence موفق applied دیگر false نمی‌شود؛ failure بعدی → `mutationApplied=true, partialMutation=true`؛ success کامل → `mutationApplied=true, partialMutation=false`. Multi-step Provider persistence را در execution context mark می‌کند و Executor از Exception type mutation را حدس نمی‌زند.
- فقط descendantی که Parent آن واقعاً ایجاد نشده با `SkippedDependency` مشخص می‌شود. `SkippedPolicy` نتیجه عادی executable Semantic v15 نیست.
- generic provider فعلی mutation خطرناک انجام نمی‌دهد و در نبود support صریح `Unsupported` برمی‌گرداند.

## Formula / Report dependency validation

برای Formula روی Entity جدید، Planner field/relationهای ساده همان owner را قبل از field فرمول‌دار قرار می‌دهد تا compile deferred روی TypeDef کامل‌تر انجام شود. Report یا Formula دارای reference موقت بعد از resolve شدن IDها با همان parser/compiler Runtime دوباره validate می‌شود؛ projected Runtime model موازی ساخته نمی‌شود.

## Provider resolution boundary

Planner/Executor از Providerهای DataExchange استفاده می‌کنند. قرارداد توسعه و انتخاب Provider در:

`dataexchange/08-provider-development-reference.fa.md`

contractهای Feature-specific در `01..05` همین پوشه باقی می‌مانند و این سند آنها را تکرار نمی‌کند.

## Verify

Verifier باید semantic intent را با Runtime read-back مقایسه کند. `verificationSucceeded=true` اثبات Metadata contract است و به‌تنهایی user-flow/UI/data behavior را ثابت نمی‌کند.

- `partiallySucceeded` clean success نیست و diagnostics/command result باید حفظ شود.
- Formula execution، Report result/filter، Validation، Action یا Workflow transition فقط با smoke واقعی behavior-verified است.
- اگر smoke API/path موجود نیست، Metadata verify شود ولی behavior با وضعیت صریحی مثل `not runtime-smoked` باقی بماند.
- check اضافه فقط وقتی موجه است که failure معنادار یا regression واقعی را بگیرد.

## Host boundary

Host endpointهای `/plan`, `/apply`, `/apply-status` و orchestration/read-back را مالک است؛ جزئیات Host در:

`Host-side documentation outside EM01 package`

Host نباید این DataExchange contract را موازی تعریف کند.

## Semantic v15 — transport/write contract

`AiChangeBatch.profileVersion` اجباری و دقیقاً `15` است. missing/v14/other version Reject می‌شود؛ compatibility apply path وجود ندارد.

Semantic reference authority فقط Selector + Context است. Runtime `Id`, `dbName`, `dependencyKey` fallback ممنوع است. `TempId` فقط داخل همان logical Batch برای dependency فنی مجاز است.

Direct typed references `"#..."` هستند؛ `{objectType,selector}` wrapper canonical نیست. exact rules, text boundary و partial-mutation reconcile: `dataexchange/13-semantic-v15-reference.fa.md`.

## Semantic v15 authority guard

هر section version-old/historical در این فایل فقط engineering history است. برای executable Semantic Export/Apply/Verify، `dataexchange/13-semantic-v15-reference.fa.md` مقدم است.


## v202 — Runtime reference authority

`# = semantic FK/reference` برای Metadata و Dynamic Row یکسان است. `externalData` kind وجود ندارد؛ `sourceRowId`/`dependencyKey` authority نیستند. Target از Property/FieldInfo/Context، row lookup از `GetDefaultFieldOrFirst()` و 0-match از FieldInfo به‌صورت type-aware مدیریت می‌شود. Plan/Apply provider payload از policy مرکزی Text Boundary می‌آیند.
