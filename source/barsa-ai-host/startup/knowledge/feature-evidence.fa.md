# Feature / Designer Evidence — Canonical Knowledge

## Purpose

این سند فقط مالک **روش‌ها و قواعد عمومی و پایدار** مربوط به `Designer Evidence` و `Feature Certification` است.

```text
Canonical Knowledge
= durable/general methods and rules

Feature Evidence
= concrete observed cases + media references + result/re-test history

Project Next Work
= active backlog / unresolved certification cases
```

اصل مرزی:

```text
Evidence ≠ Knowledge
```

exact per-feature serializer/Writer/Verifier contract نزد component owner باقی می‌ماند و caseهای جاری در این سند canonical ثبت نمی‌شوند.

## Designer Evidence

```text
Designer Evidence
= Screenshot / Video / observed interaction from the real SystemBuilder Designer UI
```

Designer Evidence با BIX `Snapshot Diagnostics` فرق دارد. Snapshot Diagnostics diagnostic package شامل Full Structured + Semantic است؛ Designer Evidence مشاهده زبان، انتخاب‌ها و interaction واقعی Designer UI است.

برای فهم یک feature در صورت نیاز این سه evidence کنار هم استفاده می‌شوند:

```text
Designer Evidence
+ Full JSON
+ Semantic JSON
```

هدف تشخیص design meaning است، نه clone کردن serializer/runtime representation.

## Evidence interpretation rules

### UI-visible ≠ universal rule

Property یا انتخابی که Designer صریحاً نشان می‌دهد evidence قوی design-significance برای همان case است، ولی یک case به‌تنهایی universal semantic contract نمی‌سازد.

### UI-hidden ≠ removable

UI-hidden را حداقل به این حالت‌ها تفکیک کن:

```text
always internal / infrastructure-only
hidden because current UI state
conditionally hidden by BusinessRule/configuration
```

صرف hidden بودن proof حذف از Semantic نیست.

### Designer language و identity

اگر Full فقط Runtime ID دارد ولی Designer یک object معنادار با caption/name انتخاب می‌کند، portable Semantic نباید numeric Runtime ID خام را meaning نهایی بداند.

مدل مفهومی مطلوب در صورت availability:

```text
stable semantic/business reference
+ human-readable caption/name
```

Caption به‌تنهایی stable identity نیست؛ rename، duplicate caption و scope باید لحاظ شوند. از این اصل subsystem عمومی Global Semantic ID جدید نتیجه نگیر.

### Semantic design-facing است

Semantic هدف clone کردن Full JSON نیست. هر fact مهم Full را مفهومی یکی از اینها classify کن:

```text
Semantic-essential
Derivable
Runtime-only
Serializer / Infrastructure Noise
Unknown / Needs Verification
```

اگر fact واقعاً Semantic-essential باشد، حذف، ambiguity یا وابستگی صرف به Runtime identity یک Gap است.

### Unknown را حدس نزن

```text
Full + Semantic insufficient
→ Unknown / Needs Designer Evidence

Designer Evidence still insufficient
→ Unknown / Needs Source/Runtime Verification
```

## Feature Certification

Semantic Read coverage به‌تنهایی support کامل را ثابت نمی‌کند. یک feature/variant در صورت claim Write support باید در مسیر Write/Apply/Verify نیز evidence متناسب داشته باشد.

روش استاندارد:

```text
Reference real feature
→ understand through Full/Semantic/Designer Evidence
→ define expected design meaning
→ reconstruct minimal design-equivalent feature in isolated target
→ Generate SystemBuilder Actions
→ Plan
→ Apply
→ Runtime Read-back
→ Verify
→ compare with expected/reference semantics
```

هدف byte-for-byte reconstruction نیست؛ **Design-equivalent reconstruction** است. Designer/UI smoke فقط وقتی لازم است که Behavior/UI claim در scope باشد.

## Certification dimensions

این dimensions مستقل گزارش شوند:

```text
Read
Write
Verify
Behavior/UI
```

مثال:

```text
Read: PASS
Write: PASS
Verify: PASS
Behavior/UI: NOT TESTED
```

یک case موفق فقط همان feature/variant و همان dimensions آزموده‌شده را certify می‌کند.

## Gap classification

حداقل:

```text
Semantic Read Gap
Write / Apply Gap
Plan / Contract Gap
Verify Gap
Runtime Behavior Gap
Designer Meaning Unknown
Reference/Test-Data Defect
Deployment/Capability Gap
```

Failure خودکار Writer bug یا Semantic bug نیست.

مسیر عمومی:

```text
Gap
→ classify smallest owning component
→ fix recommendation
→ separate Integration/engineering session when repair is needed
→ re-test same feature case
```

AR06 Integration را patch نمی‌کند.

## Designer Evidence request protocol

درخواست Screenshot/Video پراکنده نکن. پیش‌فرض تعامل با متخصص SystemBuilder کوتاه است:

```text
ID: <Object ID یا نزدیک‌ترین Parent ID>
برو: <بخش/تب/دکمه>
می‌خواهم: <property/state مشخص>
```

یا در کوتاه‌ترین حالت:

```text
<Object ID یا نزدیک‌ترین Parent ID> — <بخش/تب/دکمه>
```

اطلاعاتی مانند Priority/Object Type/semantic selector/context/Caption/reason فقط وقتی جداگانه خواسته شوند که برای resolve کردن evidence واقعاً لازم باشند. یک form/family یک تصویر عمومی؛ variant فقط برای state طراحی متفاوت. برای Video، timestamp/key-frame لازم در evidence case ثبت شود.

## Version / source awareness

- نسخه Export و Source را جدا ثبت کن؛ `old export + newer source` را defect اثبات‌شده تلقی نکن تا re-export انجام شود.
- وجود property در Source یا Full به‌تنهایی Semantic necessity را ثابت نمی‌کند.
- Source ابزار نهایی برای dark areaهای باقی‌مانده است؛ exact technical contract از Source تعیین می‌شود، meaning همچنان با Designer Evidence سنجیده می‌شود.
- مورد بسته‌شده بدون evidence جدید متناقض reopen نشود.
- Semantic باید **Designer-facing** و معیار reconstruction باید **design-equivalent** باشد.
- factی که هنگام Create/Update به‌صورت deterministic بازسازی می‌شود معمولاً noise Semantic است.
- logic بازسازی نباید به raw Runtime/DB ID منبع وابسته باشد؛ readable caption کمک فهم است، نه identity قطعی.

## Evidence persistence

Concrete case data فقط در Conversation مصرف نشود. artifact عملیاتی استاندارد:

```text
artifact:operations/feature-evidence/<case-id>.md
```

این artifact Design Authority یا Canonical Knowledge نیست.

حداقل محتوا:

```text
Case ID
Feature/Object Type
Reference System
Runtime ID / semantic selector/context when available
Parent/Owner
Export/package reference
Designer Evidence file refs + hash/timestamp
Observed UI labels/values/interactions
Relevant Full facts
Relevant Semantic facts
Expected Design meaning
Write reconstruction target/actions reference
Read-back / Verify result
Gap classification
Fix recommendation
Confidence: Observed | Inferred | Unknown
Status: PASS | PASS WITH GAPS | FAIL | UNKNOWN
```

Raw Screenshot/Video داخل StartupPayload یا canonical Knowledge embed نشود. archive/bundle جدا مجاز است و durable observations + filename/hash/timestamp در evidence Markdown باقی بمانند.

Re-test evidence قبلی را overwrite نکند؛ checkpoint/result جدید traceable ثبت شود.

## Project Next Work boundary

`Source-only project documentation` فقط backlog فعال و unresolved certification cases را نگه می‌دارد. وجود یک case در backlog به معنی Rule عمومی یا confirmed product defect نیست.

وقتی AR06 یک backlog case را واقعاً اجرا می‌کند، evidence concrete باید در `artifact:operations/feature-evidence/<case-id>.md` persist شود.

## Secondary use — future Web SystemBuilder

Designer Evidence یک asset چندمصرفی است:

```text
Semantic / AI understanding
+ Feature certification
+ future Designer/Web rewrite reference
```

ولی UI قدیمی target UX authority نیست؛ فقط behavior/history/reference است.

## Promotion rule

```text
Concrete Case
→ Feature Evidence

General Proven Rule
→ Canonical Knowledge
```

و نه:

```text
Concrete Case
→ Canonical Knowledge
```

Promotion فقط وقتی مجاز است که evidence کافی، قابل‌تعمیم و با owner صحیح وجود داشته باشد. هنگام promotion فقط Rule عمومی منتقل شود؛ Runtime IDs، sample captions، sample semantic selector/contexts، case-specific values و re-test history در evidence layer باقی بمانند مگر واقعاً بخشی از Rule عمومی باشند.

اگر fix واقعی component انجام شد، owner Source + exact docs + Support Matrix + same feature evidence re-test باید sync شوند؛ قبل از fix، exact contract را طوری مستند نکن که repair اعمال‌شده به نظر برسد.
