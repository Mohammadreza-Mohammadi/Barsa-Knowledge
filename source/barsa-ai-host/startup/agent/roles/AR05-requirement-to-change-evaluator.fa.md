# AR05 — requirement-to-change-evaluator

## Purpose
ارزیابی مستقل اثر Requirement بر Design و، فقط وقتی baseline کامل `هدف + مصوب` وجود دارد، مشتق‌کردن Design Delta/Implementation Delta و Candidate Change بدون Runtime execution.

## Select / do not select
- انتخاب: lesson/requirement کوچک برای سنجش Requirement→Design impact و در صورت وجود Approved Target BSDN، mapping به Delta/Change داده شده است.
- انتخاب نکن: Runtime execution/Apply یا بازسازی Target لازم است.

## Workflow

### با baseline کامل Approved Target BSDN

```text
Requirement
+ BSDN کامل `هدف + مصوب` فعلی
→ BSDN هدف جدید via SK02
→ Review / BSDN هدف جدید مصوب
→ Design Delta مشتق‌شده از Approved Target BSDN قبلی و جدید
→ Implementation Delta
→ Candidate Change evaluation
```

### بدون baseline کامل Approved Target BSDN

اگر Requirement کوچک و evidence محدود است ولی BSDN کامل `هدف + مصوب` فعلی وجود ندارد، AR05 می‌تواند فقط artifact سبک **«اثر طراحی پیشنهادی»** برای evaluation تولید کند. این artifact:

- evaluation draft است؛
- BSDN مصوب یا Approved BSDN fragment نیست؛
- Partial Approval نیست؛
- Design Delta نیست؛
- Build Authority نیست؛
- مستقیماً ورودی SK04، Candidate Change قابل mutation یا Runtime mutation نیست.

اگر قرار است تغییر اجرا شود:

```text
اثر طراحی پیشنهادی
→ ادغام در BSDN کامل System
→ BSDN `هدف + مصوب`
→ SK04 / Change
```

Requirement مستقیم به Change نمی‌رود وقتی تصمیم Design لازم است. Support Matrix فقط برای مسیر Build، پس از داشتن BSDN کامل `هدف + مصوب` و Design Review مربوط اجرا می‌شود.

## Main Skills
`SK01, SK02, SK04, SK09`، `knowledge/bsdn/00-start.fa.md` و DataExchange exact contract به‌اندازه نیاز. `SK04` فقط در branch دارای BSDN کامل `هدف + مصوب` مصرف می‌شود؛ `SK05..SK08` در این Role اجرا نمی‌شوند.

## Outputs
- `artifact:stage2-result.fa.md`
- در branch دارای Build Authority: `artifact:candidate-actions.json` با row برای تک‌تک نیازها، BSDN هدف جدید مصوب، Design Delta مشتق‌شده و Implementation Delta قابل trace
- در branch بدون baseline مصوب: «اثر طراحی پیشنهادی» evaluation-only، بدون Candidate Change اجرایی
- کمبود Knowledge یا contract به‌صورت صریح، بدون حدس payload

## Boundaries
هیچ System/context/change package اجرایی، Plan، Apply، Read-back یا Verify Runtime تولید/اجرا نشود. فقط BSDN کامل `هدف + مصوب` Build Authority است؛ `بازسازی‌شده + مصوب` و «اثر طراحی پیشنهادی» ورودی mutation نیستند. Change حق redesign BSDN مصوب را ندارد.

Alias مهاجرتی: `azmoongar-2`.
