# کانبان بارسا — از درخواست کاربر تا تغییر تأییدشده

یک نیاز خام («روی موجودیت BarcodeReader یک گزارش لیستی لازم دارم») از هفت لِین
می‌گذرد و در انتها یک `AiChangeBatch` اعتبارسنجی‌شده بیرون می‌آید که انسان روی
بارسا اعمالش می‌کند.

```text
ورودی → طراحی → آماده → پیاده‌سازی → بازبینی → آماده اعمال → تمام
new    architecture  ready  implementing  review   approved…    integrated
       ↓                           ↓          ↓         ↓
  needs-clarification           failed    rejected   conflict
  needs-investigation
```

ساختار، نام state‌ها، قرارداد `barsa-agent-manager v1` و دو گیت انسانی عیناً
همان چیزی است که در workflow موجود شما کار می‌کند؛ آنچه عوض شده **جنس کار**
است: اینجا چیزی compile نمی‌شود، پس به‌جای build/lint/test پنج گیت دیگر هست.

## سه دقیقه تا اولین برد

لازم: فقط **Python 3.8 یا بالاتر**. نه npm، نه build، نه پکیج بیرونی.

```bash
git clone <این مخزن> && cd Barsa-Knowledge
python3 tools/kanban_server.py
```

```text
کنسول کانبان: http://127.0.0.1:4310/
مخزن: /path/to/Barsa-Knowledge
manager: /path/to/Barsa-Knowledge/tools/manager.py
```

این سه خط باید چاپ شوند و terminal **مسدود بماند**. اگر بلافاصله به prompt
برگشت و چیزی چاپ نشد، سرور بالا نیامده.

### روی ویندوز

دو چیز که وقت می‌گیرند اگر از قبل ندانی:

```powershell
python tools\kanban_server.py            # نه python3
```

`python3` روی ویندوز معمولاً همان stub فروشگاه مایکروسافت است: ساکت بیرون
می‌آید، بدون خطا و بدون سرور. `python` یا `py -3` درست است.

**تداخل پورت با BarsaAgent:** پیش‌فرض هر دو `4310` است. اگر BarsaAgent بالا
باشد، مرورگر با *او* حرف می‌زند نه با این کنسول — و چون UI انگولارش build
نشده، جواب می‌دهد `{"error":"UI build پیدا نشد. ابتدا npm run build را اجرا
کنید."}`. آن پیام از BarsaAgent است، نه از اینجا؛ این کنسول اصلاً npm لازم
ندارد. راهش:

```powershell
python tools\kanban_server.py --port 4311
```

از این نسخه به بعد خود سرور تشخیص می‌دهد و می‌گوید چه کسی روی پورت نشسته،
به‌جای اینکه ساکت در سایهٔ او بالا بیاید.

**encoding:** پایتون روی ویندوز به یک stdout که pipe است، code page سیستم
(معمولاً cp1252) می‌دهد — و JSON این ابزار پر از فارسی است. نتیجه‌اش
`UnicodeEncodeError` بود و کنسول می‌گفت «خواندن برد ناموفق». هر سه ورودی CLI
حالا stdout و stderr خودشان را صریح UTF-8 می‌کنند و هر زیرپروسه‌ای هم با
`PYTHONIOENCODING=utf-8` اجرا می‌شود. اگر خودِ کنسول ویندوز فارسی را نشان
نمی‌دهد، این کار را بکن (ولی دیگر لازم نیست برای جلوگیری از خطا):

```powershell
chcp 65001
```

مرورگر را روی همان آدرس باز کن. `.agent-work/` از قبل در مخزن هست، پس برد
خالی نیست: تسک ۰۰۰۱ (تمام‌شده) و ۰۰۰۲ (لغوشده) به‌عنوان دو مثال واقعی
آنجا هستند.

**درخواست دادن:** دکمهٔ «نیاز تازه» بالا راست → slug، نوع نیاز، و متن درخواست
به زبان خودت → «بساز».

