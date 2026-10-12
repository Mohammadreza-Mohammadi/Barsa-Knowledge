# وضعیت فعلی و ادامهٔ کار — تست با Barsa.Ai.Host واقعی

این فایل برای شروع یک گفتگوی تازه است. هدف یک جملهٔ مشخص دارد:
**اولین اجرای واقعی `Barsa.Ai.Host.exe` و اثبات قراردادی که تا امروز فقط از
باینری بازسازی شده.**

همه چیز روی `main` نشسته است. آخرین کامیت‌های مربوط: `86b534c`, `9a44e75`,
`b747646`, `20c7254`, `844dd1c`.

---

## ۱. این مخزن چیست

یک خط لولهٔ کامل، همه با پایتون و فقط کتابخانهٔ استاندارد. هیچ npm و هیچ
وابستگی بیرونی ندارد.

```
source/            باینری‌ها و مستندات بارسا (ورودی خام)
dist/              بستهٔ دانش استخراج‌شده از باینری‌ها
dist-report/       بستهٔ مخصوص «ساخت گزارش»، بازتولیدپذیر
tools/             استخراج‌گر، کامپایلر گزارش، مدیر کانبان، کنسول
.agent-work/       وضعیت کانبان: تسک‌ها، تلاش‌ها، رویدادها
docs/              مستندات
```

برای فهم سریع، به ترتیب این سه را بخوان:

1. `README.md`
2. `docs/kanban.md` — معماری کانبان، ماشین حالت، گیت‌ها
3. `docs/Barsa.Ai.Host.exe.config.example` — **مهم‌ترین فایل برای کار فعلی**

## ۲. کانبان در یک نگاه

هفت لِین، ماشین حالت ۱۵ وضعیتی، چهار نقش (`intake`, `architect`,
`implementer`, `reviewer`) و دو گیت انسانی.

```
ورودی → طراحی → آماده → پیاده‌سازی → بازبینی → آماده اعمال → تمام
                   ↑                                  ↑
            گیت تأیید مشخصات                   گیت تأیید اعمال
```

خروجی نهایی یک `change-batch.json` است که پس از تأیید انسان، از طریق
`Barsa.Ai.Host` روی خودِ بارسا اعمال می‌شود.

پنج گیت تأیید محلی قبل از هر اعمال اجرا می‌شوند: `lint`, `selectors`,
`unknowns`, `scope`, `order`. کدشان در `tools/barsa_kanban/verify.py`.

### نظم شواهد

کل پروژه روی یک قاعده ایستاده: هر ادعا سطح شاهد دارد.

```
CrossVerified > Verified > Observed > Inferred > Unknown
Documented  ← جدا: جملهٔ خودِ وندور در سند، نه استنباط از IL
```

گیت `unknowns` «دقیقاً به اندازهٔ شواهد» سخت‌گیر است. مثلاً تا وقتی فهرست
عملگرهای شرط را نداشتیم، نوشتن هر شرط غیرخالی ممنوع بود؛ از وقتی سند خودِ
Host آن ۱۸ عملگر را گفت، قاعده شد «هر `operator` باید در این ۱۸ باشد».
واژگان در `dist/index/host-vocabulary.json` است و از
`source/barsa-ai-host/startup/` ساخته می‌شود.

**این قاعده را شل نکن.** اگر تستی شکست چون گیت سست‌تر شده، ورودی تست را
عوض کن، نه گیت را — مگر اینکه شاهد تازه‌ای رسیده باشد.

## ۳. کاری که در جریان است

تا امروز قرارداد HTTP این Host کاملاً از IL بازسازی شده و بعد با سند خودِ
وندور (`source/barsa-ai-host/startup/host-api.fa.md`) و کلاینت PowerShell
خودشان (`startup/tools/barsa-ai.ps1`) مقابله شده. هیچ اختلافی پیدا نشد:

```
http://127.0.0.1:17840    هدر X-Barsa-Ai-Key
/health /systems /pull /snapshot /snapshot-diff /lint /plan /apply /apply-status
POST /apply  body = {"planId": "..."}
```

**ولی هنوز هیچ‌کدام یک‌بار هم واقعاً اجرا نشده.** این تنها شکاف باقی‌مانده
است و کار فعلی همین است.

### کجا گیر است

کاربر `Barsa.Ai.Host.exe` را از `F:\Barsa-Knowledge\source` اجرا کرد. سه
خطا به ترتیب دیده شد و هر سه تشخیص داده شده:

| خطا | تشخیص |
|---|---|
| `WinError 10061` از کلاینت ما | host بالا نبود. کلاینت درست کار کرد. |
| `NullReferenceException` در `WaitUntilConnectionReady` | `DBConnectionString` در config نبود، پس `DefaultConfigMgr.ConnectionInfo` تهی شد. |
| `Barsa.Spl.UnreachableCode` در `GlobalConnectionInfo.#l3c` | رشتهٔ اتصالی که کپی شد برای محیط دیگری بود. |

### آنچه دربارهٔ `DBConnectionString` ثابت شده

