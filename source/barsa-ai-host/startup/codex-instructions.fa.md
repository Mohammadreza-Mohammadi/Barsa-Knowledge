# Codex Project Workflow

## Tool

از مسیر نسبی همین Startup استفاده کن:

```text
<StartupRoot>/tools/barsa-project.ps1
```

فایل‌ها UTF-8 هستند. مسیر دارای `[]` را Literal بخوان.

## Host internal project state

Host برای هر Runtime database state/project directory داخلی نگه می‌دارد. این path implementation detail است و Agent-facing contract نیست:

```text
<workspaceRoot>/projects/<connectionKey>/
  project.json
  systems/<System.Name>/
  changes/
  plans/
  results/
  .barsa/
```

`workspaceRoot` را از `/health` بگیر؛ path حدسی یا project-name اضافی نساز. `<workspaceRoot>/host/current` فقط Working Data داخلی Host است.

## Discovery / Pull / Inspect

- System list را فقط وقتی مأموریت/Workflow فعال نیاز دارد بگیر.
- search روی Name/Caption؛ match مبهم را حدس نزن.
- فقط System لازم را Pull کن.
- در `systems/<System.Name>/` باید مستقیماً محتوای System باشد.
- Inspect: top-level → object مرتبط → فقط فایل‌های لازم.

نمونه:

```powershell
& $tool init
& $tool status
& $tool systems -Query "..."
& $tool pull -SystemIds "<id>[,<id>]"
```

## Knowledge routing

برای design ابتدا `knowledge/00-start.fa.md` و Feature مرتبط را بخوان. برای Change دقیق:

```text
knowledge/deep/change-model.md
knowledge/deep/field-types.md
knowledge/deep/views-layouts.md
knowledge/deep/rules-constraints.md
knowledge/deep/conditions.md
knowledge/deep/reports-folders.md
knowledge/deep/formulas.md
```

همه Deepها را برای هر کار نخوان.

## Canonical Build Flow

برای Role `AR01 system-developer`، Build Intent یا واژه‌هایی مثل «بساز/ایجاد کن» فقط end-to-end mission را آغاز می‌کنند. ترتیب عادی و کوتاه:

```text
Understand
→ BSDN Draft
→ confirm material ambiguities
→ Finalize / Approve BSDN
→ capability + Writer support mapping
→ Change
→ Plan / Apply
→ Runtime Read-back / Verify
```

هیچ Requirement مستقیماً به Change/Package shortcut نمی‌شود. تصمیم design مؤثر در Change اختراع نمی‌شود. اگر Writer بخشی را نمی‌سازد، Requirement در BSDN باقی می‌ماند، بخش‌های مستقل قابل‌ساخت می‌توانند ادامه یابند و verdict کل `partial/incomplete` می‌ماند. `AR03 integration-developer` role-switch داخل Business/System Session نیست؛ Integration gap گزارش و repair در Engineering Session جدا انجام می‌شود.

## Semantic Change

Operationها: `create/update/delete`.

- Update = patch.
- property غایب = no change.
- **Intended-change omission:** هر section/property اختیاری که بخشی از تغییر طراحی‌شده نیست باید اصلاً در payload نیاید؛ empty/default explicit value جای omission نیست. این rule عمومی شامل `selectedRules`, `layout`, `formSettings`, `tabs`, `visibility`, `readonly`, `rules` و سایر local override sectionهاست. Writer/Agent نباید برای «بدون تغییر» `[]`, `{}`, `false`, `0` یا default محلی materialize کند، چون ممکن است override محلی بسازد.
- Delete = explicit.
- tempId فقط در همان logical Batch است. پس از persistence، wave/exchange بعدی object را با Semantic selector/context دوباره resolve کن؛ `temporaryIds/sessionReferenceMap` و Runtime read-back فقط execution/diagnostic evidence هستند و typed Runtime `id` authority Semantic نیست.
- Change را به‌صورت پیش‌فرض per-object/per-report خرد نکن؛ همه تغییرهای ready که قبل از اجرا به Runtime read-back میانی نیاز ندارند تا حد منطقی در یک Batch قرار بگیرند، حتی اگر از نظر موضوعی مرتبط نباشند. dependency قابل حل با `tempId`/Planner به‌تنهایی دلیل شکستن Batch نیست.
- Batch را برای dependency واقعی به نتیجه Runtime، contract نامعلوم/diagnosis، یا پیچیدگی نامعقول بشکن؛ هدف کم‌کردن round-trip با حفظ فهم‌پذیری است، نه بزرگ‌ترین Batch ممکن.
- Feature/property خارج `support-matrix` یا Deep contract را حدس نزن.
- قبل از ساخت Change، Requirement را به Featureهای **ضروری** بشکن و همان `support-matrix` موجود را کنترل کن؛ خروجی capability جداگانه نساز.
- Feature ضروری unsupported را با primitive غیرهم‌معنا **بی‌صدا جایگزین نکن**. فقط replacement واقعاً هم‌معنا مجاز است.
- blocker را تا حد ممکن محلی نگه دار: اگر یک sub-requirement قابل ساخت نیست ولی بخش‌های دیگر مستقل و معتبرند، جزء مشکل‌دار را از Change سالم جدا کن، بقیه را Plan/Apply کن و آن جزء را `blocked/not-built` گزارش کن. کل mutation را فقط وقتی متوقف کن که dependency واقعی یا خطر نتیجه غلط/ناسازگار/مخرب وجود دارد.
- Plan `unsupported/invalid` قبل از mutation یعنی persisted state تغییر نکرده است. contract صحیح را از compact diagnostics/Context/Deep بگیر، همان logical Change کامل را اصلاح و دوباره Plan کن؛ supported subset را فقط برای سبزشدن Apply جدا نکن. Split فقط با persisted-ID requirement، capability unsupported واقعی یا runtime/transaction boundary واقعی مجاز است.

