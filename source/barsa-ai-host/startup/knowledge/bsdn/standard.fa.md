# BSDN v0.5 — Barsa System Design Notation

## ۱. تعریف

BSDN مدل فشرده، پایدار و قابل continuation **Desired Business/System Design** است.

اصل:

```text
Complete in Elements
Sparse in Obvious Properties
```

BSDN باید آن‌قدر کامل باشد که Implementor مجبور به حدس Business/System Design نشود، و آن‌قدر مینیمال بماند که به DSL دوم SystemBuilder تبدیل نشود.

## ۲. Authority و hierarchy

```text
Requirements = requested behavior / constraints
BSDN = Desired Design Authority
Support Mapping = technical feasibility/support
Runtime / Read-back = Actual Implementation truth
Current Progress = operational snapshot
Actions / Change / Package = implementation mechanism
```

ساختار canonical طراحی:

```text
Project
→ System
→ Section
```

Authority به **Design Scope** تعلق دارد، نه physical file.

```text
One Design Fact
→ One Canonical Owner
```

مالک معمولاً System یا Section است. سایر scopeها فقط summary/reference می‌دهند.

## ۳. Scopeهای پروژه

سه مفهوم مستقل:

```text
Solution Landscape
Current Delivery Scope
Current Build Scope
```

Solution Landscape می‌تواند Current/Future/External/Reference را نشان دهد. Current Delivery Scope همان scopeای است که قبل از Build باید Requirement/Design آن complete/minimal و cross-checked باشد. Current Build Scope subset همان Delivery Scope برای Wave فعلی است.

Future/External detail فقط تا حد knowledge/dependency واقعی ثبت می‌شود؛ اطلاعات نامعلوم اختراع نمی‌شود.

## ۴. Requirement artifact ≠ BSDN

Requirement stage قبل از Design تفصیلی اجباری است. Requirement Business-oriented است و Writer payload/API/runtime ID را تعریف نمی‌کند.

ساختار مطلوب:

```text
artifact:requirements/system-a/sec-01.md
artifact:requirements/system-a/sec-02.md
artifact:requirements/system-b/sec-01.md
```

Requirement material می‌تواند key سبک مثل `REQ-WORK-017` داشته باشد؛ این key فقط traceability است و Runtime/Semantic identity نیست.

هر موضوع مهم Requirement یکی از statusهای ساده را دارد:

```text
Captured
Not Applicable
Blocking Ambiguity
Deferred / Non-blocking
Missing Information
```

Blocking فقط یعنی بدون حل آن Design material ممکن است اشتباه شود.

## ۵. Overall BSDN per System

هر System یک Overall BSDN دارد:

```text
artifact:design/overall/system-a-BSDN.md
artifact:design/overall/system-b-BSDN.md
```

Overall BSDN همان Skeleton/summary canonical System است و داخل همان فایل Section‌بندی می‌شود.

برای هر Section در صورت مرتبط بودن:

```text
Purpose
Main Entities
Main Relations
Important Fields
Main Process Skeletons
  Main stages
  Main actors
  Main forms
Main Reports / Outputs
Major Business Rules
Major Code / Automation Responsibilities
Security Summary
External Relations
Dependencies
Known Design Gaps / Open Questions
Reference to detailed Section BSDN
```

Overall Design همزمان refine می‌کند:

```text
Entity / Relation Skeleton
↔
Process / Actor / Form / Output Skeleton
```

Process می‌تواند Entity/Relation تازه کشف کند و Entity model می‌تواند Process را اصلاح کند؛ این رفت‌وبرگشت قبل از Build طبیعی است.

## ۶. Detailed BSDN per Section

ساختار canonical پیش‌فرض پروژه‌های بزرگ:

```text
artifact:design/systems/system-a/sec-01-BSDN.md
artifact:design/systems/system-a/sec-02-BSDN.md
artifact:design/systems/system-b/sec-01-BSDN.md
```

```text
System = owner folder
Section = canonical detailed BSDN scope
```

Workflow/Process BSDN مستقل و فایل‌بندی artifact-type مانند entities/workflows/reports به‌صورت default ساخته نشوند.

اگر یک Section از نظر اندازه واقعاً غیرقابل مدیریت شد، physical split ممکن است؛ ولی ownership همان Section می‌ماند.

## ۷. Split = Move, Not Copy

در split:

```text
1. destination canonical artifact create
2. detailed Design move
3. source به summary/reference تبدیل
4. authoritative duplicate حذف
5. semantic Design و ownership ثابت
```

کپی کامل Design در دو artifact ممنوع است.

## ۸. External System و Shared Owner

System خارجی در Solution Landscape System مستقل است:

```text
System: SCCIS
Type: External
```

فقط known/required model ثبت شود؛ External Design به معنی Build authority روی آن سیستم نیست.

Shared concept بدون owner ممنوع است. اگر Organization/Security/Notification owner مستقل material دارد، System canonical owner مشخص شود؛ consumerها فقط reference می‌دهند.