شناسهٔ سیستم را از تو نمی‌پرسد. فهرست سیستم‌های بسته را نشان می‌دهد و
پیش‌فرضش **«بگذار از متن درخواست تشخیص بدهد»** است:

```text
— بگذار از متن درخواست تشخیص بدهد —
باركد — 8 موجودیت
Meta01 — 129 موجودیت  (بستهٔ selector ندارد)      ← غیرفعال
...
```

سیستمی که بستهٔ selector ندارد غیرفعال است، چون بدون آن هیچ selectorی قابل
اثبات نیست. ساختنش یک دستور است:

```bash
python3 tools/report_compiler.py --scope system=<id>
python3 tools/manager.py systems          # فهرست، با همین ستون
```

اگر انتخاب نکنی، نقش Intake باید از متن بفهمد کدام سیستم است. **اگر نفهمید
حدس نمی‌زند**: `questions.md` می‌نویسد با نامزدها و دلیل ابهام، و تسک روی گیت
`clarification` می‌ایستد.

**پاسخ به سؤال:** روی همان کارت (با نشان نارنجی `clarification`) بزن. کشو روی
تب «گیت» باز می‌شود و **خودِ پرسش‌ها آنجا نوشته شده‌اند** — لازم نیست دنبال
فایل بگردی. زیرش یک جعبهٔ پاسخ است و دو دکمه:

```text
فقط ثبت کن              پاسخ در request.md ثبت می‌شود، اجرا نمی‌رود جلو
ثبت پاسخ و ادامهٔ اجرا   ثبت می‌شود و همان‌جا run بعدی شروع می‌شود
```

پاسخ تو عیناً به انتهای `request.md` به‌عنوان `## Clarification NNN` اضافه
می‌شود — تنها جایی که حرف تو به نقش بعدی می‌رسد. اگر پاسخ خودِ spec را عوض
می‌کند (نه فقط رفع ابهام)، چک‌باکس respec را بزن تا از نو از Intake بگذرد.

گیت `spec-approval` هم همین‌طور: متن `proposed-task.md` را همان‌جا در پنل
می‌بینی، نه در تب دیگری.

**دیدن خروجی:** روی کارت بزن. کشو باز می‌شود با پنج تب:

```text
نمای کلی   وضعیت، قفل scope، بودجهٔ هر نقش، نتیجهٔ پنج گیت، جدول شواهد داوری
گیت        هر کاری که الان با توست: تأیید spec، پاسخ ابهام، تأیید اعمال
فایل‌ها     هر artifact — از proposed-task.md تا change-batch.json
رویدادها   کل تاریخچهٔ تغییرناپذیر، با زمان
لاگ        خروجی زندهٔ run روی SSE
```

خروجی نهایی همیشه یک فایل است: `change-batch.json` در پوشهٔ تسک، که از تب
«فایل‌ها» هم قابل دیدن است.

### بدون کنسول هم می‌شود

کنسول فقط یک پوسته روی CLI است؛ هر کاری از خط فرمان هم انجام می‌شود:

```bash
python3 tools/manager.py import-issue --slug نیاز-من --kind report.create \
    --request-file need.txt
python3 tools/manager.py run 0003        # تا اولین ایست جلو می‌رود
python3 tools/manager.py status          # برد، JSON
python3 tools/manager.py artifact 0003 --path change-batch.json
```

### چه کسی نقش‌ها را بنویسد

پیش‌فرض `manual` است: هر `run` می‌ایستد و می‌گوید نقش بعدی دقیقاً چه فایلی
باید بنویسد. یعنی یا خودت می‌نویسی، یا `prompt.md` همان attempt را به یک agent
می‌دهی.

برای اینکه خودکار برود، در `.agent-work/config/agent-runtime.yaml`:

```yaml
defaultProvider: claude
providers:
  claude:
    enabled: true
```

