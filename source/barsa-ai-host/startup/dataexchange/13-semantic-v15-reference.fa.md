# Semantic v15 — DataExchange Technical Contract

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


## v202 — Authoritative reference contract

- `#Key` / `#[Target]Key` universal semantic FK/reference است؛ Metadata/Data representation جدا ندارند.
- Target از Property/FieldInfo/Context استنتاج می‌شود؛ Dynamic Row lookup authority=`TypeDef.GetDefaultFieldOrFirst()`.
- `externalData` Semantic kind نیست؛ `sourceRowId`/`dependencyKey` reconstruction authority نیستند.
- 0-match=`UnresolvedSemanticReference`; فقط FieldInfo-proven empty/sentinel مجاز است، وگرنه command-local failure. fake row ممنوع.
- Semantic text=`ی/ک`; provider/DB boundary=`ي/ك`; Plan و Apply policy مشترک دارند.
- Parameter absent defaults: `input=false`, `notAutoRemove=false`; CurrentUser=context.
- Source-certified String/RichString includes `contains`/`doesNotContain`/`startsWith`/`doesNotStartWith`; unknown operator explicit Unsupported.
- Contract revision=`v15-qtr-v202`; runtime fingerprint از deployed binaries است، نه hard-coded update id.

## Current authoritative runtime contract

این سند مرجع فنی مرکزی Semantic v15 برای Agent/Host در Package Mode است. جزئیات feature-specific در سایر `dataexchange/*` باقی می‌ماند، اما هرجا سند قدیمی با این فایل تعارض دارد، این فایل برای Semantic Export/Apply/Verify مقدم است. Source واقعی SystemBuilder authority رفتار است؛ contradiction قطعی با Source باید `STOP/GAP` شود، نه fallback حدسی.

## Version / execution boundary

```text
profileVersion = 15
```

- Runtime جدید فقط v15 را می‌پذیرد.
- ورودی بدون `profileVersion`، v14 یا هر نسخه دیگر Reject است.
- v14 فقط historical/frozen artifact است و executable input نیست.
- compatibility bridge / legacy apply path برای v14 وجود ندارد.

## Semantic object discriminator `$type`

Semantic snapshot objectهای اصلی self-describing هستند. `$type` canonical و انگلیسی است:

```text
system
entity
field
relation
view
report
workflow
```

Navigation node در صورت serialize شدن به JSON از `navigationPage`, `navigationGroup`, `navigationReport`, `navigationRoot` استفاده می‌کند؛ directory-only placement فایل JSON جدا لازم ندارد.

برای FieldDef، `fieldType` subtype را مشخص می‌کند و `$type` سطح object را:

```json
{"$type":"field","fieldType":"string"}
{"$type":"relation","fieldType":"singleRelation"}
```

`$type` read-only Semantic metadata است. ownership/Compose از relation واقعی مدل و placement از Navigation می‌آید. در `AiChangeBatch`، `objectType` envelope همچنان dispatch authority است و `$type` داخل `properties` author نمی‌شود. Snapshotهای قدیمی بدون `$type` برای read/diagnostic قابل تحمل‌اند؛ Export جدید باید `$type` را تولید کند.

## Semantic authority

```text
Semantic Identity / Semantic Reference
→ authority برای Export / Apply / Verify

Runtime ID / dbName / sourceRowId / dependencyKey
→ semantic authority نیست
```

`TempId` فقط reference فنی داخل همان logical `AiChangeBatch` است و Semantic identity نیست. Runtime ID فقط implementation/read-back detail است و fallback Semantic resolution نمی‌شود.

## Selector grammar

همه Semantic Selectorها با `#` شروع می‌شوند:

```text
#Key
#[Target]Key
#Part1|Part2|Part3
#[TargetPart1|TargetPart2]KeyPart1|KeyPart2
```

نمونه:

```text
#پرسنل
#پرسنل|ویرایش پرسنل
#[شهر]تهران
#[منابع انسانی|پرسنل]12345
#@SplUser
#[@SplUser]admin
```

separator یگانه `|` است. comma separator و `semanticId` قدیمی superseded هستند.

Escapes:

```text
\|  literal pipe
\[  literal [
\]  literal ]
\@  literal leading @
\\  literal backslash
\#  literal # inside selector
```

Leading-hash precedence:

```text
#ABC    → selector Key=ABC
##ABC   → literal #ABC
###ABC  → selector Key=#ABC
####ABC → literal ##ABC
```

## Context / shortening

Context از Batch execution state جدا است و حداقل شامل:

```text
System
TypeDef / Entity
ActiveField
FieldType
TargetTypeDef when Source semantics prove it
```

