# BSDN v0.5 — Lifecycle

## ۱. Truth / Authority

```text
Requirements = requested behavior truth
BSDN = Desired Design truth
Support Mapping = implementation support truth
Runtime / Read-back = Actual Implementation truth
Current Progress = operational snapshot
Verified Release = immutable historical checkpoint
```

Runtime اگر با Progress تعارض دارد، actual status را تعیین می‌کند؛ Runtime Desired BSDN را rewrite نمی‌کند.

## ۲. سه Scope

```text
Solution Landscape
Current Delivery Scope
Current Build Scope
```

Current Delivery Scope قبل از Build باید Requirement/Design complete/minimal و cross-checked باشد. Current Build Scope می‌تواند در هر Wave subset یا ترکیب چند Section/System باشد.

## ۳. Forward lifecycle

```text
Sources
→ System/Section decomposition
→ Section Requirements for Current Delivery Scope
→ Requirement completeness/minimality
→ Overall BSDN for all relevant Systems
→ cross-system skeleton consistency
→ Detailed BSDN for all relevant Sections
→ BSDN completeness/minimality
→ Support Mapping
→ Execution Authorization
→ Generate SystemBuilder Actions
→ Plan / Apply
→ Runtime Read-back
→ Step/Wave Verify
→ Section Verify
→ System Verify
→ Final Delivery Verify
→ Verified Release
```

Stage formal است ولی approval per-stage gate نیست.

## ۴. Requirement stage

Requirement stage برای پروژه‌های واقعی اجباری است. Agent قبل از کامل‌شدن Requirement Current Delivery Scope، Build یک Section را شروع نمی‌کند.

هر Section Requirement canonical Markdown دارد و material ambiguity باید به `Blocking Ambiguity` یا non-blocking/deferred روشن تبدیل شود.

Requirement stage SystemBuilder implementation را طراحی نمی‌کند.

## ۵. Overall Design stage

برای هر System relevant یک Overall BSDN ساخته/به‌روز می‌شود. ابتدا Entity/Relation و Process/Actor/Form/Output skeleton همزمان refine می‌شوند.

قبل از Detailed Design consistency زیر بررسی شود:

```text
ownership
cross-section relations
process boundaries
actors
external/shared systems
dependencies
naming
duplicated concepts
circular ownership
```

Design ownership تا حد ممکن روشن و acyclic باشد؛ Business relation واقعی برای satisfy کردن این rule حذف نمی‌شود.

## ۶. Detailed Section Design

Detailed BSDN per Section owner scope است. همه material elements باید دیده شوند؛ obvious properties sparse بمانند.

Workflow بزرگ همچنان داخل owner Section canonical است؛ physical split فقط در ضرورت واقعی و با `Move, Not Copy`.

## ۷. Completeness / Minimality Gates

Requirement و BSDN هر دو دو check دارند:

```text
Completeness
Minimality
```

Gate برای Build فقط material است؛ Future/Deferred non-blocking بی‌دلیل current delivery را متوقف نمی‌کند.

## ۸. Design lifecycle facts

- `Draft`: Design هنوز material ambiguity/open design دارد.
- `Finalized`: Design Current Delivery/Build target در scope مربوط material-complete و ambiguity مؤثر صفر است.
- `User-Approved`: User همان Design را صریحاً پذیرفته است.
- `Execution-Authorized`: اجرای Generate Actions/Build برای Current Build Scope مجاز است.

`Finalized ≠ User-Approved`.

در Explicit Direct Build، User می‌تواند presentation/review visible را delegate کند؛ Design reasoning و canonical Markdown حذف نمی‌شوند و unseen Design به‌دروغ User-Approved نامیده نمی‌شود.

## ۹. Support Mapping

Support Mapping بعد از Design Current Delivery Scope و قبل از Build تهیه/refresh می‌شود.

Statusهای ساده:

```text
Supported
Partial
Unsupported
Unknown
Deployment Unavailable
Contract Ambiguous
```

Design را duplicate نکند؛ فقط BSDN address/key + status + evidence/reference لازم.

نبود support برای capability اصلی SystemBuilder مجوز تغییر Requirement/BSDN نیست.

## ۱۰. Early capability probe vs core contract validation

Early Probe عمدتاً برای Optional/External/Deployment/Provider/Designer-specific capability است:

```text
GIS
SMS
SCCIS
KM storage
Print Designer
External Providers
```

برای capabilityهای core وجود primitive کلی assumption است؛ ولی **shape دقیق contract قبل از persistence validate می‌شود**:

```text
performer binding
condition shape
relation path
update/delete operation
workflow-local references
registration binding
```

fail → `No mutation` + BSDN unchanged + Implementation Gap.

## ۱۱. Generate SystemBuilder Actions

ورودی:

```text
Current Target BSDN scopes
+ SystemBuilder Knowledge
+ Support Mapping
+ Runtime/Semantic context when technically needed
```

خروجی:

```text
Exact Changes / Actions
+ expected Read-back / Verify expectations
```

این مرحله Writer payload/defaults/runtime IDs/API shape را resolve می‌کند و Business/System Design تازه نمی‌سازد.

## ۱۲. Current Target BSDN Scope / Build Wave

Primary planning unit = Section، اما Wave لزوماً یک Section نیست:

