# Change Construction — guidance

این سند راهنمای **ساخت Change از طراحی مصوب** است؛ قرارداد machine-level Change/Plan/Apply اینجا تعریف نمی‌شود.

مرجع فنی canonical DataExchange برای envelope، patch، reference/tempId، dependency/order، `ErrorPolicy`، deferred validation، Provider resolution، skipped states، Plan/Apply و Verify:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/07-ai-change-runtime-reference.fa.md`

قراردادهای Feature-specific در `01..05` DataExchange همان component هستند.

## هدف Change Construction

Change باید intent طراحی مصوب را به کمترین مجموعه mutationهای روشن تبدیل کند؛ **حق ندارد Design جدید اختراع کند**. اگر طراحی برای تبدیل به Change کافی نیست یا capability لازم در Integration وجود ندارد، مسئله به Design/Support Matrix برگردد.

## Grouping منطقی

- mutationهایی که یک intent واحد و dependency روشن دارند می‌توانند یک گروه coherent باشند.
- فقط برای راحتی implementation، یک Requirement را بی‌دلیل per-object یا per-report خرد نکن.
- برعکس، بخش‌هایی را که تصمیم مرحله بعد واقعاً به Runtime read-back مرحله قبل وابسته است در یک Change مبهم ادغام نکن.
- diagnosability مهم است: گروه باید آن‌قدر کوچک باشد که failure قابل نسبت‌دادن بماند، و آن‌قدر بزرگ که dependency طبیعی Requirement را نشکند.
- siblingهای مستقل را بی‌دلیل reorder نکن؛ ترتیب business/design را حفظ کن مگر dependency واقعی خلاف آن را ایجاب کند.

## Dependency مفهومی

قبل از ساخت payload این وابستگی‌ها را در طراحی تشخیص بده:

- مالکیت: System → Entity → Field/View/Report و سایر childها.
- reference: یک object به object دیگری که باید وجود داشته باشد وابسته است.
- semantic prerequisite: مثلاً Formula query-backed به Report helper واقعی نیاز دارد.
- navigation فقط وقتی Requirement user-facing بودن را می‌خواهد dependency delivery است؛ helper داخلی را بی‌دلیل در Folder قرار نده.

نحوه بیان فنی dependency/temp reference و ترتیب Planner فقط در DX07 تعریف می‌شود.

دو boundary مهم هنگام ساخت payload:

- **Entity completeness را به machine invariant تبدیل نکن.** Requirement ممکن است Entity را همراه Field/Relation بخواهد و Design باید همان outcome را کامل کند، اما Planner حق ندارد صرفاً چون Create Entity در همان Batch Field/Relation ندارد آن را invalid کند. این تصمیم design-level است.
- **Relation را به شکل Field Change نفرست.** scalar/non-relation Field از `objectType:"field"` استفاده می‌کند؛ relation semantic از `objectType:"relation"` و `properties.fieldType` دقیق (`singleRelation`, `listRelation`, ...) استفاده می‌کند. parent/targetهای same-wave می‌توانند typed `tempId` باشند و اگر DX07 آنها را resolve می‌کند، گرفتن real ID به‌تنهایی دلیل split نیست.

## استفاده از Feature knowledge

- Entity/Field/Relation: `knowledge/features/entity-field-relation.fa.md`
- View/Layout/Rule: `knowledge/features/view-layout-rule.fa.md`
- Report/Folder: `knowledge/features/report.fa.md`
- Formula: `knowledge/deep/formulas.md`
- Condition: `knowledge/deep/conditions.md`
- Workflow: `knowledge/features/workflow.fa.md`

برای property/JSON/writeStatus دقیق به DataExchange owner مراجعه کن، نه به این سند.

## قواعد تصمیم

- Requirement و Design را به payload shape تبدیل نکن تا Support Matrix همان capability را تأیید نکرده باشد.
- unsupported feature را با primitive غیرهم‌معنا شبیه‌سازی نکن.
- raw Runtime/serialized metadata را برای پرکردن gap تولید نکن.
- اگر کاربر متن exact code/formula داده، آن را بدون دلیل معنایی بازنویسی نکن.
- failure یک Change دلیل تغییر Skillهای دیگر نیست؛ منشأ failure را route کن.

## Verify boundary

Change success با Verify مستقل سنجیده می‌شود. semantic metadata verification اثبات رفتار UI/data execution نیست؛ smoke رفتاری فقط وقتی لازم و ممکن است جدا انجام شود.
