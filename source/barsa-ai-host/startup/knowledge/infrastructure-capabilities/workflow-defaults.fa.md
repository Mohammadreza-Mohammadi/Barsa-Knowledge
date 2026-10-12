# قابلیت‌های پیش‌فرض Workflow، Actor Resolution و Advanced Activity

## وضعیت

- نوع: Host Built-in Capability Knowledge
- membership فعلی فقط از آخرین Excelهای curated
- inactive registrationها از Catalog قابل پیشنهاد حذف شده‌اند.
- Runtime numeric IDها authority نیستند؛ identity دانش semantic است.
- raw code فقط evidence است.

---

# 1. مدل Workflow

```text
WorkflowDef
-> VariableDef[]
-> ActorDef[]
-> ActivityDef[]
-> ChoiceDef[] / Connections
```

Actor خودش performer نیست. Performer از Calculation capability تعیین می‌شود.

---

## Performer registration resolution

Actor performer در Change با همان calculation قابل فهم Barsa بیان می‌شود:

```json
{
  "performer": {
    "calculation": "(کاربر) آغاز کننده فرآیند",
    "parameters": {}
  }
}
```

در Plan، family واقعی `نحوه محاسبه` از relation metadata خود `ActorDefInfo.AssignmentTypeDef` resolve می‌شود. سپس Central Infrastructure Registration Resolver عنوان `calculation` را در Default String Field همان family به Runtime Id همین deployment تبدیل و cache می‌کند.

قواعد مهم:

- Runtime ID داخل Knowledge/Change hard-code نمی‌شود.
- GlobalId در این مسیر استفاده نمی‌شود.
- symbolic capability key ساختگی وجود ندارد؛ عنوان واقعی registration همان locator خوانای Knowledge است.
- Settings contract از metadata registration می‌آید؛ برای مثال `موجوديت پارامتر` اگر TypeDef معتبر بدهد Settings object ساخته می‌شود، و اگر ندهد Settings=`none` است.
- اضافه‌شدن calculation جدید نباید branch caption-specific در `AiWorkflowChangeProvider` لازم داشته باشد.

### StarterUserActorDefId — legacy compatibility only

`StarterUserActorDefId` یک setting قدیمی برای compatibility است و از performer semantics مستقل است. AI Writer:

```text
MUST NOT define it
MUST NOT infer it
MUST NOT assign/set it
MUST NOT modify it
MUST NOT use it to bypass Assignment creation/verification
```

مقدار موجود legacy در read-back می‌تواند دیده/حفظ شود، ولی authority Actor performer فقط `ActorDefInfo.AssignmentId → registration resolved from family + calculation caption` است.


## Actor defaults — v137

برای Actor جدید، اگر `assignmentType` در Change نیامده باشد مقدار مؤثر صریحاً `OnFirstUsage` است. این property enum خود Product است و برای آن Infrastructure registration ساخته/resolve نمی‌شود.

`WorkDistributeType` Infrastructure-backed است. family واقعی آن:

```text
فرآيند پيشرفته 2.نحوه توزيع كار
```

است. در omission مقدار semantic پیش‌فرض:

```text
همه افراد
```

است و باید در Plan با Central Infrastructure Registration Resolver به Runtime Id همان deployment تبدیل شود. `0` default معتبر AI نیست.

Catalog واقعی exportشده برای این family:

- `همه افراد` — active — **default**
- `انتخاب اولين فرد` — active
- `انتخاب اولين فرد داخل سيستم` — inactive
- `همه افراد داخل سيستم` — active

این captionها عین `عنوان`های export واقعی هستند. Runtime numeric IDها فقط evidence همان deployment هستند و وارد Knowledge نمی‌شوند. Writer از captionها behavior switch نمی‌سازد؛ caption فقط locator semantic برای Central Resolver است.

# 2. Wiring Actor / Performer

```text
WorkflowActorDef
-> انتخاب انجام‌دهنده
   -> نحوه محاسبه
   -> optional زیر‌فرم Settings
```

نمونه واقعی دو حالت را تأیید کرده است:

- Formula Calculation دارای Settings object است.
- `(کاربر) آغاز کننده فرآیند` Settings object ندارد.

---

# 3. Calculation Catalog قابل پیشنهاد

چهار registration که در Excel اخیر `غیرفعال = درست` بودند حذف شده‌اند:

- `(کاربر) بدست آوردن سمت مرتبط`
- `(سمت/کاربر) لیست`
- `(کاربر) انتخاب سمت`
- `انجام دهنده یک فعالیت`

Catalog فعال فعلی:

## `(سمت) بدست آوردن سمت مرتبط`

Purpose:
یافتن Position نسبت به یک Actor/Position مبنا با استفاده از Rule جستجوی ساختار سازمانی.

Use when:
performer یک سمت سازمانی relative به Actor دیگری است.

Do not use when:
User ثابت، Position ثابت یا مقدار مستقیم Field کافی است.