از آن به بعد هر `run` خودش نقش را اجرا می‌کند (`claude -p`, با
`--permission-mode acceptEdits` و ابزار محدود به خواندن/نوشتن). عمداً خاموشِ
پیش‌فرض است: هر اجرا توکن مصرف می‌کند.

دو گیت انسانی سر جایشان می‌مانند — خودکار شدن نقش‌ها یعنی نوشتن artifactها
خودکار می‌شود، نه تأیید کردن.

**محافظ:** بعد از هر اجرای agent، Manager با `git status` بررسی می‌کند که نقش
چیزی بیرون پوشهٔ تسک ننوشته باشد؛ اگر نوشته باشد، transition انجام نمی‌شود و
فایل‌ها نام برده می‌شوند.

یک اجرای واقعی از همین مسیر، با `defaultProvider: claude` و بدون نوشتن هیچ
فایلی به دست: چهار نقش پشت سر هم، هر پنج گیت پاس، مصرف بودجه ۱ از هر نقش،
و توقف روی گیت اعمال:

```text
اجرای provider claude برای نقش architect …
نقشه پذیرفته شد. scope قفل شد: entity:#BarcodeReader, report:#بارکدخوان‌ها
اجرای provider claude برای نقش implementer …
هر پنج گیت پاس شد — رفت به بازبینی.
اجرای provider claude برای نقش reviewer …
گیت apply-approval باز است:
  .agent-work/tasks/0001-بارکدخوان-ها/change-batch.json
  sha256 8265f5ef98564cfa · 1 فرمان
```

## چه کسی چه چیزی می‌نویسد

| نقش | state | خروجی |
|---|---|---|
| intake | `new` | `proposed-task.md` با ACهای شماره‌دار، `release-note.md` |
| architect | `architecture` | `plan.md`، `tests.md`، `handoff.md` + بلوک `proposal` |
| implementer | `implementing` | `change-batch.json`، `implementation-report.md` |
| reviewer | `review` | `review.md` + جدول شواهد |
| **Manager** | همه | `manifest.yaml`، `events.jsonl`، `task.md`، `verify.json`، `BOARD.md` |

ردیف آخر مرز مالکیت است: هیچ نقشی `manifest.yaml` را نمی‌نویسد، و Manager هیچ
artifact نقشی را.

## پنج گیت verification

به‌جای build و test. Manager خودش اجرایشان می‌کند و **حرف خودِ نقش را در این
تصمیم قبول نمی‌کند**:

| گیت | چه چیزی را ثابت می‌کند |
|---|---|
| `lint` | batch از linter قرارداد با صفر finding رد می‌شود (warning هم شکست است) |
| `selectors` | هر selector در index همان scope هست، یا tempId همان batch است |
| `unknowns` | چیزی که بستهٔ دانش Unknown می‌داند نوشته نشده |
| `scope` | فقط اشیائی که تسک قفلشان را دارد لمس شده‌اند |
| `order` | ترتیب structuralOrder، و والد پیش از فرزند |

گیت `unknowns` دلیل وجود کل این خط لوله است. یک batch با عملگر شرطِ حدسی از
linter **رد می‌شود** و بی‌صدا کار غلط می‌کند؛ این گیت جلویش را می‌گیرد.

نکتهٔ مهمش این است که این گیت دقیقاً به اندازهٔ شواهدی که به آن داده‌ایم
سخت‌گیر است، نه بیشتر و نه کمتر:

| وقتی بسته واژگان را دارد | وقتی ندارد |
|---|---|
| هر `operator` باید در فهرست مستندشده باشد | هیچ شرط غیرخالی نوشته نمی‌شود |
| هر `nullBehavior` در فهرست خودش | — |
| هر `folder.kind` در فهرست خودش | `kind` اصلاً نوشته نمی‌شود |
| کلیدهای `parameters` در فهرست خودش | `parameters` اصلاً نوشته نمی‌شود |
| هر کلید ناشناختهٔ clause رد می‌شود | — |
| ارجاع درون‌بسته‌ای باید `objectType` و `tempId` را با هم داشته باشد | — |

