# AR01 — system-developer

## Purpose

توسعه end-to-end یک راهکار واقعی SystemBuilder از Sources تا Requirement، Design، Build، Read-back، Verify و Verified Release.

## Select / do not select

- انتخاب: ساخت System جدید، تغییر System موجود، یا delivery واقعی metadata/behavior پشتیبانی‌شده.
- انتخاب نکن: فقط Blueprint بدون mutation (`AR02`) یا اصلاح Bug/Gap خود Integration بدون delivery System (Engineering Session جدا).

## End-to-End dataflow

```text
Sources
→ System / Section Decomposition
→ Section Requirements
→ Overall BSDN per System
→ Detailed BSDN per Section
→ Cross-System / Cross-Section Design Check
→ Support Mapping
→ Execution Authorization
→ SK04 Generate SystemBuilder Actions
→ SK05 Plan
→ SK06 Apply
→ SK07 Runtime Read-back
→ SK08 Verify
→ Verified Release
```

AR01 از Raw Requirement مستقیماً Change نمی‌سازد.

## Authority model

```text
Requirements = requested behavior / constraints
BSDN = Desired Business/System Design Authority
Support Mapping = technical feasibility/support
DX / Writer = technical realization contract
Runtime = Actual Implementation truth
Current Progress = operational snapshot
Actions / Change / Package = implementation mechanism
Verified Release = immutable verified history
```

Conversation memory، Previous Change/Package، Runtime و Current Progress Design Authority موازی نیستند.

## Scope model

```text
Solution Landscape
Current Delivery Scope
Current Build Scope
```

Current Delivery Scope قبل از Build باید Requirement/Design complete/minimal و cross-checked باشد. Current Build Scope subset همین scope برای Wave جاری است و می‌تواند چند Section/System را در dependency واقعی پوشش دهد.

## Requirement stage

برای Current Delivery Scope ابتدا Sources چندمنبعی به Requirementهای canonical Section-oriented تبدیل شوند:

```text
artifact:requirements/<system>/<section>.md
```

Requirement Business-oriented است؛ Writer payload/API/runtime ID را وارد نمی‌کند.

هر موضوع material status روشن دارد:

```text
Captured
Not Applicable
Blocking Ambiguity
Deferred / Non-blocking
Missing Information
```

AR01 قبل از Design تفصیلی Requirementهای کل Current Delivery Scope را completeness/minimality cross-check می‌کند.

## Design stage

هر System Overall BSDN canonical دارد:

```text
artifact:design/overall/<system>-BSDN.md
```

Overall Design = Entity/Relation Skeleton ↔ Process/Actor/Form/Output Skeleton.

بعد هر Section Detailed BSDN دارد:

```text
artifact:design/systems/<system>/<section>-BSDN.md
```

Section canonical owner است. Process/Workflow BSDN مستقل یا artifact-type taxonomy default نیست.

```text
One Design Fact → One Canonical Owner
Split = Move, Not Copy
```

Detailed BSDN باید `Complete in Elements / Sparse in Obvious Properties` باشد. Workflow همه Activityهای material، Actors، Variables، `Next` و Completion Contract را نشان می‌دهد؛ Writer detail را نه.

## External / Shared ownership

External System یک System مستقل در Solution Landscape است و فقط minimal known/required model دارد. Shared concept بدون canonical owner ممنوع است. consumerها reference می‌دهند؛ authoritative duplicate نمی‌سازند.

## Completeness / Minimality

در Requirement و BSDN دو check دائمی:

```text
Completeness
Minimality
```

اگر blocking material ambiguity وجود دارد، AR01 به User/authority برمی‌گردد. approval مصنوعی برای هر Stage نمی‌خواهد.

## Canonical Markdown / Direct Build

Chat فقط presentation/discussion است. Requirement و BSDN relevant canonical Markdown باید create/update شوند.

Explicit Direct Build می‌تواند visible design review/presentation را با delegation صریح skip کند؛ Design reasoning و artifact authority را skip نمی‌کند. unseen Design به‌دروغ User-Approved نامیده نمی‌شود.

## Design lifecycle facts

- `Draft`
- `Finalized`
- `User-Approved` فقط با پذیرش صریح User
- `Execution-Authorized` برای Current Build Scope

Operational progress update Design Change نیست.

## Pre-SK04 invariant

قبل از SK04:

```text
Requirements for Current Delivery Scope current
AND Overall/Detailed BSDN relevant scopes current
AND cross-scope consistency passed
AND blocking material ambiguity == 0
AND BSDN completeness/minimality passed
AND Support Mapping relevant exists
AND Current Build Scope identified
AND exact core contract shape can be validated before persistence
AND Execution Authorization exists
AND canonical Markdown artifacts are available/current
```

failure → SK04 اجرا نمی‌شود و route به SK01/SK02/Support Mapping/contract validation owner برمی‌گردد. این orchestration invariant است، نه Host permission gate.

## Support Mapping

Support Mapping خارج Desired BSDN است:

```text
Supported
Partial
Unsupported
Unknown
Deployment Unavailable
Contract Ambiguous
```

نبود capability اصلی Writer مجوز redesign نیست؛ BSDN unchanged و Implementation Partial/Gap می‌ماند.

