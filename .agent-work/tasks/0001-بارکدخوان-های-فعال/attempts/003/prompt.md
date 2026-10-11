# Implementer — .agent-work/tasks/0001-بارکدخوان-های-فعال

Task dir: .agent-work/tasks/0001-بارکدخوان-های-فعال
Attempt dir: .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/003
بستهٔ دانش: dist-report

## نقش تو

نقشهٔ Architect را به یک `AiChangeBatch` واقعی تبدیل کن. نقشه را دوباره طراحی
نکن؛ اگر نقشه غلط است، `outcome: failed` بده و بگو چرا — شکست خودگزارش‌شده
پذیرفته است، batch غلطِ بی‌صدا نه.

## Context Package

- .agent-work/tasks/0001-بارکدخوان-های-فعال/task.md، .agent-work/tasks/0001-بارکدخوان-های-فعال/plan.md، .agent-work/tasks/0001-بارکدخوان-های-فعال/tests.md
- .agent-work/tasks/0001-بارکدخوان-های-فعال/handoff.md
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/003/previous-rejection.md — اگر هست، اول همین
- dist-report/common/RECIPES.md و dist-report/common/REPORT-CONTRACT.md
- dist-report/systems/1011413550000000100/index/selectors.json — **منبع selectorها**

## خروجی مجاز

- .agent-work/tasks/0001-بارکدخوان-های-فعال/change-batch.json — خودِ کار
- .agent-work/tasks/0001-بارکدخوان-های-فعال/implementation-report.md — چه ساختی و چرا همین شکل
- .agent-work/tasks/0001-بارکدخوان-های-فعال/changelog.md — برای مهندس بعدی (نه برای کاربر؛ آن release-note است)
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/003/failure.md — فقط وقتی `outcome: failed`
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/003/result.yaml

## شکل batch

```json
{
  "profileVersion": 15,
  "policy": { "errorPolicy": "continueIndependent", "ignoreUnsupported": false },
  "changes": [ { "commandId": "...", "operation": "create", "objectType": "report",
                 "parent": { "objectType": "entity", "selector": "#..." },
                 "properties": { "name": "...", "reportType": "list" } } ]
}
```

## چیزی که Manager خودش می‌سنجد (پس خودت قبلش بسنج)

بعد از تو، Manager پنج گیت را مستقل اجرا می‌کند و حرف `result.yaml` را برای
این تصمیم قبول نمی‌کند:

1. `lint` — همان linter قرارداد، صفر finding (warning هم شکست است)
2. `selectors` — هر selector باید در index این scope باشد یا tempId همین batch
3. `unknowns` — شرط غیرخالی، `parameters` و `folder.kind` ممنوع‌اند
4. `scope` — فقط اشیائی که تسک قفلشان را دارد
5. `order` — ترتیب structuralOrder، و والد پیش از فرزند

قبل از نوشتن `result.yaml` خودت اجرا کن:

```bash
python3 tools/manager.py verify 0001
```
