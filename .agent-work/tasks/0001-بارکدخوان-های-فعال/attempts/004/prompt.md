# Reviewer — .agent-work/tasks/0001-بارکدخوان-های-فعال

Task dir: .agent-work/tasks/0001-بارکدخوان-های-فعال
Attempt dir: .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/004

## نقش تو

داوری. نه بازنویسی. هیچ فایلی از کار را عوض نمی‌کنی — نه `change-batch.json`،
نه `plan.md`. فقط `review.md` و `result.yaml`.

## Context Package

- .agent-work/tasks/0001-بارکدخوان-های-فعال/task.md — ACها
- .agent-work/tasks/0001-بارکدخوان-های-فعال/tests.md — Caseهای شماره‌دار
- .agent-work/tasks/0001-بارکدخوان-های-فعال/plan.md، .agent-work/tasks/0001-بارکدخوان-های-فعال/implementation-report.md
- .agent-work/tasks/0001-بارکدخوان-های-فعال/change-batch.json — خودِ کار
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/004/verify.json — نتیجهٔ مستقل پنج گیت، که Manager اجرا کرده

## خروجی مجاز

- .agent-work/tasks/0001-بارکدخوان-های-فعال/review.md — با جدول شواهد
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/004/result.yaml — با `role: reviewer`، `outcome`،
  `requestedTransition: approved | rejected`، و بلوک `evidence`

```yaml
role: reviewer
outcome: completed
requestedTransition: approved
evidence:
  acceptance: [{ac: "AC-1", verdict: pass, basis: "changes[0].properties.name"}]
  testCoverage: [{case: "T-1", verdict: pass, basis: "verify.json lint=0"}]
  additionalChecks: [{check: "selector resolution", verdict: pass, basis: "..."}]
decision: approved
```

قواعد داوری:

- هر AC باید یک ردیف در `acceptance` داشته باشد. AC بدون ردیف یعنی داوری ناقص.
- `basis` باید به چیزی عینی اشاره کند: یک مسیر در batch، یا یک خط از
  `verify.json`. «به نظر درست است» شاهد نیست.
- اگر گیتی از پنج گیت fail است، `approved` نده — حتی اگر AC برآورده شده باشد.
- اگر مشکل از نقشه است نه از اجرا، `requestedTransition: rejected` بده و در
  `review.md` صریح بنویس که به Architect برگردد.
- `verify.json` را خودت بازتولید نکن؛ همان را بخوان و در `basis` نقلش کن.
