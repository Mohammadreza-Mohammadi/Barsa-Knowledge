# Workflow

## When to use

Workflow برای **process lifecycle persisted** است؛ وقتی Requirement شامل چند مورد از اینهاست:

- actor/assignment
- wait/event
- multi-step transition
- parallel/subprocess
- process history/state
- approval/rejection lifecycle

اگر فقط state transition ساده است و Requirement action/process persisted واقعی نمی‌خواهد، status/enum کافی‌تر است. وجود واژه‌های «ارسال/تأیید/رد» به‌تنهایی کافی نیست؛ اگر کاربر Action کنترل‌شده، actor، transition rule یا history فرآیند می‌خواهد، status دستی جای Workflow نیست.

## Workflow vs BusinessRule

- BusinessRule: رفتار local/short-lived form.
- Workflow: process persisted و actor/time/event.

## Workflow vs Business Status

Runtime workflow state و domain status را خودکار یکی فرض نکن. در سیستم واقعی explicit status synchronization دیده شده است.

## رفتارهای مهم شناخته‌شده

- Choice code با `false` transition را cancel نمی‌کند.
- Condition خروجی‌ها را به‌ترتیب می‌بیند و رسیدن به Else مسیر را همان‌جا انتخاب می‌کند.
- ActivityRun قبل از execution persist می‌شود و failure می‌تواند persisted state باقی بگذارد.
- transaction rollback عمومی مبنای امن طراحی Workflow نیست.

## Requirement → Design → Integration

سه لایه را قاطی نکن:

1. **Requirement:** lifecycle مطلوب، actorها، branchها، form/data intent و acceptance criteria.
2. **Workflow Design:** process graph صحیح مستقل از محدودیت Writer: Actor/Lane، Start/End، Activities، Transitions، Conditions، operational wiring به Entity/View/Rule/Action. برای هر Human task، Design باید performer strategy واقعی را هم مشخص کند (`process starter` یا assignment محاسباتی/Source-backed)؛ Actor فقط با label یک lane عملیاتی نیست. برای خروجی SimpleForm نیز Design باید بین plain output و behavior پیشرفته‌ای که Settings می‌خواهد تفکیک کند.
3. **Integration Support:** پس از کامل‌شدن Design، Support Matrix و exact DX11 تعیین می‌کنند کدام بخش همان Design قابل Change است. limitation Integration نباید Design را silently به status/BusinessRule یا graph ناقص downgrade کند.

قالب فشرده Design در صورت Workflow واقعی:

```text
Workflow: <purpose/name>
Actors/Lanes:
- ...
Flow:
Start → ... → [condition] ... → End
Conditions:
- ...
Operational wiring:
- Activity → Entity/Variable
- Activity → View/Form
- Rule/Action فقط اگر Requirement و contract واقعی دارد
Support Matrix:
- supported / blocked per element
```

## Current Integration

Workflow Read/Export و semantic Write/Verify اکنون expanded create/write Source-backed دارند. exact machine contract فقط در `dataexchange/11-workflow-reference.fa.md` است.

Write v137 شامل Workflow root، Entity-backed variable، Actor، `Start / SimpleForm / Condition / Finish / Fork / Join / ExecuteCode / SubProcess / CustomActivity` و normal/conditional/else/loop transition است. objectهای داخلی graph مرحله‌ای persist و سپس با ID واقعی wire می‌شوند؛ در Start، `StartVariableId` و `SubKey1/VariableId` به همان Variable persisted اشاره می‌کنند. Custom Activity نیز registration caption را در Plan داخل family واقعی deployment به Runtime ID resolve کرده، Settings usage-specific را می‌سازد و back-referenceهای Workflow/Activity را با ID واقعی wire می‌کند. `StarterUserActorDefId` مستقل و می‌تواند `0` یا Actor واقعی باشد.

