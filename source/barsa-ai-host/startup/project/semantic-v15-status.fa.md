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


## v202 authoritative contract cleanup

Current contract: universal `#` selector, no metadata/data split, no `externalData` kind; 0-match=`UnresolvedSemanticReference` with FieldInfo-driven unresolved value. Parameter defaults=false, CurrentUser=context, Source-certified contains فعال، Navigation relative-order و Formula authority حفظ شده‌اند. Runtime fingerprint revision=`v15-qtr-v217`. Older version sections below are Historical.

## Semantic shape/export baseline: update-v164
## Runtime reconstruction/apply implementation: update-v174+
## Host synchronization package: update-v166

Authority:

```text
Semantic v15 Contract = Active / Authoritative
Knowledge baseline     = knowledge/semantic-v15-current.fa.md
Technical contract     = dataexchange/13-semantic-v15-reference.fa.md
Semantic shape/export baseline = update-v164
Runtime reconstruction/apply implementation = update-v174+
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

## update-v171 — Runtime Reconstruction v10 implementation

Baseline factual این Delta: `update-v170` توسط operator Apply + Build + Restart شده است.

`update-v171` sync implementation با Final Implementor Contract v10 است و redesign Semantic v15 نیست. محورهای اجرا: fresh per-command semantic context، Plan/Apply same-target binding، ContinueIndependent در Host bridge، dbName preserve/remap با evidence، remap-aware structured metadata/verifier، و decoded-pixel image verification.

```text
Static/source implementation = updated in v171
Real Barsa build/deploy       = must be run after applying v171
Full 452-command rerun        = Pending
Re-export + Semantic Compare  = Pending
Runtime Certification         = Pending
```

## update-v174 — direct v172 final blocker closure

Baseline applied by operator = `update-v172`. `update-v173` was not applied; v174 includes its focused linter/remap lifecycle changes plus canonical/context-independent DbNameRemap owner/object identities. Build/Deploy/Full Reconstruction/Re-export/Semantic Compare remain required for Runtime Certification.

## update-v175 — focused Runtime follow-up after v174

Authoritative baseline این Delta همان post-v174 Source است. Scope محدود به 11 failure/contract item ثبت‌شده است و redesign ندارد. Static/source implementation شامل System symmetry، Report FieldItem conversion، typed report/view references، scalar referenceField operator، same-batch binding fix، verifier classification/date normalization، Navigation knowledge و historical external-data classification (superseded by v202 UnresolvedSemanticReference) است. Enum materialization lifecycle و View shared resolver موجود حفظ شده‌اند و framework موازی ساخته نشده است.

```text
Build/Deploy                           = Pending operator environment
Fresh Full Reconstruction             = Pending
Re-export + Semantic Compare          = Pending
Runtime Certification                 = Pending
```

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

## v177 — focused correction on v176

```text
baseline = v176
update = v177
package/static validation = PASS when locally validated
build = PendingRuntimeExecution
deploy/restart = PendingRuntimeExecution
T1..T10 behavioral/runtime = PendingRuntimeExecution
Frozen Runtime Golden = PendingRuntimeExecution
End-to-End Golden = PendingRuntimeExecution
```

Scope فقط StopBatch/SkippedPolicy executable cleanup، `defaultEditView` central Reference Contract، Layout/textLocation bidirectional round-trip و `reportRelation` SOC→IOC projection است. FieldDef `orderNumber` فقط relative sibling order بین همه Field/Relationهای همان Entity را بیان می‌کند.



## v178 focused correction

Static/source target is limited to the four v178 blockers. Build/Deploy/runtime behavioral gates are not inferred from source and remain `PendingRuntimeExecution` until evidence is produced. Runtime fingerprint identifies `updateId=v178` and `socContractRevision=v15-qtr-v178`.

## v179 focused correction

- baseline عملیاتی برای این بسته: v175؛ بسته v179 cumulative است و fixهای معتبر v176..v178 را نیز حمل می‌کند.
- Workflow nested references در pre-resolution از central Semantic reference semantics استفاده می‌کنند؛ cross-wave selector معتبر است و Runtime ID authored ممنوع می‌ماند.
- Build/Deploy/Runtime acceptance بدون اجرای واقعی `PendingRuntimeExecution` است.
- TEST-2 non-participating sibling فقط evidence/micro-test است؛ Acceptance ناقص ورودی باعث تغییر الگوریتم ordering نشده است.

## v180 focused correction

Baseline is operational v179. New scope is only the Workflow reference pipeline distinction between authored SOC and resolved IOC. Build/Deploy/Runtime gates remain `PendingRuntimeExecution` until executed in the target environment.