`Barsa.Ai.Host.exe.config` دو دستهٔ نامرتبط کلید می‌خواهد. کلیدهای
`AiHost.*` را خودِ `AiHostSettings.Load` می‌خواند. سه کلید دیگر را **بارسا**
از همان فایل می‌خواند و بدون آنها host بالا نمی‌آید:

```
DBProvider           System.Data.SqlClient
DBConnectionString   مقدار رمزشدهٔ بارسا
RemotingUsage        None برای اتصال مستقیم به SQL
```

فرمت مقدار سه بخش است، روی `%` جدا می‌شود — همان `ldc.i4.3` در `ParseText`:

```
Sql:<server>/<instance>,Db=<database>  %  V1  %  <payload رمزشده>
```

payload بایت‌های hex جداشده با `-` و طولش مضرب ۱۶ است، یعنی block cipher با
بلوک ۱۶ بایتی. **کلیدش ثابت است و در باینری‌ها حمل می‌شود، نه مشتق از
ماشین**: دو رشتهٔ اتصال از دو محیط کاملاً بی‌ربط، ۱۷ بایت اولشان
بایت‌به‌بایت یکسان است. پس `AllowedComputerName` — که `#l3c` روی
`ConditionClass` ست می‌کند — یک فیلد *درون* payload رمزگشایی‌شده است.

نتیجه: این مقدار را **نه می‌شود دستی ساخت و نه از محیط دیگری آورد.**

**چیزی که ثابت نشده:** کدام شاخه در `#l3c` استثنا را پرت می‌کند. آن متد
control-flow مبهم‌سازی شده و رشته‌هایش از یک resource رمزشده با Hashtable
می‌آیند. رمزگشایی‌اش یک پروژهٔ جداست و کمکی هم نمی‌کند، چون payload معتبر را
فقط خودِ بارسا می‌تواند تولید کند.

## ۴. قدم بعدی

کاربر گفته **روی همین ماشین یک نصب بارسای کارکرده دارد** که به دیتابیس وصل
می‌شود. آن config یک `DBConnectionString` معتبر برای همین کامپیوتر دارد.

### الف) ساخت config

برای اینکه رشتهٔ ۴۸۵ کاراکتری دستی کپی نشود، `tools/make_host_config.py`
نوشته شده. کلیدهای بارسا را عیناً کپی می‌کند، بازخوانی می‌کند و بایت‌به‌بایت
مقایسه؛ ناهمخوانی، فایل را پاک می‌کند. رشتهٔ اتصال را هرگز چاپ نمی‌کند.

```powershell
python tools\make_host_config.py `
  --from "C:\<نصب بارسا>\Barsa.Eorg.Ui.Win.exe.config" `
  --out  "C:\<نصب بارسا>\Barsa.Ai.Host.exe.config" `
  --api-key "<یک کلید>" --user "<کاربر بارسا>" --password "<پسورد>" `
  --workspace "C:\barsa-ai-work"
```

نکته‌های مهم:

- `--from` باید config برنامه‌ای باشد که **روی همین ماشین واقعاً بالا
  می‌آید**.
- `Barsa.Ai.Host.exe` باید **داخل پوشهٔ نصب بارسا** باشد و از همان‌جا اجرا
  شود. `BarsaRuntime.Initialize` اول دنبال config خودِ بارسا می‌گردد.
  اجرا از `source/` همان چیزی بود که به این بن‌بست خورد.
- نسخه را چک کن: `source/Barsa.Ai.Host.exe` نسخهٔ `4.1.203.0` است. اگر نصبِ
  کاربر نسخهٔ دیگری است، exe باید با نصب بخواند.
- `--workspace` را بیرون مخزن گیت بده. host زیرپوشه‌های
  `current/exports/plans/results/snapshots` می‌سازد.
- `AiHost.ApiKey` را خالی نگذار. `IsAuthorized` وقتی کلید خالی باشد مستقیم
  `true` برمی‌گرداند — از IL ثابت شده، حدس نیست.
- خالی‌گذاشتنِ یک مقدار یعنی «پیش‌فرض کد»، نه «هیچ»: `AiHostSettings.Get`
  مقدار را `Trim` می‌کند و اگر خالی باشد پیش‌فرض را می‌گذارد. پیش‌فرض
  `AiHost.Password` رشتهٔ `كاربر محلي سكو` است.

### ب) اجرا

از پوشهٔ نصب بارسا، در یک PowerShell که باز بماند:

```powershell
.\Barsa.Ai.Host.exe
```

موفقیت این سه پیام است (از `AiHttpServer::Run`):

```
Barsa.Ai.Host HTTP listener started at http://127.0.0.1:17840/
Workspace: ...
Barsa.Ai.Host ready: ...
```

پیام‌های شکست و معنای هر کدام:

| پیام | یعنی |
|---|---|
| `Barsa config file was not found: ...` | بیرون پوشهٔ نصب اجرا شده |
| `Barsa login failed for AI Host user:` | `AiHost.UserName`/`Password` را بارسا قبول نکرد |
| `Barsa.Ai.Host is already running.` | نمونهٔ دیگری بالاست (mutex تک‌نمونه‌ای) |
| `NullReferenceException` در `WaitUntilConnectionReady` | `DBConnectionString` نیست |
| `UnreachableCode` در `#l3c` | رشتهٔ اتصال برای این محیط معتبر نیست |

