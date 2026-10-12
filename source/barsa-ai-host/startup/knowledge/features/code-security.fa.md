# Code / Security

## Code

اولویت عمومی:

```text
Declarative Metadata
→ Wrapper / MetaObject
→ Direct SQL فقط برای نیاز خاص
```

Code وقتی justified است که Metadata/Formula/Rule/Report/Workflow کافی، خوانا یا مناسب performance/integration نباشد.

کاربردهای واقعی Code شامل BL/UI UserCode، Formula/Expression compiled، service/integration و generated wrapper است.

Dynamic Code در branch بررسی‌شده sandbox فعال قابل اتکا نشان نداده؛ builder code را trusted code ببین.

Standalone generic Code writer در Integration فعلی وجود ندارد. Code مربوط به Formula/Rule/Report از contract همان Feature پیروی می‌کند.

## Security

Security یک plane واحد نیست. بسته به Feature می‌تواند Entity/Object، Field، Report، View/Form/Record، Service و navigation را درگیر کند.

### اصل مهم

Security UI/report را enforcement خودکار Code مستقیم فرض نکن. Code/Integration باید boundary لازم را صریح رعایت کند.

## Current Integration

دانش Read/Design Security وجود دارد، ولی general semantic Security writer فعلی وجود ندارد. payload یا permission mutation حدسی ساخته نشود.
