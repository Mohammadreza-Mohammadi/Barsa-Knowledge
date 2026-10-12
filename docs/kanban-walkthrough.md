# یک تست کامل، از صفر

این سند یک سناریوی واقعی است که خط‌به‌خط اجرا و خروجی‌هایش از اجرای واقعی
کپی شده، نه از حافظه. چیزی که می‌سازیم: **یک گزارش لیستی روی موجودیت «بازدید
گیت»** — و عمداً یک بار اشتباه می‌کنیم تا ببینیم گیت‌ها کجا جلویش را می‌گیرند.

> روی ویندوز به‌جای `python3` بنویس `python` (یا `py -3`). `python3` آنجا
> معمولاً stub فروشگاه مایکروسافت است و ساکت بیرون می‌آید، بدون خطا و بدون
> اجرا. متن‌های چندخطی را هم در فایل بگذار و `--request-file` بده؛ quote کردن
> متن چندخطی در cmd.exe سرِ اولین newline قطع می‌شود.

---

## نقشهٔ ذهنی: چه کسی چه وقت کار می‌کند

```text
ورودی ──→ طراحی ──→ آماده ──→ پیاده‌سازی ──→ بازبینی ──→ آماده اعمال ──→ تمام
 │          │                     │             │              │
intake   architect           implementer    reviewer      انسان (تو)
 │          │                     │             │              │
 └ AC ها    └ نقشه + قفل scope    └ batch       └ جدول شواهد    └ «اعمال کردم»
    ↓                                              
 گیت spec-approval (تو تأیید می‌کنی)
```

دو جا کار دست توست: **تأیید spec** و **اعمال نهایی**. بقیهٔ ایست‌ها گیت انسانی
نیستند؛ آنجا Manager منتظر است یک نقش فایل‌هایش را بنویسد.

هر `run` یک قدم جلو می‌رود و می‌ایستد. کد خروجش می‌گوید چرا ایستاد:

| کد | یعنی |
|---:|---|
| `0` | تمام شد |
| `10` | منتظر تو یا منتظر یک نقش |
| `20` | متوقف — چیزی رد شد |
| `30` | بدون پیشرفت (باگ) |

---

## قدم ۰ — آماده‌سازی، یک‌بار برای همیشه

```bash
python3 tools/manager.py init --system 1011413550000000100
```

```text
نوشته شد: .agent-work/config/repository.yaml
نوشته شد: .agent-work/config/agent-runtime.yaml
نوشته شد: .agent-work/config/prompts/architect.md
...
```

ساخته شد: `.agent-work/` با config و چهار prompt نقش. اگر از قبل بود، چیزی
بازنویسی نمی‌شود.

پیش‌نیاز: بستهٔ دانش آن سیستم باید ساخته شده باشد، وگرنه هیچ selectorی قابل
اثبات نیست:

```bash
python3 tools/report_compiler.py --scope system=1011413550000000100
```

---

## قدم ۱ — نیاز را بده (لِین: ورودی)

```bash
cat > need.txt <<'TXT'
روی موجودیت «بازدید گیت» یک گزارش لیستی لازم دارم با دو ستون: بارکدخوان و
توضیحات. اسمش «بازدیدهای امروز». فیلتر ندارد و خودش اجرا شود.
TXT

python3 tools/manager.py import-issue \
    --slug بازدیدهای-امروز --kind report.create --request-file need.txt
```

```json
{ "ok": true, "taskId": "0001",
  "taskDir": ".agent-work/tasks/0001-بازدیدهای-امروز" }
```

متن تو **عیناً** `request.md` می‌شود. هیچ AC و قالبی اضافه نمی‌شود — آن کار
نقش Intake است.

```bash
python3 tools/manager.py run 0001
```

```text
نقش intake باید این‌ها را بنویسد:
  - proposed-task.md
  - release-note.md
  - .agent-work/tasks/0001-بازدیدهای-امروز/attempts/001/result.yaml
دستور کامل نقش: .agent-work/tasks/0001-بازدیدهای-امروز/attempts/001/prompt.md
[10] منتظر توست
```

