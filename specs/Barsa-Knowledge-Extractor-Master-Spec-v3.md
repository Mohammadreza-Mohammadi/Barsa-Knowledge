# Barsa Knowledge Extractor — Master Specification v3

> نسخه: 3.0  
> وضعیت: Master Specification  
> هدف: استخراج یک Knowledge Layer قابل اعتماد از DLLهای Barsa، Exportهای Legacy و Exportهای JSON جدید، و منطق Import/Export  
> ورودی: `source/`  
> خروجی: `dist/`  
> اصل بنیادی: **هیچ Fact بدون Evidence تولید نشود و هیچ Format/Capability صرفاً از روی نام فایل یا حدس فرض نشود.**

---

# 0. چرا نسخه 3 لازم شد؟

تحلیل اولیه نشان داد Barsa حداقل دو خانواده Export دارد:

```text
1) Legacy MetaExport
   .metaexport
   ↓
   GZip
   ↓
   BinaryFormatter
   ↓
   System.Data.DataSet

2) Barsa.AiExport
   JSON-based
   profileVersion = 15
   ↓
   Variant A: single JSON document
   Variant B: ZIP package containing JSON files
```

همچنین در DLLهای Barsa APIهای Import/Export متناظر برای مسیر Legacy مشاهده شده‌اند، از جمله:

```text
BixHelper.Export(...)
BixHelper.Import(...)

NewExportManager.Export(...)
NewImportManager.Import(...)

SerializationHelper2.BinarySerializeToFile(...)
SerializationHelper2.DeserializeDataSetFromFile(...)

FixIdForImport.Init()
FixIdForImport.FixAll()

BixHelper.Clone(...)
```

این یافته‌ها باید در اجرای v3 **دوباره از Binary Evidence تأیید شوند** و صرفاً به عنوان حقیقت hard-code نشوند.

فرمت JSON جدید ممکن است هنوز در حال توسعه باشد و ممکن است نقص یا تفاوت رفتاری با Legacy داشته باشد.

بنابراین:

> Legacy MetaExport فعلاً **reference baseline** برای رفتار انتقالی شناخته‌شده Barsa است، نه حقیقت مطلق کل محصول.

و:

> Barsa.AiExport باید با Legacy، DLLها، Exporter و Importer به‌طور مستقل Cross-Validate شود.

---

# 1. ساختار Repository

ساختار پیشنهادی:

```text
repo/
│
├── source/
│   │
│   ├── dll/
│   │   ├── *.dll
│   │   └── *.exe
│   │
│   ├── exports/
│   │   ├── legacy/
│   │   │   └── *.metaexport
│   │   │
│   │   ├── ai-json/
│   │   │   ├── *.json
│   │   │   └── *.zip
│   │   │
│   │   └── pairs.json              # اختیاری
│   │
│   ├── exporter/
│   │   ├── source-code/
│   │   ├── decompiled/
│   │   └── notes/
│   │
│   ├── importer/
│   │   ├── source-code/
│   │   ├── decompiled/
│   │   └── notes/
│   │
│   ├── configs/
│   ├── executables/
│   └── supplemental/
│       ├── mrt/
│       ├── json/
│       └── other/
│
├── dist/
│
├── tools/
│
├── specs/
│   └── Barsa-Knowledge-Extractor-Master-Spec-v3.md
│
└── README.md
```

## 1.1 سازگاری با ساختار فعلی

اگر DLLها و Exportها مستقیماً داخل `source/` هستند، Extractor باید بدون نیاز به جابه‌جایی فایل‌ها آن‌ها را recursively پیدا و classify کند.

Classification نباید فقط بر اساس extension باشد.

مثلاً:

```text
*.zip
```

ممکن است:

```text
- ZIP واقعی باشد
- JSON متنی با extension اشتباه .zip باشد
```

پس همیشه باید ابتدا magic bytes / content sniffing انجام شود.

---

# 2. ورودی‌های فعلی شناخته‌شده

در ورودی فعلی حداقل چهار نمونه Export وجود دارد.

## Legacy samples

```text
*.metaexport
```

نمونه‌ها شامل فایل‌هایی از خانواده:

```text
Push Notification ... .metaexport
باركد ... .metaexport
```

مشاهده فعلی:

```text
GZip magic:
1F 8B

After GZip:
BinaryFormatter stream
System.Data assembly/type references
DataSet-based payload
```

## New AI/JSON samples

نمونه‌هایی از خانواده:

```text
Push Notification ... .zip
باركد ... .zip
```

مشاهده فعلی:

### نمونه Push Notification

فایل با extension `.zip` ولی content واقعی:

```text
UTF-8 JSON document
```

Root:

```json
{
  "tree": [...],
  "manifest": {
    "format": "Barsa.AiExport",
    "profileVersion": 15
  }
}
```

### نمونه باركد

ZIP واقعی با:

```text
manifest.json
+
multiple JSON files
```

Manifest مشاهده‌شده شامل:

```json
{
  "format": "Barsa.AiExport",
  "profileVersion": 15,
  "producer": "Barsa.Meta.DataExchange",
  "producerVersion": "4.1.203.0"
}
```

این اطلاعات باید توسط Extractor از خود فایل‌ها دوباره استخراج و Evidence شود.

---

# 3. اصل تشخیص Format

قبل از هر تحلیل Semantic:

```text
Detect Physical Format
      ↓
Detect Logical Format
      ↓
Detect Version
      ↓
Choose Parser
```

