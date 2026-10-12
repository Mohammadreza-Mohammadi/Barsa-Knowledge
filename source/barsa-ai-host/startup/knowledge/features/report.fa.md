# Report / Query / Folder

## Report چیست

Report را primitive مرکزی query/collection/projection/aggregation ببین، نه فقط چاپ.

Use when:
- list/search/query لازم است.
- projection یا relation-path لازم است.
- parameter/condition/sort/group لازم است.
- aggregate/query helper لازم است.
- collection query-backed باید در UI مصرف شود.

## Report vs View

- View → interaction یک object.
- Report → collection/query/projection.

## Folder / delivery

Folder/navigation جای placement است؛ Report metadata و navigation exposure را یکی فرض نکن.

- Report **user-facing** که Requirement می‌گوید کاربر آن را ببیند/استفاده کند، فقط با وجود Metadata کامل تلقی نمی‌شود؛ باید placement قابل دسترسی داشته باشد یا placement موجود مناسب reuse شود.
- Report helper داخلی برای Formula/query navigation نمی‌خواهد مگر Requirement صریحاً آن را user-facing کند.
- برای navigation hierarchy معنادار `Page → Group → Report` را در نظر بگیر و قبل از Mutation Context موجود را ببین؛ property/lifecycle دقیق Folder در DX05 است.

## Current Integration

Integration برای Reportهای معمول semantic read/write/verify و اجزای query رایج را دارد؛ جزئیات exact در DX05 است. typeهای تخصصی ممکن است فقط common lifecycle/support داشته باشند؛ designer-specific payload را حدس نزن. Condition semantics بین Report و BusinessRule مشترک است و technical contract آن در DX10 است.

## Query contract و reuse

برای `EXISTS / NOT EXISTS / SUM / COUNT` و هر Query چندرکوردی که در Rule، Guard، Formula، Report یا Button مصرف می‌شود حداقل این semantics را روشن کن:

- Source Entity
- Parameters
- Predicate
- Aggregation یا نحوه مصرف نتیجه
- Freshness در نقطه تصمیم
- اگر edit/current-row مهم است، self-exclusion یا semantics رکورد جاری

این Queryها را Condition ساده Field-to-Field جا نزن.

دو Query/Predicate فقط وقتی reuse شوند که semantics آنها **معادل** باشد. subset/superset یا اشتراک بخشی از conditionها equivalence نیست؛ Query قوی‌تر یا ضعیف‌تر را جای Requirement دیگر نگذار.

## Dependent parameter / candidate source

اگر انتخاب یک Parameter به Parameter دیگر وابسته است، intent وابستگی را صریح طراحی کن:

- Parent parameter
- Child parameter
- candidate source
- filter relation/predicate
- رفتار Child قبل از انتخاب Parent
- reset/refresh رفتار Child هنگام تغییر Parent

اگر Writer contract دقیق candidate binding معلوم نیست، payload حدس نزن و selector بدون فیلتر را approximation قرار نده؛ intent صحیح را نگه دار و `Integration Gap` ثبت کن.

## Action-ready Report

برای Report لازم، source entity، پارامترهای مرتب، parameter behavior، condition/null semantics، ستون‌های مرتب، sort در صورت نیاز، helper یا user-facing بودن، placement برای Report کاربر و dependent candidate source در صورت وجود باید روشن باشد. فقط propertyهایی را pin کن که Requirement یا correctness به آنها وابسته است.

## انتخاب‌های کاربردی

- UX پنل Parameter، runtime-supplied parameter و candidate dependencies را در طراحی روشن کن؛ property/value دقیق را از DX05 بگیر.
- native Parameterهای FieldInfo را hard-code نکن؛ exact names/behavior در DX01/DX05 است.
- inline editing، alternate edit target و parameter-entity فقط وقتی Requirement interaction آنها را می‌خواهد انتخاب شوند؛ contract دقیق در DX05 است.

## Common mistakes

- duplicate کردن data برای گزارش.
- استفاده از View به‌عنوان query collection.
- ساخت Report helper و قرار دادن بی‌دلیل در navigation.
- flatten کردن relation path یا حدس payload وقتی Runtime evidence کافی نیست.

## When deep

برای design/edge case عمیق `knowledge/deep/reports-folders.md` و `knowledge/deep/conditions.md` را بخوان؛ برای JSON/write/read exact به DX05 و DX10 route کن.

## Portable Report local references

Parameter در scope Report با name/local semantic reference شناخته می‌شود، نه Runtime parameter id. constant user/data نیز raw source row id را Design identity نمی‌داند. Navigation leaf به Report target متصل است؛ leaf title/icon از target derivable است و sibling order Design fact است.

