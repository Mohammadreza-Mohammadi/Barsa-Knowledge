# Project Status — Semantic v15

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


- Verify unresolved substitution: selector باید دوباره resolve شود؛ فقط still-unresolved + FieldInfo-safe actual به‌صورت NonCertified warning پذیرفته می‌شود، نه VerificationFailed.

## Semantic v15 — Contract consolidation v202 (Historical; superseded by v205)

این بخش وضعیت جاری را supersede می‌کند؛ بخش‌های نسخه‌ای قدیمی‌تر فقط Historical هستند.

- `#Key` و `#[Target]Key` تنها مدل canonical برای semantic FK/reference هستند. Data Row و Metadata Object representation جدا ندارند.
- Target ابتدا از Property/FieldInfo/FieldType/`SemanticResolutionContext` استنتاج می‌شود؛ Target داخل selector فقط وقتی لازم است که Context آن را تعیین نکند.
- Dynamic Row با همان Semantic resolver و `TypeDef.GetDefaultFieldOrFirst()` resolve می‌شود. Runtime ID، `sourceRowId` و `dependencyKey` semantic authority نیستند.
- `externalData` یک Semantic v15 reference kind نیست و `externalDataMappings` فقط legacy authored input ممنوع است.
- `0 match` یعنی `UnresolvedSemanticReference`. Writer فقط اگر FieldInfo/SystemBuilder یک empty/sentinel واقعی را مجاز بداند همان مقدار type-aware را می‌نویسد؛ در غیر این صورت خطای command-local می‌دهد. fake row ساخته نمی‌شود.
- Text boundary مرکزی است: Semantic/Application از `ی/ک` و DB/provider payload از `ي/ك` استفاده می‌کند. Plan و Apply از یک Provider payload policy عبور می‌کنند؛ per-feature Unicode normalization ممنوع است.
- Report Parameter: `input` و `notAutoRemove` در صورت absence برابر `false` هستند. `currentUser` یک context parameter است، نه ordinary input parameter.
- Report scalar conditionهای Source-certified فعلی: `equal`, `notEqual`, `greaterThan`, `lessThan`, `greaterThanOrEqual`, `lessThanOrEqual` و برای String/RichString نیز `contains`, `doesNotContain`, `startsWith`, `doesNotStartWith`. operator ناشناخته explicit Unsupported است.
- Formula activation authority فقط FormulaClass/HasFormula است؛ stale AutoCalc MetaCode Formula فعال ایجاد نمی‌کند.
- Navigation order با relative sibling sequence مقایسه می‌شود، نه raw numeric order.
- Runtime fingerprint از binary واقعی Host/DataExchange/Barsa.Meta و `socContractRevision=v15-qtr-v202`, profile 15 و build identity ساخته می‌شود؛ `updateId` hard-coded authority نیست.
## Current state — Semantic v15 Apply Lifecycle v206 + Runtime Golden Pending

Authority:

```text
Semantic v15 Contract = Active / Authoritative
Knowledge baseline     = knowledge/semantic-v15-current.fa.md
Technical contract     = dataexchange/13-semantic-v15-reference.fa.md
Semantic shape/export baseline = update-v164
Runtime reconstruction/apply implementation = update-v174+
Host synchronization package = update-v166
```

Certification:

| Stage | Status |
|---|---|
| Static/Source Review | GO |
| Real Semantic Export audit | GO |
| Build (v164) | Pending / not recorded as certified |
| Deploy | Pending |
| Runtime Apply on suitable/clean Target | Pending |
| Final Read-back | Pending |
| Export → Apply → Export | Pending |
| Semantic Compare | Pending |
| Runtime Certification | Pending |

`update-v164` **نباید** Runtime Certified، Round-trip PASS یا production-certified ثبت شود تا proof واقعی بالا تکمیل شود.

آخرین Real Export audit ثبت‌شده در KM جاری:

```text
Semantic JSON files                       = 654
Navigation report placements              = 495
Report placements missing report selector = 0
nested {objectType,selector} refs          = 0
synthetic navigation refs                  = 0
parentRef leakage                          = 0
numeric field references                   = 0
known Report child id leakage              = 0
```

Known gaps/limitations فعلی:

- بعضی operator semantics مانند `contains` هنوز کامل Source-certified نیستند.
- Report Parameter با `FieldInfo == null` Unsupported/Invalid است.
- Report duplicate ambiguity و normalization ambiguity non-certified هستند.
- View/Entity Navigation placement فعلاً Source-confirmed نیست.
- Universal UID / rename-aware reconciliation deferred است.
- Column `~index` integration round-trip هنوز proof واقعی می‌خواهد.
- Apply → Re-export → Semantic Compare روی clean Target هنوز اجرا نشده است.

Next milestone:

```text
Build → Deploy → Export → Apply → Read-back → Re-export → Semantic Compare
```

---

## Runtime implementation status — update-v171

```text
Baseline applied by operator = update-v172
Current focused implementation delta = update-v174 (direct delta on applied v172; includes v173 follow-up + canonical remap identity blocker fix)
Final Runtime contract       = Semantic v15 Runtime Reconstruction / Apply v10
```

در `update-v171` implementation با contract نهایی sync شده است: per-command context، Plan→Apply binding conflict، ContinueIndependent تا Host bridge، dbName deterministic remap/evidence و remap-aware verify/structured metadata، و image pixel semantic verification.

این ثبت **Runtime Certification نیست**. Build/Deploy و همان سناریوی full real reconstruction باید روی محیط Barsa اجرا و نتیجه Re-export/Semantic Compare ثبت شود.

---

## Runtime implementation status — update-v175

```text
Baseline authoritative                 = post-update-v174 source
Current focused implementation delta   = update-v175
Semantic shape/export baseline         = v164/v15 contract retained
Runtime reconstruction/apply contract  = v175 focused follow-up
Runtime Certification                  = Pending real full reconstruction
```

v175 فقط mismatchهای اثبات‌شده System/Report/View/reference/binding/verify/navigation/external-data و Agent Knowledge را می‌بندد. Runtime ID authority، Rebuild Compiler/API/framework جدید و compatibility برای payload آزمایشی قدیمی اضافه نشده است.

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
- Runtime fingerprint شامل deployed Host/DataExchange/Barsa.Meta identity، `updateId=v176`، profile 15 و `socContractRevision=v15-qtr-v176` است.
- `socContractHash`, timings و failure-index در این Update P1/Deferred هستند مگر بدون بزرگ‌کردن Scope قابل تکمیل باشند.
- Runtime Golden frozen known-good SOC باید قبل از End-to-End Golden با Agent PASS شود.
- Build/Deploy/Restart و Golden واقعی فقط با evidence محیط Runtime قابل certify هستند؛ Source/package validation جای آن را نمی‌گیرد.

## v177 acceptance status

Implementation package: `update-v177`. Static/package validation می‌تواند قبل از Deploy انجام شود؛ Build/Deploy/T1..T10/Runtime Golden/E2E Golden تا اجرای واقعی فقط `PendingRuntimeExecution` هستند و Success فرض نمی‌شوند.



## v178 focused correction status

Static/source scope: cross-wave pre-resolution selector, canonical-only `defaultEditView`, pre-projection validation of derived `reportRelation.target`, and cycle-safe FieldDef sibling ordering. Runtime fingerprint target: `updateId=v178`, `socContractRevision=v15-qtr-v178`. Build/Deploy/T1..T10/Runtime Golden/E2E Golden: `PendingRuntimeExecution` until real execution evidence exists.

## v179 focused correction

- baseline عملیاتی برای این بسته: v175؛ بسته v179 cumulative است و fixهای معتبر v176..v178 را نیز حمل می‌کند.
- Workflow nested references در pre-resolution از central Semantic reference semantics استفاده می‌کنند؛ cross-wave selector معتبر است و Runtime ID authored ممنوع می‌ماند.
- Build/Deploy/Runtime acceptance بدون اجرای واقعی `PendingRuntimeExecution` است.
- TEST-2 non-participating sibling فقط evidence/micro-test است؛ Acceptance ناقص ورودی باعث تغییر الگوریتم ordering نشده است.

## v180 — Workflow Reference Pipeline

Workflow authored SOC vs resolved IOC reference phases are separated. Canonical selector strings are accepted end-to-end; Planner/Executor generated Runtime IDs remain internal and valid only after Resolve. Runtime execution gates remain evidence-based.