واژگان از `dist/index/host-vocabulary.json` می‌آید، که استخراج‌گر از مستندات
خودِ `Barsa.Ai.Host` (زیر `source/barsa-ai-host/startup/`) می‌سازد. نبودشان
خطا نیست — گیت به حالت بستهٔ قبلی برمی‌گردد.

همان مرجع، مسیر canonical ناوبری را هم صریح می‌گوید:
`system → page → group → report placement`. یعنی برای دیده‌شدن یک گزارش لازم
نیست پوشهٔ موجودی را با selector نام ببریم — کل مسیر در همان یک batch با
`tempId` ساخته می‌شود. دستور R2 در بسته گزارش حالا دقیقاً همین شکل است.

یک مثال از اینکه چرا خواندن سند باید با دقت باشد: همان مرجع شرط، `DoseNotContain`
را به‌عنوان یک typo داخلی نام می‌برد که **وارد قرارداد نمی‌شود**. استخراج‌گر
اولین بار همان را هم برداشته بود؛ حالا فهرست دقیقاً سر پاراگراف تمام می‌شود و
یک تست جداگانه ثابت می‌کند آن نام از گیت رد نمی‌شود.

## دو گیت انسانی

**spec-approval** — بعد از Intake. با تأیید، Manager همان `proposed-task.md` را
به‌عنوان `task.md` مهر می‌زند و hash درخواست و spec را ثبت می‌کند. هیچ طراحی‌ای
روی یک spec تأییدنشده انجام نمی‌شود.

**apply-approval** — آخرین گیت، جای merge. دو حالت دارد، و در هر دو حالت
Manager اول مکانیکی ثابت می‌کند batch همان چیزی است که گیت رویش باز شد
(مقایسهٔ sha256) و هنوز از هر پنج گیت رد می‌شود:

```console
$ python3 tools/manager.py answer 0001 --approve
خطا: batch بعد از باز شدن گیت عوض شده است (0d75493… → e7f0d95…).
```

| `integration.appliedBy` | `--approve` یعنی |
|---|---|
| `human` | «من خودم اعمال کردم». Manager به بارسا دست نمی‌زند. |
| `barsa-host` | «اعمالش کن». Manager خودش batch را به Barsa.Ai.Host می‌دهد. |

## اعمال خودکار روی بارسا

`Barsa.Ai.Host.exe` یک HTTP listener است که جلوی مسیر نوشتن معنایی نشسته.
مسیرها و هدرش از IL خودِ همان assembly بیرون آمده، نه از حدس:

```text
GET  /health                 بالا هست؟ روی کدام دیتابیس؟ runtimeFingerprint
GET  /systems                سیستم‌هایی که می‌بیند
POST /lint      <batch>      linter ساختاری، سمت سرور
POST /plan      <batch>      → planId + disposition
POST /apply     {planId}     همان plan را اعمال می‌کند
GET  /apply-status ?planId=  → state، result، error

هدر   X-Barsa-Ai-Key
پیش‌فرض http://127.0.0.1:17840/   (کلید تنظیم: AiHost.HttpPrefix)
```

### `connection.yaml` — تنها جایی که می‌گوید به کدام بارسا وصلیم

```yaml
# .agent-work/config/connection.yaml
schemaVersion: 1
label: "محیط تست"                    # در هدر کنسول دیده می‌شود

host:
  prefix: "http://127.0.0.1:17840/"  # AiHost.HttpPrefix
  apiKeyEnv: BARSA_AI_HOST_KEY       # نام متغیر محیطی، نه خود کلید
  timeoutSeconds: 180
  maxWaitSeconds: 600
  requireCleanPlan: true

database:
  server: "SQL01"
  name: "BarsaTest"
  instance: ""
  enforce: true
```

