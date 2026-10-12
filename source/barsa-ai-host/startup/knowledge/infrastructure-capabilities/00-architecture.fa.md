# دانش عملیاتی قابلیت‌های زیرساختی پیش‌فرض

## وضعیت سند

- نوع: Host Operational Capability Knowledge
- دامنه فعلی: فقط capabilityهای پیش‌فرض canonical شده برای Build
- محل Host: `knowledge/infrastructure-capabilities/*`
- این سند فقط دانشی را نگه می‌دارد که Agent در Build فعلی باید مصرف کند.
- Generic discovery/extraction، Global ID architecture و طراحی عمومی extension infrastructure در Host Knowledge فعلی قرار نمی‌گیرند.
- این Knowledge، Role/Skill contract نیست؛ BSDN authority نیست؛ DX/Writer authority نیست؛ Runtime registry جدید نیست.
- BSDN تصمیم مؤثر Design را تعیین می‌کند؛ این Knowledge mechanism semantic/Settings contract شناخته‌شده را برای selection می‌دهد؛ exact machine mapping فقط نزد DX/Writer می‌ماند.

---

# 1. Scope فعلی

Host فقط سه family زیر را canonical می‌کند:

1. Role / Actor / Performer Calculation
2. Advanced / Custom Workflow Activity
3. Dynamic Command Definition / Usage

Membership فقط از curated latest lists همین سه family می‌آید.

Base Entities و persisted samples فقط برای فهم Settings contract و wiring استفاده می‌شوند و membership جدید ایجاد نمی‌کنند.

Inactive registrationها از Catalog عملیاتی حذف می‌شوند.

تمام registrationهای active موجود در Catalog از نظر Host **هم‌سطح** هستند.

> Active capabilityها رتبه‌بندی، کم‌اهمیت، specialized یا legacy فرض نمی‌شوند مگر اینکه source صریحاً آن را inactive/deprecated اعلام کرده باشد.

Selection فقط بر اساس semantic fit انجام می‌شود.

وضعیت curation فقط یکی از این سه مقدار است:

```text
confirmed
inferred
needs-review
```

Persisted usage، code، export یا documentation فقط **نوع evidence** هستند و status جدید ایجاد نمی‌کنند.

---

## v136 — Family + Caption → Runtime ID Resolution

در Barsa برای registrationهای Infrastructure، Knowledge عدد Runtime ID را نگه نمی‌دارد و GlobalId نیز در این مسیر استفاده نمی‌شود. ورودی قابل فهم Build همان **family واقعی registration + عنوان canonical آن** است.

```text
Business intent
→ registration family واقعی deployment
→ عنوان registration در Knowledge/Change
→ Central Infrastructure Registration Resolver
→ Runtime numeric Id همین deployment
→ Settings metadata / Writer wiring
```

قواعد:

- Family باید از metadata معتبر خود platform بیاید، نه حدس Writer. برای Workflow Performer، family از `ActorDefInfo.AssignmentTypeDef` و relation field `نحوه محاسبه → TargetTypeId` resolve می‌شود.
- عنوان registration locator معنایی/خوانای Knowledge است؛ Runtime numeric ID فقط نتیجه lookup همان deployment است و در فایل Knowledge hard-code نمی‌شود.
- Resolver مرکزی از `TypeDef.DefaultFieldId`، `FieldDef.FieldInfo as StringInfo` و `TypeDef.DbName` استفاده می‌کند و فقط همان registration لازم را از DB می‌خواند؛ کل Catalog در startup preload نمی‌شود.
- normalization متن Metadata با helper خود Platform (`FixFarsiText`) انجام می‌شود؛ اختلاف `ی/ي` و `ک/ك` mismatch نیست.
- lookup موفق در process cache می‌شود: `(TypeDefId + normalized caption) → RuntimeId` و reverse `(TypeDefId + RuntimeId) → caption`. Cache فقط optimization است و semantic authority جدید ایجاد نمی‌کند.
- Plan/Preflight همه registrationهای لازم را قبل از اولین mutation resolve می‌کند؛ Apply همان Runtime IDs resolved را مصرف می‌کند و Writer وسط mutation دوباره DB/catalog lookup نمی‌کند.
- Caption برای **پیداکردن record داخل family صحیح** مجاز و لازم است؛ اما Writer نباید business behavior را با branchهایی مثل `if (caption == "پایان")` استنتاج کند. Settings Type از metadata خود registration (`موجوديت پارامتر` / `فرم ويرايش`) می‌آید.
- اگر record پیدا نشد یا ambiguous بود، همان command در preflight fail می‌شود و Workflow mutation شروع نمی‌شود.