## Physical formats

```text
GZip
ZIP
Plain JSON
XML
Binary
Unknown
```

## Logical formats

```text
Barsa.LegacyMetaExport
Barsa.AiExport
Unknown
```

## Variant

```text
Legacy.DataSet.BinaryFormatter

AiExport.SingleJson
AiExport.ZipJsonPackage
```

Extension فقط یک hint است.

---

# 4. خروجی نهایی

تمام خروجی‌ها فقط در:

```text
dist/
```

قرار گیرند.

ساختار:

```text
dist/
│
├── README.md
├── MANIFEST.md
├── ARCHITECTURE.md
├── CAPABILITIES.md
├── DOMAIN-MAP.md
├── CONFIDENCE-REPORT.md
├── RUNTIME-GAPS.md
├── MISSING-INPUTS.md
├── REANALYSIS-REPORT.md
├── ERRORS.md
├── CHANGELOG.md
│
├── domains/
│   ├── authentication.md
│   ├── session-security.md
│   ├── startup-bootstrap.md
│   ├── metadata-system.md
│   ├── entities-fields-relations.md
│   ├── business-logic.md
│   ├── database-access.md
│   ├── navigator.md
│   ├── reporting.md
│   ├── stimulsoft.md
│   ├── forms-ui.md
│   ├── workflow.md
│   ├── serialization.md
│   ├── remoting.md
│   ├── configuration.md
│   ├── data-exchange.md
│   ├── legacy-metaexport.md
│   ├── ai-export.md
│   └── system-reconstruction.md
│
├── formats/
│   ├── format-detection.md
│   ├── legacy-metaexport.md
│   ├── legacy-dataset-schema.md
│   ├── id-reference-model.md
│   ├── ai-export.md
│   ├── ai-export-single-json.md
│   ├── ai-export-zip-package.md
│   ├── ai-export-profile-version.md
│   └── import-compatibility.md
│
├── comparison/
│   ├── legacy-vs-ai-export.md
│   ├── semantic-coverage.md
│   ├── missing-in-ai-export.json
│   ├── extra-in-ai-export.json
│   ├── mismatched-values.json
│   ├── mismatched-types.json
│   ├── id-mapping-differences.json
│   └── scope-equivalence.json
│
├── assemblies/
├── types/
├── scenarios/
├── models/
│   ├── normalized-system-model.md
│   ├── normalized-system-model.schema.json
│   ├── normalized-samples/
│   └── reconstruction-order.md
│
├── evidence/
│   ├── strings.md
│   ├── sql-fragments.md
│   ├── config-keys.md
│   ├── discovered-tables.md
│   ├── call-paths.md
│   ├── legacy-export-observations.md
│   ├── ai-export-observations.md
│   ├── importer-observations.md
│   ├── exporter-observations.md
│   ├── format-evidence.md
│   └── cross-validation.md
│
└── index/
    ├── assemblies.json
    ├── types.json
    ├── methods.json
    ├── properties.json
    ├── fields.json
    ├── references.json
    ├── capabilities.json
    ├── config-keys.json
    ├── sql-fragments.json
    ├── tables.json
    ├── export-formats.json
    ├── legacy-dataset-tables.json
    ├── ai-export-properties.json
    ├── import-actions.json
    ├── normalized-model.json
    └── knowledge-index.json
```

---

# 5. Confidence Model

هر Fact دقیقاً یکی از این‌ها را داشته باشد:

```text
CrossVerified
Verified
Observed
Inferred
Unknown
```

## CrossVerified

حداقل دو evidence مستقل و معنادار.

مثال:

```text
DLL contains relation metadata
+
Legacy export contains corresponding relation representation
+
Importer processes it
```

## Verified

مستقیماً در یک artifact قابل اثبات.

## Observed

از static behavior/call path دیده شده ولی اجرا نشده.

## Inferred

استنباط منطقی ولی غیرقطعی.

## Unknown

اطلاعات کافی وجود ندارد.

---

# 6. Evidence IDs

تمام Evidenceها stable ID بگیرند:

```text
EVID-DLL-000001
EVID-IL-000001
EVID-LEGACY-000001
EVID-AIEXP-000001
EVID-IMP-000001
EVID-EXP-000001
EVID-CONFIG-000001
```

هر Fact مهم حداقل یک Evidence ID داشته باشد.

---

# 7. اصل مهم: Legacy مرجع مقایسه است، نه حقیقت مطلق

به دلیل سابقه و وجود Importer متناظر، Legacy MetaExport برای بررسی compatibility **baseline قوی‌تری** است.

اما Extractor حق ندارد فرض کند:

```text
Legacy contains every Barsa feature
```

ممکن است قابلیت جدید فقط در AiExport وجود داشته باشد.

پس برای هر Concept:

```text
DLL evidence
Legacy evidence
AiExport evidence
Importer evidence
Exporter evidence
```

جداگانه گزارش شود.

---

# 8. Phase 1 — Input Discovery

کل `source/` recursively scan شود.

برای هر فایل:

```text
Path
Extension
MagicBytes
PhysicalFormat
LogicalFormat
SHA256
Size
DetectedEncoding
Confidence
```

---

# 9. Phase 2 — Assembly Inventory

برای Assemblyها:

```text
FileName
AssemblyName
AssemblyVersion
FileVersion
TargetFramework
Architecture
PublicKeyToken
MVID
SHA256
References
Resources
TypesCount
```

Managed و Native جدا شوند.

