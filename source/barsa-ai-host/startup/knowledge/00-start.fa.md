# SystemBuilder Knowledge — Start

برای طراحی عادی SystemBuilder، normative مسیر Agent از `knowledge/bsdn/00-start.fa.md` و `skills/05-ai-skills.fa.md` می‌آید. Working Knowledge meaning/when/design guidance را می‌دهد؛ exact machine contract نزد component مالک است.

## Authority

```text
Requirements = requested behavior / constraints
Overall + Detailed BSDN = Desired Design Authority
Support Mapping = feasibility/support
DX / Writer = exact technical contract
Runtime / Semantic = Actual Implementation evidence
KM = knowledge cache, not Design authority
```

Previous Change/Package و Conversation memory جای canonical artifacts را نمی‌گیرند.


## Current Semantic v15 knowledge

- Current knowledge baseline: `knowledge/semantic-v15-current.fa.md`
- Current project/certification status: `knowledge/semantic-v15-status.fa.md`
- Exact machine contract: `dataexchange/13-semantic-v15-reference.fa.md`

برای Semantic v15، این baseline بر prompt/knowledge قدیمی مقدم است مگر Source واقعی SystemBuilder contradiction قطعی نشان دهد. تصمیم‌های بسته‌شده دوباره redesign نشوند؛ در uncertainty، `GAP/Unsupported` بهتر از heuristic/fallback است.

## Design routing

```text
Sources
→ System/Section Requirements
→ Overall BSDN per System
→ Detailed BSDN per Section
→ completeness/minimality + cross-scope check
→ Support Mapping
→ Feature/Deep knowledge only as needed
→ exact DataExchange contract
→ Generate SystemBuilder Actions
→ Build / Read-back / Verify
```

Design اولیه `Entity/Relation Skeleton ↔ Process/Actor/Form/Output Skeleton` است. Detailed BSDN باید `Complete in Elements / Sparse in Obvious Properties` باشد.

## Knowledge routing

- BSDN authority/lifecycle: `knowledge/bsdn/00-start.fa.md`
- Design heuristics: `knowledge/design.fa.md`
- feature guidance: `knowledge/features/*`
- complex patterns only when needed: `knowledge/patterns.fa.md`
- infrastructure capabilities lookup-first: `knowledge/infrastructure-capabilities/*`
- feature/designer evidence + certification: `knowledge/feature-evidence.fa.md`
- current support summary: `knowledge/support-matrix.fa.md`
- exact DataExchange contract: `dataexchange/*` in Package Mode / Source owner in repository

## Feature routing

```text
data / identity        → Entity / Field / Relation
presentation           → View / Layout
calculated value       → Formula
conditional form UX    → BusinessRule
query / list           → Report
persisted process      → Workflow
runtime/config context → Parameter / Setting / Config
structured domain cfg  → Settings Entity
custom behavior        → Code only when declarative is insufficient
security boundary      → Security
```

## Capability boundary

SystemBuilder core capability و Integration support یکی نیستند. نبود support core Desired Design را کوچک نمی‌کند؛ Support Mapping gap را نگه می‌دارد. Optional/external/deployment capability می‌تواند early-probe شود. exact core contract shape مثل performer/condition/relation/update-delete/local-ref قبل از persistence validate می‌شود.

## Evidence

Real System/Failure/Scenario evidence است، نه Best Practice خودکار. Rule عمومی باید authority یا reasoning قابل تعمیم داشته باشد. Metadata verification و behavioral runtime proof جدا گزارش شوند.

برای feature-level unknown/gap:

```text
Full JSON + Semantic JSON + Designer Evidence only where needed
→ expected design meaning
→ optional isolated reconstruction
→ Apply / Read-back / Verify
→ classified evidence
```

`Designer Evidence` Screenshot/Video/observed interaction از Designer UI است و با BIX `Snapshot Diagnostics` یکی نیست. قواعد کامل در `knowledge/feature-evidence.fa.md` است.
