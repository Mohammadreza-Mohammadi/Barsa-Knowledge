# Workflow Writer — DataExchange Exact Contract (v136)

این سند contract machine-level Writer/Verifier است. Design authority در Host/BSDN باقی می‌ماند؛ این سند تصمیم business جدید نمی‌گیرد.

## Change shape

`objectType:"workflow"`، create زیر Parent System. properties:

```json
{
  "name":"...",
  "description":"...",
  "isActive":true,
  "variables":[],
  "actors":[],
  "activities":[],
  "transitions":[]
}
```

برای Create هر چهار array باید حاضر باشند. graph داخلی از `key` local استفاده می‌کند؛ dependencyهای بیرونی مانند Entity/View/Workflow/Report با typed `id/tempId` هستند. `diagram` اگر صریحاً ارسال شود unsupported است؛ Agent/Writer geometry payload نمی‌سازد. از v137 Create پس از persistence/reload graph تمام می‌شود؛ هیچ `SlWorkflowDesignManager/DiagramControl/GenerateDiagram` اجرا نمی‌شود و `Diagram2` می‌تواند null باشد. هر Workflow Update واقعی در v137 فعلاً `Diagram2` را clear می‌کند و regeneration ندارد.

## Persisted same-change reference rule

Writer root را persist می‌کند، سپس Variable/Actor/Activity/Choiceهای جدید را مرحله‌ای persist می‌کند و wiring داخلی را فقط با **ID واقعی persisted** می‌نویسد. Custom Activity نیز دو مرحله‌ای است: Activity ابتدا ID می‌گیرد، Settings با back-reference واقعی ساخته می‌شود و سپس `CustomActivityDefInfoId` روی Activity update می‌شود.

Start invariant:

```text
WorkflowVariableDef.Id
→ StartActivity.Info.StartVariableId
→ StartActivity.VariableId / SubKey1
```

`startVariable` اگر آمده باشد key Variable است؛ در غیر این صورت `variable` همان Start Variable است. `StarterUserActorDefId` legacy compatibility setting است: v135 AI Writer آن را تعریف/infer/set/update نمی‌کند و performer را از آن نتیجه نمی‌گیرد. `starterActor` ورودی compatibility قدیمی است و برای AI create جدید نباید emit شود.

`startType`: `createNewForm | useExistingForm | none`. یک Workflow می‌تواند بیش از یک Start داشته باشد؛ از جمله `createNewForm` و `useExistingForm` روی همان Variable.

Terminal path می‌تواند `finish` استاندارد یا `customActivity` با registration معنایی `پایان` باشد.

## Variable

```json
{
  "key":"form",
  "name":"فرم فرآیند",
  "entity":{"objectType":"entity","id":123},
  "otherUserAccessType":1
}
```

`entity` می‌تواند same-batch `tempId` باشد. `otherUserAccessType` optional است.

## Infrastructure registration preflight

قبل از `WorkflowDef.Create()`، Plan تمام registrationهای Infrastructure لازم را resolve می‌کند:

```text
performer.calculation
→ Assignment relation TargetTypeId
→ family واقعی نحوه محاسبه
→ Central Resolver(DefaultField + DB + FixFarsiText + cache)
→ RuntimeRegistrationId

customActivity.registration
→ family واقعی نوع فعالیت پیشرفته
→ RuntimeRegistrationId
→ registration.فرم ويرايش → Settings TypeDef
```

`workDistribute` نیز قبل از mutation در family واقعی `فرآيند پيشرفته 2.نحوه توزيع كار` / `ActorDefInfo.WorkDistributeTypeTypeDef` resolve می‌شود. در omission، semantic default `همه افراد` در Plan resolve می‌شود. بعد از preflight موفق، `AiWorkflowChangeProvider` هیچ `RequireRegistration`/catalog lookup انجام نمی‌دهد و فقط Runtime IDs/Settings metadata resolved را مصرف می‌کند. unresolved/ambiguous registration یک command-local preflight failure است و `Workflow mutation = 0`.

Runtime numeric ID و GlobalId داخل Knowledge/Change این مسیر ذخیره نمی‌شوند؛ locator قابل فهم همان registration caption واقعی Barsa است.

## Actor / performer

Existing assignment همچنان پشتیبانی می‌شود:

```json
{
  "key":"approver",
  "name":"تأییدکننده",
  "assignmentType":"onFirstUsage",
  "assignmentId":123,
  "workDistributeType":456
}
```

برای portable semantic selection، `workDistribute` caption واقعی family `فرآيند پيشرفته 2.نحوه توزيع كار` است؛ omission = `همه افراد`. `workDistribute` و `workDistributeType` هم‌زمان ارسال نشوند.

Writer می‌تواند Assignment object را بسازد:

```json
{
  "key":"approver",
  "name":"تأییدکننده",
  "assignmentType":"onFirstUsage",
  "performer":{
    "calculation":"(کاربر) آغاز کننده فرآیند",
    "parameters":{}
  }
}
```

`AssignmentType` مستقل از وجود Assignment است؛ `none` باعث reject یا حذف `AssignmentId` نمی‌شود. برای Assignmentهای infrastructure که calculation ندارند، `performer.kind` می‌تواند به‌تنهایی نوع assignment را تعیین کند.

Confirmed calculation create patterns:

| calculation | Settings Entity | semantic parameters |
|---|---|---|
| `(کاربر) آغاز کننده فرآیند` | none | none |
| `(سمت) انتخاب سمت` | `محاسبه-سمت ثابت` | `انتخاب سمت` |
| `(کاربر) انتخاب کاربر` | `محاسبه-کاربر ثابت` | `انتخاب کاربر` |
| `(سمت/کاربر) فیلد فرم` | `محاسبه-فيلد فرم` | `فرم فرآيند`, `فيلد`, optional workflow context |
| `(سمت/کاربر) فرمول محاسبه` | `محاسبه-فرمول محاسبه` | `كد`, optional `فرم فرآيند`, workflow context |

`parameters` scalar یا typed reference می‌پذیرد. lookup registration/type/field با semantic caption + DB Arabic canonicalization انجام می‌شود؛ numeric ID fixture hard-code نمی‌شود.

## Activities

Create subset v130:

- `start`
- `simpleForm`
- `condition`
- `finish`
- `fork`
- `join`
- `executeCode`
- `subProcess`
- `customActivity`

### SimpleForm

`variable → VariableId/SubKey1` و `actor → ActorId/SubKey2`.

`view` optional است: omission/null → `TypeViewId=0`; typed View reference → explicit View. `autoApproveIfPreviousActorUserIsActorOfThis` optional است.

### ExecuteCode

```json
{"key":"code1","name":"...","type":"executeCode","variable":"form","actor":"actor1","code":"..."}
```

`code` الزامی است و در `ExecuteCodeActivityDefInfo.Code` persist می‌شود.

### SubProcess

```json
{
  "key":"sub1",
  "name":"ارجاع به زیرفرآیند",
  "type":"subProcess",
  "variable":"form",
  "subProcess":{"objectType":"workflow","id":123},
  "itemResolveReport":{"objectType":"report","id":456},
  "subProcessActor":"expert"
}
```

`subProcess` الزامی است؛ report و actor زیرفرآیند optional هستند. `subProcessActor` ترجیحاً key یکی از Actorهای همین Workflow است (همان الگوی `SubKey2` در fixtureهای واقعی)؛ typed `workflowActor` reference نیز برای Actor موجود پشتیبانی می‌شود. هیچ Runtime ID نمونه hard-code نمی‌شود.

### Custom / Advanced Activity

```json
{
  "key":"end2",
  "name":"پایان پیشرفته",
  "type":"customActivity",
  "registration":"پایان",
  "settings":{
    "parameters":{}
  }
}
```

Plan Custom Activity `registration` caption را قبل از mutation در family واقعی deployment به Runtime registration resolve می‌کند. Settings Entity از `فرم ويرايش` همان resolved registration می‌آید؛ registration جدید ساخته نمی‌شود. Writer فقط binding آماده را مصرف، Settings usage-specific را می‌سازد، `WorkflowDef` و `ActivityDef` را در صورت وجود field wire می‌کند و `CustomActivityTypeId/CustomActivityDefInfoId` را persist می‌کند. Writer terminal semantics را از Caption «پایان» استنتاج نمی‌کند؛ Standard Finish مسیر مستقل خود را دارد.

در `settings.parameters` علاوه بر scalar/typed reference، local references زیر پشتیبانی می‌شوند:

```json
{"workflowVariable":"form"}
{"workflowActor":"approver"}
{"workflowActivity":"task1"}
{"currentWorkflow":true}
{"currentActivity":true}
```

## Choice / transition

Plain transition:

```json
{"from":"edit","to":"finish","name":"تأیید"}
```

برای خروجی SimpleForm سه حالت معتبر است:

- omission → `SettingsId=0`؛
- `settingsId` → attach Settings موجود؛
- `settings` → create `تنظيمات اتصال فعاليت فرم` جدید.

نمونه create:

```json
{
  "from":"edit",
  "to":"finish",
  "name":"تأیید",
  "settings":{
    "parameters":{
      "نمايش تأييديه":true
    }
  }
}
```