و در `repository.yaml` فقط یک خط: `integration.appliedBy: barsa-host`.

**اینجا هیچ connection string دیتابیسی نیست، و عمداً نیست.** این مخزن هرگز
مستقیم به SQL وصل نمی‌شود؛ مسیر نوشتن از `Barsa.Ai.Host` می‌گذرد و او
connection خودش را از config خودِ بارسا می‌گیرد. دو جا برای یک حقیقت —
«روی کدام دیتابیس می‌نویسیم» — خطرناک‌ترین نوع drift است.

چیزی که در `database` می‌نویسی **هویت مورد انتظار** است. host در `/health`
می‌گوید واقعاً به چه چیزی وصل است، و Manager قبل از هر اعمال این دو را
مقایسه می‌کند:

```console
$ python3 tools/manager.py answer 0001 --approve
خطا: host به دیتابیسی وصل است که connection.yaml انتظارش را ندارد، پس هیچ
چیزی اعمال نشد.
  name: انتظار 'BarsaTest'، ولی host می‌گوید 'BarsaProd'
```

این گیت برای همان روزی نوشته شده که کسی host را به production برگردانده و
یادش رفته بگوید. مقدار درست را از `host --health` بردار. خالی گذاشتن هر
کلید یعنی همان یکی مقایسه نمی‌شود؛ `enforce: false` یعنی کل مقایسه خاموش.

کلید **هرگز** در این فایل نیست؛ اگر `apiKey` در آن بگذاری، config رد می‌شود.
مقدارش را از محیط بگذار:

```bash
export BARSA_AI_HOST_KEY=...      # ویندوز: $env:BARSA_AI_HOST_KEY = "..."
```

با این تنظیم، `answer <id> --approve` این دنباله را اجرا می‌کند:

```text
۱. verify دوباره — پنج گیت، و sha256 برابر با چیزی که گیت رویش باز شد
۲. GET  /health        → اگر host نیست، همین‌جا می‌ایستد؛ هیچ چیز بسته نمی‌شود
۳. POST /plan          → planId و disposition
۴. اگر isValid=false یا canApplyCleanly=false → اعمال نمی‌شود
۵. POST /apply         → اگر status=rejected، اعمال نشد
۶. GET  /apply-status  → تا رسیدن به یک state پایانی
۷. فقط اگر state=applied → تسک integrated می‌شود
```

هر «نه» در این زنجیره تسک را باز نگه می‌دارد، متن خودِ host را در
`apply-failure.md` می‌نویسد، و همان را به `previous-rejection.md` تلاش بعدیِ
implementer می‌دهد. چیزی دور زده نمی‌شود.

بعد از موفقیت، manifest این‌ها را نگه می‌دارد:

```yaml
batch:
  appliedBy: barsa-host
  planId: plan-001
  hostState: applied
  runtimeFingerprint: ...
  approvedSha256: ...
```

قبل از اینکه به این مسیر اعتماد کنی، ارتباط را خشک امتحان کن — این فرمان‌ها
هیچ چیزی را عوض نمی‌کنند:

```bash
python3 tools/manager.py host --preflight 0001   # همهٔ بررسی‌ها، به ترتیب
python3 tools/manager.py host --health
python3 tools/manager.py host --systems
python3 tools/manager.py host --lint 0001        # linter سمت سرور
python3 tools/manager.py host --plan 0001        # plan می‌سازد، اعمال نمی‌کند
```

`--preflight` همان چیزی است که قبل از اولین اعمال واقعی باید ببینی:

```text
  appliedBy              ✓  barsa-host
  کلید                   ✓  از BARSA_AI_HOST_KEY خوانده شد
  batch                  ✓  1 فرمان
  پنج گیت محلی           ✓  پاس
  health                 ✓  ready · دیتابیس SQL01/BarsaTest · <fingerprint>
  سیستم تسک              ✓  1011413550000000100 در 9 سیستم
  lint سمت سرور          ✓  {"status": "succeeded", "profileVersion": 15}
  plan                   ✓  planId=… valid=True clean=True فرمان=1 خطا=0

هیچ چیزی اعمال نشد — این دستور فقط می‌خواند.
```

