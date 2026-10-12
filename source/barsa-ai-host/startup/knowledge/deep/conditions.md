# Condition — semantic/design guidance

Condition یک predicate قابل ترکیب برای Report و BusinessRule است. در طراحی آن را به سه primitive مفهومی ببین:

- **leaf**: یک predicate روی Field/path و یک operator/value/parameter.
- **all**: همه childها باید برقرار باشند.
- **any**: حداقل یک child برقرار باشد.

این ساختار می‌تواند recursive باشد. هدف Knowledge انتخاب درست predicate و composition است؛ JSON canonical، compatibility، normalization، Writer/serialization و persistence contract در DataExchange تعریف می‌شود:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md`

## انتخاب شرط

- شرط ساده را با leaf ساده نگه دار؛ بی‌دلیل به custom SQL/code تبدیل نکن.
- برای چند requirement همزمان از `all` استفاده کن؛ برای alternatives واقعی از `any`.
- nesting فقط وقتی منطق Requirement واقعاً precedence جدا می‌خواهد اضافه شود.
- relation traversal را از path رسمی metadata استفاده کن؛ SQL join حدسی نساز.
- null/date behavior را بر اساس semantics Requirement انتخاب کن؛ enum/value فنی را از DX10 بگیر.

## Report Parameter

Condition گزارش می‌تواند به Parameter همان Report وابسته باشد. اگر Parameter از Runtime/FieldInfo مقدار native می‌گیرد، dynamic value را hard-code نکن. BusinessRule parameter list گزارش ندارد؛ پس parameter-backed Report semantics را به Rule تعمیم نده.

فهرست و shape دقیق Parameter/Condition در DX10 و contract Report در DX05 است.

## BusinessRule branches

برای Rule بدون Condition، action مستقیم کافی است. وقتی رفتار شرط‌دار لازم است:

- هر branch یک Condition و actionهای خودش دارد.
- Else fallback است، نه شرط دوم مصنوعی.
- Else را از نظر طراحی آخر در نظر بگیر؛ branch بعد از Else معنای قابل اتکایی برای طراحی جدید ندارد.
- condition/action structure را فقط به اندازه Requirement پیچیده کن.

BusinessRule technical contract: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/04-business-rules-constraints.fa.md`.

## Edge cases و عدم حدس

- predicateهای aggregate/cardinality روی collection فقط وقتی طراحی شوند که capability واقعی SystemBuilder و Integration برای آنها روشن باشد.
- custom SQL/code آخرین انتخاب است، نه جایگزین shortcut برای primitiveهای موجود.
- نمونه واقعی evidence است؛ operator یا pattern جدید از یک نمونه منفرد تعمیم داده نشود.
