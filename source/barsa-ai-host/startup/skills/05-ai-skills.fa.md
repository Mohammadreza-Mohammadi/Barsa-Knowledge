# AI Skills Architecture

## هدف و اصول

این سند مرجع اصلی معماری مهارت‌های AI پروژه است. Status هر Skill بلوغ عملیاتی فعلی پروژه را نشان می‌دهد؛ نه capability خود SystemBuilder و نه authority یک claim دانشی.

اصول ثابت:

- هر Skill ورودی، خروجی، مسئولیت و مرز مستقل دارد.
- Requirement truth خواسته/قید است؛ Overall + Detailed BSDN scopes Desired Business/System Design Authority هستند.
- BSDN authority به canonical **System/Section Design Scope** تعلق دارد، نه physical Markdown file.
- canonical Markdown BSDN artifact برای portable continuation لازم است؛ Chat substitute آن نیست.
- Semantic Model/Runtime/Previous Change/Current Progress/Conversation memory Design Authority موازی نیستند.
- SK04 فقط Current Build Scope از Finalized/Execution-Authorized BSDN scopes + relevant Support Mapping را به exact Actions تبدیل می‌کند و Business Design تازه نمی‌سازد.
- Planning فقط validation/dependency/order فنی را انجام می‌دهد؛ Apply فقط Plan را اجرا می‌کند.
- Verify actual state را در hierarchy Step/Wave → Section → System → Final Delivery در برابر Current Target BSDN scopes می‌سنجد.
- فرآیند بزرگ می‌تواند Skillها را از طریق contract ورودی/خروجی orchestration کند، بدون ادغام مسئولیت‌ها.

## روش عملیاتی استاندارد AI

```text
Sources
→ SK01 System/Section Requirements
→ Requirement Completeness + Minimality for Current Delivery Scope
→ SK02 Overall BSDNs per System
→ Cross-System/Section Skeleton Check
→ SK02 Detailed BSDNs per Section
→ BSDN Completeness + Minimality
→ Support Mapping
→ Execution Authorization / Current Build Scope
→ SK04 Generate SystemBuilder Actions + expected Verify
→ SK05 Plan / core contract validation
→ SK06 Apply
→ SK07 Read Actual State
→ SK08 Step/Wave → Section → System → Final Delivery Verify
→ Verified Release
```

Authorityها جدا هستند: Requirement خواسته/قید، BSDN Desired Design، Runtime actual state، Support Mapping feasibility و Action/Package implementation mechanism است.

### Feature Certification orchestration (AR06)

Feature-by-feature certification **Skill جدید نیست**. `AR06 feature-worker` از Skillهای موجود استفاده می‌کند:

```text
SK03 Full/Semantic read evidence
→ SK04 actions for isolated reconstruction when needed
→ SK05 Plan/contract validation
→ SK06 Apply
→ SK07 Read-back
→ SK08 Verify
→ SK09 case/governance/evidence continuity
```

Designer Evidence و روش certification در `knowledge/feature-evidence.fa.md` تعریف می‌شود. AR06 patch Integration انجام نمی‌دهد؛ gap را به AR03/Implementor route می‌کند. `SK01/SK02` فقط وقتی وارد شوند که meaning همان feature واقعاً به Requirement/Design reasoning نیاز داشته باشد.

سه Scope:

```text
Solution Landscape
Current Delivery Scope
Current Build Scope
```

Current Delivery Scope قبل از Build Requirement/Design complete/minimal و cross-checked می‌شود. Current Build Scope subset یا Wave چندSection/چندSystem است.

### 1. SK01 — Requirement Analysis

SK01 Sources ناهمگون را به Requirement canonical System/Section تبدیل می‌کند:

```text
artifact:requirements/<system>/<section>.md
```

Requirement Business-oriented است و Writer/API/runtime ID را طراحی نمی‌کند. هر موضوع material یکی از `Captured / Not Applicable / Blocking Ambiguity / Deferred-Non-blocking / Missing Information` است. قبل از SK02 detailed، Requirement کل Current Delivery Scope completeness/minimality می‌شود.

### 2. SK02 — Overall + Detailed System Design

ابتدا برای همه Systemهای relevant Overall BSDN:

```text
artifact:design/overall/<system>-BSDN.md
```

که Entity/Relation Skeleton را همزمان با Process/Actor/Form/Output Skeleton refine می‌کند. سپس cross-System/Section ownership/dependency check.

بعد Detailed BSDN هر Section:

```text
artifact:design/systems/<system>/<section>-BSDN.md
```

`One Design Fact → One Canonical Owner`; split=`Move, Not Copy`; Process/Workflow BSDN مستقل default نیست. Design=`Complete in Elements / Sparse in Obvious Properties`.

### 3. Support Mapping

بعد از Design Current Delivery Scope و قبل از Build. statusها بیرون Desired BSDN می‌مانند: `Supported / Partial / Unsupported / Unknown / Deployment Unavailable / Contract Ambiguous`.

Core capability limitation مجوز redesign نیست. Optional/external/deployment/provider capability می‌تواند early-probe شود؛ exact core contract shape قبل از persistence validate می‌شود.

### 4. Pre-SK04 invariant

```text
Requirements current for Current Delivery Scope
+ Overall/Detailed BSDNs current
+ cross-scope consistency passed
+ completeness/minimality passed
+ blocking material ambiguity = 0
+ Support Mapping relevant exists
+ Current Build Scope known
+ Execution Authorization exists
+ canonical Markdown artifacts current
```

failure → SK04 MUST NOT RUN. این orchestration invariant است، نه Host gate.

### 5. Generate Actions / Plan / Apply

SK04 exact Actions و expected read-back را از BSDN + Knowledge + Support Mapping + runtime technical context می‌سازد؛ Design جدید نمی‌سازد.

SK05 exact shapeها مثل performer/condition/relation/update/delete/local-ref را قبل از persistence validate و dependency/order را Plan می‌کند.

SK06 همان Plan را با ContinueIndependent policy فعلی اجرا می‌کند.

### 6. Read-back / Verify

بعد از هر step material: `Apply → Read-back → Verify`.

Verify hierarchy:

```text
Step/Wave
→ Section
→ System
→ Final Current Delivery Scope
```

