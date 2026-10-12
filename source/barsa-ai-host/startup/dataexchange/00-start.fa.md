# Barsa.Meta.DataExchange — AI Technical Docs

این پوشه فقط contractهای فنی مستقیم DataExchange با SystemBuilder و storage/helperهای متعلق به همین component را نگه می‌دارد.

مرجع روش کار Agent، طراحی و Working Knowledge عمومی SystemBuilder:

`source:Meta/Core/Barsa.Ai.Host/Docs/AI/knowledge/00-start.fa.md`

محتوای این پوشه:

- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/01-field-types-reference.fa.md` — mapping فنی FieldInfo/Designer/Create-Update.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/02-field-serialization.fa.md` — قرارداد semantic serialization Field.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/03-view-layout-reference.fa.md` — قرارداد فنی View/Layout serializer/writer.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/04-business-rules-constraints.fa.md` — قرارداد فنی Rule/Constraint.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/05-report-folder-reference.fa.md` — قرارداد فنی Report/Folder.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/06-bix-snapshot-reference.fa.md` — Full/Semantic projection، Snapshot materialization و diagnostics contract.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/07-ai-change-runtime-reference.fa.md` — AiChangeBatch، patch/tempId/dependency، Plan/Apply/ErrorPolicy/Verifier contract.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/08-provider-development-reference.fa.md` — provider resolution/development و specialized/generic provider contract.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/09-knowledge-storage-reference.fa.md` — storage/lifecycle فنی HK/KM روی Entityهای موجود.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/10-condition-reference.fa.md` — قرارداد machine-level مشترک Condition برای Report/BusinessRule.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/11-workflow-reference.fa.md` — قرارداد exact Workflow definition/graph writer, same-wave references و Runtime Verify.
- `source:Meta/Core/Barsa.Meta.SemanticExchange/Docs/AI/12-dynamic-command-reference.fa.md` — قرارداد exact Dynamic Command usage/settings writer و read-back برای capabilityهای supported.

دانش طراحی مثل «چه زمانی Report یا Relation انتخاب شود» در این component تکرار نمی‌شود.
