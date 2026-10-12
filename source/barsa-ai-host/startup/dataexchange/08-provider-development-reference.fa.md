# DataExchange Provider Development Reference

این سند مالک راهنمای توسعه Providerهای Semantic Change در `Barsa.Meta.DataExchange` است. Host Provider semantics یا patch/lifecycle قرارداد DataExchange را تعریف نمی‌کند.

## قبل از تغییر Provider

1. semantic Feature و intent آن را از Working Knowledge مشخص کن؛ مرجع Source آن: `source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/00-start.fa.md`.
2. وضعیت support واقعی را از `source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/support-matrix.fa.md` بخوان.
3. Source رسمی Designer/Runtime/SystemBuilder را برای create/update/delete و side-effectها بررسی کن.
4. کمترین Provider تخصصی لازم را بساز؛ framework عمومی قبل از نیاز نساز.

## قواعد Provider

- Specialized Provider بر generic مقدم است.
- Generic fallback فقط وقتی مجاز است که mutation عمومی واقعاً امن باشد؛ fallback فعلی در نبود support صریح `Unsupported` است.
- Runtime API رسمی باید lifecycle را انجام دهد؛ AI/DataExchange layer نباید schema/ID/RelationDef/cache behavior متعلق به SystemBuilder را تقلید کند.
- Update patch-based است؛ property غایب no-change است.
- local/explicit state نوشته می‌شود، نه effective/inherited state.
- dependency و temp-id از Core مشترک Change/Planner reuse می‌شوند و Provider قرارداد موازی نمی‌سازد.
- read-back/verifier باید همان semantic contract Feature را ببیند.
- validation deferred فقط وقتی استفاده می‌شود که Runtime reference لازم هنوز به‌علت tempId وجود ندارد؛ بعد از resolve باید با Provider واقعی تکرار شود.

قرارداد عمومی Batch/Plan/Apply/`ErrorPolicy`/dependency در:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/07-ai-change-runtime-reference.fa.md`

## پایان تغییر Provider

برای Feature touched، این حلقه باید با contract همان Feature هم‌راستا بماند:

```text
Read contract
Write contract
Plan validation
Apply
Runtime read-back
Verify
support-matrix
Feature/technical reference when needed
```

اگر Source برای بخشی کافی نیست، همان بخش `Unsupported/Pending` بماند؛ API/property یا behavior حدسی ساخته نشود.

## Ownership

- serializer/provider/action contract → همین component و `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/*`.
- Host orchestration/endpoint → `source:Meta/Core/Barsa.Ai.Host/Docs/AI/host/*`.
- SystemBuilder design guidance → `source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/*`.

تعریف یک contract کامل Provider در Host یا Working Knowledge duplication محسوب می‌شود.