Previous Change design oracle نیست. Runtime actual-state truth است.

### ساخت سیستم جدید

Requirement/Design کل Current Delivery Scope قبل از Build کامل می‌شود؛ Build بعداً Section-oriented و dependency-aware wave می‌شود. Future غیرمسدودکننده Build جاری را block نمی‌کند.

### تغییر سیستم موجود

Runtime/Semantic فقط actual-state evidence است. canonical Requirement/BSDN affected scopes restore/update می‌شوند؛ material drift روشن؛ سپس Support Mapping/Actions/Build/Verify.

### مسیریابی خطا

- Requirement gap/ambiguity → SK01
- Design ambiguity/ownership/completeness → SK02
- Integration capability/support → Support Mapping
- Action mapping → SK04
- contract/dependency/preflight → SK05
- mutation/recovery → SK06 + SK07
- mismatch/evidence classification → SK08

### Continuation / operational state

Operational artifacts خارج BSDN:

```text
artifact:operations/current-progress.md
artifact:operations/support-mapping/*
artifact:operations/releases/*
```

Continuation: current-progress → Overall System BSDNs → relevant Requirement/Section BSDNs → referenced owner scopes → Support Mapping → Runtime only for actual state → regenerate Actions. Conversation/Previous Package substitute artifacts نیستند.

### Partial mutation

failure after persistence → STOP → SK07 read-back → reconcile → evidence-based recovery. Blind retry ممنوع. `mutationApplied` پس از اولین persistence true می‌ماند.

### Technical fix

Writer/Verifier/Adapter fix بدون intended Design change → Requirement/BSDN unchanged.

### Terminology

```text
Section = Business ownership/planning unit
Current Delivery Scope = design-before-build scope
Current Build Scope / Wave = execution subset, possibly multi-section/system
مرحله ساخت = technical phase ordering
```

`Wave` identifier داخلی موجود rename نمی‌شود.

### منابع روش جاری

Normative BSDN contract از `knowledge/bsdn/*`، Design guidance از `knowledge/design.fa.md`، technical exact contract از DataExchange Source-backed docs و Support Mapping/Runtime evidence از scope جاری مصرف می‌شوند.

## چرخه KM v1 — Full Generate و Incremental Update

KM یک Cache استنتاجی است و تولید متن آن **Skill-level AI responsibility** است؛ Host فقط storage/lifecycle را فراهم می‌کند. Apply هیچ KM را خودکار تولید یا invalid نمی‌کند. `AR01` فقط در **stable mission checkpoint نهایی**—آخرین mutation لازم انجام‌شده، correction باز صفر، cumulative Verify نهایی موفق و Outcome Ledger بدون pending قابل‌اجرا—مگر opt-out صریح User، SK10 را به‌صورت پیش‌فرض orchestration می‌کند. KM schema و target typeهای v1 تغییر نکرده‌اند.

قرارداد اولیه `AiKnowledge.Content`:

```json
{
  "summary": "...",
  "keyPoints": ["..."],
  "drillDown": [
    {
      "targetType": "entity",
      "targetId": 123,
      "semanticSelector": "#Meta02|Person",
      "reason": "..."
    }
  ]
}
```

هر `drillDown` باید `targetType + targetId` قابل مصرف توسط Host داشته باشد. `targetType` فقط `system / entity / field / view / report / workflow` است؛ Relation target مستقل ساخته نمی‌شود. `semanticSelector` فقط اگر برای human/drill-down hint در KM لازم باشد از selector canonical `#...` گرفته می‌شود؛ `semanticId` قدیمی تولید/مصرف نشود. بخش خالی Serialize نمی‌شود. `IsValid=true` فقط KM جاری و قابل مصرف است؛ `IsValid=false` Cache قبلی را از مصرف جاری خارج می‌کند ولی Content آن برای incremental regeneration حفظ می‌شود.

**مرز مهم:** `drillDown` یک navigation/knowledge pointer است؛ اما برای **Full Generate(System)** یک Rule محدود و صریح داریم: targetهای اصلی که همان اجرا برای System `drillDown` انتخاب می‌کند باید در همان Full Generate، فقط در سطح مستقیم زیر System، Child KM مستقل materialize شوند. این Rule recursive نیست؛ `drillDown`های داخل Child KMها الزام eager materialization ندارند. targetهای انتخاب‌نشده نیز همچنان می‌توانند بعداً lazy ساخته شوند.

### شروع context و Full Generate سطح System

برای شروع کار روی یک System، KM اولین context سطح System است. اگر System KM وجود ندارد:

```text
GET /systems
→ انتخاب System id
→ GET current System KM
→ اگر موجود بود: Use System KM as first context
→ اگر missing بود: obtain Full System Semantic با capability موجود system-semantic
→ analyze complete current System Semantic
→ importance-based selection of direct knowledge targets
→ generate selected Child KMs in memory
→ generate concise System KM with matching selective drillDown
→ one Package km-save batch: selected children first, System last
→ verify aggregate storage result
→ Use System KM
```

در EM01 این flow **یک Package persistence exchange** دارد، نه یک exchange برای هر Child. action جدیدی ساخته نمی‌شود؛ exact single+batch transport contract متعلق به `agent/package-protocol.fa.md` و generated `chat-protocol.json` است.

`Full Generate(System)` یعنی knowledge hierarchy اولیه از وضعیت کامل فعلی System بازسازی می‌شود: System KM + فقط یک لایه Childهای مهم منتخب. این به معنی ساخت KM برای همه metadata یا materialization recursive hierarchy نیست. `Full Generate(Entity/View/Report/Workflow/Field)` target-local همان Target باقی می‌ماند.

### System drillDown — hierarchical + selective + materialized first layer

System KM باید concise knowledge map باشد:

```text
summary سطح System
+ keyPoints سطح System
+ selective drillDown pointers
```

از Full System Semantic، targetهای مهم در typeهای موجود بررسی می‌شوند:

- core/business-critical Entity؛
- View مهم برای operation/UX/workflow؛
- Report مهم، به‌خصوص user-facing/business-significant؛
- Workflow مهم؛
- Field فقط وقتی knowledge مستقل، reusable و واقعاً باارزش دارد.