Traversal:

```text
Push → process → Pop
```

Qualifier فقط به‌اندازه context گمشده اضافه می‌شود. مثال View:

```text
No context     → #System|Entity|View
System context → #Entity|View
Entity context → #View
```

Property/schema نوع resolver را تعیین می‌کند؛ type معلوم از Property دوباره در reference تکرار نمی‌شود.

## Direct semantic references

Typed property مستقیماً selector string می‌گیرد:

```json
"field": "#عنوان"
"entity": "#پرسنل"
"view": "#نمای اصلی"
"report": "#گزارش پرسنل"
"systemId": "#منابع انسانی"
"target": "#شهر"
```

`{objectType,selector}` برای typed property canonical نیست. Target clause فقط برای heterogeneous reference معتبر است، مانند:

```json
"selectedRules": ["#[businessRule]کنترل مبلغ"]
```

## FieldItem / Self

FieldItem traversal با Semantic identity path یکی نیست. Chain canonical:

```json
"field": {"items":["#استان","#شهر","#عنوان"]}
```

`path`/flattening به `#A|B|C` canonical نیست. Segment فقط Source-confirmed extra semantics را نگه می‌دارد.

Self Runtime Field نیست:

```json
"field":{"self":true}
```

Parameter Self نیز `self:true` دارد؛ از نام `{خود}` inference نشود و Runtime `id=0` placeholder ممنوع است.

## Report local identity

Parameter:

```text
local key = Name
Name empty → Error
Name duplicate inside Report → Error
no ~index fallback
```

Column:

```text
1. usable Alias
2. semantic caption/display
3. empty/duplicate → ~index
```

`~<digits>` namespace generated local-index است. natural key با همین shape باید literal escape شود. اعتبار `~index` وابسته به پایداری canonical `columns[]` order در Export→Apply→Re-export است.

Matrix و سایر report-local refs selector-based هستند. Source Runtime ID برای Column/Group/Parameter/JoinAlias/Condition/FormatCondition و structural children در Export omit و در Apply never-assign است.

## BusinessRule / UniqueConstraint

Definition discriminator:

```json
{"type":"businessRule"}
{"type":"uniqueConstraint"}
```

Rule local identity scope = Owner Entity + subtype.

- Caption non-empty + unique → Caption key.
- empty/duplicate → deterministic short key از `EorgGlobalIdHelper.GenerateGlobalId(rule.Id)` → SHA-256 UTF-8 → decimal digit stream → `~` + 6 digits، سپس 8/10/... در collision.
- `string.GetHashCode()` ممنوع.
- این fallback Universal UID نیست.

Rule internal Field reference باید selector باشد؛ Runtime Field ID خام ممنوع است.

## Code / SQL / Formula

MetaCode envelope/noise فنی نباید leak کند. وقتی Property semantics را تعیین می‌کند:

```json
"code": "return value;"
"sql": "select ..."
```

metadataهایی مثل `id/address/addressInTarget/layer/location/parameterTypeDefId` فقط به دلیل internal MetaCode model صادر نمی‌شوند.

Formula nuance: اگر Source semantics واقعی مثل `executionTime` یا formula kind لازم است، Formula می‌تواند structured object بماند. Formula را کورکورانه به string flatten نکن؛ implementation noise حذف و semantics واقعی حفظ شود.

## Picture Group / SystemItemGroup

Picture Group identity = `Name` در scope همان Pictures Field:

```text
empty/duplicate Name → Error
no Runtime ID/hash/index fallback
```

Source `id/value` در Semantic حذف می‌شوند.

SystemItemGroup:

```json
{"caption":"فیلد متنی"}
```

reference:

```json
"systemItemGroup":"#فیلد متنی"
```

`group:n` superseded است. empty/duplicate → ambiguity/error.

## Navigation

Synthetic refs زیر ممنوع‌اند:

```text
page:n
group:n
placement:n
report:n
parentRef
```

Hierarchy از nesting JSON می‌آید.

Source-confirmed target در baseline v164 فقط Report است؛ View/Entity placement تا Source proof اضافه نشود `GAP/N/A` است.

Container identity:

```text
Page  → Name within Parent
Group → Name within Parent
```

Report placement identity:

```text
kind=report + target Report selector within Parent
```

Apply:

```text
0 match → Create
1 match → Update
>1 → Ambiguity/Error
omitted existing node → no implicit delete
```

Name comparison از v15 text boundary عبور می‌کند. NavItem name برای Report placement identity مستقل نیست. Runtime-ID/ordinal fallback ممنوع است.

## Relation / Dynamic Row

Dynamic Row key field فقط:

```csharp
typeDef.GetDefaultFieldOrFirst()
```

Standard Relation:

```text
#تهران
```

General Relation:

```text
#[شهر]تهران
```

Cross-system:

```text
#[منابع انسانی|پرسنل]12345
```

Global:

```text
#[@SplUser]admin
```

SingleRelation به‌عنوان dynamic-row default semantic key تا contract مستقل Source-proven نشده Unsupported + Warning است.

## FieldInfo-driven conversion

Converter بر اساس FieldInfo واقعی انتخاب می‌شود، نه CLR value type. deterministic/pure/invariant semantics از Source استخراج و داخل DataExchange reimplement می‌شود؛ code/expression evaluation و side-effect حذف می‌شوند. اگر safe semantics ثابت نشد: `Unsupported + Warning`.

Date/Enum support در v159+ Source-derived اضافه شده است. `GetCaptionFromValue/GetValueFromCaption` primary semantic dependency نیست.

حالات زیر مستقل‌اند:

```text
absent
null
""
unsupported
```

Unsupported silently omit نشود.

## Text boundary

```text
DB:          Arabic ي / ك
Application: Persian ی / ک
```

```csharp
ToDatabaseText(...)    => FixFarsiText()
ToApplicationText(...) => FixFarsiTextReverse(...)
```

Boundary برای همه strings، شامل Code/Expression/SQL/Regex/URL/raw text اعمال می‌شود. Selector syntax دست‌نخورده می‌ماند؛ parsed selector components پیش از Runtime lookup DB-normalize می‌شوند. Verify/read-back comparison در v15 canonical Application text را مصرف می‌کند.

Normalization ambiguity → Warning + First Match + non-certified.

## Comparison operators

فقط Source-confirmed semantics پیاده شود. رفتار `equal` به operatorهای دیگر تعمیم حدسی داده نشود؛ unknown value semantics → Unsupported + Warning.

## Partial mutation / reconcile

```text
Failure without mutation
→ fail + block dependents
→ proven-independent branches may continue

Failure with partial mutation
→ PartialMutation=true
→ affected branch blocked
→ NeedsReconcile

shared/unknown effect
→ Immediate Reconcile

otherwise
→ aggregated Final Read-back / Reconcile
```

Final verifier باید failed partial mutations را نیز read-back کند.

## Rename / UID

Universal `$uid` در v15 فعلی وجود ندارد. Rename-aware synchronization تضمین نمی‌شود:

```text
semantic key changes → Create ممکن است رخ دهد
old object → implicit delete نمی‌شود
```

اگر در آینده UID اضافه شد reconciliation-only است و Semantic Selector نمی‌شود.

## Current implementation / certification state

```text
Contract                    = Active / Authoritative
Semantic shape/export baseline             = update-v164
Runtime reconstruction/apply implementation = update-v174+
Code review                  = GO
Real Semantic Export         = GO
Build certification (v164)   = Pending / not recorded as certified
Deploy                       = Pending
Runtime Apply clean Target   = Pending
Export→Apply→Export          = Pending
Semantic Compare             = Pending
Runtime Certification        = Pending
```

`update-v164` Runtime Certified یا Round-trip PASS نیست.

## Superseded — do not reintroduce

```text
v14 executable compatibility
comma selector separator
semanticId path model
Runtime ID/dbName/dependencyKey semantic fallback
nested {objectType,selector} for typed properties
FieldItem flattened selector path
Report child source IDs
synthetic Navigation refs
blind Navigation subtree rebuild
Universal UID in current v15
```

## Next required proof

قبل از redesign جدید:

```text
Build
→ Deploy
→ Source Export
→ Apply on suitable/clean Target
→ Final Read-back
→ Re-export
→ Semantic Compare
```

تمرکز Compare: Rule fallback key، Report Parameter، Column order/~index، Matrix refs، Self، FieldItem chains، Picture/SystemItemGroup، Navigation, Code/SQL/Formula, Relations/GeneralRelation.

---

# Runtime Reconstruction Contract Sync — update-v171 (Final Implementor Contract v10)

این بخش وضعیت اجرایی قبلی این سند را supersede می‌کند؛ Semantic v15 redesign نشده است.

```text
One Semantic Contract
One Reference Resolver behavior
One Per-command SemanticResolutionContext
One Canonical Read-back
One Semantic Verifier
```