---

# 10. Phase 3 — Type / Method / IL Index

همان قواعد v2 حفظ شوند:

```text
Types
Methods
Properties
Fields
Events
Attributes
Inheritance
Interfaces
Calls
CalledBy
String literals
SQL
Config
Reflection
```

---

# 11. ECMA-335 Reader Limitations

اگر محیط decompiler کامل ندارد و reader اختصاصی استفاده می‌شود:

قابلیت‌های مطمئن:

```text
metadata tables
signatures
references
method tokens
basic IL opcode stream
string literals
direct call edges
```

قابلیت‌های محدود:

```text
complex control flow
virtual dispatch
delegates
state machines
async transformations
exception flow
reflection target resolution
dynamic invocation
```

این محدودیت‌ها باید در:

```text
RUNTIME-GAPS.md
```

ثبت شوند.

---

# 12. DataExchange Domain

`Barsa.Meta.DataExchange` و وابستگی‌های آن high priority هستند.

به‌طور خاص جستجو و تحلیل شوند:

```text
BixHelper
NewExportManager
NewImportManager
SerializationHelper2
ExportDataSource
ImportTreeForm
GetImportData
FixIdForImport
Clone
ExportJson
ImportJson
AiExport
profileVersion
manifest
```

وجود هیچ‌کدام hard-code نشود؛ باید verify شوند.

---

# 13. سؤال حیاتی 1 — Mapping واقعی API به Format

Extractor باید دقیقاً تعیین کند:

```text
BixHelper.Export
    → کدام format؟

BixHelper.Import
    → کدام format؟

NewExportManager.Export
    → کدام format؟

NewImportManager.Import
    → کدام format؟

BixHelper.ExportJson
    → Barsa.AiExport؟

آیا ImportJson وجود دارد؟

آیا Import() فرمت JSON را هم می‌پذیرد؟
```

این‌ها نباید از نام Method حدس زده شوند.

برای هر API:

```text
Input
Output
Physical format
Logical format
Serializer
Compression
Call path
Confidence
```

---

# 14. سؤال حیاتی 2 — آیا JSON Import دارد؟

باید روشن شود:

```text
Barsa.AiExport
```

فقط Export جدید است یا:

```text
Export + Import
```

هر دو را پشتیبانی می‌کند.

جستجو:

```text
ImportJson
AiImport
ReadAiExport
DeserializeAiExport
profileVersion
Barsa.AiExport
manifest.json
```

اگر پیدا نشد:

```text
Status: Unknown
```

نه:

```text
Unsupported
```

---

# 15. Legacy MetaExport Detection

برای `.metaexport`:

```text
GZip magic
↓
decompressed payload signature
↓
BinaryFormatter markers
↓
System.Data/DataSet evidence
```

ثبت شود.

هیچ unsafe BinaryFormatter deserialization با اجرای object graph انجام نشود مگر در sandbox اختصاصی و opt-in.

---

# 16. Legacy Payload Analysis

هدف:

کشف DataSet schema.

باید تا جای ممکن استخراج شود:

```text
DataTable names
Column names
Data types
Row counts
Primary keys
Reference columns
Special metadata tables
```

به‌خصوص:

```text
$IdEmbeddingFields
```

اگر واقعاً وجود داشت.

---

# 17. `$IdEmbeddingFields`

این table / structure high priority است.

مقادیر مشاهده‌شده احتمالی:

```text
pk
fk
idpattern
idlist
```

Extractor باید:

```text
raw value
normalized value
meaning
consumer method
affected table/column
```

را ثبت کند.

---

# 18. Case-insensitive normalization

اگر semantic markerهایی مثل:

```text
fk
FK
Fk
```

وجود داشتند:

برای comparison:

```text
normalized = lower-case invariant
```

ولی مقدار اصلی حفظ شود:

```json
{
  "raw": "FK",
  "normalized": "fk"
}
```

هیچ row فقط به دلیل casing حذف نشود.

---

# 19. SQL Identifier Casing

برای SQL Server identifierها comparison به شکل case-insensitive انجام شود، مگر evidence مشخص کند collation حساس به case است.

Original casing همیشه حفظ شود.

---

# 20. FixIdForImport Analysis

اگر مشاهده شد:

```text
FixIdForImport.Init()
FixIdForImport.FixAll()
```

باید Call Graph کامل‌تر استخراج شود.

هدف:

```text
How IDs are discovered
How PK/FK are remapped
How embedded IDs are rewritten
How idpattern/idlist work
When FixAll executes
```

---

# 21. Clone Semantics

اگر:

```text
BixHelper.Clone
```

Export و Import را chain می‌کند:

ثبت شود:

```text
Clone uses DataExchange roundtrip
```

و exact call path مستند شود.

این Evidence مهمی برای قابلیت Reconstruction است.

---

# 22. Legacy Import Tree / Diff

اگر:

```text
GetImportData()
→ IActiveDataSource
→ ImportTreeForm
```

تأیید شد، تحلیل شود:

```text
How incoming objects are represented
How current DB objects are compared
What change states/icons exist
Whether diff occurs before apply
```

اگر UI strings یا enums برای:

```text
Added
Changed
Deleted
Same
Conflict
```

وجود داشت استخراج شوند.

---

# 23. AI Export Detection

برای هر Barsa.AiExport:

manifest استخراج شود.

فیلدهای مهم:

```text
format
profileVersion
producer
producerVersion
buildId
```