Selection بر **اهمیت برای فهم System** تکیه می‌کند: domain centrality، business significance، operational importance، نقش در Workflow، user-facing بودن، dependency/reuse significance، reference از objectهای مهم دیگر و business behavior قابل‌توجه. اندازه/complexity خام مثل تعداد Column/Parameter/Condition یا بزرگ‌بودن View فقط signal کمکی است و به‌تنهایی دلیل انتخاب نیست. Reportهای internal/helper فقط وقتی انتخاب می‌شوند که evidence مستقل business/system importance داشته باشند. quota ثابت و all-object generation ممنوع است.

برای هر target انتخاب‌شده، Child KM target-specific از همان Full Semantic موجود تولید می‌شود؛ pull جداگانه برای هر Child ممنوع است وقتی context کافی حاضر است. System KM جزئیات structure/interaction/parameter/stage Childها را dump نمی‌کند؛ همان target detail در Child KM قرار می‌گیرد و System فقط summary/keyPoints سطح System و pointer را نگه می‌دارد.

محتوای Child:

- **Entity:** purpose/domain role، structure/behavior مهم، dependencyهای مهم و drill-down معنادار.
- **Field:** فقط business meaning/behavior/dependencies مستقل و reusable.
- **View:** user/business purpose، interaction/sectionهای مهم و owner Entity/context.
- **Report:** business purpose، data/context، parameter/behavior عمده در سطح Semantic و navigation significance در صورت user-facing بودن.
- **Workflow:** purpose، stage/transitionهای اصلی و participating targetهای مهم.

KM جای exact payload/property serialization را نمی‌گیرد؛ آن قرارداد متعلق به DataExchange است.

### Batch persistence و completion

بعد از generation در memory، request batch با این ordering ساخته می‌شود:

```text
selected Child KM 1
selected Child KM 2
...
selected Child KM N
System KM
```

تمام Childهای اصلی System drillDown باید item متناظر داشته باشند و System item **آخر** باشد. Host قبل از mutation کل shape را validate می‌کند و سپس itemها را از endpoint storage موجود sequentially اجرا می‌کند. اگر Child save fail/ambiguous شود، itemهای بعدی اجرا نمی‌شوند و System KM جدید نباید نوشته شود. موفقیت‌های قبلی partial result هستند و پنهان نمی‌شوند. transaction سراسری تازه‌ای فرض نمی‌شود.

row reuse lifecycle موجود per item حفظ می‌شود: current row → reuse؛ correlated previous-invalid → reuse؛ single invalid row → reuse؛ legacy ambiguity → surfaced. برای Full Generate لازم نیست برای N target ابتدا N بار `km-current` بگیری؛ storage write با target و `id=0/omitted` reuse semantics موجود را اعمال می‌کند.

Completion فقط وقتی مجاز است که aggregate batch `succeeded` باشد و همه‌ی selected Childها و System item موفق باشند. wording مناسب:

> System KM و Child KMهای مهم منتخب از Semantic کامل فعلی تولید و در یک Package exchange ذخیره شدند؛ System KM به‌عنوان parent آخر ذخیره شد.

اگر deployment اساساً AI Knowledge storage موجود را ندارد، result `unavailable` یک **availability state** است: delivery/Verify خود System می‌تواند موفق باقی بماند و KM به‌صورت `unavailable` گزارش می‌شود. اگر storage وجود دارد ولی mapping/identity/persistence یک target منتخب fail شود، KM `incomplete` است؛ target مهم از selection/drillDown حذف نمی‌شود. `partiallySucceeded`، `ambiguous`، target-resolution `failed` یا storage-present failure نباید «KM کامل شد» گزارش شوند.

### Lazy child KM برای targetهای انتخاب‌نشده

Lazy behavior حذف نمی‌شود. وقتی بعداً مأموریت به targetی نیاز دارد که در Full Generate اولیه انتخاب/materialize نشده است:

```text
System/Parent KM یا evidence target
→ km-current(child)
→ اگر موجود بود: Use Child KM
→ اگر missing بود: obtain sufficient Semantic با capability واقعی
→ Full Generate همان Child target
→ km-save(child)
→ check storage result
→ Use Child KM
```

Capability retrieval جعل نمی‌شود:

- **Entity:** `target-semantic(entity)` در صورت نیاز.
- **View / Report / Workflow:** direct `target-semantic` advertised نیست؛ Full/System Semantic owning System reuse یا pull می‌شود و child دقیق از nesting/context + selector canonical پیدا می‌شود. Runtime `targetId` فقط برای KM storage/lifecycle فنی است و `semanticId` قدیمی استفاده نمی‌شود. owning System حدس زده نمی‌شود.
- **Field:** direct `target-semantic(field)` اختراع نمی‌شود؛ Semantic owner Entity/System استفاده می‌شود.

### Incremental Update

Incremental فقط KM rowهای existing/materialized affected + parent System لازم را maintain می‌کند. missing Child KM صرفاً به‌دلیل propagation ساخته نمی‌شود؛ استثنای materialization انتخابی فقط Full Generate(System) اولیه است.

اگر چند KM موجود affected باشند، EM01 می‌تواند همان `km-save` batch را برای:

```text
affected existing Child KM(s)
→ parent System KM last
```

استفاده کند تا persistence یک Package exchange باشد. هر item همان lifecycle storage و ambiguity behavior single save را دارد.

نمونه‌ها:

- Field change و Entity KM موجود → Entity KM update + System KM update؛ اگر Entity KM missing است فقط برای propagation create نشود.
- Report/View/Workflow KM موجود و affected → own KM update + parent System در صورت dependency روشن؛ اگر own KM missing است propagation آن را materialize نمی‌کند.
- fallback Full فقط همان Target را rebuild می‌کند، مگر Create System یا مأموریت صریح `Full Generate(System)` hierarchy initialization باشد.

### Default maintenance trigger after System delivery

در Role `AR01`، پس از final Apply + Runtime Read-back + Verify outcome، SK10 به‌صورت پیش‌فرض اجرا می‌شود مگر User **صریحاً** opt-out کرده باشد. این continuation نیازمند prompt دوم نیست و Host hook/background job نیست.

