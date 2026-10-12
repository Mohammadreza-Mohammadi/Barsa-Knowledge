# Field / Relation — design guidance

این سند برای **انتخاب semantic type و رفتار مناسب** است؛ property/writeStatus/constructor/serialization دقیق فقط نزد DataExchange تعریف می‌شود:

- type/property capability: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/01-field-types-reference.fa.md`
- semantic serialization/write shape: `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/02-field-serialization.fa.md`

## انتخاب نوع

- نوع را از معنای domain انتخاب کن، نه از convenience UI یا CLR guess.
- Relation را وقتی بساز که identity/ownership/navigation واقعی بین objectها وجود دارد؛ برای متن/عدد ساده relation نساز.
- one-to-many، many-to-many، hierarchy و inheritance semantics یکسان نیستند؛ primitive نزدیک به Requirement را انتخاب کن.
- system-managed/audit fields را فقط وقتی Requirement یا lifecycle واقعی ایجاب می‌کند صریح طراحی کن.
- binary/file/picture semantics را از data requirement جدا کن؛ configured state read-back جای payload write نیست.

## Update

تغییر type موجود را design shortcut فرض نکن. اگر Requirement type fundamentally دیگری می‌خواهد، migration impact را در Design روشن کن. missing property/no-change، writer-specific limits و delete mechanics در DX01/DX02 است.

## Formula/default value

Formula برای derived value است؛ DefaultValue برای initial/default semantics. query-backed Formula را با Report helper واقعی طراحی کن و raw serialized metadata نساز. guidance بیشتر: `knowledge/deep/formulas.md`.

## Native parameters و advanced FieldInfo

بعضی Field types behavior/parameterهای native دارند. از نام مشابه capability جدید اختراع نکن؛ exact runtime names/values را فقط از DX01 بگیر.

## Verify boundary

semantic read-back باید intent درخواست‌شده را نشان دهد؛ internal defaults/caches را به requirement تبدیل نکن. persistence یا behavior خارج metadata در صورت اهمیت، verification جدا می‌خواهد.

## Portable binary Designer state

وجود image/icon فقط با `configured:true` برای reconstruction کافی نیست. Semantic باید payload را به package asset قابل حمل تبدیل کند و Writer/Verifier همان asset contract را consume/verify کنند. Hash برای integrity است؛ source Runtime id identity asset نیست.

