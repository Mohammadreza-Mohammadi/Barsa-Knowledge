# View / Layout — design guidance

View presentation/interaction یک Entity است. Layout arrangement semantic همان View است. exact property shape، inheritance serialization، Writer/parser و persistence contract فقط در DataExchange است:

`source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/03-view-layout-reference.fa.md`

## Default-first

View/Layout سفارشی فقط وقتی بساز که Requirement interaction یا UX متفاوت می‌خواهد. اگر رفتار default native کافی است، metadata اضافه نساز.

## Inheritance

local/explicit intent را طراحی کن؛ effective/resolved state را copy-back نکن. inherited، local-empty و local-default ممکن است معنای متفاوت داشته باشند؛ technical null/default contract را از DX03 بگیر.

## Layout structure

- Fieldهای اصلی و پرتکرار در مسیر دید سریع باشند.
- Group/Tab فقط وقتی مفهوم یا workflow روشن ایجاد می‌کند اضافه شود.
- list/detail، متن بلند و فایل معمولاً بخش ثانویه‌اند.
- raw pixel/geometry/DevExpress XML design contract AI نیست.

## Rule integration

selected BusinessRule/Constraint فقط وقتی View واقعاً به آن interaction نیاز دارد اضافه شود. Rule design در `knowledge/deep/rules-constraints.md` است.

## Verify boundary

semantic layout verification metadata را تأیید می‌کند؛ rendering واقعی UI proof جداست. normalization/persistence دقیق در DX03 است.
