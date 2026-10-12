# Codex / Direct Session Entry

این فایل entry point اجرایی است، نه authority موازی AR/SK/EM.

1. از `agent/role-registry.fa.md` Role مناسب Prompt طبیعی کاربر را resolve کن و `AR code + name + brief approach` را کوتاه اعلام کن.
2. Role انتخاب‌شده sticky است؛ silent role switching ممنوع است. `integration-developer / AR03` می‌تواند در ابتدای یک Engineering Session مستقل برای مأموریت patch Integration انتخاب شود، اما مقصد switch داخل Business/System Session فعال نیست؛ آن Session defect Integration را به‌صورت gap گزارش می‌کند و repair در Session مهندسی جدا شروع می‌شود.
3. Execution Mode را از environment/delivery تشخیص بده و کوتاه اعلام کن. این entry معمولاً `EM02 — Direct HTTP` است؛ Mode جدید اختراع نکن.
4. فقط سند Role فعال و references لازم آن را بخوان. مشاهده Role/Knowledge دیگر آن را فعال نمی‌کند.
5. Custom Prompt کاربر mission/scope/constraint همان Session است و taxonomy رسمی را بازتعریف نمی‌کند.
6. schema/API/capability حدسی نساز. برای Knowledge از `knowledge/00-start.fa.md` route کن و برای API از `host-api.fa.md` استفاده کن.
7. اگر Prompt برای شروع کافی است کار را طبق Workflow Role فعال شروع کن؛ صرفاً اعلام نکن «Startup را خواندم، حالا چه کار کنم؟».

Default response language فارسی است مگر کاربر صریحاً زبان دیگری بخواهد.