### راه‌اندازی خود host

`Barsa.Ai.Host.exe` قبل از بالا آمدن این‌ها را لازم دارد (از
`BarsaRuntime.Initialize`):

```text
۱. فایل config خودِ بارسا کنارش باشد — Barsa.Spl.FileUtil.ConfigPath.
   نباشد: «Barsa config file was not found». یعنی باید داخل پوشهٔ نصب
   بارسا اجرا شود، نه جای دیگر.
۲. دیتابیس در دسترس باشد — در حلقه صبر می‌کند و لاگ می‌دهد
   «cannot connect to database; waiting for connection».
۳. login موفق با AiHost.UserName/Password — وگرنه
   «Barsa login failed for AI Host user: …».
۴. بعد InitApplicationsRemoting، StartApplications و MetaService.Init2.
۵. فقط یک نمونه هم‌زمان: «Barsa.Ai.Host is already running.»
```

نمونهٔ کامل appSettings با همهٔ کلیدها و پیش‌فرض‌هایشان:
[`Barsa.Ai.Host.exe.config.example`](Barsa.Ai.Host.exe.config.example).

**هشدار امنیتی:** اگر `AiHost.ApiKey` خالی باشد، `IsAuthorized` بدون هیچ
بررسی‌ای `true` برمی‌گرداند — یعنی هر برنامه‌ای روی آن ماشین می‌تواند
`POST /apply` بزند. روی هر محیطی جز یک ماشین کاملاً شخصی، کلید بگذار.

### وضعیت‌های /apply-status

از مرجع رسمی خودِ host (`startup/host-api.fa.md`):

```text
ready · applying      هنوز کار دارد
applied               تنها حالت موفق
faulted               شکست
unknown               host نمی‌تواند ثابت کند اجرای قبلی چه کرد
```

`unknown` خطرناک‌ترین است و مرجع صریح می‌گوید **اعمال مجدد خودکار ممنوع**.
این client هم همان‌جا می‌ایستد و می‌گوید تصمیمش با انسانی است که لاگ host را
جلویش دارد. هر حالت ناشناختهٔ دیگری هم پایانی حساب می‌شود، نه «هنوز در حال
اجرا» — وگرنه یک شکست به timeout تبدیل می‌شود.

### چه چیزی اینجا تأیید نشده

هیچ host واقعی از ماشینی که این کد روی آن نوشته شد در دسترس نبود. شکل
درخواست‌ها و پاسخ‌ها از باینری خوانده شده و client در برابر یک stub که
دقیقاً همان‌ها را پیاده می‌کند تست شده
(`tools/test_kanban_host.py`، ۱۵ تست). این یعنی منطق client درست است، نه
اینکه بازسازی قرارداد صددرصد با سرور واقعی می‌خواند. اولین اجرای واقعی ممکن
است یک کلید را متفاوت ببیند؛ آن یک یافته دربارهٔ `barsa_host.py` است، نه
دلیلی برای شل کردن یک گیت. `host --health` و `host --plan` دقیقاً برای همین
هستند: قبل از اولین اعمال واقعی، قرارداد را با چشم خودت ببین.

## قفل scope

به‌جای قفل مسیر فایل، قفل **شیء بارسا**:

```yaml
scope:
  allow: ["entity:#BarcodeReader", "report:#بارکدخوان‌های فعال"]
```

دو تسک نمی‌توانند هم‌زمان یک گزارش را عوض کنند، چون نتیجه به این بستگی پیدا
می‌کرد که کدام batch اول اعمال شود. قفل فقط در `integrated`/`cancelled`/
`abandoned` آزاد می‌شود — `blocked` همچنان نگهش می‌دارد.