Absent field باید absent گزارش شود، نه null فرضی.

---

# 24. AI Export Physical Variants

حداقل دو variant فعلی شناخته شده‌اند:

## Variant A — Single JSON

```text
physical = plain JSON
extension may be .zip
root:
  tree
  manifest
```

## Variant B — ZIP JSON Package

```text
physical = ZIP
contains:
  manifest.json
  hierarchical JSON files
```

Extractor باید تعیین کند این تفاوت ناشی از چیست:

```text
different API?
different option?
different selected scope?
different export profile?
different output mode?
different version?
```

تا زمان اثبات:

```text
Reason: Unknown
```

---

# 25. سؤال حیاتی 3 — چرا دو Variant JSON وجود دارد؟

در DLLها / exporter logic جستجو شود:

```text
SingleFile
Package
Zip
Archive
SplitFiles
ExportProfile
OutputMode
SaveAsZip
Tree
manifest.json
```

هدف:

یافتن switch واقعی بین:

```text
AiExport.SingleJson
AiExport.ZipJsonPackage
```

---

# 26. `profileVersion`

`profileVersion = 15` دیده شده.

باید مشخص شود:

```text
What is a profile?
Where profileVersion is declared?
Is 15 schema version?
Is it export selection profile version?
Does importer gate on it?
How does it evolve?
```

تا زمان اثبات فقط:

```text
Observed value: 15
Meaning: Unknown
```

---

# 27. Producer Version

اگر manifest شامل:

```text
producer = Barsa.Meta.DataExchange
producerVersion = 4.1.203.0
```

بود:

به Assembly inventory cross-link شود.

بررسی:

```text
does producerVersion equal assembly file version?
does it affect format?
```

---

# 28. AI Export Tree Schema

برای Single JSON:

تمام JSON pathها استخراج شوند.

مثال:

```text
$.tree[*]
$.tree[*].$type
$.tree[*].selector
$.tree[*].MetaTypeDef
$.tree[*].MetaReport
...
```

برای هر property:

```text
path
observed type
presence frequency
sample count
semantic guess
confidence
```

Semantic guess بدون Evidence باید `Inferred` بماند.

---

# 29. AI Export ZIP Schema

برای ZIP package:

```text
directory hierarchy
file naming
special bracketed folders
entity.json
view files
navigation files
manifest.json
```

تحلیل شود.

باید پاسخ دهد:

```text
Does directory hierarchy carry semantics?
Are names identifiers or captions?
Is selector stored inside files?
Can files be reordered?
```

---

# 30. `$type` Catalog

تمام مقدارهای:

```text
"$type"
```

جمع‌آوری شوند.

مثال‌های احتمالی:

```text
system
entity
field
relation
report
view
navigationReport
navigationGroup
navigationPage
```

فقط مقدارهای مشاهده‌شده ثبت شوند.

برای هر `$type`:

```text
count
properties
parent types
children
legacy counterpart
DLL counterpart
confidence
```

---

# 31. Selector Semantics

AiExport از patternهایی مثل:

```text
#EntityName
#FieldName
```

استفاده می‌کند.

باید مشخص شود:

```text
selector unique scope چیست؟
system-wide?
entity-local?
path-like?
caption-based?
stable across export?
used for relations?
```

بدون Evidence معنای selector حدس قطعی زده نشود.

---

# 32. ID Semantics در AiExport

بررسی شود:

```text
id
selector
DbName
target
parent references
```

آیا JSON جدید:

```text
raw DB IDs
```

را حمل می‌کند یا:

```text
semantic selectors
```

یا هر دو.

این برای portability حیاتی است.

---

# 33. Relation Semantics

برای relationها:

```text
$type
selector
fieldType
target
id
```

و هر property دیگر استخراج شود.

Legacy counterpart و DLL type پیدا شود.

---

# 34. Entity Semantics

برای entity:

```text
selector
caption
DbName
fields
views
relations
rules
```

فقط propertyهای مشاهده‌شده.

---

# 35. Report Semantics

برای reportها:

```text
metadata
query
template
parameters
custom fields
navigation presence
```

هر چیزی که واقعاً در sample یا DLL دیده شود.

---

# 36. Form / View Semantics

اگر Viewهای JSON وجود دارند ولی Legacy sample corresponding structure مبهم است:

وضعیت:

```text
AiExport: Observed
Legacy: Unknown/Observed
DLL: ...
```

جداگانه ثبت شود.

---

# 37. Workflow Semantics

عدم وجود workflow در sample به معنای عدم پشتیبانی format نیست.

باید بنویسد:

```text
Not observed in supplied samples
```

نه:

```text
Unsupported
```

---

# 38. Business Rules

اگر Business Rule در AiExport دیده شود:

```text
type
scope
code/definition
references
```

استخراج و با DLL/Legacy cross-map شود.

---

# 39. Scope Equivalence — قانون بسیار مهم

دو Export فقط وقتی Full Semantic Comparison شوند که Selection Scope آن‌ها معادل باشد.

Filename equality کافی نیست.

مثلاً:

```text
Push Notification
```

با:

```text
Push Notification + الگو + پورتال
```

ممکن است Scope یکسان نداشته باشد.

پس comparison pipeline:

```text
Extract selection roots
↓
Normalize semantic identity
↓
Compare selected object sets
↓
Compute scope-equivalence confidence
↓
Only then compare counts/content
```

---

# 40. Scope Equivalence Levels

```text
Exact
Partial
Candidate
Different
Unknown
```

