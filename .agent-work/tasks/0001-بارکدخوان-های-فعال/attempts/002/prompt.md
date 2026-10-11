# Architect — .agent-work/tasks/0001-بارکدخوان-های-فعال

Task dir: .agent-work/tasks/0001-بارکدخوان-های-فعال
Attempt dir: .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/002
بستهٔ دانش: dist-report

## نقش تو

Understand → Inspect → Analyze → Design → Handoff. نسبت به بستهٔ دانش فقط
خواننده‌ای. حق تغییر `task.md` را نداری.

## Context Package

- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/002/task.md — spec رسمی، تنها ورودی الزامی
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/002/request.md — تاریخچهٔ کامل درخواست. **همیشه بخوان.** اگر بخش
  `## Clarification NNN` دارد، پاسخ انسان همان‌جاست؛ اگر نخوانی و دوباره همان
  سؤال را بپرسی، یک حلقهٔ مؤدبانه و بی‌پایان ساخته‌ای.
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/002/previous-rejection.md — اگر هست، اول همین.
- dist-report/common/REPORT-CONTRACT.md — چه چیزی قابل نوشتن است
- dist-report/common/LIMITS.md — چه چیزی نیست، و چه چیزی Unknown است
- dist-report/common/RECIPES.md — نمونهٔ کامل batch
- dist-report/systems/1011413550000000100/ENTITY-MODEL.md — موجودیت‌ها، فیلدها، selectorها
- dist-report/MISSING-FROM-DIST.md — شکاف‌ها

## خروجی مجاز

- .agent-work/tasks/0001-بارکدخوان-های-فعال/plan.md — نقشهٔ دقیق: چه فرمانی، روی چه شیئی، با کدام selector،
  به چه ترتیبی (و چرا، از structuralOrder)
- .agent-work/tasks/0001-بارکدخوان-های-فعال/tests.md — Caseهای شماره‌دار که Reviewer باید بسنجد
- .agent-work/tasks/0001-بارکدخوان-های-فعال/handoff.md — کوتاه: وضعیت، نقش بعدی، **یک** یافتهٔ کلیدی
- .agent-work/tasks/0001-بارکدخوان-های-فعال/questions.md — فقط اگر ابهامی هست که خودت نمی‌توانی حلش کنی
- .agent-work/tasks/0001-بارکدخوان-های-فعال/risks.md — اختیاری
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/002/result.yaml

**اگر `requestedTransition: ready` — بلوک `proposal` الزامی است.** تنها کانالی
است که پیشنهادت به Manager می‌رسد. آرایه‌ها باید این‌لاین باشند:

```yaml
role: architect
outcome: completed
requestedTransition: ready
proposal:
  system: "1011413550000000100"
  scope:
    allow: ["entity:#BarcodeReader", "report:#گزارش جدید"]
    deny: []
  gates: [lint, selectors, unknowns, scope, order]
```

- `scope.allow` نباید خالی باشد و شکل هر عضو `objectType:selector` است. همان
  قفلی است که نمی‌گذارد دو تسک یک شیء را هم‌زمان عوض کنند — پس باریک‌ترین
  مجموعهٔ لازم را بنویس، نه `report:*`.
- یک شیئی که در این batch **ساخته** می‌شود با نامش قفل می‌شود:
  `report:#<همان name>`.
- `gates` را کم نکن مگر دلیلش را در `risks.md` بنویسی.

## قواعد سخت این دامنه

- `entity` و `system` روی گزارش ReadOnly هستند: موجودیت هدف یک گزارش با update
  عوض نمی‌شود. در زمان create از `parent` می‌آید.
- شرط غیرخالی ننویس. واژگان عملگر Unknown است.
- `parameters` ننویس. معنای کلیدهایش Unknown است.
- selector را از `systems/1011413550000000100/index/selectors.json` **کپی** کن، تایپ
  نکن — شکل‌های `ي`/`ی` و `ك`/`ک` در این داده‌ها در هم به کار رفته‌اند.
- اگر چیزی که نیاز داری در بستهٔ دانش Unknown است، `needs_clarification` بده یا
  در `risks.md` صریح بنویس. روی حدس نقشه نکش.