```text
Current Target BSDN Scope
=
Relevant Overall System scopes
+ 1..N relevant Section BSDNs
+ referenced owner scopes required by dependencies
```

اگر dependency/atomicity/cross-system wiring لازم کند، یک Wave می‌تواند چند Section/System را پوشش دهد. Active System واحد hard-code نشود.

## ۱۳. Build ordering

Dependency topology مقدم است؛ phase priority بعد از آن:

```text
1. System
2. Structural Model
   Entities
   primitive Fields
   Relations
   structural references
3. Entity Details
   Formulas
   BusinessRules
   Views
   Entity events/code
4. Workflows
5. Reports / Commands / Navigation / final wiring
6. Verify
```

Section/Execution planning/Build phase سه مفهوم مستقل‌اند. `ContinueIndependent` برای nodeهای proven-independent حفظ می‌شود.

## ۱۴. Read-back / Verify cadence

بعد از هر implementation step material:

```text
Apply
→ Read-back
→ Verify
```

در پایان Section، سپس System و در پایان Current Delivery Scope cumulative Verify انجام می‌شود. Errorها تا آخر پروژه جمع نمی‌شوند.

## ۱۵. Partial mutation

اگر failure بعد از persistence رخ داد:

```text
STOP
→ Runtime Read-back
→ reconcile persisted state
→ recovery decision
→ repair/delete/resume/retry only with evidence
```

Blind retry/create/update ممنوع است.

Mutation reporting invariant:

```text
before first successful persistence → mutationApplied=false
once any persistence succeeds       → mutationApplied=true forever
failure after persistence            → partialFailure=true
```

نتیجه failure تا حد ممکن persistedRootId/affected IDs/lastSuccessfulStage را برگرداند؛ نبود آن recovery gap است.

## ۱۶. Operational artifacts

Operational state داخل BSDN انباشته نشود.

```text
artifact:operations/current-progress.md
artifact:operations/support-mapping/platform.md
artifact:operations/support-mapping/<system>.md
artifact:operations/releases/<release>.md
```

`current-progress` فقط latest snapshot:

```text
Current Delivery Scope
Current Build Scope / Wave
Completed
In Progress
Pending
Current Gaps
Next Intended Work
Latest Verified Release
Evidence refs
```

Execution diary/TRY history ممنوع.

## ۱۷. Continuation

در Session/Exchange جدید:

```text
1. current-progress را برای operational scope بخوان
2. Overall BSDN Systemهای درگیر را بخوان
3. Requirement و Detailed BSDN Sectionهای relevant را load کن
4. referenced owner scopes را در صورت dependency load کن
5. Support Mapping relevant را restore کن
6. Runtime/read-back را فقط برای actual implementation status استفاده کن
7. stale Progress را reconcile کن
8. Actions لازم را از Current BSDN دوباره تولید کن
```

Conversation memory و Previous Package/Change جای canonical artifacts را نمی‌گیرند.

## ۱۸. Package / Apply safety

هر Candidate version جدید می‌گیرد. baseline transport باید latest actually proven/applicable workspace باشد، نه candidate unapplied فرضی.

برای update/delete preimage و postimage byte hash، برای create `MISSING` و exact write/delete accounting حفظ شود. mismatch → `STOP`; force overwrite ممنوع.

Package validation/ZIP review/overwrite simulation ≠ Applied/Runtime proof.

## ۱۹. Technical Fix vs Design Change

اگر intended Business/System behavior عوض شد:

```text
Requirement update
→ BSDN update
→ new Actions
```

اگر فقط Writer/Verifier/Integration/Adapter fix شد و Design قبلی درست بود:

```text
Requirement unchanged
BSDN unchanged
Support/Implementation refresh
```

Technical retry Desired BSDN را تغییر نمی‌دهد مگر Requirement change یا inconsistency واقعی Design resolve شده باشد.

## ۲۰. Version evolution / Migration

نسخه بعد:

```text
New Source / Change Request
→ impact affected Systems/Sections
→ update Requirements
→ update Overall/Detailed BSDNs where needed
→ impacted consistency check
→ Compatibility/Migration analysis
→ Support Mapping refresh
→ Generate Actions
→ Build/Verify
→ New Verified Release
```

Migration concernها بیرون steady-state BSDN:

```text
Field/Relation changes
Entity split/merge
Existing data/config/security migration
Workflow definition + running instances
External contract compatibility
Code behavior compatibility
```

## ۲۱. Workflow versioning

اگر definition تغییر می‌کند و instance فعال وجود دارد، Release/Runtime policy باید مشخص کند new/old instances، parallel versions و migration چگونه مدیریت می‌شوند. این steady-state BSDN نیست.

## ۲۲. Verified Release

فقط پس از Apply + cumulative Verify واقعی:

```text
Release identifier
BSDN reference/revision
Runtime/Semantic checkpoint
Verification result
```

Verified Release historical و immutable است. Current Runtime همچنان actual-state truth است.

## ۲۳. Reverse / existing system

Runtime evidence برای شناخت وضعیت موجود استفاده می‌شود؛ سپس Requirement/Design authority establish/reconcile می‌شود. Reverse artifact به‌خودی‌خود Target Design Authority نیست تا وقتی review/decision لازم انجام نشده باشد.
