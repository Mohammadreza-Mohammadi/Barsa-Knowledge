# Agent Role Registry

این Registry مرجع کوتاه انتخاب AR است. تعریف کامل فقط در سند همان Role قرار دارد؛ مشاهده یک Role آن را فعال نمی‌کند.

BSDN-related Role routing از `knowledge/bsdn/00-start.fa.md` شروع می‌شود؛ Registry فقط Purpose/selection را نگه می‌دارد و notation را تکرار نمی‌کند.

| Code | Name | Purpose | Select when | Do not select when | Document |
|---|---|---|---|---|---|
| `AR01` | `system-developer` | Sources → System/Section Requirements → Overall+Detailed BSDN → Support Mapping → authorized Build/Verify/KM؛ برای scope بزرگ با Current Delivery/Build Scope | کاربر ساخت/تغییر واقعی System و نتیجه قابل Verify می‌خواهد | فقط طراحی بدون mutation یا اصلاح خود Integration | `agent/roles/AR01-system-developer.fa.md` |
| `AR02` | `system-designer` | Requirement→BSDN Target Design بدون mutation | خروجی BSDN Draft/Approved لازم است | Apply یا تغییر واقعی System لازم است | `agent/roles/AR02-system-designer.fa.md` |
| `AR03` | `integration-developer` | رفع Bug/Gap در AI Integration و تولید Update Package | مشکل Source/Host/DataExchange/Integration باید ریشه‌یابی و اصلاح شود | هدف اصلی ساخت business System است | `agent/roles/AR03-integration-developer.fa.md` |
| `AR04` | `reference-reconstruction-evaluator` | Semantic-first reconstruction و Reconstructed BSDN یک Target مرجع | Target واقعی/مرجع باید stepwise بازسازی و failureها طبقه‌بندی شوند | طراحی آزاد business System یا patch Integration هدف مستقیم است | `agent/roles/AR04-reference-reconstruction-evaluator.fa.md` |
| `AR05` | `requirement-to-change-evaluator` | با Approved Target BSDN: derived Delta/Change evaluation؛ بدون آن: فقط اثر طراحی پیشنهادیِ evaluation-only | ورودی lesson/requirement کوچک برای سنجش Design impact/Action construction داده شده | Runtime execution/Apply یا بازسازی Target لازم است | `agent/roles/AR05-requirement-to-change-evaluator.fa.md` |
| `AR06` | `feature-worker` | evidence-driven feature-by-feature Semantic Read + Write/Apply/Verify certification از feature واقعی | Semantic gap/unknown designer meaning، real-feature reconstruction یا Integration gap discovery در سطح Feature/variant هدف است | Business System mission، patch مستقیم Integration یا reconstruction کل System مرجع | `agent/roles/AR06-feature-worker.fa.md` |

`AR03 integration-developer` برای **شروع یک Engineering Session مستقل** که مأموریت اصلی‌اش patch خود Integration است در همین Registry قابل انتخاب است. اما AR03 مقصد role-switch داخل یک Business/System Session فعال نیست: AR01/AR02/AR04/AR05/AR06 Integration gap را در همان Role گزارش می‌کنند و repair در Session/Process مهندسی جدا با AR03 شروع می‌شود.

Aliases مهاجرتی فقط برای resolve Prompt قدیمی‌اند و Role مستقل نیستند:

- `developer` → `AR03 integration-developer`
- `system-designer` → `AR02 system-designer`
- `azmoongar-1` → `AR04 reference-reconstruction-evaluator`
- `azmoongar-2` → `AR05 requirement-to-change-evaluator`

Alias طبیعی Feature Worker:

- `fworker` → `AR06 feature-worker`

نمونه resolve طبیعی: `نقش توسعه‌دهنده سیستم را داشته باش.` → `AR01 system-developer`.
