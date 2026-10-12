# BSDN — راهنمای شروع

BSDN مرجع **Desired Business/System Design** است؛ Requirement می‌گوید چه می‌خواهیم، Runtime می‌گوید چه واقعاً ساخته شده و Support Mapping می‌گوید Integration فعلی چه مقدار از Design را می‌تواند پیاده کند.

مسیر استاندارد AR01:

```text
Sources
→ System / Section Decomposition
→ Section Requirements
→ Overall BSDN per System
→ Detailed BSDN per Section
→ Cross-System / Cross-Section Design Check
→ Support Mapping
→ Generate SystemBuilder Actions
→ Build / Apply
→ Runtime Read-back
→ Verify
→ Verified Release
```

دو کنترل دائمی در همه مراحل:

```text
Completeness
+
Minimality
```

## Scopeهای اصلی

سه Scope را یکی نکن:

```text
Solution Landscape
= تمام System/Sectionهای شناخته‌شده Current/Future/External/Reference

Current Delivery Scope
= scopeای که Requirement و Design آن در Mission/Release جاری باید کامل و cross-checked شود

Current Build Scope
= subsetای که در Wave فعلی واقعاً Apply می‌شود
```

```text
Current Build Scope ⊆ Current Delivery Scope ⊆ Solution Landscape
```

Future/Deferred غیرمسدودکننده نباید Build جاری را متوقف کند؛ ولی dependency material آنها روی Current Delivery Scope باید روشن باشد.

## Authorityهای اصلی

```text
Requirements
= truth of requested behavior / constraints

Overall + Detailed BSDN
= Desired System Design truth

Support Mapping
= technical support / feasibility truth

Runtime / Read-back
= Actual Implementation truth

Current Progress
= operational snapshot

Action / Change / Package
= implementation mechanism

Verified Release
= immutable historical verified checkpoint
```

Chat، Previous Change/Package، Runtime و Current Progress جای canonical Requirement/BSDN را نمی‌گیرند.

## Canonical artifact contract

ساختار پیش‌فرض پروژه‌های بزرگ:

```text
artifact:requirements/<system>/<section>.md
artifact:design/overall/<system>-BSDN.md
artifact:design/systems/<system>/<section>-BSDN.md
artifact:operations/current-progress.md
artifact:operations/support-mapping/<system-or-platform>.md
artifact:operations/releases/<release>.md
```

- `System = folder / owner boundary`
- `Section = canonical detailed Requirement/BSDN scope`
- artifactهای Process/Workflow/Entity/Report جدا به‌صورت taxonomy اصلی نساز.
- `One Design Fact → One Canonical Owner`.
- split فیزیکی فقط `Move, Not Copy` است.
- Requirement/BSDN canonical باید portable Markdown باشند؛ Direct Build فقط presentation را می‌تواند skip کند، نه artifact authority را.

## Design rule

Detailed BSDN باید:

```text
Complete in Elements
Sparse in Obvious Properties
```

باشد. اگر Workflow بیست Activity material دارد، همه باید دیده شوند؛ ولی propertyهای بدیهی Writer به Generate Actions واگذار شوند.

Design اولیه هر System/Section همزمان این دو skeleton را refine می‌کند:

```text
Entity / Relation Skeleton
↔
Process / Actor / Form / Output Skeleton
```

## Build / Verify rule

قبل از mutation:

```text
Requirement/Design current scope ready
+ Support Mapping ready
+ exact core contract shape validated
+ material ambiguity = 0
+ canonical artifacts current
+ execution authorized
```

Core capability نبودن در Integration مجوز redesign نیست. اگر exact performer/condition/relation/update/delete shape قابل بیان نیست: `No mutation`، BSDN unchanged و Implementation Gap ثبت شود.

بعد از partial mutation:

```text
STOP
→ Runtime Read-back
→ Reconcile actual persisted state
→ Recovery decision
```

Blind retry/create/update ممنوع است.

Verify در سطوح Step/Wave، Section، System و Final Delivery انجام می‌شود و همیشه Runtime را با **Current Target BSDN** مقایسه می‌کند، نه با Previous Package.

## برای جزئیات

- notation و ownership: `knowledge/bsdn/standard.fa.md`
- lifecycle/continuation/build: `knowledge/bsdn/lifecycle.fa.md`
- verification: `knowledge/bsdn/verification.fa.md`
- Design heuristics: `knowledge/design.fa.md`
