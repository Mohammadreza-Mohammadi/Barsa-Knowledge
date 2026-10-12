# AI Integration Support Matrix

این جدول دو سؤال را جدا می‌کند:

1. SystemBuilder این capability را دارد؟
2. Integration فعلی آن را semantic Read/Write/Verify می‌کند؟

در AR01 این سند **Current Delivery/Build Scope از Overall + Detailed BSDNهای relevant** را مصرف می‌کند. Support Mapping Design Authority نیست و statusهای `Supported / Partial / Unsupported / Unknown / Deployment Unavailable / Contract Ambiguous` داخل Desired BSDN نوشته نمی‌شوند. mapping scope-based و refreshable است؛ unsupported implementation Desired BSDN را rewrite یا silently simplify نمی‌کند و فقط implementation outcome را partial/gap می‌کند. `Wave` می‌تواند چند Section/System dependency-linked را پوشش دهد و identifier داخلی موجود rename نمی‌شود.

| Feature | Design knowledge | Read | Write | Verify | وضعیت فعلی |
|---|---:|---:|---:|---:|---|
| System | yes | yes | create | yes | update/delete provider ندارد |
| Entity | yes | yes | create/update | yes | delete unsupported |
| Field | yes | yes | broad C/U/D | yes | 47 semantic type؛ caveatهای descriptor |
| Relations | yes | yes | broad C/U/D | yes | `inheritanceChild` direct create ممنوع |
| Formula code | yes | yes | yes | metadata | compile/metadata؛ اجرای data جدا smoke شود |
| Formula query/aggregate | yes | yes | yes | metadata | Report-backed؛ data execution smoke مهم است |
| View/Layout | yes | yes | yes | semantic | UI proof نیست |
| UniqueConstraint | yes | yes | yes | yes | current provider |
| BusinessRule unconditional | yes | yes | yes | yes | current provider |
| BusinessRule conditional | yes | yes | `branches[]` | yes | shared ComplexCondition |
| Report common/core | yes | yes | yes | yes | list/tree/matrix/calendar/forum + common settings |
| Statistics/Dashboard/Print | yes | yes | base/common lifecycle | common | designer-specific payload partial/deferred |
| Folder/navigation | yes | yes | yes | yes | Page/Group/Report placement |
| Workflow | yes | yes | extended v137 create/root-edit | yes for supported graph | Root/Variable/Actor + persisted same-change refs؛ StartVariableId/SubKey1؛ Actor performer؛ AssignmentType omission=OnFirstUsage؛ WorkDistribute omission=همه افراد via central preflight resolver؛ Start/SimpleForm/Condition/Finish/Fork/Join/ExecuteCode/SubProcess/CustomActivity؛ Form Connection Settings؛ Workflow graph authority؛ Create does not generate/require Diagram2؛ Edit currently clears Diagram2؛ Workflow root semantic export + local graph refs + reverse-resolved infrastructure captions |
| Dynamic Command | yes | yes | create yes for catalog Definitions with resolvable `فرم ويرايش` Settings Entity | usage/settings/parameter read-back | `MetaCommand → دستور پويا usage → تعريف دستور registration + تنظيمات + پدر`؛ Definition از deployment capability binding در Plan resolve می‌شود و ساخته نمی‌شود؛ v130 نمونه‌های `نمایش پیغام`، `اجرای کد منطق کاری` و `اجرای فرآیند` را regression می‌کند؛ UI surface attachment contract جدا و تا وقتی Source-backed Writer مستقل ندارد unsupported است |
| Settings/Configuration | yes | source-dependent | no general writer | no general verify | چند mechanism مستقل؛ payload حدسی ممنوع |
| Deployment/BIX | yes | tooling/source | خارج از generic Semantic Change | n/a | deployment lifecycle مستقل از Metadata Change معمول |
| Snapshot diagnostics | n/a | yes | diagnostic capture | Full Structured + Semantic diff | development/gap discovery؛ BIX DataSet فقط capture داخلی و خارج از normal Verify |
| Menu | yes | no dedicated semantic contract | no | no | coverage بعدی در صورت نیاز |
| Standalone Code | yes | export exists by owner context | no generic writer | no | Code داخل Formula/Rule/Report جداست |
| Security | yes | metadata/read paths exist | no general writer | no general writer | design knowledge موجود؛ write scope عمومی ندارد |


## Feature Certification semantics

Support family-level با certification case-level یکی نیست. برای feature/variantهای بررسی‌شده، dimensions مستقل بمانند:

```text
Read
Write
Verify
Behavior/UI
```

مثلاً `Read=PASS / Write=PASS / Verify=PASS / Behavior-UI=NOT TESTED` claim معتبر است؛ یک case موفق همه variantها را Certified نمی‌کند. روش عمومی در `knowledge/feature-evidence.fa.md` است؛ concrete case evidence در `artifact:operations/feature-evidence/<case-id>.md` و backlog unresolved در `Source-only project documentation` نگهداری می‌شود.

وجود export به‌تنهایی `Supported` کلی نیست و failure نیز خودکار Writer/Semantic bug نیست؛ ابتدا `Semantic Read / Write-Apply / Plan-Contract / Verify / Runtime Behavior / Designer Meaning / Test-Data / Deployment` classify شود.

برای design/semantic caveatهای عمیق به `knowledge/deep/*` مراجعه شود؛ برای exact property/type/payload/write/validation contract از DataExchange owner استفاده کن (`dataexchange/00-start.fa.md`). هیچ `partial/source-dependent` به معنی اجازه حدس payload نیست.

### v136 Infrastructure registration resolution
Workflow Performer / WorkDistribute / Custom Activity و Dynamic Command registrationها در Plan با family واقعی metadata + registration caption و Central cached DB resolver به Runtime ID تبدیل می‌شوند. symbolic capability key، GlobalId یا Runtime ID hard-coded در Knowledge استفاده نمی‌شود؛ Apply registration rediscovery ندارد.


### Current Semantic v15 status — v164

Semantic v15 contract/real export در baseline v164 پذیرفته شده‌اند، اما Runtime certification هنوز pending است. exact status: `knowledge/semantic-v15-status.fa.md`. هیچ `Read/Write/Verify` family صرفاً از static/export evidence به Round-trip Certified ارتقا داده نشود.

### HISTORICAL — v147 semantic/read-write implementation status

برای System visibility، SystemItemGroup، Entity DbName/dbType/group assignment، portable asset، reverse relation direct-field ref، external data refs، Report parameter refs و Folder order/icon، Source implementation در candidate v147 وجود دارد اما تا Build + Runtime Re-export + round-trip Read-back/Verify اجرا نشود status آنها **Certified** نیست. `Read / Write / Verify / Behavior-UI` مستقل گزارش می‌شوند. Folder access/security writer همچنان `Unknown/Source-contract pending` است و generic payload ندارد.