- **Create System:** `Full Generate(System)` از Semantic/current state نهاییِ واقعی پس از Verify.
- **Edit System:** `Incremental Update` از Actual Delta و KMهای materialized affected؛ اگر previous/current evidence برای incremental کافی یا قابل‌اعتماد نیست، Full مناسب همان scope انجام می‌شود.
- intended Change/Plan منبع truth KM نیست؛ اگر correction انجام شد، KM فقط از state نهایی پس از correction/read-back ساخته می‌شود.
- `KM=unavailable` فقط برای نبود واقعی storage پذیرفته است و System delivery را fail نمی‌کند. storage-present integration failure برابر `KM=incomplete` است و selection را کوچک نمی‌کند.

### Lifecycle عملیاتی

```text
Change
→ Read Actual Delta
→ تشخیص affected materialized KM + parent لازم
→ Invalidate همان KMهای affected
→ Read previous invalid KM as needed
→ Incremental Update when sufficient
→ otherwise Full Generate همان Target
→ one single/batch km-save according to affected set
→ verify storage result
```

Invalidate فقط validity را تغییر می‌دهد و Content را حفظ می‌کند. regeneration برای Target موجود row تازه نمی‌سازد؛ ambiguity legacy به Agent برگردانده می‌شود و candidate حدس زده نمی‌شود. Host storage lifecycle را فراهم می‌کند؛ selection/generation/content همچنان مسئول Skill است.

### Completion wording

Full Generate(System) موفق فقط پس از persist شدن تمام selected first-level Child KMها و سپس System KM completion می‌شود. Lazy materialization targetهای انتخاب‌نشده completion جداگانه‌ی همان Target است و hierarchy را recursive نمی‌کند.

## روش رسمی ارزیابی و بهبود Skillها

ارزیابی و بهبود AI باید Skillمحور و با کنترل انسانی متناسب با ریسک باشد. شکست یک سناریوی چندمرحله‌ای به‌تنهایی نشان نمی‌دهد همه Skillهای زنجیره معیوب‌اند؛ ابتدا باید منشأ اختلاف مشخص شود و اصلاح در کوچک‌ترین Skill مسئول انجام شود.

روند استاندارد:

```text
سناریو
→ اجرا
→ مشاهده اختلاف
→ تشخیص Skill مسئول
→ کوچک‌ترین اصلاح
→ ارزیابی مجدد همان سناریو
→ کنترل پسرفت روی چند سناریوی قبلی مرتبط
→ در صورت نیاز تأیید انسانی
```

### طبقه‌بندی منشأ خطا

قبل از هر اصلاح، اختلاف حداقل در یکی از این حوزه‌ها طبقه‌بندی شود:

- `Requirement` — ورودی، scope، قید یا acceptance criteria مبهم/ناقص/اشتباه بوده است.
- `Knowledge` — دانش لازم ناکافی، قدیمی، کم‌اعتبار یا با provenance نامشخص بوده است.
- `Semantic Model` — Read/Projection/Mapping معنایی وضعیت واقعی را درست نمایش نداده است.
- `System Design` — مدل انتخاب‌شده Requirement را درست یا با کمترین پیچیدگی پوشش نداده است.
- `Support Matrix` — capability خود SystemBuilder و capability جاری Integration اشتباه تشخیص داده شده‌اند.
- `Change Construction` — Design مصوب به Change درست تبدیل نشده است.
- `Plan` — validation/dependency/order فنی نادرست بوده است.
- `Apply` — اجرای Plan یا handling خطای اجرایی نادرست بوده است.
- `Read` — وضعیت واقعی قبل/بعد از تغییر نادرست یا ناقص خوانده شده است.
- `Verify` — expected و actual درست مقایسه یا verdict درست صادر نشده است.
- `AI Method` — orchestration، routing، confidence handling یا رعایت مرز Skillها مشکل داشته است.

این طبقه‌بندی diagnosis است، نه مجوز تغییر همه حوزه‌های مرتبط. اگر evidence کافی برای تعیین منشأ وجود ندارد، ابتدا داده لازم جمع شود و اصلاح حدسی انجام نشود.

### قواعد اصلاح و کنترل پسرفت

- اصلاح در کوچک‌ترین Skill یا قرارداد دانشی مسئول انجام شود؛ Skillهای دیگر فقط وقتی تغییر کنند که evidence مستقل نشان دهد خود آنها نیز defect دارند.
- هر اصلاح مهم با همان سناریویی که خطا را آشکار کرده دوباره ارزیابی شود. سپس چند سناریوی قبلی مرتبط برای regression بررسی شوند؛ اندازه regression set باید متناسب با scope اصلاح باشد، نه الزاماً بزرگ.
- برای سناریوهای مهم، سه artifact مفهومی جدا نگه داشته شوند: `input/requirement`، `real evidence` و `approved expectation/evaluation criteria`. Evidence واقعی به‌تنهایی oracle پاسخ صحیح نیست.
- ارزیابی نباید به تطابق لفظ‌به‌لفظ با یک پاسخ ثابت محدود شود. معیار اصلی درستی تصمیم‌ها، پوشش Requirement، رعایت قیود، حفظ مرز Skillها و نبود پیچیدگی/تغییر اضافی است.
- Real System، نمونه Export، failure واقعی و case تاریخی می‌توانند منبع سناریو و evidence باشند، اما طراحی موجود خودکار Best Practice یا expected design محسوب نمی‌شود.
- یک failure یا تجربه منفرد خودکار به Rule عمومی تبدیل نمی‌شود. Rule عمومی فقط با evidence کافی، provenance روشن و منطق قابل‌تعمیم ثبت شود.

### کنترل انسانی

- تغییرهای حساس، تصمیم‌های کم‌اطمینان، تغییر Rule عمومی، تغییر authority/semantics یا نتیجه‌ای که impact مهم و غیرقابل‌برگشت دارد، قبل از تثبیت نیازمند کنترل انسانی متناسب با موضوع است.
- اصلاح کوچک، محلی و روشن که contract پذیرفته‌شده را صرفاً درست اجرا می‌کند، به‌صورت پیش‌فرض رفت‌وبرگشت اجباری با `reviewer` ایجاد نمی‌کند؛ مگر governance مأموریت همان review را الزام کرده باشد.
- اگر AI برای حل یک مشکل چند بار متوالی به اصلاحات جانبی یا Skillهای غیرمسئول کشیده شد، ادامه اصلاح متوقف و diagnosis/مسیر به `leader` برگردانده شود.

