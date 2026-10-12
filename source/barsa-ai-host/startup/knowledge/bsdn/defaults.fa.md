# BSDN v0.5 — Defaults

Defaults برای فشرده نگه‌داشتن BSDN هستند، نه برای پنهان‌کردن تصمیم طراحی.

اصل:

> اگر omission باعث دو طراحی مؤثر شود، آن مورد Default نیست و باید صریح نوشته شود.

در v0.5 عمداً Default فنی گسترده‌ای برای propertyهای SystemBuilder تعریف نمی‌شود.

موارد قابل حذف:
- ستون‌های عادی Report وقتی نقش خاصی ندارند.
- جزئیات ظاهری کم‌اثر View وقتی Layout خاصی طراحی نشده.
- metadata داخلی/شناسه Runtime.
- تنظیمات فنی‌ای که رفتار معمول SystemBuilder آنها را قطعی می‌کند و انتخاب طراحی جدید نمی‌سازد.

مواردی که در صورت غیر بدیهی بودن نباید حذف شوند:
- مقصد Relation
- تک/چند بودن Relation
- ترکیبی/سلسله‌مراتبی/معکوس بودن مؤثر
- محل منطق
- Event یک Rule
- نقش/مسئول Activity
- شرط شاخه مهم
- Workflow Completion Contract و end-state effectهای material
- View اصلی/خاص در صورت تصمیم طراحی
- Aggregate/Subreport/Code Column مهم
- Binding منطقی خارجی

رشد Defaultها:

```text
یک BSDN
→ دو پیاده‌سازی مستقل
→ مشاهده اختلاف
```

اختلاف غیرمؤثر → candidate Default.
اختلاف مؤثر → باید در BSDN صریح شود.