Writer در Settings جدید، `WorkflowDef` و در صورت وجود Variable source، `Variable` و `موجوديت مرتبط` را خودکار wire می‌کند. `شرط نمايش` یا سایر relationها فقط وقتی صریحاً با typed/local reference داده شوند نوشته می‌شوند؛ object حدسی ساخته نمی‌شود.

Condition transition از grammar مشترک DX10 استفاده می‌کند. non-else condition به `variable` local key نیاز دارد. Else با `else:true` است. برای Condition Choice، `codeVariable` و `customCode` نیز optional هستند و به `CodeVariableDefId` و `CustomCode2` map می‌شوند.

## Read-back / Verify

برای graph پشتیبانی‌شده حداقل verify می‌شود:

- root/Variable/Actor و same-change IDs؛
- StartVariableId/SubKey1؛ `StarterUserActorDefId` فقط read-only legacy compatibility و خارج از AI write authority است؛
- performer Assignment/Settings و optional no-calculation kind؛
- WorkDistribute semantic/id؛
- SimpleForm default/explicit View؛
- Fork/Join type؛
- ExecuteCode code؛
- SubProcess references؛
- Custom Activity registration + Settings + WorkflowDef/ActivityDef back-reference؛
- Choice topology، existing/created Form Connection Settings، canonical Condition، optional Choice code fields.
- `Diagram2` derived/optional است؛ Create آن را تولید یا require نمی‌کند و Update فعلاً آن را clear می‌کند.

NRE روی invalid/same-change reference contract معتبر نیست؛ failure باید diagnostic/domain-specific باشد.

## Existing Workflow update

v130 graph mutation Workflow موجود را عمومی نمی‌کند. `name/description/isActive` root patch supported است؛ graph patch موجود `Unsupported` باقی می‌ماند.

## Fixture scope

v125 fixture برای regression پایه حفظ می‌شود. fixtureهای Workflow واقعی ارائه‌شده در مأموریت v130 برای اثبات وجود Fork/ExecuteCode/SubProcess/Custom Activity/Choice Settings و Actor patterns استفاده می‌شوند؛ numeric IDs آنها authority یا portable contract نیستند.


## v137 defaults

- `assignmentType` omitted → `OnFirstUsage`؛ enum Product است و Infrastructure resolver ندارد.
- `workDistribute/workDistributeType` omitted → `همه افراد` → Central Resolver → Runtime Id non-zero before mutation.
- Catalog واقعی `نحوه توزيع كار`: `همه افراد` (default/active)، `انتخاب اولين فرد` (active)، `انتخاب اولين فرد داخل سيستم` (inactive)، `همه افراد داخل سيستم` (active).

## v137 Semantic Export

Workflow root زیر System semanticId می‌گیرد. Childهای Actor/Variable/Activity/Choice persistent semanticId ندارند؛ exporter local `ref` همان document را می‌سازد و wiring را با `variableRef/actorRef/fromRef/nextRef` قابل فهم می‌کند. Runtime IDs حفظ می‌شوند. WorkDistribute، performer calculation و Custom Activity registration canonical semantic caption حاصل از reverse `AiInfrastructureRegistrationResolver` را نیز صادر می‌کنند.

## v179 — Nested Semantic references before Resolve

در executable Semantic v15، nested referenceهای Workflow از همان Semantic reference rule مرکزی استفاده می‌کنند:

```text
same logical batch → tempId
persisted / prior-wave → Semantic selector/context
Runtime ID → IOC only; authored SOC invalid
```

این قاعده حداقل برای `variable.entity` و referenceهای activity مانند `view`, `subProcess`, `itemResolveReport` و object-form `subProcessActor` اعمال می‌شود. Pre-resolution validation فقط shape/type/selector را اعتبارسنجی می‌کند و وجود Runtime ID را قبل از Resolve الزام نمی‌کند. malformed selector، wrong objectType و Runtime-ID authority قبل از Apply رد می‌شوند.

## v180 — Workflow Reference Pipeline

Workflow typed nested references use one central Semantic reference interpretation across Lint, Plan, Resolve, Provider and Apply.

```text
AUTHORED SOC
same-wave   → tempId
cross-wave  → canonical Semantic selector
Runtime id  → forbidden

RESOLVED IOC
selector/tempId → Host resolve → Runtime object/id
Runtime id      → valid internal execution evidence
```

Provider/Apply must not re-run authored-SOC Runtime-ID rejection against Planner/Executor generated IOC state. Canonical persisted references are selector strings; object-form selector is internal/compatibility input and is normalized by Host. Workflow Apply consumes selector strings through the shared Semantic reference contract/resolver; it does not require Agent-authored Runtime IDs or Workflow-only selector grammar.

Covered typed paths include `variable.entity`, `activity.view`, `activity.subProcess`, `activity.itemResolveReport` and object-reference `activity.subProcessActor` where applicable.