### ارزیابی مستقل Skillها

سناریوی ارزیابی هر Skill باید تا حد ممکن ورودی/خروجی همان Skill را isolate کند. سناریوی end-to-end برای سنجش orchestration مفید است، اما failure آن ابتدا با taxonomy بالا به Skill مسئول نسبت داده می‌شود و مستقیماً به تغییر همه Skillها منجر نمی‌شود.

## SK01 — Requirement Analysis

- **هدف:** تبدیل Sources بزرگ/چندمنبعی به Requirement canonical System/Section برای Current Delivery Scope، بدون انتخاب Design SystemBuilder و بدون Change.
- **ورودی:** User/Owner sources، documents/legacy/database/metadata/UI/workflow/report/interview/operational evidence و Runtime context فقط اگر understanding سیستم موجود به آن وابسته است.
- **خروجی:** `artifact:requirements/<system>/<section>.md` برای Sectionهای relevant با Purpose، Actors، Business Objects/Data، Process trigger/stages/decisions/exceptions/completion، Rules، Forms، Reports/KPI، Automation، Security، Integrations، Configuration/Master data، future relations، ambiguity/missing info و source refs.
- **Status:** هر موضوع material یکی از `Captured / Not Applicable / Blocking Ambiguity / Deferred-Non-blocking / Missing Information`.
- **Coverage:** قبل از Design detailed، Requirement کل Current Delivery Scope completeness/minimality و cross-section coverage می‌شود؛ Section آخر می‌تواند requirement/data dependency Section اول را قبل از Build اصلاح کند.
- **Stable keys:** material Requirement می‌تواند `REQ-*` local documentation key داشته باشد؛ Runtime/Semantic identity نیست.
- **Minimality:** Writer payload/API/DB name/runtime ID/WorkflowVariableDef/package history/TRY status وارد Requirement نشود مگر Source خودش technical constraint صریح داده باشد.
- **Approval:** User approval per-stage لازم نیست؛ فقط Blocking material ambiguity یا business authority decision به User route شود.
- **مسئول آن نیست:** طراحی Entity/Workflow/View/Report، Support Mapping، Change، Plan، Apply یا Verify.
- **روش آزمون:** multi-source fixture → decomposition + Section Requirement files + coverage statuses؛ no early Design/Build.
- **وضعیت فعلی:** `ناقص`.

## SK02 — System Design / Overall + Detailed BSDN

- **هدف:** تبدیل Requirementهای Current Delivery Scope به Desired Design canonical در دو سطح Overall System و Detailed Section، مستقل از limitation Integration.
- **ورودی:** canonical Section Requirements؛ Overall/Detailed BSDNهای فعلی در Edit؛ Runtime Semantic فقط برای existing-state/drift evidence.
- **Overall output:** برای هر System relevant یک `artifact:design/overall/<system>-BSDN.md` با Section skeleton شامل Main Entities/Relations/Important Fields و Main Process/Actors/Forms/Outputs/Rules/Automation/Security/External dependencies.
- **Detailed output:** برای هر Section relevant یک `artifact:design/systems/<system>/<section>-BSDN.md` canonical. Section owner تمام Entity/Field/Relation/Formula/BusinessRule/View/Workflow/Report/Code behavior design-relevant خودش است.
- **Initial model:** `Entity/Relation Skeleton ↔ Process/Actor/Form/Output Skeleton` همزمان refine شود. قبل از Detailed Finalization، Overall همه Systemهای Current Delivery Scope از نظر ownership/dependency/naming/shared/external/cross-system flow cross-check شوند.
- **Ownership:** `One Design Fact → One Canonical Owner`. external/shared concepts owner System روشن دارند. Process/Workflow BSDN مستقل و artifact-type taxonomy default نیست. split فقط `Move, Not Copy`.
- **Completeness:** `Complete in Elements / Sparse in Obvious Properties`. Workflow material باید Variables، Actors، همه Activityهای material، `Next` و Completion Contract داشته باشد؛ technical default/property mapping به SK04 واگذار شود.
- **Lifecycle:** Draft → Finalized؛ User-Approved فقط پذیرش صریح User؛ Execution-Authorized fact جدا. Direct Build presentation را skip می‌کند، نه canonical Markdown artifacts/design reasoning را.
- **Gaps:** Requirement Gap در Requirement، Design Gap در owning BSDN، Implementation Gap بیرون BSDN. Integration limitation Design را rewrite نمی‌کند.
- **مسئول آن نیست:** Support Mapping technical status، Writer payload/runtime ID، Plan/Apply یا workaround برای unsupported contract.
- **روش آزمون:** multi-system fixture باید Overall + Section files، stable ownership، no duplicate design، complete Workflow elements و minimal properties بدهد.
- **وضعیت فعلی:** `ناقص`.

## SK03 — Semantic Model Read / Generation

- **هدف:** نمایش semantic و قابل مصرف AI از actual state SystemBuilder؛ در Reverse، فراهم‌کردن evidence برای Reconstructed BSDN بدون تبدیل Semantic به Design authority.
- **ورودی:** وضعیت/metadata واقعی خوانده‌شده از SystemBuilder یا fixture معادل آن، همراه scope خواندن.
- **خروجی:** Semantic Model وضعیت موجود با coverage/status روشن؛ در Reverse فقط evidence لازم برای BSDN بازسازی‌شده.
- **Reverse evidence rule:** Source Priority برابر `Semantic → referenced Report/Workflow when needed → Code last` است. وقتی منبع معتبر فعلی پاسخ لازم را داده، Stop Condition برقرار است و over-search/cross-check غیرضروری ممنوع است. External Binding حل‌نشده با حدس تکمیل نمی‌شود.
- **دانش مجاز:** semantics اثبات‌شده SystemBuilder، AI Integration Read/serialization/export contracts، Current Source/Runtime Evidence و mappingهای پذیرفته‌شده. برای Semantic v15، `dataexchange/13-semantic-v15-reference.fa.md` + `knowledge/semantic-v15-current.fa.md` authority هستند؛ v14/semanticId/legacy fallback استفاده نشود.
- **وابستگی‌های مجاز:** Read Actual State برای گرفتن وضعیت واقعی؛ contractهای فنی DataExchange/Host مربوط به Read.
- **مسئول آن نیست:** تحلیل Requirement، انتخاب طراحی، ساخت Change، Plan، Apply یا تصمیم درباره مطلوب‌بودن وضعیت موجود.
- **روش آزمون مستقل:** metadata/runtime fixture معلوم به Skill داده شود و projection معنایی با expected fixture مقایسه شود؛ Design و Change Construction در آزمون دخیل نباشند.
- **سناریوی مناسب ارزیابی:** وضعیت/metadata معلوم با reference، default، inheritance یا projectionهای قابل‌تشخیص که expected semantic representation آن از evidence مستقل معلوم است.
- **وضعیت فعلی:** `ناقص`.