## Exact

same semantic selected roots proven.

## Partial

shared subset proven.

## Candidate

filename/name resembles but not proven.

## Different

scope clearly differs.

## Unknown

insufficient evidence.

---

# 41. Optional `pairs.json`

اگر کاربر مطمئن است دو Export از یک Selection هستند، می‌تواند فایل اختیاری بدهد:

```json
[
  {
    "id": "barcode",
    "legacy": "source/exports/legacy/باركد....metaexport",
    "aiExport": "source/exports/ai-json/باركد....zip",
    "scope": "exact"
  }
]
```

ولی Extractor باید همچنان structural check انجام دهد.

---

# 42. Comparison Rule

اگر scope:

```text
Exact
```

باشد:

Full comparison.

اگر:

```text
Partial
```

باشد:

فقط intersection.

اگر:

```text
Candidate / Unknown
```

باشد:

هیچ compatibility percentage کلی تولید نشود.

---

# 43. Legacy → Normalized Adapter

Legacy parser باید DataSet representation را به `NormalizedSystemModel` تبدیل کند.

هر normalized property:

```text
value
source table
source column
source row identity
confidence
```

---

# 44. AiExport → Normalized Adapter

هر دو variant JSON باید به همان model تبدیل شوند.

هدف:

```text
Legacy
  ↓
NormalizedSystemModel
  ↑
AiExport
```

comparison باید روی normalized model انجام شود، نه raw serialization.

---

# 45. Normalized System Model

حداقل envelope:

```json
{
  "system": null,
  "entities": [],
  "fields": [],
  "relations": [],
  "reports": [],
  "views": [],
  "navigation": [],
  "businessRules": [],
  "workflows": [],
  "webServices": [],
  "extensions": {}
}
```

وجود collection به معنی support قطعی نیست.

هر section باید availability metadata داشته باشد.

---

# 46. Provenance در Normalized Model

هر node:

```json
{
  "_provenance": {
    "format": "Barsa.AiExport",
    "source": "...",
    "path": "...",
    "confidence": "Verified",
    "evidence": []
  }
}
```

---

# 47. Unknown vs Empty

قانون سخت:

```text
[] = proven empty
null = unknown/not extracted/not represented
```

مثال:

```json
"workflows": null
```

اگر sample اطلاعات کافی ندارد.

این اصل برای AI بسیار مهم است.

---

# 48. Semantic Identity

برای match کردن objectهای دو format اولویت:

```text
stable semantic key
selector
known mapped ID
DB name
type + name + parent
caption
```

Caption به تنهایی weak key است.

---

# 49. Match Confidence

هر matched object:

```text
ExactIdentity
StrongMatch
WeakMatch
Unmatched
```

WeakMatch نباید برای automatic bug assertion استفاده شود.

---

# 50. Legacy vs AiExport Comparison

برای scopeهای معادل:

```text
Systems
Entities
Fields
Relations
Reports
Views
Navigation
Rules
Workflow
WebServices
Other metadata
```

مقایسه شوند.

---

# 51. Difference Types

```text
MissingInAiExport
ExtraInAiExport
ValueMismatch
TypeMismatch
ReferenceMismatch
OrderingOnly
CasingOnly
RepresentationDifference
UnknownMapping
```

---

# 52. Bug Candidate Rules

یک تفاوت فقط وقتی `BugCandidate` باشد که:

1. scope equivalent باشد؛
2. semantic match قوی باشد؛
3. Legacy representation معتبر باشد؛
4. DLL/importer نشان دهد concept واقعاً مهم است؛
5. تفاوت صرفاً representation نباشد.

در غیر این صورت:

```text
Difference
```

نه Bug.

---

# 53. JSON Export Quality Report

تولید:

```text
comparison/semantic-coverage.md
```

مثال structure:

```text
Concept      Legacy   AiExport   Match Status
Entity       yes      yes        CrossVerified
Field        yes      yes        ...
Relation     yes      yes        ...
View         ?        yes        ...
Workflow     ?        ?          Unknown
```

---

# 54. Coverage Percentage Safety

درصد compatibility فقط وقتی تولید شود که:

```text
scope = Exact
+
identity matching sufficiently strong
```

در غیر این صورت:

```text
Compatibility percentage: Not computable
```

---

# 55. Importer / Exporter Re-analysis

با اطلاعات جدید این بخش باید **دوباره اجرا شود**.

هدف:

تفکیک call pathهای:

```text
Legacy export
Legacy import
AiExport export
AiExport import (if any)
```

---

# 56. Mandatory Re-analysis Questions

Agent باید این سؤالات را دوباره پاسخ دهد و در `REANALYSIS-REPORT.md` بنویسد:

### A. Export API mapping

```text
کدام Method دقیقاً Legacy تولید می‌کند؟
کدام Method AiExport تولید می‌کند؟
```

### B. JSON import

```text
آیا AiExport importer دارد؟
```

### C. JSON variant switch

```text
چرا یک AiExport plain JSON است و دیگری ZIP package؟
```

### D. profileVersion

```text
profileVersion=15 دقیقاً چیست؟
```

### E. scope

```text
هر sample دقیقاً چه object roots را شامل می‌شود؟
```

### F. ID model

```text
Legacy ID remap چگونه است؟
AiExport reference model چگونه است؟
```

### G. Diff

```text
ImportTreeForm diff دقیقاً چه states را نمایش می‌دهد؟
```

### H. transaction