Settings Entity:
`محاسبه-بدست آوردن سمت مرتبط`

Parameters:
- `با شروع از نقش` -> Workflow Actor
- `قاعده بدست آوردن سمت مرتبط` -> Search Rule

Context:
Workflow context به Settings تزریق می‌شود.

Selection:
قبل از Formula برای organizational lookup ترجیح دارد.

---

## `(سمت/کاربر) فیلد فرم`

Purpose:
گرفتن User/Position از Field یکی از Variable/Formهای Workflow.

Use when:
خود داده فرم performer را نگه می‌دارد.

Settings Entity:
`محاسبه-فیلد فرم`

Parameters:
- `فرم فرآیند` -> Workflow Variable
- `فیلد` -> Metadata Field

Do not use when:
performer باید با hierarchy یا query محاسبه شود.

---

## `(سمت/کاربر) گزارش`

Purpose:
محاسبه performer از نتیجه Report.

Use when:
mapping performer واقعاً query/report-based و پیچیده است.

Settings Entity:
`محاسبه-گزارش`

Parameters:
- `گزارش` -> Report
- `فرم فرآیند` -> optional Workflow Variable context
- `نحوه بدست آوردن انجام دهنده` -> نحوه برداشت نتیجه

Do not use when:
رابطه مستقیم Field یا organizational lookup کافی است.

---

## `(سمت/کاربر) فرمول محاسبه`

Purpose:
محاسبه User/Position با Code.

Use when:
هیچ capability semantic مناسب‌تر نیاز را پوشش نمی‌دهد.

Settings Entity:
`محاسبه-فرمول محاسبه`

Parameters:
- `کد`
- `فرم فرآیند` -> optional Workflow Variable context

Rule:
Formula fallback است، نه انتخاب اول.

---

## `(سمت) انتخاب سمت`

Purpose:
انتخاب Position ثابت.

Settings Entity:
`محاسبه-سمت ثابت`

Parameter:
- `انتخاب سمت` -> Position / Work Center

Use when:
performer واقعاً ثابت است.

---

## `(کاربر) انتخاب کاربر`

Purpose:
انتخاب User ثابت.

Settings Entity:
`محاسبه-کاربر ثابت`

Parameter:
- `انتخاب کاربر` -> User

Use when:
performer واقعاً User مشخص است.

---

## `(سمت/کاربر) انتخاب گروه امنیت`

Purpose:
استفاده از اعضای یک Security Group به‌عنوان performer set.

Settings Entity:
`محاسبه-گروه امنیت`

Parameter:
- `گروه امنیت` -> Security Group

Use when:
business intent واقعاً گروه امنیتی موجود را هدف گرفته است.

---

## `(سمت) آغاز کننده فرآیند`

Purpose:
استفاده از Position آغازکننده Workflow.

Settings Entity:
`محاسبه-سمت آغاز کننده فرآیند`

Parameter:
- `در نظر گرفتن اولین سمت کاربر در صورت چند سمتی`

Use when:
performer باید Position starter باشد.

---

## `(کاربر) آغاز کننده فرآیند`

Purpose:
استفاده از User آغازکننده Workflow.

Settings:
`none`

رفتار:
مستقیماً starter user را از WorkflowRun می‌گیرد.

نکته:
مقدار raw `27` در ستون موجودیت پارامتر semantic contract لازم برای Build نیست؛ این capability در usage واقعی بدون Settings object مشاهده شده است.

---

# 4. Actor selection by semantic fit

تمام registrationهای active این Catalog هم‌سطح و معتبرند. انتخاب فقط با intent و semantic fit انجام می‌شود؛ برای نمونه:

- User/Position ثابت → capability ثابت متناظر
- آغازکننده Workflow → starter capability متناظر
- performer موجود در داده فرم → field-form capability
- جستجوی ساختار سازمانی → organizational lookup capability
- query/report-based performer → report capability
- منطق محاسباتی واقعاً code-based → formula capability

این فهرست ranking یا priority نیست.

---

# 5. Advanced Activity wiring

Advanced Activity با `registration` واقعی خود در family `نوع فعالیت پیشرفته` resolve می‌شود. Writer نباید از Caption registration behavior مثل terminal بودن را استنتاج کند. Standard `type=finish` مستقل و registration-free باقی می‌ماند؛ Custom Activity registration و Settings Type فقط از metadata واقعی registration wire می‌شوند.


```text
WorkflowActivityDef.Info
-> Custom Activity Registration
-> Settings object
```

Settings object معمولاً به Activity/Workflow context متصل است.

Builder باید Settings Entity همان registration را بشناسد و object usage-specific از آن بسازد.

---

# 6. Advanced Activity Catalog فعال فعلی

آخرین Excel 11 registration را در scope دارد و هیچ‌کدام به‌صورت صریح inactive=true ثبت نشده‌اند.

## انتظار زمانی