## SK04 — Generate SystemBuilder Actions / Change Construction

- **هدف:** Current Target BSDN Scope را به exact SystemBuilder Changes/Actions و expected read-back تبدیل کند، بدون Design جدید.
- **ورودی authoritative:** relevant Overall + Detailed BSDN scopes، Support Mapping، Execution Authorization؛ Runtime/Semantic context فقط برای IDs/current state/registrations فنی. Raw Requirement فقط trace evidence است.
- **Current Target BSDN Scope:** relevant Overall System scopes + `1..N` relevant Section BSDNs + referenced owner scopes required by dependency. Active System واحد hard-code نشود.
- **Precondition:** Current Delivery Scope Design complete/minimal/cross-checked؛ blocking ambiguity صفر؛ canonical artifacts current؛ Support Mapping relevant؛ Current Build Scope known؛ Execution Authorized.
- **خروجی:** exact Changes/Actions + expected read-back/Verify expectations برای همان Design addresses. Actions باید از Current BSDN + Knowledge + Support Mapping + current runtime context قابل بازتولید باشند؛ Previous Package authority نیست. هر Semantic Change باید `profileVersion=15` داشته باشد و exact references/contexts از `dataexchange/13-semantic-v15-reference.fa.md` بیاید.
- **Support boundary:** Unsupported core outcome Desired BSDN را simplify نمی‌کند؛ Change فقط supported subset را می‌سازد و gap explicit می‌ماند.
- **Omission:** فقط intended property/section emit شود؛ omitted optional = no change. empty/default unrelated sections emit نشوند.
- **Build phase priority:** System → Structural Model (all Entities → primitive Fields → Relations/structural refs) → Entity Details (formulas/rules/Views/events) → Workflows → Reports/Commands/Navigation/final wiring. dependency topology مقدم است.
- **Primary View wiring:** اگر BSDN View اصلی تعیین کرده، create View به‌تنهایی کافی نیست و default/main wiring همان Design باید در Actions باشد.
- **Report user-facing:** owner/source و placement/navigation design-relevant باید همراه Report realization شود؛ presence metadata بدون required placement complete نیست.
- **Workflow:** exact DX workflow contract قبل از construction مصرف شود؛ schema/property حدس زده نشود. Actor performer در Final BSDN باید performer semantic متناظر در Change داشته باشد؛ omission performer با starterActor/description جبران نمی‌شود.
- **Workflow local refs:** local keys فقط در shapeهای contract-supported emit شوند؛ SK04 unsupported local-ref kind را invent نمی‌کند. SK05 باید exact shape را preflight کند.
- **Infrastructure registration:** registration caption/family واقعی و Central Resolver contract فعلی مصرف شود؛ runtime IDs/GlobalIds hard-code یا catalog preload نشوند.
- **Cross-step references:** `tempId` فقط داخل همان logical Batch معتبر است. برای object persisted در wave/exchange بعدی، Semantic selector/context دوباره authority resolution است؛ Runtime ID/read-back فقط diagnostic/technical evidence است و semantic target fallback نمی‌شود.
- **مسئول آن نیست:** Requirement/design decision تازه، mutation، Plan workaround یا تغییر BSDN برای عبور از Writer limitation.
- **روش آزمون:** fixed BSDN + support mapping + baseline semantic → exact supported Actions + gaps + expected verify; no Plan/Apply.
- **وضعیت فعلی:** `ناقص`.

## SK05 — Plan

- **هدف:** validation/dependency/order فنی و **core contract-shape validation before persistence** بدون Mutation.
- **ورودی:** SK04 Changes/Actions + technical context.
- **خروجی:** executable Plan + machine-readable diagnostics/blockers.
- **Core validation examples:** performer binding، condition shape، relation path، update/delete contract، workflow-local refs، required parent/target، registration resolution. fail این validation → no mutation؛ BSDN unchanged؛ gap/Change correction به owner route شود.
- **Dependency-aware preflight:** command-local failure همان command + transitive dependents را block کند؛ batch-fatal فقط duplicate identity/dependency cycle/broken execution context و contractهای واقعاً global. proven-independent nodes قابل ادامه‌اند.
- **Infrastructure preflight:** registration/capability bindings قبل mutation resolve و immutable شوند؛ Writer وسط mutation rediscovery نکند.
- **Zero-mutation recovery:** Plan failure state را تغییر نمی‌دهد؛ SK05 برای سبزشدن Plan Design/Change را silently rewrite/split نمی‌کند.
- **مسئول آن نیست:** Design، mutation یا semantic invention.
- **وضعیت فعلی:** `موجود`.

## SK06 — Apply

- **هدف:** اجرای دقیق Plan معتبر روی Runtime و گزارش persistence واقعی.
- **ورودی:** Plan + runtime target.
- **خروجی:** command results، real/temporary IDs، diagnostics، `mutationApplied` و `partialFailure` درست.
- **Mutation reporting:** قبل اولین persistence `mutationApplied=false`; بعد اولین persistence true و هرگز false نمی‌شود؛ failure بعد از persistence → `partialFailure=true`. exception type برای inference mutation استفاده نشود.
- **Partial mutation:** contract v15 طبق `dataexchange/13-semantic-v15-reference.fa.md`: partial mutation → `NeedsReconcile`; shared/unknown effect → Immediate Reconcile؛ در غیر این صورت aggregated final read-back/reconcile. Blind repair/delete/retry قبل از reconcile ممنوع است و proven-independent branchها فقط طبق contract ادامه دارند.
- **ContinueIndependent:** command failure transitive dependents را Skip می‌کند و proven-independent nodes ادامه دارند مگر strict/batch-fatal policy.
- **Recovery evidence:** result تا حد امکان persisted root/child IDs و last successful stage را حفظ کند؛ نبود این evidence gap recovery است.
- **مسئول آن نیست:** Design/Change creation یا acceptance verdict.
- **وضعیت فعلی:** `موجود`.