- Runtime ID هیچ‌گاه authority در canonical Semantic v15 نیست؛ same logical batch فقط `tempId` و cross-wave فقط selector/context.
- هر command با context معنایی تازه شروع می‌شود. Plan binding داخلی می‌تواند Runtime ID resolved را فقط برای staleness check نگه دارد؛ Apply باید همان target را ببیند وگرنه `Conflict` بدهد.
- `ContinueIndependent`: batch-fatal کل Apply را متوقف می‌کند؛ command-local failure فقط همان branch وابسته را متوقف می‌کند. Plan summary بین `canApplyAny` و `canApplyAll` فرق می‌گذارد.
- `dbName` در Semantic می‌ماند: اگر آزاد بود exact preserve؛ collision => deterministic unique target name + Warning + explicit `DbNameRemap` evidence + continue. Verifier/structured metadata فقط remap ثبت‌شده را مصرف می‌کنند. SQL/Code/Expression هرگز blind textual rewrite نمی‌شوند.
- Portable image `sha256` فقط transport/package integrity است. Semantic image equality با decode و مقایسه width/height/pixels انجام می‌شود، نه PNG byte hash.
- Icon فقط وقتی supported است که Save→Reload→Read-back→Verify پایدار باشد؛ در غیر این صورت باید پیش از mutation Unsupported شود.

Implementation baseline بعد از این sync: `update-v171` روی baseline `v170`.
Runtime / full round-trip certification همچنان Pending است تا سناریوی کامل واقعی Export→Package→Plan→Apply→Read-back→Verify→Re-export→Semantic Compare اجرا شود.


## Runtime reconstruction follow-up v173

Package authored payload lint قبل از ZIP از Runtime authority مرکزی استفاده می‌کند: duplicate commandId، dependency cycle، malformed selector grammar و root `externalDataMappings` blocking هستند. `DbNameRemap` فقط با exact key `OwnerSemanticIdentity + ObjectSemanticIdentity + SourceDbName` معتبر است و final result/verify نباید temp-only یا owner-ambiguous mapping را مصرف کند.

## Runtime reconstruction final blocker closure v174

`update-v174` is the direct package for the applied v172 baseline because v173 was not deployed. DbNameRemap artifact keys use full/context-independent canonical semantic identities for both owner and object plus SourceDbName. Runtime IDs are execution-only lookup evidence and never part of the key. Finalized create remaps must contain canonical identities; exact matching prevents cross-system same-name tolerance.

---

## Runtime reconstruction follow-up v175

Authoring/Write contract نهایی این follow-up:

```text
same-wave reference       = tempId
persisted/cross-wave      = semantic selector + owner context
Runtime ID                = execution evidence only
reportId                  = report semantic reference
typeViewId                = view semantic reference
referenceField.operator   = scalar, e.g. "equal"
```

Report FieldItem:

```text
single field  -> typed Field reference
self          -> { self: true }
path          -> { items: [ Field reference / {field: Field reference, ...} ] }
```

Export Snapshot مستقیماً Write payload نیست؛ object-specific converter/Writer shape باید رعایت شود.

Navigation از provider موجود Folder استفاده می‌کند:

```text
Root Folder       -> Runtime/System-owned; Agent does not create
Page              -> folder kind=page
Group             -> folder kind=group
Report Placement  -> folder kind=report
```

application-data row selector که روی Target وجود ندارد نباید fake/materialize شود؛ v202 آن را `UnresolvedSemanticReference` می‌داند و FieldInfo تعیین می‌کند empty/sentinel معتبر است یا command-local failure لازم است.

---

## Runtime follow-up — update-v176 / SOC ↔ IOC QTR scope

- Agent فقط **SOC** را author می‌کند؛ IOC و Runtime ID فقط داخل Host/DataExchange هستند.
- Export و Apply برای QTR scope دو جهت یک mapping deterministic هستند؛ Host inference آزاد/LLM ندارد.
- dependency ساخت Child فقط به **وجود واقعی Parent** وابسته است، نه موفقیت همه‌ی post-save stageها.
- `ParentNotCreated` با `UnresolvedDependency` متفاوت است.
- command-level failure دیگر policy-based global stop ایجاد نمی‌کند؛ independent branch باید ادامه یابد.
- بعد از اولین persistence قطعی، `realId` / owner / semantic identity / mutation stage به‌صورت execution receipt حفظ و `tempId` همان batch bind می‌شود.
- partial mutation بعد از persistence، object را nonexistent نمی‌کند؛ reconcile failure محلی و `Reconstruction=Incomplete` است.
- Report FieldItem همان embedded SOC contract واحد Parser/Validator/Resolver/Writer/Verifier را استفاده می‌کند؛ direct same-wave `tempId` و persisted selector معتبرند.
- Navigation همان `folder` موجود با `kind=page|group|report` است؛ Root را Runtime می‌سازد. `order` معنای relative sibling order دارد، نه raw Runtime number.
- Layout باید از authority موجود `AiViewRuleModel` برای Read/Write/Verify استفاده کند؛ Agent XML author نمی‌کند.
- Date normalization فقط Field/Property-aware است؛ String شبیه تاریخ exact String باقی می‌ماند.
- canonical lint قبل از Package/Plan باید shapeهای قابل تشخیص محلی را با همان Provider contract رد کند.
- Historical v176 fingerprint expectation; superseded by v202 binary-derived fingerprint + `socContractRevision=v15-qtr-v202`.
- `socContractHash`, timings و failure-index در این Update P1/Deferred هستند مگر بدون بزرگ‌کردن Scope قابل تکمیل باشند.
- Runtime Golden frozen known-good SOC باید قبل از End-to-End Golden با Agent PASS شود.
- Build/Deploy/Restart و Golden واقعی فقط با evidence محیط Runtime قابل certify هستند؛ Source/package validation جای آن را نمی‌گیرد.

