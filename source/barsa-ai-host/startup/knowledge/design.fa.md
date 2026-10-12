# Design — Simple, Complete, Buildable

## قانون اول

**ساده‌ترین Design صحیح را انتخاب کن که Requirement را کامل برآورده می‌کند و از روی آن Implementor مجبور به حدس Business/System Design نباشد.**

سادگی بعد از semantic correctness می‌آید؛ limitation Integration مجوز ساده‌سازی معنای مطلوب نیست.

## Authority و مسیر طراحی

```text
Sources
→ System/Section Requirements
→ Overall System BSDNs
→ Detailed Section BSDNs
→ Support Mapping
→ Generate SystemBuilder Actions
→ Runtime
→ Verify Runtime ↔ Current Target BSDN
```

Requirement و BSDN دو authority متفاوت‌اند: Requirement truth خواسته‌هاست؛ BSDN truth طراحی مطلوب. Runtime actual-state truth و Support Mapping feasibility truth است.

Previous Change/Package، Writer، Runtime، Current Progress و Conversation memory Design Authority موازی نیستند.

## Scope / Ownership

ساختار:

```text
Project
→ System
→ Section
```

هر Design Fact یک owner canonical دارد. Shared concept و External System نیز owner/system روشن دارند. artifact-type taxonomy مثل `entities/workflows/reports` ساختار اصلی Design نیست.

سه Scope:

```text
Solution Landscape
Current Delivery Scope
Current Build Scope
```

Design Current Delivery Scope قبل از Build complete/minimal و cross-checked می‌شود؛ Build Wave می‌تواند subset چند Section/System باشد.

## Initial Design = Entity + Process Skeleton

Design اولیه نباید Entity-only یا Process-only باشد:

```text
Entity / Relation Skeleton
↔
Process / Actor / Form / Output Skeleton
```

Process می‌تواند Entity/Relation کشف کند؛ Data model هم Process را اصلاح می‌کند. این refinement قبل از Build انجام شود تا Section آخر مجبور نشود Runtime ساخته‌شده Section اول را برای Design correct کند.

## Complete in Elements, Sparse in Obvious Properties

اگر Workflow بیست Activity material دارد، همه بیست Activity در BSDN دیده شوند. اگر یک property از convention SystemBuilder قطعی، بدون Business meaning و تقریباً در همه implementationها یکسان است، به Generate Actions واگذار شود.

این rule برای Entity/Field/View/Rule/Report/Workflow/Code behavior هم برقرار است.

## Requirement-ready ≠ Design-ready ≠ Payload-ready

- Requirement-ready: خواسته/قید روشن است.
- Design-ready: SystemBuilder semantic design روشن و material ambiguity صفر است.
- Payload-ready: Support Mapping و exact technical contract برای Action generation آماده است.

Writer detail را برای payload-ready شدن وارد BSDN نکن.

## Design by owner

Entity، Relations، BusinessRules، Views و entity events/code کنار owner Entity/Section بمانند. Workflow در Section owner تعریف شود و entityهای Section دیگر را duplicate نکند؛ فقط reference بدهد.

Code source واقعی داخل BSDN نیست؛ behavior contract کنار Event/Object owner ثبت می‌شود.

## Semantic fit قبل از سادگی

ابتدا primitive باید با Requirement از نظر معنا منطبق باشد؛ سادگی فقط بین گزینه‌های semantic-valid معیار است.

- state ساده → enum/status field، نه Workflow.
- Process واقعی با actor/wait/history/multi-step persistence → Workflow.
- UI conditional → View/BusinessRule؛ نه Workflow.
- collection/projection/aggregate → Report/query primitive، نه Entity مصنوعی مگر lifecycle داده مستقل وجود دارد.
- UX visibility جای Security enforcement نیست.

## Defaults را domain decision نکن

property را فقط وقتی explicit کن که Requirement/correctness به آن وابسته است. default native/canonical کافی را بی‌دلیل pin نکن.

## Traceability متناسب با ریسک

Design decision material باید به Requirement/evidence/necessity روشن trace شود. این quality rule است، نه provenance schema برای تک‌تک فیلدها.

Stable documentation keyهای سبک مجازند؛ subsystem semantic identity جدید ممنوع.

## سطح واقعی enforcement

هر Rule/Constraint مشخص کند در کجا enforce می‌شود:

```text
Field/property validation
BusinessRule / View behavior
Workflow Guard
Query / Code
Security/Server capability
unknown/unverified
```

Presentation را enforcement واقعی جا نزن.

## freshness

اگر decision به داده مشتق‌شده وابسته است، Design باید روشن کند مقدار stored/query-time است، چه زمانی تازه می‌شود و decision چگونه مقدار معتبر را مصرف می‌کند؛ نیاز نیست بخش ثابت BSDN برای freshness بسازی.

## Partial delivery بدون تغییر معنا

اگر capability/contract برای outcome موجود نیست:

```text
Desired BSDN unchanged
Support Mapping = Partial/Unsupported/Unknown
Implementation = Partial
Gap explicit
```

ممنوع:

```text
silently replace Workflow with status/BusinessRule
silently remove Security
silently simplify cross-record behavior
```

## External / Future Design

External/Future System فقط تا حد knowledge واقعی و dependency Current Delivery Scope detail می‌شود. minimal known/required external model مجاز است؛ internals نامعلوم اختراع نمی‌شود.

## Material ambiguity

Agent فقط وقتی به User برمی‌گردد که تصمیم material Business/System لازم باشد یا دو Design material معقول باقی مانده باشد. approval مصنوعی برای هر مرحله ممنوع است.

## Design Review

پیش از Finalize Current Delivery Scope بپرس:

1. آیا Requirement مهمی بی‌Design/Gap مانده؟
2. آیا عنصر materialی summary شده و Implementor باید آن را حدس بزند؟
3. آیا property بدیهی/Writer/runtime detail وارد Design شده؟
4. آیا یک Design Fact چند owner دارد؟
5. آیا Entity/Process skeleton با هم سازگارند؟
6. آیا cross-System/Section relation و ownership روشن است؟
7. آیا Workflow Activity/Actor/Next/Completion Contract reconstruction را ممکن می‌کند؟
8. آیا support gap باعث redesign شده؟

این پرسش‌ها quality review هستند؛ normative contract در `knowledge/bsdn/*` است.

## Technical fix boundary

Writer/Verifier/Adapter/Integration fix اگر intended Design را تغییر نمی‌دهد:

```text
Requirement unchanged
BSDN unchanged
Support/Implementation refresh
```

Design Change فقط با تغییر requirement/intended behavior یا اصلاح inconsistency واقعی Design رخ می‌دهد.

## Pattern usage

اگر Requirement ترکیبی از family/subtype، lifecycle/status/access، Workflow+business status، operational collection/query، external/read-centric data یا hierarchy پیچیده است، patternهای relevant را بررسی کن؛ Pattern evidence است نه default Design.

## محدودیت‌های مهم

- transaction rollback را بدون contract قطعی فرض نکن.
- concurrency را Last-Write-Wins فرض نکن مگر evidence وجود داشته باشد.
- Formula error swallow یا Security UI enforcement را فرض نکن.
- Import ممکن است partial/nontransactional باشد.
- capability declaration را با runtime proof یکی نکن.
