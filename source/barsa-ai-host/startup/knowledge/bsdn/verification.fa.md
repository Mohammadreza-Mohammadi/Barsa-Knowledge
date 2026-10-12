# BSDN v0.5 — Verification

## Truth model

```text
BSDN = Desired Design
Runtime / Read-back = Actual Implementation
Support Mapping = supported/unsupported feasibility
Current Progress = cached operational snapshot
Previous Change/Package = implementation evidence, not design oracle
```

Verify actual state را با **Current Target BSDN scopes** مقایسه می‌کند.

## ۱. Change Verification

بررسی می‌کند Change/Action همان Design intended را پوشش داده و semantics اضافی نساخته است.

- این سطح قبل/پس از Plan می‌تواند اجرا شود.
- success آن Runtime persistence را اثبات نمی‌کند.
- unsupported Design outcome باید gap بماند، نه اینکه از expected حذف شود.

## ۲. Runtime Verification

بعد از Apply، read-back واقعی بررسی می‌شود:

```text
element existence
property/reference correctness
operational wiring
absence of unintended delta
```

`applied=true` ≠ `verified=true`.

## ۳. Step / Wave Verification

بعد از هر implementation step material:

```text
Apply
→ Read-back
→ compare with expected subset derived from BSDN
```

Failure باید همان scope را متوقف/route کند؛ Errorها تا انتهای Section انباشته نشوند.

## ۴. Section Verification

در پایان Build Section:

```text
Runtime Section
↔
Detailed Section BSDN
```

Entity/Relation/View/Rule/Workflow/Report/Code behavior outcomes relevant همان Section بررسی شوند.

## ۵. System Verification

بعد از Sectionهای System:

```text
System Runtime
↔
Overall System BSDN + Detailed Section BSDNs
```

Cross-section relation/wiring، shared owner reference و process boundary نیز بررسی شوند. PASS مستقل Sectionها به‌تنهایی System PASS نیست.

## ۶. Final Delivery / Mission Verification

در پایان Current Delivery Scope:

```text
Actual Runtime of all relevant Systems
↔
Current Target BSDN scopes
```

Requirement coverage و Support Mapping gaps برای verdict نهایی trace می‌شوند.

`Last package succeeded ≠ Mission complete`.

## ۷. Expected Verify از Design مشتق شود

Generate Actions باید expected read-back را تا حد ممکن از BSDN تولید کند؛ Verifier Design را از صفر حدس نزند.

مثال:

```text
WF-W1 / A04
Expected:
- Activity exists
- Actor = ops
- View = initial-review
- outgoing branches = expected set
```

## ۸. Workflow Verify

صرف وجود Workflow root کافی نیست. در scope supported حداقل بررسی شود:

```text
Variables
Actors + performer binding
Activities
Start/End
Transition topology / branches / loops
Conditions
SimpleForm→View wiring
important effects
Completion Contract / Business end state
```

اگر integration بخشی را unsupported کرده، outcome همان بخش `partial/unsupported` می‌ماند و graph ناقص complete اعلام نمی‌شود.

## ۹. Entity/View/Rule/Report wiring

- Primary View فقط با وجود View PASS نیست؛ default/main wiring باید همان expected Design باشد.
- BusinessRule علاوه بر definition، selected usage/wiring design-relevant باید verify شود.
- Report user-facing علاوه بر metadata، owner/source و placement/navigation material را verify کند.
- cross-record/query/behavior smoke فقط اگر capability واقعی اجرا شده و evidence دارد PASS می‌شود.

## ۱۰. Normalization

comparison می‌تواند representationهای معادل Runtime را canonicalize کند، ولی normalization:

```text
Source of Truth نیست
artifact authority جدید نیست
Design را تغییر نمی‌دهد
```

مثلاً typed relation path و numeric runtime path اگر semantic-equivalent هستند باید قبل از mismatch canonicalize شوند.

Verifier false-negative باید Verifier bug/gap ثبت شود؛ Writer صحیح را برای سبزکردن Verify تغییر نده.

## ۱۱. Descriptor/read-back gaps

اگر property requested در read-back نیست، بدون raw evidence نتیجه نگیر که persistence صحیح یا غلط بوده است.

مسیر:

```text
Write
→ raw metadata/storage when available
→ Semantic read-back
→ Verify
```

سپس bug به Writer/Persistence/Exporter/Verifier نسبت داده شود.

## ۱۲. Runtime vs Progress

اگر Progress می‌گوید Completed ولی Runtime object missing است:

```text
actual implementation status = Missing
Progress = stale
Desired BSDN = unchanged
```

Progress reconcile می‌شود، BSDN rewrite نمی‌شود.

## ۱۳. Partial mutation / recovery verification

اگر `mutationApplied=true` و operation failed:

```text
Read-back first
→ identify persisted root/children
→ reconcile IDs/stage
→ choose recovery
```

Blind retry ممنوع. recovery action نیز بعد از Apply دوباره read-back/verify می‌شود.

## ۱۴. Drift قبل از Edit

برای update existing System:

```text
Current Target BSDN affected scopes
↔
Runtime affected scopes
```

material drift قبل از new change روشن شود. کل System بدون نیاز دوباره خوانده نشود.

## ۱۵. Evidence honesty

گزارش باید تفکیک کند:

```text
Source/static
Package ZIP review
Preimage reconciliation
Build
Canonical Apply
Runtime Read-back
Behavioral smoke
Continuation behavior
Cross-System behavior
```

اجرا نشده = `NO`، نه PASS.

```text
fixture exists ≠ Behavioral PASS
static PASS ≠ Runtime PASS
package validated ≠ Applied
```

اگر ZIP/source را شخصاً inspect نکرده‌ای، evidence report را direct inspection معرفی نکن.

## ۱۶. Verified Release gate

Verified Release فقط وقتی ثبت می‌شود که:

```text
required mutations completed
open corrective mutation = 0
Section/System/Final Delivery verification complete for claimed scope
unsupported/deferred/unavailable outcomes explicit
runtime checkpoint traceable
```

Release history داخل BSDN انباشته نمی‌شود.

## ۱۷. Traceability

حداقل:

```text
Requirement key/address
→ BSDN address
→ Action/outcome
→ actual read-back/verify evidence
```

این mapping lightweight است و authority مستقل نیست.
