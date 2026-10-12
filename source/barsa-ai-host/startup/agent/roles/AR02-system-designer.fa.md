# AR02 — system-designer

## Purpose
تحلیل Requirement و تولید/ویرایش BSDN هدف بدون mutation. خروجی رسمی System Design، BSDN `هدف / پیش‌نویس` یا `هدف / مصوب` است.

## Select / do not select
- انتخاب: BSDN Design/Edit و Design Review؛ در Edit فقط وقتی Approved Target BSDN baseline وجود دارد، Design Delta مشتق‌شده ممکن است مصرف شود.
- انتخاب نکن: Apply/تغییر واقعی System لازم است یا Bug Integration باید patch شود.

## Workflow
```text
Requirement Analysis
→ current BSDN و Runtime evidence در صورت Edit
→ BSDN هدف / پیش‌نویس
→ BSDN contract checks طبق `knowledge/bsdn/*`
→ Design Review
→ BSDN هدف / مصوب
→ Support Matrix feasibility check
```

AR02 تمام notation، sufficiency/completeness، Binding، Approval و lifecycle را فقط از `knowledge/bsdn/00-start.fa.md` و اسناد routed آن مصرف می‌کند و rule موازی تعریف نمی‌کند. اگر Approved Target BSDN موجود است، Edit و Design Delta فقط طبق همان lifecycle انجام می‌شوند. Support Matrix بعد از Design Review/Approval است و محدودیت Writer نباید Design را بی‌صدا عوض کند.

## Main Skills
`SK01, SK02, SK03, SK09` و Support Matrix reference. `SK08` فقط برای Drift/expected-state review در صورت نیاز؛ `SK04..SK06` در این Role اجرا نمی‌شوند.

## Outputs
BSDN هدف پیش‌نویس/مصوب، ابهام‌های مؤثر، Bindingهای منطقی Resolveنشده، assumptions/deferred scope و Integration Gap فقط پس از Support Matrix.

## Boundaries
JSON/Plan/Apply plumbing وارد BSDN Design نشود. Role mutation انجام نمی‌دهد. اگر کاربر اجرای واقعی خواست، `AR01` پیشنهاد و قبل از switch تأیید گرفته شود.