```text
Import rollback/transaction واقعاً چگونه است؟
```

### I. duplicate policy

```text
Create / Overwrite / Skip / Merge / Fail؟
```

### J. version gate

```text
Core Version یا export version واقعاً validate می‌شود؟
```

---

# 57. Do Not Preserve Old Conclusions Blindly

v3 نباید صرفاً `dist/` قبلی را patch کند.

برای بخش‌های DataExchange:

```text
formats
import-export
normalized-model
cross-validation
capabilities
scenarios
```

باید re-analysis واقعی انجام شود.

DLL inventory فقط اگر hash/MVID تغییر نکرده reuse شود.

---

# 58. Existing Dist Migration

اگر `dist/` قبلی وجود دارد:

```text
dist-old/
```

یا snapshot داخلی گرفته شود.

v3 باید delta report تولید کند:

```text
What changed because dual-format export was discovered?
```

---

# 59. Capability Model Update

Capabilities باید format-aware شوند.

مثلاً:

```text
DataExchange.Legacy.Export
DataExchange.Legacy.Import
DataExchange.Legacy.Clone
DataExchange.Legacy.PreviewDiff

DataExchange.AiExport.Export
DataExchange.AiExport.Import   // only if verified
```

نه یک generic:

```text
System.Export
```

بدون distinction.

---

# 60. Scenario Model Update

سناریوها:

```text
export-system-legacy.md
import-system-legacy.md
clone-system-legacy.md
preview-import-diff.md

export-system-ai-json.md
import-system-ai-json.md      // only if verified
compare-legacy-ai-export.md
```

---

# 61. Security Rule — BinaryFormatter

Legacy payload نباید با untrusted runtime deserialization مستقیم باز شود.

Preferred:

```text
static binary inspection
isolated parser
safe schema extraction
sandbox
```

اگر اجرای BinaryFormatter برای تحقیق اجتناب‌ناپذیر بود:

```text
explicit opt-in
isolated process
no network
no credentials
throwaway environment
```

---

# 62. Export Sample Data Privacy

در docs فقط structure ثبت شود.

Business values شخصی/حساس کپی نشوند مگر برای Evidence ضروری و بعد redact شوند.

---

# 63. Error Model

Parser failureها باید format-specific باشند:

```text
PhysicalFormatDetectionError
GZipDecodeError
LegacyPayloadParseError
JsonParseError
ZipPackageError
ManifestError
NormalizationError
ScopeMatchError
SemanticMatchError
```

---

# 64. Deterministic Output

همه JSONها:

```text
stable ordering
stable IDs
UTF-8
pretty formatted
```

برای Git diff.

---

# 65. Incremental Mode

Hash شود:

```text
DLL
Legacy sample
AiExport sample
Exporter
Importer
Config
```

تغییر sample باید فقط pipelineهای وابسته را invalidate کند.

---

# 66. Dependency-based Cache Invalidation

مثلاً تغییر AiExport sample:

```text
re-run:
format detection
ai schema
normalization
comparison
knowledge index
```

ولی:

```text
do not re-run unchanged assembly inventory
```

---

# 67. Knowledge Index برای AI

`knowledge-index.json` باید task-oriented باشد.

Chunkهای مناسب:

```text
Barsa legacy import model
Barsa AiExport entity schema
Relation mapping
Report metadata
ID remapping
Navigator metadata
Stimulsoft integration
```

نه dump بزرگ method list.

---

# 68. Chunk Size

هر chunk:

```text
one coherent concept
source references
confidence
tags
```

از chunkهای چندده‌هزارخطی پرهیز شود.

---

# 69. Raw Index vs Agent Knowledge

دو سطح خروجی:

```text
Raw Technical Index
    ↓
Curated Knowledge Index
```

Raw:

```text
all types
all methods
all strings
```

Curated:

```text
architectural concepts
capabilities
scenarios
format semantics
```

---

# 70. Report Designer View

در آینده Report Agent باید ترجیحاً این بخش‌ها را مصرف کند:

```text
NormalizedSystemModel
Reporting
Metadata
Entities / Fields / Relations
Navigator
Stimulsoft
DataExchange
```

نه کل 58MB raw knowledge.

---

# 71. AI Trust Policy

LLM consumer باید:

```text
CrossVerified > Verified > Observed > Inferred > Unknown
```

را رعایت کند.

برای API signature:

```text
only Verified
```

برای architecture explanation:

```text
Verified + Observed
```

برای hypothesis:

```text
Inferred explicitly labeled
```

---

# 72. Assembly Name Collision

Index key نباید فقط:

```text
AssemblyName
```

باشد.

Key مناسب:

```text
path + module identity + SHA256
```

یا stable artifact ID.

`.dll` و `.exe` همنام نباید overwrite شوند.

---

# 73. SQL Case Handling

Table/column identity normalization case-insensitive باشد، original spelling حفظ شود.

False conflict ناشی از casing نباید تولید شود.

---

# 74. Substring Matching ممنوع

Cross validation نباید conceptها را با substring خام match کند.

مثلاً:

```text
File
```

نباید به:

```text
ExportFileNameHelper
```

صرفاً به دلیل substring match شود.

Matching باید semantic/token/type-aware باشد.

---

# 75. Structured Signals

برای concept detection اولویت:

```text
exact type
exact member
known JSON path
known table/column
call relation
inheritance
attribute
```

و بعد naming heuristic.

---

# 76. Obfuscation

اگر symbol obfuscated است:

```text
strings
references
interfaces
base types
calls
serialization shape
```

وزن بیشتری بگیرند.

---

# 77. Missing Inputs — چه چیزهایی هنوز خیلی مفیدند؟

اگر موجود باشند، این artifacts کیفیت تحلیل را بالا می‌برند:

## Priority 1

```text
سورس یا decompile واقعی Barsa.Meta.DataExchange.dll
```

خصوصاً:

```text
BixHelper
NewExportManager
NewImportManager
FixIdForImport
ExportJson
```

## Priority 2

```text
دو Export کاملاً هم‌scope از یک سیستم:
Legacy + AiExport
```

یعنی دقیقاً همان selection در هر دو.

## Priority 3

```text
نمونه AiExport با:
relation
report
view
business rule
workflow
web service
```

تا coverage format بهتر شود.

## Priority 4

```text
نمونه‌ای که بعداً با AiExport دوباره Import شده باشد
```

اگر چنین مسیر UI/API وجود دارد.

## Priority 5

```text
EXE + CONFIG واقعی DataExchange/System Builder
```

برای version/config gates.

---

# 78. Important: Same-Scope Golden Pair

بهترین artifact بعدی برای validation یک Golden Pair است:

```text
یک سیستم کوچک ولی کامل
```

با انتخاب دقیق یکسان:

```text
Export Legacy
Export AiExport
```

در یک نسخه Barsa و در یک زمان نزدیک.

Golden Pair بهتر است شامل:

```text
2-3 entities
primitive fields
single relation
multi relation
view
report
navigation
business rule
parameter
```

باشد.

---

# 79. Golden Pair Manifest

برای جلوگیری از ابهام کاربر می‌تواند کنار آن بنویسد:

```json
{
  "pairId": "golden-001",
  "barsaVersion": "4.1.203.0",
  "selection": [
    "..."
  ],
  "legacy": "...metaexport",
  "aiExport": "...zip"
}
```

اختیاری ولی بسیار مفید.

---

# 80. Validation Against Importer

اگر Legacy importer می‌تواند package را preview کند:

از static call model استفاده شود تا مشخص شود چه چیزهایی importer واقعاً مصرف می‌کند.

یک field که در export وجود دارد ولی importer هرگز نمی‌خواند:

```text
serialization-only / unused / future / metadata
```

ممکن است باشد.

نباید خودکار semantic-critical فرض شود.

---

# 81. Importer Read-Set

برای Importer یک Read-Set بساز:

```text
table/column/property
→ consuming method
```

---

# 82. Exporter Write-Set

برای Exporter:

```text
source property
→ exported location
```

---

# 83. Roundtrip Matrix

ترکیب:

```text
Barsa source
→ Exporter Write-Set
→ Serialized field
→ Importer Read-Set
→ Barsa destination
```

این قوی‌ترین static evidence برای semantic mapping است.

---

# 84. Lossy Export Detection

اگر source field export نمی‌شود یا export field import نمی‌شود:

```text
PotentialLoss
```

ثبت شود.

ولی فقط در scope/capability معتبر.

---

# 85. AiExport Bug Detection

برای JSON جدید، bug candidateها به صورت جداگانه:

```text
MissingSemanticObject
BrokenReference
WrongType
WrongSelector
MissingRequiredProperty
InconsistentVariantSerialization
ProfileVersionMismatch
PackageManifestMismatch
```

---

# 86. Variant Consistency

اگر یک semantic object در Single JSON و ZIP variant هر دو قابل مشاهده است:

مقایسه شود که normalization یکسان تولید می‌کنند.

هدف:

```text
Normalize(SingleJson) == Normalize(ZipJson)
```

برای scope یکسان.

---

# 87. Manifest Consistency

ZIP:

```text
manifest.json
```

Single JSON:

```text
root.manifest
```

باید به یک normalized manifest تبدیل شوند.

---

# 88. Extension Mismatch

فایلی با `.zip` که JSON plain است:

```text
Warning: ExtensionDoesNotMatchPhysicalFormat
```

این warning است، نه parse error.

---

# 89. Version Matrix

تولید:

```text
formats/version-matrix.md
```

مثلاً:

```text
Artifact
ProducerVersion
ProfileVersion
PhysicalVariant
LogicalFormat
```

---

# 90. Reconstruction Feasibility

Breakdown:

```text
Concept        Legacy   AiExport   Import Proven?
System
Entity
Field
Relation
View
Report
Navigation
Rule
Workflow
WebService
```

---

# 91. “Not observed” با “Unsupported” فرق دارد

قانون سخت:

```text
Not observed in samples
≠
Unsupported by format
```

Unsupported فقط وقتی گفته شود که code/validation صریحاً reject کند.

---

# 92. Runtime Gaps

موارد فعلی که باید همچنان Unknown بمانند مگر Evidence جدید پیدا شود:

```text
Import atomicity
Rollback guarantees
Duplicate policy
Version gate behavior
Some blob semantics
Runtime-only dynamic calls
```

---

# 93. Final README

باید بسیار خلاصه پاسخ دهد:

```text
Barsa چیست؟
چه Subsystemهایی کشف شدند؟
چند export format دارد؟
کدام format برای چه کاری است؟
چه چیزهایی cross-verified هستند؟
چه چیزهایی unknown هستند؟
AI باید کدام knowledge layer را مصرف کند؟
```

---

# 94. Final Architecture

در صورت Evidence کافی چیزی شبیه:

