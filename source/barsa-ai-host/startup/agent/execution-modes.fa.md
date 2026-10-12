# Execution Modes

Execution Mode فقط transport/execution mechanics است؛ AR workflow یا Skill semantics را تکرار نمی‌کند.

## EM01 — Package

```text
Host ↔ upload/download artifacts ↔ Agent
```

Agent HTTP مستقیم به Host انجام نمی‌دهد. Host Package Protocol عملیات معنایی را به Runtime/Knowledge lifecycle route می‌کند. Bootstrap اولیه دو artifact هم‌Exchange-ID دارد: `<EID>-START-HERE.en.md` و `<EID>-upload-ai-gen.zip`.

## EM02 — Direct HTTP

Agent Host API را برای همان عملیات معنایی فراخوانی می‌کند. EM02 فقط وقتی انتخاب شود که environment/delivery قرارداد مستقیم Host API را واقعاً expose کرده باشد؛ initial Package bundle آن قرارداد را حمل نمی‌کند. اگر چنین قرارداد مستقیمی در environment موجود نیست، EM01 انتخاب شود.

## Selection

کاربر لازم نیست EM را بداند. Agent آن را از environment/delivery/resources موجود resolve و ابتدای Session کوتاه اعلام می‌کند. Mode تازه اختراع نمی‌شود. تغییر EM به معنی تغییر AR نیست.
