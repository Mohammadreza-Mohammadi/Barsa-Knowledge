# Design Patterns — Use Only When Complexity Is Real

این Patternها از Systemهای واقعی و Knowledge Pack استخراج شده‌اند. **Default design نیستند.** فقط وقتی Requirement واقعاً چند Feature/lifecycle پیچیده دارد از آنها استفاده کن.

## 1. Base Entity + Subtype Family

```text
Base Entity
├─ Subtype A
├─ Subtype B
└─ Subtype C
```

مناسب وقتی domain واقعاً family از نوع `is-a` دارد و identity/lifecycle/Fieldهای مشترک در Parent معنی دارند. برای variation ساده یا reuse چند Field، inheritance نساز.

## 2. Lifecycle-specific Views

```text
base/inherited View
+ status/access condition
+ BusinessRule.applyView
→ create/review/approved/read-only View
```

وقتی همان object در مرحله‌های مختلف interaction متفاوت دارد. Viewهای متعدد را برای تفاوت ظاهری جزئی نساز؛ تفاوت lifecycle/interaction باید واقعی باشد.

## 3. Generic Workflow on a Polymorphic Family

یک Workflow عمومی می‌تواند روی family subtypeها reuse شود و تفاوت‌ها با hook/actor/subprocess مناسب مدیریت شوند. Workflow inheritance را به‌عنوان default فرض نکن.

مناسب وقتی process اصلی مشترک است ولی subtype behavior محدود و مشخص دارد.

## 4. Explicit Workflow ↔ Domain Status Bridge

Workflow runtime state و business status دو مفهوم مستقل‌اند. اگر business object باید status داشته باشد، sync را explicit طراحی کن؛ از runtime state به‌طور implicit business meaning نساز.

## 5. Security-aware UI, Separate Enforcement

BusinessRule/View می‌تواند براساس access/service condition UI مناسب نشان دهد؛ این UX است. Backend/Code enforcement همچنان boundary مستقل دارد.

## 6. ReportRelation for Operational Collection UI

برای collection query-driven که ownership/FK مستقیم لازم ندارد، `ReportRelation` می‌تواند embedded operational list بدهد. آن را جای domain Relation واقعی استفاده نکن.

## 7. Query-based Integration Entity

برای dataهای external/subsystem/core که مصرف read-centric دارند، query/view-backed Entity در سیستم‌های واقعی دیده شده است. فقط وقتی source data بیرونی است و CRUD مستقل SystemBuilder لازم نیست مناسب است.

## 8. Hierarchical Base Information

Hierarchy برای taxonomy/organization tree واقعی مناسب است. صرف recursive بودن یک relation دلیل استفاده از hierarchical infrastructure نیست.

## قاعده استفاده

قبل از انتخاب Pattern:

1. Requirement فعلی بدون Pattern حل می‌شود؟ اگر بله، همان راه ساده‌تر را نگه دار.
2. Pattern با semantics domain تطابق دارد یا فقط شبیه UI نمونه است؟
3. آیا Real System فقط evidence استفاده است، نه Best Practice مطلق؟
4. آیا Integration فعلی Featureهای لازم را Write می‌کند؟ `knowledge/support-matrix.fa.md` را ببین.
