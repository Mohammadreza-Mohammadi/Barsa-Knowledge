# View / Layout / BusinessRule

## View

View همان Entity data را با presentation/interaction متفاوت ارائه می‌کند. View فقط layout نیست؛ settings و runtime switching نیز دارد.

View جدید وقتی بساز که همان object در context/lifecycle متفاوت interaction متفاوت نیاز دارد.

### Default-first

قبل از ساخت View/Layout سفارشی بررسی کن آیا Requirement واقعاً interaction یا UX خاص می‌خواهد. اگر Layout/ترتیب/Group/Tab خاص، local readonly/visibility، selected Rule، Button/Command یا رفتار متفاوت فرم لازم نیست، View/Layout سفارشی نساز و از رفتار native/default موجود استفاده کن.

Blueprint برای هر Entity یکی از دو حالت را روشن کند:

- `native-default`: `Custom View/Layout required: no`؛ Action سفارشی View/Layout لازم نیست.
- `custom-exact`: فقط وقتی Requirement واقعاً آن را لازم دارد؛ نام/شناسه، default بودن، ترتیب Controlها، Group/Tab/Section، layout mode، local field settings، selected Rules و Command/Buttonهای لازم باید بدون ابهام مشخص باشند.

عبارت‌هایی مثل «فیلدهای اصلی شامل...» برای `custom-exact` کافی نیست. geometry/pixel/XML همچنان implementation detail است، نه بخش Blueprint.

## Layout

Layout باید semantic و UX-aware باشد؛ raw DevExpress XML، pixel، Location/Size contract AI نیست.

در inheritance:
- local/explicit state را design/write کن.
- effective/resolved state را copy-back نکن.
- `null` و local default معنی یکسان ندارند؛ Deep را ببین.


## Layout UX — default heuristic

برای فرم عملیاتی معمول:
- Fieldهای اصلی و پرتکرار بالا و بدون تغییر Tab دیده شوند.
- Fieldهای کوتاه و هم‌معنا در 1–2 ستون گروه‌بندی شوند.
- list/detail، متن بلند، فایل و بخش‌های ثانویه پایین فرم قرار گیرند.
- چند بخش ثانویه معمولاً در `tabs` تمام‌عرض پایین Root تمیزتر است.
- group/nesting فقط وقتی مفهوم یا جریان کار روشن ایجاد می‌کند اضافه شود.

اینها heuristic UX هستند، نه validation contract. geometry/pixel/XML همچنان generation detail است.

## BusinessRule

برای event/condition/action محلی فرم استفاده کن:
- visibility/read-only/mandatory state
- applyView
- field/action behavior
- validation/UX condition

Workflow را برای این رفتارهای کوتاه‌عمر نساز.

### Formula vs Rule

Formula = value derived.
BusinessRule = event/condition/action.

### Conditional Rule

Integration Condition مشترک Report/BusinessRule را reuse می‌کند. مدل Condition موازی یا raw dump نساز؛ exact shape در DX10 است.

## Security caution

Security-aware View/Rule برای UX خوب است، ولی backend enforcement مستقل است. Client/UI Rule را hard security boundary فرض نکن.

## When deep

- View inheritance و `selectedRules`.
- layout semantic tree.
- branch/condition/action design edge case.
- exact Change/property contract را از DX03/DX04/DX10 بخوان.