Actor performer می‌تواند علاوه بر legacy assignment موجود، `انتخاب انجام دهنده` را از calculationهای confirmed بسازد: آغازکننده فرآیند (بدون Settings)، سمت ثابت، کاربر ثابت، Field فرم و فرمول محاسبه (با Settings Entityهای catalog). `AssignmentType` اگر omitted باشد `OnFirstUsage` است؛ explicit `None/OnFirstUsage/OnEachUsage` همچنان semantics مستقل دارند و وجود Assignment را نفی نمی‌کنند. WorkDistribute omission نیز semantic default `همه افراد` دارد و در Plan resolve می‌شود.

SimpleForm `view` اجباری نیست؛ اگر BSDN UX خاص نخواهد Writer `TypeViewId=0` native/default را حفظ می‌کند. خروجی SimpleForm با omission یک Choice ساده با `SettingsId=0` است؛ Settings موجود می‌تواند attach شود و v130 می‌تواند `تنظيمات اتصال فعاليت فرم` usage-specific جدید را با Workflow/Variable/Entity context بسازد.

Runtime هنوز capabilityهای بیشتری مثل Wait/Event و custom registrations متعدد دارد. v130 primitiveهای Fork/Join/SubProcess/ExecuteCode و generic CustomActivity registration+Settings wiring را پوشش می‌دهد. از v137 Workflow graph authority است: Create هیچ Diagram تولید نمی‌کند و `Diagram2` برای success/verify الزامی نیست؛ root edit فعلی `Diagram2` را clear می‌کند و regeneration انجام نمی‌دهد. Capabilityهای Custom فقط وقتی Settings Entity/parameters در Infrastructure Knowledge معلوم باشند ساخته می‌شوند؛ format حدسی تولید نمی‌شود. Graph mutation کامل Workflow موجود همچنان unsupported است؛ فقط root `name/description/isActive` update می‌شود.

Semantic v15 Runtime ID را semantic authority نمی‌داند. Workflow root با `SystemName + WorkflowDef.Title` resolve می‌شود و referenceهای v15 باید selector/context canonical داشته باشند؛ childهای graph می‌توانند local `ref` همان document را برای wiring نگه دارند. wiring با `variableRef/actorRef/fromRef/nextRef` قابل فهم است و Infrastructure refs canonical semantic caption/family را صادر می‌کنند؛ Runtime ID فقط internal plan/apply binding است و در Semantic authority/output portable نقش ندارد.

قاعده mutation:
- Design صحیح ابتدا ساخته می‌شود؛ سپس unsupportedهای local صریح blocker/partial-delivery می‌شوند.
- Workflow واقعی را برای عبور از limitation با BusinessRule/status هم‌معنا فرض نکن.
- اگر lifecycle ساده واقعاً Requirement مستقل را کامل پوشش دهد، status/enum می‌تواند طراحی خودش باشد؛ این تصمیم Design است، نه fallback Integration.


## v135 binding/legacy notes

- Actor performer authority = family + calculation caption resolution → `ActorDefInfo.AssignmentId`; `StarterUserActorDefId` legacy compatibility-only است و AI Writer آن را define/infer/set/modify نمی‌کند.
- Infrastructure registrationها قبل از Workflow mutation با Central Resolver به Runtime IDs immutable resolve می‌شوند؛ Apply registration rediscovery ندارد.
- Standard Finish مستقل از Advanced/Custom registration است؛ Writer terminal semantics را از Caption Custom Activity استنتاج نمی‌کند.


## v137 — Graph authority / defaults / semantic export

- Create: `Infrastructure Preflight → persist graph → reload graph → verify`; هیچ UI Designer/Diagram generator اجرا نمی‌شود.
- Edit فعلی: هر edit واقعی `Diagram2` را clear می‌کند؛ این policy موقت است.
- `assignmentType` omitted → `OnFirstUsage`.
- `workDistribute` omitted → `همه افراد` از family `فرآيند پيشرفته 2.نحوه توزيع كار`, resolved before mutation.
- Workflow root semantic identity از `SystemName + Title` دارد؛ `semanticId` قدیمی استفاده نمی‌شود و child local refs فقط document/export-scoped هستند.
- duplicate Activity/Transition caption مجاز است؛ local refs به caption وابسته نیستند.