Purpose:
متوقف‌کردن flow تا زمان/بازه زمانی مشخص.

Settings Entity:
`CATimeEventCatch`

Behavior:
timer-based suspension/resume.

Use when:
ادامه Workflow به زمان وابسته است.

Do not use when:
صرفاً delay UI یا logic synchronous لازم است.

---

## انتظار رخداد

Purpose:
suspend کردن Workflow تا Event موردنظر دریافت شود.

Settings Entity:
`CAEventCatch`

Parameters/semantics:
- Event
- optional target/receiver formula
- optional Workflow Variable context
- optional post-receive code

Use when:
continuation asynchronous و event-driven است.

---

## ارسال رخداد

Purpose:
publish/throw کردن Event.

Settings Entity:
`CAEventThrow`

Parameters/semantics:
- Event
- optional receiver/target formula
- optional parameters formula
- optional Workflow Variable context

Use when:
Workflow باید event-based integration/notification trigger کند.

---

## پایان

Purpose:
پایان branch/Workflow بر اساس semantics این activity type.

Settings Entity:
`CAIntermediateEnd`

Parameters:
برای usage observed پارامتر business خاصی لازم نبود؛ Settings object context را نگه می‌دارد.

Use when:
همین advanced end semantics لازم است؛ برای End استاندارد Writer ابتدا primitive استاندارد بررسی شود.

---

## پر کردن فرم

Purpose:
Form-oriented Activity با خروجی‌هایی که می‌توانند از configuration فرم تعیین شوند.

Settings Entity:
`CAForm`

Use when:
behavior خاص این Custom Activity لازم است؛ Human Task ساده را بی‌دلیل با آن جایگزین نکن.

---

## نمایش پیغام

Purpose:
نمایش message محاسبه‌شده برای Actor/User مربوط و branch کردن نتیجه بر اساس نوع dialog.

Settings Entity:
`فعالیت-نمایش پیغام`

Semantic parameters:
- پیام / formula
- فرم/context
- Actor/User
- نوع dialog

Use when:
داخل Workflow واقعاً interaction message/dialog لازم است.

Do not use when:
Business validation یا Human Task معمولی موردنظر است.

---

## نمایش Progress

Purpose:
اجرای code/operation همراه Progress UI برای Actor مربوط.

Settings Entity:
`فعالیت-نمایش Progress`

Semantic parameters:
- پیام
- فرم/context
- Actor/User
- execution code

Use when:
عملیات synchronous/interactive طولانی به progress UI نیاز دارد.

---

## اخذ تائیدات

Purpose:
اجرای behavior reusable اخذ تأییدات.

Settings Entity:
`فعالیت - اخذ تائیدات`

Confirmed semantic parameters:
- `قاعده` -> Rule Definition
- `نقش درخواست دهنده` -> Workflow Actor
- `فرم مورد استفاده` -> Workflow Variable

Use when:
زیرساخت خاص approval behavior لازم است.

Do not use when:
یک Human Task ساده + Choice استاندارد requirement را کامل پوشش می‌دهد.

---

## دروازه اخذ تائیدات

Purpose:
اجرای gateway/coordination خاص approval که از configuration approval و لاگ اجرا برای انتخاب actor/branch استفاده می‌کند.

Settings Entity:
`فعالیت-دروازه موازی`

Use when:
همین approval-gateway behavior موردنیاز است.

Do not use when:
Gateway استاندارد Workflow کافی است.

---

## مرزی زماندار

Purpose:
Boundary timer event با رفتار زمان‌دار و rollback/interrupt branch مربوط.

Settings Entity:
`رویداد- مرزی زماندار`

Semantic parameters observed:
- واحد
- مقدار

Use when:
boundary timeout behavior این registration لازم است.

---

## مرزی زماندار 2

Purpose:
Boundary timer event مبتنی بر TimerManager.

Settings Entity:
`CATimeEventCatch`

Use when:
semantic رفتار registration با requirement timeout/boundary مطابقت دارد.

---

# 7. ساخت Advanced Activity

```text
Design intent
-> select registration from this Catalog
-> resolve Settings Entity semantic identity
-> create Settings object
-> set semantic parameters
-> wire Settings to Activity
-> wire Activity choices/connections
-> read-back / verify
```

---

# 8. Human Task rule

```text
BSDN performer intent
-> choose Actor Calculation
-> create optional Settings
-> create/wire Actor
-> create Human Task
-> choices/outcomes
-> verify
```

Agent برای فهم mechanism نباید Workflowهای Systemهای دیگر را scan کند.

---

# 9. نکات انتخاب

- Advanced Activity با Actor Calculation یکی نیست.
- Activity اختصاصی فقط زمانی انتخاب شود که behavior اختصاصی آن لازم است.
- raw source code برای Build reasoning استفاده نشود؛ semantic description این سند authority است.
- Settings Entity/parameters باید برای ساخت object واقعی در دسترس باشند.