## SK07 — Read Actual State

- **هدف:** گرفتن وضعیت واقعی جاری Runtime/SystemBuilder بدون Mutation برای تحلیل، Semantic Model یا Verify.
- **ورودی:** target/scope مشخص SystemBuilder و پارامترهای read لازم.
- **خروجی:** وضعیت واقعی خوانده‌شده یا capture/read-back قابل trace به Runtime.
- **دانش مجاز:** Read/Pull/Snapshot/export contract جاری، Source/Runtime behavior و technical lookup rules لازم.
- **وابستگی‌های مجاز:** Runtime/SystemBuilder؛ هیچ Skill mutation لازم نیست.
- **مسئول آن نیست:** تفسیر طراحی مطلوب، تولید Change، Apply یا قضاوت acceptance.
- **روش آزمون مستقل:** Runtime fixture با state معلوم خوانده شود و خروجی با state مورد انتظار مقایسه شود؛ آزمون باید read-only بودن را نیز کنترل کند.
- **سناریوی مناسب ارزیابی:** target با state معلوم و scope خواندن مشخص که completeness/read-only بودن و traceability خروجی به Runtime قابل سنجش باشد.
- **وضعیت فعلی:** `موجود`.

## SK08 — Verify

- **هدف:** Verify مستقل Actual Runtime در hierarchy `Step/Wave → Section → System → Final Delivery Scope` نسبت به Current Target BSDN؛ Previous Change design oracle نیست.
- **ورودی:** relevant Overall/Detailed BSDN، Requirement trace/acceptance، Support Mapping gap context، actual read-back.
- **خروجی:** verified/failed/partial/metadata-only/not-runtime-smoked + meaningful differences/evidence scope.
- **Expected model:** SK04 expected read-back را از BSDN مشتق می‌کند؛ SK08 Design را از صفر حدس نمی‌زند.
- **Step/Wave:** بعد هر material Apply read-back/verify همان subset.
- **Section:** Runtime Section ↔ Detailed Section BSDN.
- **System:** Runtime System ↔ Overall + all relevant Section BSDNs؛ cross-section wiring/ownership/reference بررسی شود.
- **Final:** all Current Delivery Scope Runtime ↔ Current Target BSDN scopes + explicit unsupported/deferred/unavailable outcomes.
- **Workflow:** صرف root وجود کافی نیست؛ Variables، Actors/performer، Activities، Start/End، topology/branches/loops، conditions، View wiring، material effects و Completion Contract در supported scope read-back شوند.
- **View/Rule/Report:** existence کافی نیست؛ default/main wiring، selected rules و user-facing report placement design-relevant verify شود.
- **Normalization:** semantic-equivalent runtime representations canonicalize شوند؛ normalization authority/Design جدید نیست. false-negative verifier به Writer redesign منجر نشود.
- **Descriptor gap:** missing read-back property بدون raw evidence persistence صحیح/غلط را ثابت نمی‌کند؛ Writer/Persistence/Exporter/Verifier classification با evidence انجام شود.
- **Progress:** Runtime actual status stale Progress را اصلاح می‌کند؛ BSDN unchanged.
- **Evidence honesty:** package/static/metadata/runtime/behavioral evidence جدا؛ اجرا نشده=`NO`.
- **Verified Release:** فقط بعد required mutation complete، corrective open=0 و cumulative claimed-scope Verify. Release history داخل BSDN نیست.
- **وضعیت فعلی:** `ناقص`.

## SK09 — AI Work Management / Governance

- **هدف:** orchestration Scope/Stage/Skill بدون جذب منطق داخلی آنها.
- **Scope:** Solution Landscape، Current Delivery Scope و Current Build Scope را track کند؛ Future non-blocking را از current gate جدا نگه دارد.
- **Operational artifacts:** current-progress/support-mapping/releases را بیرون BSDN maintain کند؛ current-progress execution diary نشود.
- **Routing:** Requirement gap→SK01، Design→SK02، Support→mapping owner، Actions→SK04، preflight→SK05، mutation/recovery→SK06/SK07، verdict→SK08.
- **Approval:** per-stage approval gate نسازد؛ فقط material Business/System authority decision به User.
- **Continuation:** current-progress → Overall BSDNs → relevant Requirement/Section BSDNs → owner dependencies → Support Mapping → Runtime only for actual state.
- **Partial mutation:** no blind retry orchestration؛ read-back/reconcile first.
- **Version evolution:** Change Request impact/migration before Build؛ Technical Fix بدون Design change BSDN را touch نکند.
- **Review proportional to risk:** architecture/cross-cutting سه perspective `Architecture / Runtime-Regression / Implementor` توصیه؛ review count Host gate نیست و self-review external independent نیست.
- **وضعیت فعلی:** `ناقص`.

## SK10 — KM Generate / Update