```text
Barsa Runtime
│
├── Metadata
├── Business Logic
├── Security / Session
├── Reporting / Stimulsoft
├── Navigator
└── DataExchange
    │
    ├── Legacy MetaExport
    │   ├── DataSet
    │   ├── ID Embedding
    │   ├── Import
    │   ├── Diff
    │   └── Clone
    │
    └── AiExport
        ├── Single JSON
        └── ZIP JSON Package
```

فقط edgeهای evidence-based.

---

# 95. Mandatory Deliverables v3

حداقل:

```text
dist/formats/format-detection.md
dist/formats/legacy-metaexport.md
dist/formats/ai-export.md
dist/comparison/scope-equivalence.json
dist/comparison/legacy-vs-ai-export.md
dist/models/normalized-system-model.schema.json
dist/evidence/cross-validation.md
dist/REANALYSIS-REPORT.md
```

---

# 96. REANALYSIS-REPORT Format

```markdown
# Reanalysis Report

## Previously believed
...

## New evidence
...

## Changed conclusions
...

## Still valid
...

## Invalidated
...

## Unknown
...

## Recommended next artifact
...
```

---

# 97. Success Criteria v3

یک Agent دیگر باید بتواند بدون بازکردن source پاسخ evidence-based بدهد:

```text
Barsa چند خانواده Export دارد؟
Legacy MetaExport چگونه serialize می‌شود؟
AiExport چند physical variant مشاهده‌شده دارد؟
profileVersion فعلاً چه چیزی معلوم/نامعلوم است؟
کدام APIها Legacy را export/import می‌کنند؟
AiExport importer وجود دارد یا نه؟
ID remapping Legacy چگونه مدل شده؟
یک Entity در دو format چگونه map می‌شود؟
کدام تفاوت‌های JSON ممکن است bug باشند؟
آیا دو sample واقعاً scope یکسان دارند؟
کدام قسمت‌ها هنوز Unknown هستند؟
```

---

# 98. چیزهایی که Agent باید همین حالا دوباره بفهمد

این بخش دستور مستقیم اجرای بعدی است:

```text
1. تمام export sampleها را مجدداً sniff و classify کن.
2. نتیجه قبلی «همه exportها Legacy هستند» را invalidate کن.
3. Legacy و Barsa.AiExport را دو format family مستقل بساز.
4. BixHelper/NewExportManager/NewImportManager/ExportJson را دوباره call-graph کن.
5. mapping هر API به format واقعی را اثبات کن.
6. دنبال importer مخصوص AiExport بگرد.
7. دلیل Single JSON vs ZIP JSON را در code پیدا کن.
8. profileVersion=15 را trace کن.
9. producerVersion را به assembly version cross-check کن.
10. Legacy DataSet schema و $IdEmbeddingFields را دقیق‌تر index کن.
11. FixIdForImport را برای pk/fk/idpattern/idlist تحلیل کن.
12. ImportTreeForm/GetImportData diff semantics را تحلیل کن.
13. sampleها را فقط پس از scope matching pair کن.
14. Barcode legacy/new را به عنوان candidate pair بررسی کن؛ exact بودن را اثبات کن.
15. Push Notification legacy/new را به دلیل تفاوت ظاهری selection، خودکار exact pair ندان.
16. هر دو JSON physical variant را به یک normalized model تبدیل کن.
17. Legacy را نیز به همان normalized model تبدیل کن.
18. semantic diff فقط روی strong/exact matches اجرا کن.
19. JSON differences را BugCandidate یا RepresentationDifference طبقه‌بندی کن.
20. کل knowledge-index مربوط به DataExchange را regenerate کن.
```

---

# 99. چه چیزهایی هنوز از کاربر مفید است؟

برای ادامه، کاربر **لازم نیست DLL دیگری بدهد** اگر مجموعه فعلی کامل است.

بیشترین ارزش اطلاعاتی در این‌هاست:

### مورد اول — Golden Pair

دو Export از **دقیقاً یک Selection**:

```text
Legacy .metaexport
AiExport JSON/ZIP
```

### مورد دوم — Exporter/Importer source یا decompile واقعی

به‌خصوص `Barsa.Meta.DataExchange.dll`.

### مورد سوم — AiExport Import

اگر در UI سیستم‌ساز JSON جدید قابل Import است، یک نمونه واقعی از process یا متد مربوطه.

### مورد چهارم — Feature-rich sample

یک سیستم نمونه که عمداً شامل همه اینها باشد:

```text
Entity
Field types
Relations
View
Report
Navigation
Rule
Workflow
WebService
```

اگر feature وجود دارد.

---

# 100. اصل نهایی

هدف v3:

> **مدل واقعی Barsa را از serialization format جدا کند.**

یعنی Agent نباید Barsa را مساوی Legacy DataSet یا JSON جدید بداند.

مدل درست:

```text
                  Barsa Semantic Model
                         ▲      ▲
                         │      │
             Legacy Adapter    AiExport Adapter
                         │      │
                         ▼      ▼
                 .metaexport   JSON/ZIP
```

و Knowledge نهایی باید درباره:

```text
Barsa Semantic Model
```

باشد، با provenance کامل به formatهای واقعی.

ترتیب اعتماد:

```text
Cross-Verified Semantic Evidence
    >
Direct Binary / Export / Import Evidence
    >
Observed Static Behavior
    >
Inference
    >
Guess
```

`Guess` ممنوع است.

---

# End of Specification v3
