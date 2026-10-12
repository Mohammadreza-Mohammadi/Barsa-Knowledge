# BusinessRule / UniqueConstraint — design guidance

BusinessRule برای event/condition/action محلی metadata است؛ UniqueConstraint برای uniqueness واقعی data. technical property/persistence/Writer contract فقط در DataExchange است:

- Rule/Constraint: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/04-business-rules-constraints.fa.md`
- Condition مشترک: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md`

## انتخاب primitive

- validation/visibility/editability/form action محلی → BusinessRule.
- uniqueness data → UniqueConstraint، نه Rule نمایشی.
- process persisted یا چندمرحله‌ای → Workflow، نه Rule.
- derived value → Formula، نه Rule مگر event/action requirement مستقل وجود داشته باشد.

## Rule شرط‌دار

conditionها را با leaf/all/any معنا بده و branchها را فقط به اندازه Requirement اضافه کن. Else fallback است. Parameter semantics گزارش را به BusinessRule تعمیم نده.

Action target باید متعلق به context همان Rule باشد؛ از reference حدسی یا UI caption مبهم برای دورزدن capability استفاده نکن.

## View selection و UX

Rule می‌تواند بخشی از interaction یک View باشد، اما local UI rule امنیت backend نیست. selected Rule را فقط وقتی design آن View نیاز دارد pin کن.

## عدم حدس

اگر action/event/condition موردنیاز در Support Matrix/technical owner روشن نیست، payload داخلی Runtime نساز؛ Gap را ثبت و به capability/source review برگرد.