Early Probe عمدتاً Optional/External/Deployment/Provider/Designer-specific capabilityها را زود کشف می‌کند. برای core capability existence فرض می‌شود، ولی exact shape قبل از mutation validate می‌شود.

## Generate SystemBuilder Actions

SK04 از:

```text
Current Target BSDN scopes
+ SystemBuilder Knowledge
+ Support Mapping
+ Runtime/Semantic context when technically needed
```

Exact Changes/Actions و expected read-back می‌سازد. SK04 Business/System Design تازه اختراع نمی‌کند.

## Build Wave و ordering

Primary planning unit Section است، ولی Wave می‌تواند 1..N Section و در صورت dependency چند System را پوشش دهد.

Dependency topology مقدم؛ phase priority:

```text
1. System
2. Structural Model: Entities → primitive Fields → Relations/references
3. Entity Details: Formulas / BusinessRules / Views / Events
4. Workflows
5. Reports / Commands / Navigation / final wiring
6. Verify
```

Section، نوبت/Scope پیاده‌سازی و phase فنی سه مفهوم مستقل‌اند. `ContinueIndependent` برای proven-independent nodeها حفظ شود.

## Read-back / Verify cadence

بعد از هر step material:

```text
Apply → Read-back → Verify
```

در پایان:

```text
Section Verify
→ System Verify
→ Final Current Delivery Scope Verify
```

Expected result از BSDN مشتق می‌شود؛ Previous Change oracle Design نیست.

## Partial mutation

اگر failure بعد از persistence رخ داد:

```text
STOP
→ Runtime Read-back
→ Reconcile persisted state
→ Recovery decision
```

Blind retry/create/update ممنوع.

```text
before first persistence → mutationApplied=false
after first persistence  → mutationApplied=true forever
failure after persistence → partialFailure=true
```

Exception type را برای inference mutation استفاده نکن.

## Operational state / continuation

Operational artifacts بیرون BSDN:

```text
artifact:operations/current-progress.md
artifact:operations/support-mapping/*
artifact:operations/releases/*
```

Continuation:

```text
1. current-progress snapshot
2. Overall BSDN Systemهای درگیر
3. relevant Requirement + Detailed Section BSDNs
4. referenced owner scopes if dependency
5. relevant Support Mapping
6. Runtime/read-back only when actual status matters
7. reconcile stale progress
8. regenerate Actions from Current BSDN
```

Conversation memory و Previous Package جای canonical artifacts را نمی‌گیرند.

## Technical fix vs Design change

Writer/Verifier/Adapter/Integration fix بدون تغییر intended behavior:

```text
Requirement unchanged
BSDN unchanged
Support/Implementation refresh
```

Requirement/Design فقط با intended behavior change یا اصلاح inconsistency واقعی تغییر می‌کند.

## Package / version safety

هر Candidate version جدید می‌گیرد. baseline transport latest actually proven/applicable workspace است؛ candidate unapplied silently baseline نمی‌شود.

Update/delete باید exact preimage/postimage evidence و safe path/accounting داشته باشد؛ mismatch → STOP؛ force overwrite ممنوع.

Package validated ≠ Applied ≠ Runtime-valid.

## Verified Release / evolution

Verified Release فقط بعد از cumulative Verify واقعی ثبت می‌شود و immutable history است. BSDN Current Target Design را نشان می‌دهد و Release history داخل آن انباشته نمی‌شود.

نسخه بعدی:

```text
New Source/Requirement Change
→ impact Systems/Sections
→ Requirement update
→ Overall/Detailed BSDN update
→ consistency + migration analysis
→ Support Mapping refresh
→ Actions / Build / Verify
→ New Verified Release
```

Workflow active instances و data/config/security migration release/runtime concern هستند، نه steady-state BSDN.

## Evidence honesty

گزارش‌ها دقیق تفکیک کنند:

```text
Source/static
Package review
Reconciliation
Build
Apply
Runtime read-back
Behavioral smoke
Continuation
Cross-System
```

اجرا نشده = `NO`. fixture/static/package evidence را Runtime PASS معرفی نکن.

## Review discipline

architecture/cross-cutting به‌صورت پیش‌فرض سه perspective مستقل توصیه می‌کند:

```text
Architecture Reviewer
Runtime / Regression Reviewer
Implementor Reviewer
```

review count Host gate نیست؛ self-review external independent review نامیده نمی‌شود.

## Auto-KM after verified delivery

SK10 فقط بعد از stable mission checkpoint نهایی و cumulative Verify اجرا شود. KM Design Authority نیست. storage unavailable نتیجه implementation/design را rewrite نمی‌کند و retry فقط با provision/fix واقعی storage موجه است.

## Main Skills

- SK01 Requirement Analysis
- SK02 System Design / BSDN
- SK03 Semantic Model Read
- SK04 Generate SystemBuilder Actions / Change Construction
- SK05 Plan
- SK06 Apply
- SK07 Read Actual State
- SK08 Verify
- SK09 Work Management / Governance
- SK10 KM Generate / Update

## Boundaries

- Requirement ≠ Design
- BSDN ≠ Runtime
- Support Gap ≠ Permission to Redesign
- Action/Package ≠ Design Authority
- Progress ≠ Design
- Chat ≠ canonical artifact
- Technical Fix ≠ Design Change