### ج) تست از سمت مخزن

```powershell
$env:BARSA_AI_HOST_KEY = "<همان کلید>"
python tools\manager.py host --health
```

از خروجی `--health` نام سرور و دیتابیس را در `.agent-work/config/connection.yaml`
بنویس. از آن به بعد Manager قبل از هر اعمال این دو را با آنچه host می‌گوید
مقایسه می‌کند و نخوانند، اعمال نمی‌شود.

```powershell
python tools\manager.py host --systems
python tools\manager.py host --preflight 0001
```

`--preflight` به ترتیب: گیت‌های محلی → `/health` → تطابق دیتابیس → سیستم تسک
→ `/lint` سمت سرور → `/plan`. **هیچ‌کدام چیزی نمی‌نویسد.** بدترین حالتش یک
plan است که در حافظهٔ host می‌ماند.

همه سبز شد:

```powershell
python tools\manager.py answer 0001 --approve
```

### د) چیزی که باید گزارش شود

**خروجی خام `/health` و `/plan`.** این تنها چیزی است که شکاف «بازسازی‌شده از
IL» تا «اجرا شد و جواب داد» را می‌بندد.

مخصوصاً **نام فیلدهای دیتابیس در پاسخ `/health`**: کد ما
`database.server` / `database.name` / `database.instance` را انتظار دارد و
این سه از IL بازسازی شده‌اند. سند وندور فقط می‌گوید «database/connection
identity» و نام دقیق فیلدها را نمی‌گوید. اگر نخوانند،
`connection.check_database` می‌گوید «host چیزی نگفت» و **اعمال را متوقف
می‌کند** — خطا به سمت امن می‌افتد، ولی باید اصلاح شود.

## ۵. دو چیز که باید بدانی

### مخزن عمومی است و دو connection string در تاریخچه دارد

از API گیت‌هاب چک شده: `private: false`.

```
source/Barsa.Eorg.Ui.Win-Any.exe.config
source/Dynamics/Barsa.EmailService.exe.config
```

هر دو `DBConnectionString` با آدرس سرور و نام دیتابیس به‌صورت متن ساده و
payload رمزشده دارند. رمزگذاری با کلید ثابتی است که **تمام باینری‌های بارسا
هم در همین مخزن عمومی هستند**.

از کامیت `e9dbbcd` در تاریخچه است، پس حذف فایل کافی نیست. `*.exe.config` به
`.gitignore` اضافه شده ولی فایل‌های track شده را untrack نمی‌کند.

به کاربر اطلاع داده شده و **منتظر تصمیم اوست**. ترتیب پیشنهادی بود: مخزن را
private کن → پسورد آن کاربر SQL را عوض کن → بعد دربارهٔ بازنویسی تاریخچه
تصمیم بگیر. **خودت چیزی را از تاریخچه پاک نکن و فایلی را حذف نکن** مگر
اینکه صریح بگوید.

### git pull روی ویندوز

کاربر این را دید:

```
error: unable to unlink old 'dist/index/systems/7097413550000000101/semantic.json'
```

یک پراسس فایل را باز نگه داشته (ادیتور، سرور Node، آنتی‌ویروس). راه حل:
آن را ببند، بعد `git status` و `git pull origin main`. اگر نشد، فایل را
دستی بردار و `git checkout --` همان مسیر — فایلِ تولیدشده است و چیزی از
دست نمی‌رود.

## ۶. تست‌ها

قبل از هر کامیت، همه را بزن:

```bash
python3 tools/test_kanban.py                    # 56
python3 tools/test_kanban_host.py               # 20
python3 tools/tests/test_host_docs.py           # 10
python3 tools/tests/test_make_host_config.py    # 8
python3 tools/tests/test_system_index.py        # 4
python3 tools/report_compiler.py --check        # بازتولیدپذیری بسته
```

همه الان سبزند. `--check` باید بگوید «۲۵ ورودی، همه هش‌ها می‌خوانند».

اگر `dist/` را از نو ساختی (`tools/extract.py`، حدود ۴۸۰ ثانیه)، بستهٔ گزارش
را هم بازبساز:

```bash
python3 tools/report_compiler.py --scope system=1011413550000000100
```

## ۷. قواعد کار

- پایتون، فقط کتابخانهٔ استاندارد. npm نه.
- روی برنچ `claude/serene-heisenberg-eg8974` کار کن و به `main` مرج کن.
  کاربر صریح خواسته تغییرات روی `main` بنشیند.
- پیام کامیت: چه عوض شد و **چرا**، و اگر چیزی ثابت نشده، همان‌جا بنویس که
  نشده.
- گیت‌ها را برای سبز شدن تست شل نکن.
- چیزی که از IL خواندی و چیزی که استنباط کردی را در مستندات از هم جدا نگه
  دار. این پروژه ارزشش همین است.