این مدل عمداً symbolic capability key جداگانه تعریف نمی‌کند. نام قابل فهم همان عنوان واقعی registration در family مربوط است.

---

# 2. Identity در Host Knowledge

برای این سه Infrastructure family، Host Knowledge identity عملیاتی را با **family + canonical registration caption** بیان می‌کند. مثال:

```text
Family: نحوه محاسبه
Caption: (کاربر) آغاز کننده فرآیند

Family: تعریف دستور پویا
Caption: نمایش پیغام
```

Runtime numeric ID بخشی از Knowledge نیست و هنگام Plan از DB همان deployment resolve می‌شود. GlobalId در این مسیر استفاده نمی‌شود.

### Canonicalization Caption برای Runtime resolution

Captionهای Knowledge می‌توانند با glyphهای فارسی نوشته شوند. Resolver قبل از query از convention موجود Platform (`FixFarsiText`) استفاده می‌کند و سپس query محدود روی Default String Field همان TypeDef می‌زند. Verification/read-back نیز همان normalization را برای comparison مصرف می‌کند.

این normalization فقط lookup/compare را پایدار می‌کند؛ Caption رفتار Business را تعیین نمی‌کند و numeric ID نیز semantic identity دائمی نیست.

---

# 3. حداقل Contract لازم برای Build

برای هر capability:

```text
Capability semantic identity
Purpose
When to use
When not to use

Settings:
  none
یا
  Settings Entity semantic identity
  semantic fields required to create Settings object
  type/reference semantics

Family usage wiring
```

Settings/Parameter Entity باید شناخته شود چون Builder ممکن است لازم باشد object واقعی از همان Entity بسازد.

---

# 4. سه wiring canonical

## Actor / Performer

```text
WorkflowActorDef
-> انتخاب انجام‌دهنده
-> Calculation Registration
-> optional Settings object
```

## Advanced Activity

```text
WorkflowActivityDef
-> Advanced Activity Registration
-> usage-specific Settings object
```

## Dynamic Command

```text
MetaCommand / supported parent
-> Dynamic Command usage
-> Dynamic Command Definition
-> usage-specific Settings object
```

---

# 5. Code Evidence

Raw Win/Web/Business/Calculation code Knowledge مصرفی Agent نیست.

در curation از code فقط برای استخراج semantic behavior استفاده می‌شود:

- what it does
- inputs / outputs
- side effects
- when to use
- when not to use
- limitations

Agent در Build نباید برای فهم default capability دوباره code را reverse-engineer کند.

---

# 6. Build-time Rule

```text
Approved BSDN
-> required capability
-> Host Capability Knowledge
-> semantic selection
-> DX support check
-> targeted runtime resolution / availability / binding
-> Implementation Mapping
-> Change
```

ممنوع:

```text
Build
-> scan unrelated Systems
-> inspect persisted examples
-> rediscover default mechanisms
```

Persisted sample فقط evidence curation است.

---

# 7. Absent from Knowledge

> `Absent from Knowledge != Unsupported`

اگر capability در Catalog فعلی نیست، وضعیت عملیاتی آن **Unknown / not covered by current Knowledge scope** است؛ نه `Unsupported`.

نبود capability در Catalog فعلی مجوز discovery آزاد Systemهای دیگر در Build نیست. Agent باید Knowledge/Capability gap را گزارش کند.