**اینجا چه شد:** Manager یک پوشهٔ attempt ساخت، prompt نقش و context را داخلش
گذاشت، و ایستاد. با provider `manual` هیچ agent صدا زده نمی‌شود.

نقش را اجرا کن: فایل `prompt.md` را به Claude (یا هر agent) بده، یا خودت
بنویس. سه فایل بالا باید ساخته شوند. `proposed-task.md` باید ACهای شماره‌دار
داشته باشد، چون Reviewer بعداً روی همان شماره‌ها جدول می‌سازد.

```bash
python3 tools/manager.py run 0001
```

```text
Intake تمام شد. گیت spec-approval باز است: proposed-task.md را ببین.
[10] منتظر توست
```

---

## قدم ۲ — گیت اول: تأیید spec (کار تو)

`proposed-task.md` را کنار `request.md` بخوان. اگر درست است:

```bash
python3 tools/manager.py answer 0001 --approve
```

```text
spec تأیید شد و task.md مهر خورد. ادامه: run 0001
```

**اینجا چه شد:** Manager همان متن را به‌عنوان `task.md` کپی کرد و hash درخواست
و spec را در manifest ثبت کرد. از این به بعد `task.md` سند رسمی است و هیچ
نقشی حق تغییرش را ندارد.

اگر غلط بود:

```bash
echo "AC-3 دو پهلوست: منظور ستون است یا فیلتر؟" > reason.txt
python3 tools/manager.py answer 0001 --reject --reason-file reason.txt
```

متن رد به `previous-rejection.md` تلاش بعدی Intake می‌رود.

---

## قدم ۳ — طراحی (لِین: طراحی → آماده)

```bash
python3 tools/manager.py run 0001
```

```text
نقش architect باید این‌ها را بنویسد:
  - plan.md
  - tests.md
  - handoff.md
  - .agent-work/tasks/0001-بازدیدهای-امروز/attempts/002/result.yaml
```

`prompt.md` این نقش دقیقاً می‌گوید چه چیزی از بستهٔ دانش بخواند. مهم‌ترین
خروجی‌اش بلوک `proposal` در `result.yaml` است — تنها کانالی که پیشنهادش به
Manager می‌رسد:

```yaml
role: architect
outcome: completed
requestedTransition: ready
proposal:
  system: "1011413550000000100"
  scope:
    allow: ["entity:#بازدید گیت", "report:#بازدیدهای امروز"]
    deny: []
  gates: [lint, selectors, unknowns, scope, order]
```

```bash
python3 tools/manager.py run 0001
```

```text
نقشه پذیرفته شد. scope قفل شد: entity:#بازدید گیت, report:#بازدیدهای امروز
نقش implementer باید این‌ها را بنویسد:
  - change-batch.json
  - implementation-report.md
```

**اینجا چه شد:** Manager بلوک `proposal` را اعتبارسنجی کرد (شکل
`objectType:selector`، وجود objectType در قرارداد، وجود index برای آن سیستم)،
بررسی کرد هیچ تسک زنده‌ای این اشیاء را قفل نکرده باشد، و دو transition پشت سر
هم زد: `architecture → ready → implementing`.

selector یک گزارش را از کجا بیاوری:

```bash
python3 -c "import json;[print(s['objectType'], s['selector']) for s in json.load(open('dist-report/systems/1011413550000000100/index/selectors.json'))['selectors']]"
```

---

## قدم ۴ — پیاده‌سازی، و جایی که گیت گاز می‌گیرد

حالا عمداً یک اشتباه رایج می‌کنیم: یک شرط واقعی می‌نویسیم.

```json
"condition": { "all": [ { "field": "#توضیحات", "operator": "IsNotNull" } ] }
```

خودسنجی قبل از تحویل:

```bash
python3 tools/manager.py verify 0001
```

```text
batch: change-batch.json
  lint       پاس  (errors=0 warnings=0)
  selectors  پاس  (errors=0 warnings=0)
  unknowns   رد  (errors=1 warnings=0)
  scope      پاس  (errors=0 warnings=0)
  order      پاس  (errors=0 warnings=0)
  - [unknowns] condition carries 1 clause(s); the operator vocabulary is Unknown
      changes[0].properties.condition
      Write an empty condition and let a human add the filter in the designer.
```