## ۹. اصول نگارش

1. عنصر واقعی اول: Entity/Field/Relation/View/Rule/Workflow/Activity/Report/Command/Event.
2. تصمیم design-relevant صریح؛ default بدیهی omit.
3. omission نباید دو Design material متفاوت بسازد.
4. technical Writer/runtime detail وارد BSDN نشود.
5. implementation workaround Business Design نشود.
6. Runtime evidence/history داخل BSDN انباشته نشود.
7. Gap implementation داخل Desired BSDN status نمی‌شود.
8. Material ambiguity با حدس پر نمی‌شود.

یک detail را در BSDN بنویس اگر:

```text
Business meaning دارد
یا چند Design معقول دارد
یا بدون آن Implementor مجبور به حدس می‌شود
یا برای continuation مهم است
یا برای Verify expectation می‌سازد
```

## ۱۰. Stable documentation keys

Keyهای سبک مجاز:

```text
SYS-A
SEC-WORK
ENT-REQUEST
WF-W1
A04
BR-01
REP-03
DD-01
```

فقط برای reference/traceability/continuation؛ نه Runtime ID، DB identity، SemanticKey subsystem یا persistence جدید.

## ۱۱. Entity / Field / Relation

ساختار طبیعی Section:

```text
Entity: ENT-REQUEST — درخواست انجام کار

Purpose: ...

Important Fields:
- شماره درخواست — Text — required
- شروع پیشنهادی — DateTime — required
- وضعیت — Selection/Enum — required

Relations:
- نوع برنامه → ENT-PROGRAM-TYPE — single
- متقاضی → User — single

Formulas:
...

BusinessRules:
...

Views:
...

Events / Code behavior:
...
```

نوع/mandatory/cardinality فقط وقتی design-relevant یا غیر بدیهی است صریح شود. DB name، length معمول و defaults standard به Generate Actions واگذار شوند.

Logical target روشن ولی Runtime binding حل‌نشده Design Ambiguity نیست؛ target منطقی ثبت و binding technical به Implementation واگذار می‌شود.

## ۱۲. Formula

Formula کنار owner خودش قرار می‌گیرد.

```text
Formula: انحراف زمانی
Behavior:
- اختلاف پایان واقعی و برنامه‌ریزی‌شده را به دقیقه محاسبه می‌کند.
```

expression/source code دقیق فقط وقتی خود expression Business Design است وارد BSDN شود.

## ۱۳. BusinessRule

BusinessRule زیر Entity canonical owner تعریف شود؛ View فقط selected Rule را reference کند.

```text
BusinessRule BR-01 — الزام دلیل رد/لغو

When:
- status in [ردشده، لغوشده]

Then:
- دلیل visible + mandatory

Otherwise:
- دلیل hidden + non-mandatory
```

Rule حداقل event/condition/effect material را روشن می‌کند.

## ۱۴. View / Form

در صورت اهمیت:

```text
View: بررسی اولیه
Purpose: ...
Primary/Secondary when material
Important sections/fields
Readonly/mandatory/visibility differences
Selected BusinessRules
Material UI behavior
```

layout pixel-level و designer-specific defaults لازم نیست مگر Requirement آن را constrain کرده باشد.

## ۱۵. Workflow

Workflow باید **قابل reconstruction** باشد، بدون Activity schema سنگین.

ساختار:

```text
Workflow: WF-W1 — درخواست برنامه‌ریزی‌شده

Purpose: ...

Variables:
- request → ENT-REQUEST

Actors:
- requester → process starter
- ops → مسئول تعیین‌شده روی request

Activities:

A01 — Start
Type: Start
Next:
- A02

A02 — ثبت درخواست
Type: SimpleForm
Actor: requester
View: فرم درخواست
Next:
- A03

A03 — بررسی اولیه
Type: SimpleForm
Actor: ops
View: بررسی اولیه
Next:
- نیازمند اصلاح → A04
- رد/لغو → A99
- خاموشی → A10
```

Activity default فقط:

```text
Code + Caption
Type
Actor
View
Next
```

Effect/Condition/Code behavior فقط در صورت material بودن اضافه شود.

### Transition

Transition concept واقعی Workflow است، ولی default زیر Source Activity در `Next` نمایش داده می‌شود. destination فقط Activity key کافی است. list جداگانه Transitionها فقط وقتی property مستقل material دارند.

### Workflow Completion Contract

برای هر Workflow روشن باشد:

```text
Valid Starts
Successful End State(s)
Rejected/Cancelled End State(s)
Business status effects
Records required at completion
Important side effects
Known exception/recovery expectations
```

صرف graph بدون نتیجه Business کامل نیست.

### Actor / Performer

BSDN Business Actor و binding design-relevant را نگه می‌دارد؛ registration resolver/runtime ID/Writer workaround خارج BSDN است.