## v177 focused SOC→IOC rules

- `StopBatch` authored policy معتبر نیست؛ executable v15 فقط `ContinueIndependent` است.
- `defaultEditView` از central Reference Contract resolve/verify می‌شود.
- `reportRelation.reportId` Semantic reference است؛ `target` derived و `orderNumber` reconstruction-order evidence است. Export state قبل از Provider validation به writable IOC projection تبدیل می‌شود؛ Agent Export را دستی sanitize نمی‌کند.
- FieldDef order semantic فقط relative sibling order بین همه Field/Relationهای همان Entity است؛ raw numeric equality authority نیست.



## v178 focused canonical-lint closure

- cross-wave selector معتبر یک **deferred Semantic reference** در pre-resolution lint است؛ Provider نباید قبل از Plan/Resolve وجود Runtime binding را الزام کند. Runtime ID همچنان در authored SOC ممنوع است.
- `defaultEditView` تنها property canonical Entity برای default View در executable v15 است. Aliasهای legacy `defaultView`، `defaultEditViewId` و `defaultViewId` canonical نیستند و reject می‌شوند.
- `reportRelation.target` اگر در SOC authored حضور دارد، قبل از projection با central relation→entity reference contract کامل validate می‌شود؛ malformed value نباید با derived projection پنهان شود. بعد از validation، `target` از `reportId` derive و از direct Provider write حذف می‌شود.
- `FieldDef.orderNumber` raw patch یا semantic dependency نیست. معنی آن relative sibling order بین همه Field/Relationهای همان Entity است. Planner برای presentation order edge جدید به DAG اضافه نمی‌کند؛ پس ordering نباید cycle معنایی بسازد. Runtime پس از mutation فقط slotهای order موجود siblingهای مشارکت‌کننده را بر اساس rank معنایی بازتخصیص می‌دهد و Verify sequence را می‌سنجد، نه عدد خام.
- Historical v178 fingerprint expectation; superseded by v202 binary-derived fingerprint + `socContractRevision=v15-qtr-v202`.

Runtime behavioral acceptance (Build/Deploy/T1..T10/Golden) تا اجرای واقعی محیط Target `PendingRuntimeExecution` است.

## v179 focused correction — Workflow nested references

Workflow nested object references همان boundary مرکزی Semantic v15 را مصرف می‌کنند. Pre-resolution validation برای reference معتبر cross-wave به Runtime `id` نیاز ندارد:

```text
same-wave       → tempId
persisted       → selector/context
Runtime ID      → internal IOC only
```

`variable.entity` و nested activity references باید selector معتبر را به‌عنوان unresolved-but-valid تا Plan/Resolve عبور دهند. Runtime numeric IDs، malformed selector و wrong reference type همچنان قبل از mutation نامعتبرند.

Non-participating FieldDef sibling ordering در v179 فقط micro-test/evidence است و به دلیل ناقص بودن Acceptance ورودی، الگوریتم v178 را تغییر نمی‌دهد.

## v186 — Raw JsonProperty و Semantic Contract Registry

- canonical property برای Runtime `JsonProperty` فقط `jsonProperty` است و مقدار آن **raw opaque string یا null** است؛ parse، تبدیل به flag یا nested object ممنوع است.
- `field` و `relation` از `FieldInfoBase.JsonProperty` و `report` از `Report.JsonProperty` read/write/read-back می‌شوند.
- `uiProperties` canonical نیست و authored آن باید مانند property ناشناخته reject شود؛ هیچ تبدیل ضمنی به `jsonProperty` وجود ندارد.
- معنی Object/Propertyهای ثبت‌شده در `SemanticContractRegistry` نگهداری می‌شود و Runtime provider/writer فقط adapter اجرایی است.