**این مهم‌ترین خط کل این سند است:** `lint` پاس شد. یعنی از نظر قرارداد نوشتنِ
بارسا، این batch بی‌عیب است و اگر فقط linter داشتیم، قبول می‌شد. ولی
`IsNotNull` یک **حدس** است — بستهٔ دانش می‌گوید واژگان عملگر Unknown است، چون
پروفایل فقط یک عضو دارد. گیت `unknowns` برای همین هست.

حالا فرض کن نقش این را نادیده گرفت و گفت «تمام شد»:

```yaml
role: implementer
outcome: completed
requestedTransition: review
```

```bash
python3 tools/manager.py run 0001
```

```text
verification رد شد:
  - [unknowns] condition carries 1 clause(s); the operator vocabulary is Unknown (changes[0].properties.condition)
attempt بعدی implementer همین متن را در previous-rejection.md می‌بیند.
[20] متوقف
```

**اینجا چه شد:** Manager حرف `result.yaml` را قبول نکرد و خودش پنج گیت را
اجرا کرد. تسک جلو نرفت، و یک بودجهٔ implementer مصرف شد.

```bash
python3 tools/manager.py run 0001   # attempt تازه باز می‌کند
cat .agent-work/tasks/0001-*/attempts/004/previous-rejection.md
```

```text
# چرا attempt 003 رد شد

verification مستقل Manager این موارد را پیدا کرد. متن `result.yaml` در این
تصمیم نقشی ندارد.

## گیت unknowns — 1 خطا، 0 هشدار

- **changes[0].properties.condition** — condition carries 1 clause(s); the
  operator vocabulary is Unknown
  - Write an empty condition and let a human add the filter in the designer.

همان اشتباه را تکرار نکن.
```

شرط را خالی کن (`{"all": []}`)، `result.yaml` تلاش تازه را بنویس:

```bash
python3 tools/manager.py run 0001
```

```text
هر پنج گیت پاس شد — رفت به بازبینی.
```

---

## قدم ۵ — بازبینی

Reviewer فقط داوری می‌کند؛ حق تغییر `change-batch.json` را ندارد. جدول شواهدش
اجباری است و **هر AC باید یک ردیف داشته باشد**:

```yaml
role: reviewer
outcome: completed
requestedTransition: approved
decision: approved
evidence:
  acceptance: [{ac: "AC-1", verdict: pass, basis: "changes[0].parent.selector"}, ...]
  testCoverage: [{case: "T-1", verdict: pass, basis: "len(changes)==1"}]
  additionalChecks: [{check: "پنج گیت", verdict: pass, basis: "verify.json"}]
```

اگر یک AC جا بیفتد یا یک ردیف `basis` نداشته باشد، Manager داوری را رد می‌کند
و تسک در `review` می‌ماند. «به نظر درست است» شاهد نیست.

---

## قدم ۶ — گیت دوم: اعمال (کار تو)

```bash
python3 tools/manager.py run 0001
```

```text
گیت apply-approval باز است. این batch را روی بارسا اعمال کن:
  .agent-work/tasks/0001-بازدیدهای-امروز/change-batch.json
  sha256 4c63db4ddde9e578 · 1 فرمان
بعد از اعمال: python3 tools/manager.py answer 0001 --approve
```

حالا **خودت** آن فایل را روی بارسا اعمال می‌کنی. این مخزن هیچ‌وقت به نصب بارسا
وصل نمی‌شود و هیچ‌وقت کد بارسا را اجرا نمی‌کند. بعدش:

```bash
python3 tools/manager.py answer 0001 --approve
```

```text
تسک بسته شد. قفل scope آزاد شد.
```

`--approve` اینجا یعنی «من اعمال کردم» — و حرفت بدون شاهد پذیرفته نمی‌شود.
امتحانش کن: یک کاراکتر در `change-batch.json` عوض کن و دوباره تأیید بزن:

```text
خطا: batch بعد از باز شدن گیت عوض شده است (4c63db4ddde9e578 → e7f0d95429ae6c77).
تأیید قبلی باطل است؛ run بزن تا دوباره داوری شود.
```

---

## وقتی می‌خواهی Manager خودش اعمال کند

تا اینجا `appliedBy: human` بود. اگر `Barsa.Ai.Host` بالا باشد، این خط را در
`.agent-work/config/repository.yaml` عوض کن:

```yaml
integration:
  appliedBy: barsa-host
```

و کلید را از محیط بده (هرگز داخل فایل):

```bash
export BARSA_AI_HOST_KEY=...
python3 tools/manager.py host --health      # اول خشک امتحان کن
python3 tools/manager.py host --plan 0001   # plan می‌سازد، اعمال نمی‌کند
```

حالا همان `answer 0001 --approve` معنایش «اعمالش کن» است:

```text
اعمال از طریق Barsa.Ai.Host: http://127.0.0.1:17840/
  دیتابیس: SQL01 / BarsaProd
  اثر انگشت runtime: ...
  plan plan-001: 1 command(s), 0 error(s)
  apply accepted; waiting for the host to finish
بارسا اعمال کرد. plan plan-001، state applied.
تسک بسته شد. قفل scope آزاد شد.
```

اگر host بگوید نه — هر جای زنجیره — تسک **بسته نمی‌شود**، گیت باز می‌ماند، و
متن خودِ host در `apply-failure.md` و در `previous-rejection.md` تلاش بعدی
می‌نشیند. جزئیات: [`kanban.md`](kanban.md)، بخش «اعمال خودکار روی بارسا».

---

## همین سناریو، از داخل کنسول

```bash
python3 tools/kanban_server.py --port 4310
```

بعد `http://127.0.0.1:4310/`:

1. **نیاز تازه** → slug، نوع نیاز، سیستم، متن درخواست → **بساز**.
   کارت در لِین «ورودی» ظاهر می‌شود و اجرا خودکار شروع می‌شود.
2. نوار نارنجی **منتظر تو** بالای برد، گیت‌های انسانی را نشان می‌دهد.
3. روی کارت بزن → تب **گیت**: برای spec تأیید/رد، برای ابهام textarea با
   چک‌باکس respec، برای اعمال دو مرحله (اول تیک «اعمال کردم»، بعد دکمه).
4. تب **فایل‌ها**: هر artifact و هر attempt.
   تب **لاگ**: خروجی زندهٔ `run` روی SSE.
   تب **رویدادها**: کل تاریخچهٔ تغییرناپذیر.

---

## چیزهای دیگری که ارزش امتحان دارد

**ابهام.** در Intake به‌جای `completed` بنویس `needs_clarification` و یک
`questions.md` بساز:

```bash
python3 tools/manager.py run 0001        # گیت clarification باز می‌شود
echo "منظورم گزارش «گیت ها» بود." > answer.txt
python3 tools/manager.py answer 0001 --clarify --file answer.txt
```

پاسخ به انتهای `request.md` به‌عنوان `## Clarification 001` اضافه می‌شود — تنها
جایی که پاسخ تو به نقش بعدی می‌رسد. اگر پاسخ خودِ spec را عوض می‌کند،
`--respec` اضافه کن تا از نو از Intake بگذرد.

**قفل scope.** دو تسک برای یک گزارش بساز و هر دو را تا `ready` ببر. دومی
blocked می‌شود با دلیل روشن: «این اشیاء در اختیار تسک 0001 هستند».

**برگشت.** `python3 tools/manager.py void 0001 --reason-file r.txt` آخرین
transition را برمی‌گرداند. `cancel` تسک را می‌بندد. هر دو دلیل اجباری دارند.

**بودجه.** `budget` هر نقش در `repository.yaml` است. وقتی تمام شود تسک
`blocked` می‌شود با `blocker.kind: budget-exhausted` — نه حلقهٔ بی‌پایان.

**تست‌ها.**

```bash
python3 tools/test_kanban.py        # ۲۶ تست: گیت‌ها، store، پیمایش کامل
python3 tools/test_kanban_host.py   # ۱۵ تست: مسیر Barsa.Ai.Host
```
