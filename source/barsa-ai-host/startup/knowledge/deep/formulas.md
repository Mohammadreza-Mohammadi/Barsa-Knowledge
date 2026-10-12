# Field Formula — design/usage guidance

Formula برای **مقدار مشتق‌شده** است؛ event/condition/action را با BusinessRule و process persisted را با Workflow مدل کن.

دو کاربرد اصلی در Source جاری وجود دارد:

- **code formula**: محاسبه از Fieldها/منطق همان context.
- **query-backed formula**: محاسبه‌ای که به query/report helper و aggregation نیاز دارد.

JSON/property shape، compiler syntax، patch semantics، Writer lifecycle و execution defaults در DataExchange owner است:

- Field/Formula serialization & write contract: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/02-field-serialization.fa.md`
- dependency/deferred validation در Change/Plan/Apply: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/07-ai-change-runtime-reference.fa.md`

## Code formula

- اگر Requirement فرمول دقیق می‌دهد، معنی آن را حفظ کن و خودسرانه wrapper/cast/return اضافه نکن.
- Field reference را مطابق syntax رسمی SystemBuilder بنویس؛ syntax دقیق را از DX02 بخوان و از dbName/bare identifier حدس نزن.
- conversion فقط وقتی اضافه شود که type contract/Compiler واقعاً آن را لازم بداند.

## Query-backed / aggregate formula

وقتی مقدار از مجموعه Detail یا query حاصل می‌شود، shortcut expression حدسی نساز. الگوی مناسب معمولاً:

1. query/report helper روی source درست؛
2. parameter لازم برای context parent؛
3. predicate اتصال parent/detail؛
4. aggregation موردنیاز؛
5. Formula روی Field مقصد که به همان helper اشاره می‌کند.

Report helper داخلی navigation نمی‌خواهد مگر Requirement آن را user-facing کند.

برای parent/detail aggregate، الگوی conceptual معتبر این است: helper Report روی detail → external parent context → predicate اتصال detail به parent → aggregation → Formula روی Field مقصد. Runtime فعلی parent context را از مسیر external Report parameter پشتیبانی می‌کند؛ exact Parameter flags/injection در DX05 است.

Claim قدیمی که «aggregate expression الزاماً از اولین Column گزارش helper گرفته می‌شود» در Source بازبینی‌شده این مرحله authority کافی برای تبدیل به contract عمومی نشان نداد. آن را Rule یا payload assumption نکن؛ projection لازم گزارش را متناسب با Requirement طراحی کن و اگر behavior SQL به این جزئیات وابسته شد با Source/Runtime evidence جدا تأیید کن.

## Dependency و batching

Report helper و Formula می‌توانند در یک change coherent باشند اگر dependency فنی قابل بیان و تصمیم بعدی به read-back میانی نیاز نداشته باشد. mechanics دقیق temp reference/deferred compile متعلق به DX07 است.

## Verification

Metadata read-back باید تعریف Formula موردنظر را نشان دهد. این اثبات اجرای محاسبه روی data واقعی نیست؛ اگر correctness business به نتیجه runtime وابسته است و مسیر smoke واقعی وجود دارد، آن را جدا verify کن.
