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
linter رد می‌شود و بی‌صدا کار غلط می‌کند؛ این گیت جلویش را می‌گیرد:

```text
شرط غیرخالی   → واژگان عملگر Unknown است
parameters     → معنای کلیدها Unknown است
folder.kind    → واژگان مقدار Unknown است
```

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

تنظیمش در `repository.yaml`:

```yaml
integration:
  appliedBy: barsa-host
  host:
    prefix: "http://127.0.0.1:17840/"
    apiKeyEnv: BARSA_AI_HOST_KEY   # نام متغیر محیطی، نه خود کلید
    timeoutSeconds: 180
    requireCleanPlan: true
    maxWaitSeconds: 600
```

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
python3 tools/manager.py host --health
python3 tools/manager.py host --systems
python3 tools/manager.py host --lint 0001     # linter سمت سرور
python3 tools/manager.py host --plan 0001     # plan می‌سازد، اعمال نمی‌کند
```

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

### کنسول

```bash
python3 tools/kanban_server.py --port 4310
```

بعد `http://127.0.0.1:4310/`. بدون npm و بدون build — UI یک فایل است. کنسول
هرگز `.agent-work/` را مستقیم نمی‌خواند یا نمی‌نویسد؛ هر چه نشان می‌دهد از یک
فرمان Manager آمده، پس برد نمی‌تواند با store اختلاف پیدا کند.

مسیرهای API همان مسیرهای BarsaAgent است (`/api/repos`, `.../board`,
`.../tasks/:id/run`, `.../answer`, `.../stream`, `/api/tasks/create`)، و
`capabilities` قرارداد `barsa-agent-manager v1` را جواب می‌دهد — یعنی
BarsaAgent موجود هم می‌تواند بدون تغییر به همین manager وصل شود.

## provider نقش‌ها

`.agent-work/config/agent-runtime.yaml`:

```yaml
defaultProvider: manual     # Manager هیچ agent صدا نمی‌زند
providers:
  manual: { enabled: true }
  claude: { enabled: false, command: claude }
```

با `manual`، هر `run` دقیقاً می‌گوید کدام نقش چه فایلی باید بنویسد و همان‌جا
می‌ایستد؛ وقتی فایل‌ها نوشته شدند، `run` بعدی مصرفشان می‌کند. `claude` عمداً
خاموش است: هر اجرا توکن مصرف می‌کند و روشن‌کردنش تصمیم صاحب مخزن است، نه
پیش‌فرض ابزار.

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
