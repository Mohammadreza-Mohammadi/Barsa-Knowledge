# .agent-work/

وضعیت پروتکل. **تنها نویسندهٔ این پوشه `tools/manager.py` است** — نه کنسول، نه
نقش‌ها، نه دست.

```text
BOARD.md              تولیدشده از manifestها؛ ویرایشش بی‌فایده است
config/
  repository.yaml     سیستم‌های مجاز، گیت‌ها، بودجه، چه کسی اعمال می‌کند
  agent-runtime.yaml  provider هر نقش
  prompts/*.md        دستور هر نقش — اینجا ویرایش می‌شود، نه در کد
tasks/<id>-<slug>/
  manifest.yaml       تنها جای state؛ فقط Manager می‌نویسدش
  request.md          متن خام انسان + پاسخ‌های clarification
  task.md             spec رسمی؛ Manager در لحظهٔ spec-approval مهرش می‌زند
  proposed-task.md    خروجی Intake
  plan.md tests.md handoff.md risks.md      خروجی Architect
  change-batch.json   خودِ کار
  implementation-report.md changelog.md     خروجی Implementer
  review.md           داوری
  verify.json         نتیجهٔ مستقل پنج گیت، که Manager اجرا کرده
  events.jsonl        تاریخچهٔ تغییرناپذیر
  attempts/NNN/       هر تلاش یک نقش: prompt، context، result.yaml
logs/                 لاگ عملیاتی (gitignored)
```

`attempts/NNN/previous-rejection.md` تنها جایی است که دلیل رد شدن تلاش قبلی به
نقش بعدی می‌رسد. هر prompt می‌گوید اول همان را بخوان.