## ۱۶. Code / Automation

source code واقعی داخل BSDN قرار نگیرد؛ behavior کنار Event/Object owner توصیف شود.

```text
Event: BeforeSubmit
Code:
- رکوردهای متداخل را پیدا می‌کند.
- overlap را بررسی می‌کند.
- در صورت تداخل عملیات را Block می‌کند.
```

برای behavior material در صورت نیاز:

```text
Trigger
Reads
Behavior
Writes
Result
Important failure semantics
```

## ۱۷. Report / Output

```text
Report: REP-03 — درخواست‌های انجام کار
Purpose: ...
Source: ENT-REQUEST
Main Columns: ...
Important Filters: ...
Grouping/Aggregation when material: ...
Navigation placement when material: ...
Security intent when material: ...
```

query serialization/designer properties بدیهی در BSDN بازنویسی نمی‌شوند.

## ۱۸. Security / External Contracts / Configuration

Security intent، external interaction و master/config data در owner scope ثبت می‌شوند اگر روی Design اثر دارند. نبود Writer/Security provider به‌تنهایی Desired Design را حذف نمی‌کند؛ support status در Support Mapping است.

## ۱۹. Design Decisions

فقط تصمیم‌های material/rationale-worthy:

```text
DD-01
Decision: ...
Reason: ...
Affected Systems/Sections: ...
```

ADR subsystem جدا نساز.

## ۲۰. Gapها

### Requirement Gap
در Section Requirement:

```text
Source missing
Requirement unknown
Business behavior unclear
```

### Design Gap
در owning BSDN:

```text
Requirement known
Design unresolved
Blocking ambiguity
Deferred design decision
```

### Implementation / Integration Gap
خارج BSDN در Support Mapping/execution state:

```text
Writer unsupported
Contract ambiguous
Deployment unavailable
Integration missing
Verifier/read-back limitation
```

Technical Gap حق redesign ندارد.

## ۲۱. BSDN Completeness

قبل از Build Current Delivery Scope حداقل بررسی شود:

```text
Systems
Sections
Entities
Relations
Important Fields
Processes
Actors
Activities
Views
BusinessRules
Reports / Outputs
Code / Automation
Security
External Systems
Cross-System Relations
Requirement → Design Coverage
Workflow Completion Contracts
Material Design Decisions
```

هیچ Requirement مهمی بی‌Design/Gap/Status نماند.

## ۲۲. BSDN Minimality

همزمان بررسی کن:

```text
Requirement فقط تکرار شده؟
Design Fact چندبار canonical است؟
Runtime detail وارد BSDN شده؟
Writer detail وارد BSDN شده؟
workaround فنی Business Design شده؟
property بدیهی بی‌دلیل نوشته شده؟
history اجرا وارد BSDN شده؟
Support status وارد Desired Design شده؟
```

در صورت بله حذف یا reference شود.

## ۲۳. Traceability

Mapping سبک:

```text
Requirement
→ BSDN address
→ Implementation outcome/action
→ Verify evidence
```

مثال:

```text
REQ-WORK-017
→ SYS-A / SEC-WORK / WF-W1 / A04
```

این mapping authority یا subsystem مستقل نیست.

## ۲۴. Lifecycle facts

`Draft` و `Finalized` به Design Content مربوط‌اند. `User-Approved` فقط با پذیرش صریح User true است. `Execution-Authorized` fact جدا برای ورود به Generate Actions/Build است.

User approval برای هر Stage اجباری نیست؛ اگر completeness/minimality pass و blocking ambiguity صفر باشد Agent می‌تواند ادامه دهد. فقط material Business/System decision به User برمی‌گردد.

Operational update مثل progress status تغییر Design نیست.

## ۲۵. Canonical Markdown contract

Chat/summary Design Authority نیست.

```text
Chat = discussion / presentation / clarification
Canonical Markdown = portable Requirement / Design authority
```

Normal و Explicit Direct Build هر دو Requirement/BSDN relevant را create/update می‌کنند؛ Direct Build فقط visible presentation/review را می‌تواند skip کند.

## ۲۶. Reverse / Existing System

برای System موجود:

```text
Runtime/Semantic evidence
→ Reconstructed understanding
→ Requirements/Design reconciliation
→ Current Target BSDN
```

Runtime actual-state evidence است، نه Desired Design Authority. External unresolved reference با حدس تکمیل نمی‌شود.

## ۲۷. چیزهایی که BSDN نیست

نساز:

```text
Runtime IDs
Package/TRY history
Current Progress diary
Support Mapping status داخل Design
Writer payload/API schema
source code repository
SemanticKey/Design-ID subsystem
parallel ownership graph
compiler/merge engine مستقل BSDN
artifact taxonomy بر اساس entities/workflows/reports
```

BSDN باید **ساده‌ترین مدل کافی Design** باشد که از روی آن Generate SystemBuilder Actions بدون حدس Business/System Design ممکن شود.
