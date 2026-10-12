# Report / Folder — design and usage guidance

Report primitive اصلی query/collection/projection/aggregation است؛ Folder فقط navigation/placement است. قرارداد exact Report/Column/FieldItem/Parameter/Folder lifecycle و read/write/read-back در DataExchange owner است:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/05-report-folder-reference.fa.md`

Condition technical contract مشترک Report/BusinessRule:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md`

## Report و Folder را جدا طراحی کن

- Report user-facing باید placement قابل دسترسی داشته باشد یا placement مناسب موجود reuse شود.
- Report helper داخلی برای Formula/query بی‌دلیل در navigation قرار نگیرد.
- hierarchy معمول navigation از System root به Page/Group و سپس Report می‌رسد؛ قبل از ساخت، hierarchy موجود را inspect و reuse کن.
- Report metadata را داخل Folder design ادغام نکن؛ این دو lifecycle جدا دارند.
- «قابل‌استفاده برای کاربر» یک outcome طراحی است: اگر placement مناسب موجود نیست، کوچک‌ترین Page/Group/Report placement لازم را در همان delivery طراحی کن؛ نام/hierarchy اضافی را بدون Requirement اختراع نکن. قرارداد فنی DX05 اجازه می‌دهد dependencyهای این زنجیره با `tempId` در یک logical Change wave حل شوند.
- اصطلاح «فایل مستقل Report» را object/design primitive جدید فرض نکن. در Source فعلی object مستقل Runtime همان Report metadata است و visibility/navigation با Folder report-placement ساخته می‌شود؛ شکل فایل JSON در Export فقط materialization است و قرارداد آن در DX06 است.

## انتخاب نوع Report

نوع Report را از نیاز مصرف انتخاب کن: list/query، tree، matrix، calendar، forum و سایر typeهای شناخته‌شده. وجود lifecycle پایه برای typeهای تخصصی مثل statistics/dashboard/print به معنی کامل‌بودن designer-specific payload آنها نیست؛ بخش unsupported را حدس نزن.

## Query semantics

برای هر Report لازم حداقل اینها در طراحی روشن باشند:

- source Entity؛
- projection/columnهای موردنیاز؛
- relation traversal واقعی؛
- parameters و اینکه input هستند یا runtime-supplied؛
- predicate/Condition؛
- sorting/grouping موردنیاز؛
- helper یا user-facing بودن؛
- placement در صورت user-facing بودن.

Query قوی‌تر/ضعیف‌تر را صرفاً به‌خاطر شباهت جای Query Requirement دیگری reuse نکن.

## SQL grouping vs presentation grouping

اگر Requirement aggregate/query-level grouping می‌خواهد با SQL grouping فکر کن؛ اگر فقط UI باید rowها را گروه‌بندی کند presentation/grid grouping مناسب‌تر است. این دو معنای متفاوت دارند و نباید برای convenience جای هم استفاده شوند. property/validation دقیق در DX05 است.

## Parameters و dependent candidates

برای dependent parameter intent را روشن کن: parent، child، candidate source، predicate وابستگی، رفتار قبل از انتخاب parent و refresh/reset بعد از تغییر آن. اگر Integration binding دقیق را پشتیبانی نمی‌کند، approximation خام نساز؛ Gap را حفظ کن.

Runtime-native parameterها را hard-code نکن؛ قرارداد دقیق در DX05/DX01 است.

## Formula columns و Field Formula

Report formula-column و Field formula compiler دو مسیر متفاوت‌اند. syntax یکی را به دیگری تعمیم نده. exact compiler/property contract در component owner است.

## Verification

semantic Read/Write/Verify metadata برای Report فقط همان metadata scope را اثبات می‌کند. برای Report user-facing، Verify outcome باید وجود Report، owner/target صحیح، hierarchy/placement طراحی‌شده و اشاره placement به همان Report را از read-back بررسی کند؛ duplicate ناخواسته failure است. query result/filter یا UI behavior در صورت اهمیت Requirement به smoke جدا نیاز دارد.

## Navigation Designer model

Root هر System خودکار است. Semantic hierarchy عملی: `Page → Group → placement`. Page/Group title/icon/parent/order Designer state هستند؛ placement target+parent+order دارد و title/icon از target derivable است. sibling order باید round-trip شود.