Entity جدید باید Field/Relation موردنیاز Requirement را داشته باشد؛ Field اضافی اختراع نکن.

## Execution

اگر مأموریت فعال صریحاً mutation واقعی است و اطلاعات کافی است **و در AR01 BSDN هدف مصوب + Support Mapping مرحله قبل کامل شده‌اند**:

1. Change را در `changes/` ذخیره کن.
2. BuildPlan بگیر؛ mutation نباید رخ دهد.
3. summary + warning/error/unsupported/dependency را بررسی کن.
4. اگر Plan مطابق Intent و قابل Apply است، بدون confirmation تکراری Apply کن.
5. Result را در `results/` نگه دار.
6. `runtimeReadBack` را با Intent مقایسه کن.
7. یک acceptance check کوتاه از خود Requirement انجام بده: هر نیاز یا `verified`، یا `metadata-only`، یا `blocked/not-built` است. object موجود را معادل requirement کامل فرض نکن.
8. فقط `affectedSystemIds` را Refresh کن.

اگر کاربر Review/Proposal/Plan خواسته Apply نکن.

اگر Apply/ارتباط مبهم شد:

```powershell
& $tool apply-status -PlanId "<planId>"
```

- `applied` → Result برگشتی مرجع است.
- `unknown` → Runtime را Inspect/Refresh کن و قبل از Apply جدید Plan تازه بساز.

## Design defaults مهم

- Feature-specific completion را از Feature doc مربوط بگیر؛ Startup نباید Caseهای اخیر را به Rule عمومی تبدیل کند.
- 1:N/master-detail معمول → `child.singleRelation + parent.reverseSingleListRelation`؛ `listRelation` برای many-to-many/لیست مستقل.
- Formula aggregate → `type:"query"` + Report helper واقعی؛ expression حدسی `Sum(...)` نساز.
- BusinessRule شرط‌دار → `branches[]` + canonical `ComplexCondition`؛ deferred نیست.
- Report relation path → canonical field path؛ shape حدسی نساز.
- Report helper داخلی را فقط اگر Requirement navigation دارد در Folder قرار بده.
- Layout semantic است؛ raw DevExpress XML/pixel زبان Change نیست.

## Verification boundary

`verificationSucceeded` در pipeline فعلی **semantic Metadata verification** است. آن را UI/behavior proof اعلام نکن.

برای requirement رفتاری مثل Formula execution، Report filter/result، Validation، Action یا Workflow transition:
- اگر smoke واقعی Runtime در ابزار موجود انجام شد، نتیجه behavior را گزارش کن.
- اگر ابزار smoke وجود ندارد، Metadata را verified و behavior را `not runtime-smoked` اعلام کن؛ completion رفتاری را حدس نزن.
- `partiallySucceeded` همیشه نیازمند diagnostics و ادامه/اصلاح است، حتی اگر بعضی objectها در read-back موجود باشند.

## Failure handling

```text
failure/partial
→ diagnostics + semantic read-back
→ knowledge/deep
→ Source/Context اگر لازم شد
→ fix cause
→ meaningful verify
```

اگر **Apply/mutation** partial شد یا capability واقعاً unsupported/deferred است، outcome ناقص را صریح نگه دار و payload حدسی نساز. اما Plan failure قبل از mutation را با partial delivery اشتباه نکن: در آن حالت Change کامل اصلاح و retry می‌شود و scope silently کوچک نمی‌شود.

retry کور و check انباشته نساز. Failure منفرد را هم بدون دلیل عمومی به Rule/exception جدید تبدیل نکن؛ ابتدا root cause و primitive پایه را بررسی کن.
