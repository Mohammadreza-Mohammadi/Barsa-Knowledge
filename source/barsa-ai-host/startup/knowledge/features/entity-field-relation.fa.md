# Entity / Field / Relation / Formula

## Entity

وقتی مفهوم data، identity یا lifecycle مستقل دارد Entity بساز.

نساز اگر فقط:
- چند مقدار ثابت است → enum مناسب‌تر است.
- presentation متفاوت همان داده است → View مناسب‌تر است.
- relation صرفاً data خودش ندارد → Relation مستقیم کافی است.

## Completeness طراحی Entity

به‌عنوان **design guidance**، Entity جدید معمولاً وقتی deliverable کامل محسوب می‌شود که ساختار لازم Requirement (مثلاً Field/Relationهای واقعاً لازم) نیز در design آن مشخص شده باشد؛ ساخت container خالی به‌عنوان پایان delivery معمولاً نشانه design ناقص است. این قاعده **Runtime validation اجباری DataExchange نیست**؛ `AiEntityChangeProvider` فعلی create Entity را صرفاً به‌دلیل نداشتن Field/Relation رد نمی‌کند.

## Field

Field property یک Entity است. type را براساس semantic value انتخاب کن؛ نه براساس convenience UI.

راهنمای انتخاب پرتکرار:
- شمارنده صحیح واقعی → `int`.
- مقدار اعشاری → `decimal` با precision فقط به‌اندازه نیاز واقعی.
- مبلغ → `money`.
- شماره خودکار کسب‌وکاری → معمولاً `sequence`؛ نه `string` دستی یا timestamp workaround.
- `referenceField` فقط وقتی semantics واقعاً reference به Field دیگر است؛ مقدار ذخیره/محاسبه‌شده‌ای مثل قیمت را صرفاً به‌خاطر منشأ آن `referenceField` نکن.
- `totalDigits`/تنظیمات advanced را فقط با Requirement واقعی صریح کن.

### Uniqueness

- invariant یکتایی تک‌Field → `isUnique` در صورت پشتیبانی Field.
- invariant یکتایی چندField → `UniqueConstraint`.
- UniqueConstraint invariant داده است؛ BusinessRule جای آن نیست.

برای انتخاب/معنای type از `knowledge/deep/field-types.md` استفاده کن؛ exact type/property/write contract را از `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/01-field-types-reference.fa.md` و `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/02-field-serialization.fa.md` بگیر.

### Logical Delete

فقط برای Entityهایی که Logical Delete روی آنها فعال است:
- Delete اول معمولاً `IsDeleted=1` و Delete دوم همان record را physical delete می‌کند.
- Reportها معمولاً deletedها را فیلتر می‌کنند، ولی همه load pathها را خودکار filtered فرض نکن.
- restore/archive policy اگر Requirement دارد جدا طراحی شود.

## Relation

در مرحله Change Construction، Relation هرچند در Runtime با `FieldDef` identity ذخیره می‌شود، **Field Change نیست**: `objectType:"relation"` استفاده کن و semantic type را در `properties.fieldType` بفرست. `objectType:"field" + fieldType:"singleRelation/listRelation/..."` اشتباه contract است. exact shape در DX02 و envelope/tempId در DX07 است.

### 1:N معمول

```text
Child.singleRelation → Parent
Parent.reverseSingleListRelation → همان Child.singleRelation   # فقط اگر collection معکوس لازم است
```

reverse field نمایش سمت مقابل همان رابطه است، نه relation مستقل دوم.

`listRelation` را برای master-detail عادی جایگزین FK نکن؛ independent many-to-many semantics دارد.

### `SplUser`

اگر هنگام resolve کردن نوع/Entity به `SplUser` رسیدی، آن را در System `Meta01` پیدا و resolve کن.

Hint: `fieldType:"user"` برای ارجاع به کاربر معتبر است. اگر نیاز با هر دو مدل کامل برآورده می‌شود، ترجیحاً از `singleRelation` به `SplUser` استفاده کن تا قابلیت‌های کامل‌تر Relation در دسترس بماند؛ `user` را صرفاً به‌خاطر این ترجیح خطا حساب نکن.

### Relation با data/lifecycle

Entity واسط مستقل بساز.

### Composition

Composition را وقتی Parent واقعاً مالک lifecycle Child است بررسی کن. حذف Parent می‌تواند Child را حذف کند و بعضی copy/dropdown behaviorها نیز تغییر کنند؛ آن را ضمانت transaction/atomic cascade فرض نکن، چون مسیرهای event/history کاملاً symmetric نیستند.

### reportRelation

برای مجموعه query-backed/operational display است؛ domain FK را جایگزین نمی‌کند.

### Inheritance

فقط وقتی relationship واقعاً `is-a` و family polymorphic است. برای reuse ساده inheritance نساز.

## Formula

- مقدار مشتق ساده/محاسباتی → Formula.
- `code` و Report-backed `query` در Integration فعلی پشتیبانی می‌شوند.
- Aggregate روی detail در SystemBuilder با Report helper واقعی مدل می‌شود، نه expression حدسی `Sum(...)`.

## Common mistakes

- Entity واسط بی‌دلیل برای 1:N.
- listRelation فقط برای نمایش detail.
- hard-coded duplicated data برای report.
- calculation یکسان در Client و Server.
- SQL مستقیم برای CRUD معمول وقتی Runtime object lifecycle لازم است.

## When deep

- Field type semantics یا edge case طراحی خاص.
- relation advanced/inheritance/reportRelation.
- Formula query/aggregate design.
- Change grouping/dependency guidance؛ exact payload/write contract نزد DataExchange است.

## Portable relation/data design rule

Semantic relation linkage باید Designer concept را بیان کند: reverse list relation به **direct field** وصل می‌شود و RelationDef داخلی هنگام Write resolve می‌شود. Metadata reference (Field/Entity/Report) با data-row reference یکی نیست. record/user dependency باید readable meaning داشته باشد ولی target deployment resolution باید deterministic و fail-closed باشد؛ caption-only identity ممنوع است.