## یک تست کامل

اگر می‌خواهی خودت یک بار از صفر اجرا کنی، با دستورها و خروجی‌های واقعی:
[`kanban-walkthrough.md`](kanban-walkthrough.md).

## اجرا

```bash
python3 tools/manager.py init --system 1011413550000000100
python3 tools/manager.py import-issue --slug گزارش-تازه --kind report.create \
    --request-file need.txt
python3 tools/manager.py run 0001          # تا اولین گیت جلو می‌رود
python3 tools/manager.py answer 0001 --approve
python3 tools/manager.py verify 0001       # پنج گیت، همین حالا
python3 tools/manager.py status            # برد، JSON
```

کد خروج `run` همان قرارداد است: `0` تمام · `10` منتظر انسان · `20` متوقف ·
`30` بدون پیشرفت.

### مرز کنسول

راه‌اندازی‌اش بالا آمد. نکتهٔ معماری‌اش این است: کنسول هرگز `.agent-work/` را
مستقیم نمی‌خواند یا نمی‌نویسد — هر چه نشان می‌دهد از یک فرمان Manager آمده،
پس برد نمی‌تواند با store اختلاف پیدا کند.

مسیرهای API همان مسیرهای BarsaAgent است (`/api/repos`, `.../board`,
`.../tasks/:id/run`, `.../answer`, `.../stream`, `/api/tasks/create`)، و
`capabilities` قرارداد `barsa-agent-manager v1` را جواب می‌دهد — یعنی
BarsaAgent موجود هم می‌تواند بدون تغییر به همین manager وصل شود.

## provider نقش‌ها، با جزئیات

انتخاب بین `manual` و `claude` بالا آمد. چیزی که آنجا نیامد: provider به ازای
**هر نقش** قابل تعیین است، و مدل هم همین‌طور — مثلاً طراحی و داوری روی مدل
قوی‌تر، پیاده‌سازی روی مدل ارزان‌تر:

```yaml
defaultProvider: claude
roles:
  intake:      { provider: default }
  architect:   { provider: default }
  implementer: { provider: default }
  reviewer:    { provider: manual }    # داوری را خودم می‌کنم
providers:
  claude:
    enabled: true
    allowedTools: "Read Write Edit Glob Grep"
    permissionMode: acceptEdits
    timeoutSeconds: 900
    model:
      architect: opus
      implementer: sonnet
```

`allowedTools` عمداً باریک است: یک نقش بسته را می‌خواند و artifact خودش را
می‌نویسد؛ دلیلی ندارد دستور اجرا کند.

## تست

```bash
python3 tools/test_kanban.py
```

۲۶ تست: زیرمجموعهٔ YAML، شکل ماشین حالت، **حالت منفی هر پنج گیت** (گیتی که
نتواند fail بدهد گیت نیست)، قواعد store، و یک پیمایش کامل از درخواست خام تا
`integrated` شامل رد شدن یک batch توسط گیت `unknowns`، رد شدن یک جدول شواهد
ناقص، و رد شدن تأیید نهایی وقتی batch بعد از باز شدن گیت عوض شده.

## چیزهایی که این پروتکل عمداً نمی‌کند

- **هیچ‌وقت چیزی را خودکار «درست» نمی‌کند.** هر گیت که رد شود، اجرا می‌ایستد،
  گزارش می‌دهد، و manifest دست‌نخورده می‌ماند.
- **هیچ‌وقت batch را اعمال نمی‌کند.** نه به دیتابیس وصل می‌شود، نه کد بارسا را
  اجرا می‌کند.
- **هیچ‌وقت نتیجهٔ خوداظهاری یک نقش را به‌جای شاهد قبول نمی‌کند** جایی که خودش
  می‌تواند بسنجد.
- **هیچ‌وقت بیرون `.agent-work/` نمی‌نویسد.**
