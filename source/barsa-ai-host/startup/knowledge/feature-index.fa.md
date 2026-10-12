# Feature Index

| نیاز | Feature اصلی | Working doc | Deep در صورت نیاز |
|---|---|---|---|
| داده، Field، ارتباط دامنه | Entity / Field / Relation | `knowledge/features/entity-field-relation.fa.md` | `knowledge/deep/field-types.md`, `knowledge/deep/change-model.md` |
| فرم، Layout، Viewهای مختلف | View / Layout | `knowledge/features/view-layout-rule.fa.md` | `knowledge/deep/views-layouts.md` |
| رفتار شرطی فرم / validation UX | BusinessRule | `knowledge/features/view-layout-rule.fa.md` | `knowledge/deep/rules-constraints.md`, `knowledge/deep/conditions.md` |
| مقدار محاسباتی | Formula | `knowledge/features/entity-field-relation.fa.md` | `knowledge/deep/formulas.md` |
| query/list/projection/aggregate | Report | `knowledge/features/report.fa.md` | `knowledge/deep/reports-folders.md`, `knowledge/deep/conditions.md` |
| فرایند پایدار چندمرحله‌ای | Workflow | `knowledge/features/workflow.fa.md` | Knowledge Pack / Source؛ safe-core Write/Verify در DX11 |
| runtime/config/user settings | Parameter / Setting / Config / Settings Entity | `knowledge/features/settings-deployment.fa.md` | Knowledge Pack / Source |
| import/export/deployment | BIX / deployment lifecycle | `knowledge/features/settings-deployment.fa.md` | Knowledge Pack / Source |
| BL/UI custom، integration | Code | `knowledge/features/code-security.fa.md` | Knowledge Pack / Source |
| access/security boundary | Security | `knowledge/features/code-security.fa.md` | Knowledge Pack / Source |
| feature/variant unknown، Semantic gap، Read/Write/Verify certification | Feature Certification / Designer Evidence | `knowledge/feature-evidence.fa.md` | exact owner Source/Runtime only after case classification |

اگر Requirement چند Feature را با هم ترکیب می‌کند یا lifecycle پیچیده دارد، بعد از Featureهای اصلی `knowledge/patterns.fa.md` را ببین.

قبل از تولید Change، `knowledge/support-matrix.fa.md` را کنترل کن. وجود Feature در SystemBuilder به معنی Write support کامل Integration نیست. برای evidence-driven certification یا meaning ناشناخته، `knowledge/feature-evidence.fa.md` مرجع روش است؛ یک case موفق همه variantها را خودکار Certified نمی‌کند.