- **هدف:** تولید/بازسازی KM با `Full Generate` یا `Incremental Update`؛ Current Target BSDN scopes می‌تواند context Design باشد، اما KM جای BSDN/Runtime/HK را نمی‌گیرد و Design store نیست؛ برای Full System ساخت hierarchy اولیه‌ی selective شامل System KM concise و یک لایه Child KM مستقل برای targetهای مهم منتخب، بدون all-metadata یا recursion.
- **ورودی Full Target:** Target و Semantic واقعی scope لازم؛ Current Target BSDN scopes و HK/KM معتبر در صورت مفیدبودن. Runtime actual state همچنان authority وضعیت ساخته‌شده است.
- **ورودی Full System:** Full System Semantic، inventory targetها، Current Target BSDN scopes در صورت وجود و evidence اهمیت/ارتباط آنها برای selection.
- **ورودی Incremental:** previous invalid KM targetهای materialized affected، Actual Delta واقعی، current/new affected Child KMها در صورت وجود و context semantic لازم.
- **خروجی:** `AiKnowledge.Content` مطابق KM Content v1 موجود. System Content concise است؛ selected first-level `drillDown` targetها در Full System باید Child Content مستقل متناظر نیز داشته باشند.
- **Trigger در AR01:** فقط در stable mission checkpoint نهایی اجرا می‌شود، نه بعد از intermediate Apply/Verify. Create System → Full System؛ Edit System → Incremental و فقط در صورت ناکافی‌بودن evidence fallback Full مناسب. Content/selection از actual final state است، نه intended Change. اگر ledger هنوز outcome اجرایی pending دارد، Auto-KM زودهنگام ممنوع است.
- **Full System orchestration:** Full Semantic را analyze کن → targetهای business/operationally مهم را selective انتخاب کن → Child KMهای منتخب را از همان Semantic در memory generate کن → System KM concise با همان drillDownها generate کن → در EM01 یک `km-save` batch بساز: Childها اول، System آخر → aggregate result را verify کن. completion فقط در success کامل batch.
- **Selection:** `entity/view/report/workflow` و فقط Field واقعاً knowledge-worthy بررسی شوند. domain/business/operational/workflow/user-facing/dependency significance اصل است؛ raw complexity به‌تنهایی کافی نیست، quota ثابت و all-object selection ممنوع است، internal/helper فقط با evidence مستقل اهمیت انتخاب می‌شود. **Integration/storage readiness معیار importance نیست**؛ failure فعلی Host مجوز حذف target مهم از selection، Child set یا System `drillDown` نیست.
- **Materialization boundary:** Full Generate(System) فقط یک سطح مستقیم زیر System را برای selected drillDownها materialize می‌کند؛ drillDownهای داخل Child KMها eager recursion ایجاد نمی‌کنند. targetهای انتخاب‌نشده on-demand lazy باقی می‌مانند.
- **Lazy child:** برای target انتخاب‌نشده ابتدا `km-current(child)`. Entity می‌تواند `target-semantic(entity)` بگیرد؛ View/Report/Workflow از Full/System Semantic owning System و nesting/context + selector canonical Semantic locate می‌شوند؛ Runtime `targetId` فقط lifecycle فنی KM است و `semanticId` قدیمی استفاده نمی‌شود. direct unsupported `target-semantic` اختراع نمی‌شود. Field از Semantic owner Entity/System استفاده می‌کند.
- **Content quality:** System summary/keyPoints سطح System و pointers؛ detail target-specific در Child KM. Entity/Field/View/Report/Workflow content متناسب همان target و بدون exact DataExchange serialization. `AiKnowledge.Content` باید JSON معتبر و human-readable باشد: با parser واقعی parse و سپس با indentation ثابت 2-space serialize شود؛ ترتیب preferred top-level `summary → keyPoints → drillDown` است، هر keyPoint item جدا و هر drillDown object چندخطی است. whitespace semantic نیست و string manipulation دستی برای pretty-print ممنوع است.
- **Batch persistence:** exact request/result contract متعلق به `agent/package-protocol.fa.md` و generated `chat-protocol.json` است. همه itemها قبل از mutation validate می‌شوند؛ duplicate/malformed/invalid JSON، availability storage و سپس target mapping/identity با resolver production در preflight بررسی می‌شوند. storage غایب → `unavailable` و zero mutation؛ storage موجود ولی target mapping/persistence معیوب → `incomplete/failed` و Knowledge Design تغییر نمی‌کند. execution ordered و stop-on-first-failure/ambiguity است؛ System item برای Full System آخر است.
- **Lifecycle / retry:** `id=0/omitted` per item باید storage reuse موجود را حفظ کند: current → correlated previous-invalid → single invalid → ambiguity. Skill برای جلوگیری از duplicate row، id حدسی نمی‌سازد. اگر batch قبلی partial بوده، بعد از رفع Integration **همان original selection** retry می‌شود؛ itemهای قبلاً ذخیره‌شده باید reuse شوند و target failed/notAttempted دوباره اجرا شوند. selection برای سبزکردن retry کوچک نمی‌شود.
- **Incremental:** فقط existing/materialized affected Child KM(s) + parent System لازم maintain می‌شوند؛ missing child فقط به علت propagation ساخته نمی‌شود. چند target affected می‌توانند در یک `km-save` batch با parent System آخر persist شوند.
- **وابستگی‌های مجاز:** Read Actual State/Semantic Model؛ lifecycle storage `AiKnowledge`; Package Protocol فقط برای transport exact؛ orchestration برای affected scope و selection.
- **مسئول آن نیست:** تغییر DB/KM Content schema، target type taxonomy، `/ai-knowledge` public behavior، Apply/Plan، ساخت Actual Delta حدسی، recursive/all-metadata materialization یا action تازه.
- **روش آزمون مستقل:** Full System fixture بزرگ باید چند type مهم را selective انتخاب و برای همه‌ی selected System drillDownها Child Content مستقل بسازد؛ persistence در EM01 یک batch با Childها اول/System آخر باشد. Create-System workflow بدون prompt دوم باید Full را trigger کند؛ Edit-System workflow بدون prompt دوم باید Incremental را trigger و با evidence ناکافی Full مناسب را انتخاب کند. duplicate/malformed/invalid content و unresolvable mapping باید قبل از mutation reject شود؛ storage absent باید `unavailable` با zero mutation بدهد، ولی storage-present target failure باید KM را incomplete نگه دارد و target حذف نشود. simulated execution failure/409 باید execution را متوقف و System را notAttempted کند و Agent نباید failed target را از Knowledge Design حذف کند. retry همان original selection باید rowهای قبلاً موفق را reuse کند. single و batch Content پس از save/read-back باید pretty-formatted باشد و parse آن با semantic JSON قبل از formatting برابر بماند. Incremental fixture باید missing Child را بی‌دلیل materialize نکند.
- **سناریوی مناسب ارزیابی:** `Full Generate(System) → select → generate children in memory → concise parent → one km-save batch → aggregate success`; سپس lazy target انتخاب‌نشده و incremental چند-target موجود.
- **وضعیت فعلی:** `ناقص` — storage lifecycle موجود است؛ Package batch transport در Host bridge پشتیبانی می‌شود و generation/selection/content quality همچنان مسئول AI Skill و نیازمند fixture واقعی/ارزیابی انسانی است.
