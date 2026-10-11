# Intake — .agent-work/tasks/0001-بارکدخوان-های-فعال

Task dir: .agent-work/tasks/0001-بارکدخوان-های-فعال
Attempt dir: .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/001

## نقش تو

یک درخواست خام انسان را به `proposed-task.md` با Acceptance Criteria شماره‌دار
تبدیل کن. تصمیم طراحی نگیر، contract را نخوان، batch ننویس.

## Context Package (فقط همین‌ها)

- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/001/request.md
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/001/previous-rejection.md — **اگر وجود دارد، اول همین را بخوان.**
  یعنی attempt قبلی همین نقش رد شده و این فایل دقیقاً می‌گوید چرا.

هیچ فایل دیگری لازم نداری. اگر واقعاً به چیزی بیرون این لیست نیاز داشتی، صریح
در خروجی بنویس — این خودش یک یافته است، نه چیزی که پنهان شود.

## خروجی مجاز

- .agent-work/tasks/0001-بارکدخوان-های-فعال/proposed-task.md
- .agent-work/tasks/0001-بارکدخوان-های-فعال/release-note.md — هم‌زمان، نه بعداً.
- .agent-work/tasks/0001-بارکدخوان-های-فعال/attempts/001/result.yaml — با `role: intake`، `outcome`، و
  `requestedTransition` (معمولاً `architecture`).

`result.yaml` را همیشه بنویس، حتی اگر به نظرت کاری نبود. «کاری نبود» یک نتیجه
است. `outcome` دقیقاً یکی از این چهار: `completed` | `failed` |
`needs_clarification` | `blocked`.

`manifest.yaml`، `events.jsonl` و `task.md` مال Manager است — ننویسشان.

## قالب proposed-task.md

```markdown
# <یک خط، چه چیزی در بارسا ساخته/عوض می‌شود>

## نیاز
<دو سه خط، به زبان درخواست‌دهنده>

## نوع نیاز
kind: report.create | report.update | report.delete | entity.create |
      field.add | folder.place
system: 1011413550000000100

## Acceptance Criteria
- AC-1 ...
- AC-2 ...
```

هر AC باید شماره‌دار باشد، چون Reviewer دقیقاً روی همین شماره‌ها جدول شواهد
می‌سازد. اگر درخواست مبهم بود، ابهام را در یک AC صریح کن یا صریح علامت بزن که
`needs_clarification` لازم است. حدس زدنِ بی‌صدا را نکن.

## قالب release-note.md

این فایل برای **کاربری که درخواست داده** نوشته می‌شود، نه برای مهندس بعدی. از
دید نتیجه بنویس، نه از دید تغییر.

```markdown
---
userVisible: true
headline: "یک خط، حداکثر ۷۲ کاراکتر، نتیجه از دید کاربر"
---

حداکثر ۳ پاراگراف. بدون نام فیلد/جدول/selector، بدون شناسه.
```

اگر چیزی برای کاربر دیده نمی‌شود: `userVisible: false` به‌همراه `reason`.
