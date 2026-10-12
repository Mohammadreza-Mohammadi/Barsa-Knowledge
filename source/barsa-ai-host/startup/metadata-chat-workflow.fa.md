# Barsa Package Exchange — User Flow

کاربر در `EM01 — Package` فقط artifactها را جابه‌جا می‌کند؛ HTTP مستقیم Agent به Host بخشی از این Mode نیست.

Bootstrap اولیه:

```text
ABC0001-START-HERE.en.md
ABC0001-upload-ai-gen.zip
```

هر دو `ABC0001` Exchange ID مشترک دارند. START-HERE مستقل از ZIP و bootstrap authority است؛ ZIP منابع اجرایی و `chat-protocol.json` را حمل می‌کند و `00-START-HERE` ندارد.
START-HERE تا قبل از اولین download معتبر/پردازش‌شده همان Session active می‌ماند؛ پس از ساخته‌شدن پاسخ upload بعدی، Host آن را حذف نمی‌کند و همراه artifactهای مصرف‌شده همان Session به `used/` منتقل می‌کند. failure قبل از activation باعث archive آن نمی‌شود.

ادامه exchange:

```text
ABC0002-download-ai-gen.zip
ABC0003-upload-ai-gen.zip
ABC0004-download-ai-gen.zip
...
```

- `ABC`: session سه‌حرفی Host.
- sequence مشترک رفت‌وبرگشت است.
- `upload/download` از دید کاربر است.
- command/action/schema از `chat-protocol.json` همان exchange گرفته می‌شود و حدس زده نمی‌شود.

مسیرهای workspace/state داخلی Host contract کاربر/Agent نیستند.

- Exchange ID/sequence پس از expose immutable است؛ retry/correction sequence جدید می‌گیرد.
- tempId فقط در همان Change معتبر است؛ wave بعد real ID را از result/session reference map و در اختلاف از Runtime read-back می‌گیرد.
