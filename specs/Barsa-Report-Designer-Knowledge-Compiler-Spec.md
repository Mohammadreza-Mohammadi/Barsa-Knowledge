# Barsa Report Designer Knowledge Compiler — Specification v1

> نسخه: 1.0
> وضعیت: Specification
> ورودی: `dist/` (خروجی Knowledge Extractor v3)
> خروجی: `dist-report/`
> هدف: از یک Knowledge Pack بزرگ و عمومی، یک بستهٔ کوچک، دقیق و **مخصوص ساخت گزارش** تولید شود.
> اصل بنیادی: **بسته باید compile شود، نه نوشته شود.** هر جمله در خروجی باید provenance به `dist/` و از آنجا به باینری یا artifact داشته باشد.

---

# 0. چرا این Compiler لازم است

`dist/` حدود ۶۱ مگابایت و ۲۵۳ فایل است. برای پاسخ به «معماری Barsa چیست» عالی است، ولی برای کسی که می‌خواهد **یک گزارش بسازد** سه مشکل دارد:

```text
۱. بزرگ است
   ایندکس‌های انبوه (methods.json ۲۳MB، references.json ۲۰MB)
   برای ساخت گزارش بی‌استفاده‌اند.

۲. پراکنده است
   دانش گزارش در هشت جای مختلف پخش شده:
   formats/semantic-write-contract.md، formats/report-format.md،
   index/ai-export-properties.json، index/semantic-contract.json،
   scenarios/semantic-write-pipeline.md، domains/reporting.md،
   domains/stimulsoft.md، comparison/match-report.md

۳. generic است
   «۸۱ property قابل نوشتن» می‌گوید ولی نمی‌گوید
   برای یک TreeView کدام‌ها معنا دارند و کدام‌ها نه.
```

Compiler این سه را حل می‌کند: **کوچک**، **یک‌جا**، **task-oriented**.

> این Compiler دانش جدید **تولید نمی‌کند**. فقط انتخاب، بازچینش و فشرده می‌کند. اگر چیزی در `dist/` نیست، در `dist-report/` هم نباید باشد.

---

# 1. مرز مسئولیت

```text
Knowledge Extractor  (v2/v3)      Report Knowledge Compiler  (این Spec)
──────────────────────────────    ────────────────────────────────────
باینری و artifact را می‌خواند       فقط dist/ را می‌خواند
همه‌چیز را کشف می‌کند                فقط چیزهای گزارش‌محور را برمی‌دارد
۶۱MB                              هدف: زیر ۵۰۰KB
عمومی                             task-oriented
```

Compiler **هرگز** `source/` را نمی‌خواند. اگر برای ساخت گزارش چیزی لازم است که در `dist/` نیست، این یک **نقص Extractor** است و باید در `MISSING-FROM-DIST.md` ثبت شود، نه با خواندن DLL دور زده شود.

این مرز سخت است. شکستنش یعنی دو منبع حقیقت موازی.

---

# 2. دو مصرف‌کننده، دو وظیفه

بسته باید هر دو را پشتیبانی کند:

```text
A) Authoring
   «یک گزارش لیستی از موجودیت گیت با سه ستون بساز»
   → تولید یک AiChangeBatch معتبر

B) Comprehension
   «این گزارش موجود چه می‌کند؟»
   → تفسیر یک رکورد met_Report یا یک رکورد report در AiExport
```

هر دو از یک contract تغذیه می‌شوند. وظیفهٔ B ارزان است و اگر فقط A پیاده شود، بسته نصفه است.

---

# 3. ساختار خروجی

```text
dist-report/
│
├── README.md                     یک صفحه: این چیست، چطور مصرف شود
├── REPORT-CONTRACT.md            ۸۱ property قابل نوشتن، گروه‌بندی‌شده بر اساس کار
├── REPORT-TYPES.md               ۱۲ نوع گزارش و اینکه هر کدام چه propertyهایی را معنا می‌دهد
├── COLUMNS-AND-FIELDS.md         چه چیزی می‌تواند ستون شود
├── CONDITIONS.md                 مدل شرط و عملگرها
├── PARAMETERS.md                 پارامترها و محدودیت‌هایشان
├── PLACEMENT.md                  گزارش در navigator کجا می‌نشیند
├── SELECTORS.md                  مدل ارجاع `#`
├── RECIPES.md                    نمونهٔ کامل AiChangeBatch برای هر سناریوی رایج
├── LIMITS.md                     چه چیزی قابل نوشتن نیست و چرا
├── PROVENANCE.md                 هر بخش از کجای dist/ آمده
├── MISSING-FROM-DIST.md          چیزهایی که Extractor باید اضافه کند
│
└── index/
    ├── report-pack.json          manifest، نسخه، hash ورودی‌ها
    ├── report-contract.json      جدول property ماشین‌خوان
    ├── report-enums.json         فقط enumهای گزارش‌محور
    ├── report-types.json         نوع گزارش → propertyهای مرتبط
    ├── field-types.json          subtypeهای فیلد و قابلیت ستون‌شدنشان
    ├── entity-model.json         موجودیت/فیلد/relation در scope (اختیاری)
    ├── selectors.json            ایندکس selector در scope (اختیاری)
    └── recipes.json              recipeهای ماشین‌خوان
```

---

# 4. بودجهٔ اندازه

```text
کل بسته            ≤ 500 KB
بزرگ‌ترین فایل      ≤ 150 KB
بدون scope سیستم   ≤ 120 KB
```

اگر بسته از بودجه رد شد، Compiler باید **خطا بدهد**، نه اینکه ساکت بزرگ شود. بزرگ‌شدن تدریجی همان مشکلی است که این Spec برای حلش نوشته شده.

استثنا: `entity-model.json` و `selectors.json` با تعداد موجودیت رشد می‌کنند. برای این دو سقف per-system است، نه مطلق.

---

# 5. Scope

Compiler دو حالت دارد:

```text
--scope contract        فقط قرارداد. مستقل از هر سیستمی.
--scope system=<id>     قرارداد + مدل موجودیت همان سیستم.
```

حالت `system` همان چیزی است که بسته را واقعاً قابل استفاده می‌کند: یک agent برای ساخت گزارش باید بداند **چه فیلدهایی** روی **چه موجودیتی** هست و selectorشان چیست.

منبع این مدل: `dist/models/normalized-samples/` و `dist/index/export-fields.json`. اگر سیستم خواسته‌شده در هیچ artifactی نیست، Compiler باید صریح بگوید و حالت `contract` را تولید کند، نه مدل خالی.

---

# 6. قرارداد نوشتن گزارش — منبع

```text
dist/index/semantic-contract.json
  → propertyContracts.report      ۸۵ ردیف
  → objectContracts[objectType=report]
```

واقعیت‌هایی که باید منتقل شوند:

```text
objectType          report
operations          Create, Update, Delete
structuralOrder     120      (بعد از field/relation، قبل از folder)
identity            Report.Id under entity
applyClass          Hardcoded
orderingSemantics   no
writer              AiReportChangeProvider.ApplyReportPatch   (هر ۸۱ property)
```

---

# 7. گروه‌بندی ۸۱ property

فهرست الفبایی بی‌فایده است. Compiler باید بر اساس **کار** گروه‌بندی کند. گروه‌ها:

```text
identity            name, description, systemId
shape               reportType, typeView, parameterEntity
data                columns, customSql, additionalWhere, extraQueryTemplate,
                    alternateRootTable, rootTableAlias, joinAliases, isDistinct,
                    top, includeDeleted, oracleHint
filtering           condition, treeCondition, useHierarchyConditionForRoot,
                    ignoreAdvancedSecurityCondition
shaping             sorting, grouping, sqlGrouping, matrix, useSummaryRow
presentation        gridViewStyle, gridLines, gridHideLines, gridGrouping,
                    gridShowGroupBox, gridShowSelectionChecks, gridCustomKey,
                    gridHideColumnsWhenGrouped, freeColumnSizing,
                    alternateRowMode, disableColumnHeaders, hideHeader,
                    hideRowIcon, hideToolbar, showRowNumber, calendar,
                    formatConditions, showRecordSignFormatting, showWpfChart
paging              pagingType, pageSize, dontExecuteCount
permissions         allowView, allowEdit, allowAddNew, allowRemove,
                    allowInlineEdit, autoInlineEdit, allowAddToList,
                    allowRemoveFromList, allowGridColumnSort,
                    useAdvancedAccess
preview             previewField, showPreviewField, previewState
insideView          isInsideView-family: insideViewActive, insideViewHeight,
                    insideViewRelatedField, listEditView
behaviour           immediateExecute, sharedScope, logExecutions,
                    preserveUserViewState, disableOptimizeForDisplay,
                    dontUseChildParentReport, selfReferencingField
tree                treeAutoOpenLevels
parameters          parameters, parameterPanelHeight
composition         subReports
other               forum, commandDisplayMode, alternateEditObjectColumn,
                    ignoreColumns
```

گروه‌بندی بالا **Inferred** است: از نام property و از معنای enum مرتبط. Compiler باید این را به‌عنوان Inferred علامت بزند. تنها چیزی که Verified است، خودِ فهرست propertyها و writableشان است.

هیچ propertyای نباید از قلم بیفتد. Compiler باید بررسی کند مجموع گروه‌ها = ۸۱.

---

# 8. آن چهار property که قابل نوشتن نیستند

```text
$type              ReadOnly   discriminator
entity             ReadOnly   Report.TypeDefId
system             ReadOnly   Report.SystemId
parameterLayout    ReadOnly   "Report parameter XML layout is out of
                              Semantic v15 reconstruction scope in v190"
```

این‌ها مهم‌ترین بخش `LIMITS.md` هستند:

- `entity` و `system` قابل patch نیستند. یعنی **موجودیت هدف یک گزارش را نمی‌توان با update تغییر داد**. در زمان create از `parent` می‌آید.
- `parameterLayout` یک محدودیت **اعلام‌شده** است، نه حدس. متن خودش می‌گوید در v190 خارج از scope است. پس چیدمان پنل پارامتر قابل بازسازی نیست.

Compiler باید عین این متن را نقل کند، نه بازنویسی‌اش.

---

# 9. نوع گزارش

```text
dist/index/ai-export-properties.json → enums["Barsa.Meta.ReportTypeEnum"]

0  ViewResults                      5  PrintView
1  Statistics                       6  HetrogeniousTree
2  TreeView                         7  HetrogeniousTree_NoneGraphical
3  MatrixView                       8  GauntView
4  CalendarView                     9  FormView
10 ForumView                        11 Dashboard
```

---

# 10. سؤال حیاتی ۱ — واژگان `reportType` دو تاست

در artifactهای واقعی:

```text
exports/باركد....zip            reportType: "list"
exports/Push Notification...zip  reportType: "form"
```

این‌ها **هیچ‌کدام** عضو `ReportTypeEnum` نیستند. یعنی AiExport یک واژگان معنایی جدا دارد.

نگاشت محتمل:

```text
"list"  ≈  ViewResults (0)
"form"  ≈  FormView (9)
```

ولی این **Inferred** است و Compiler حق ندارد قطعی بنویسدش.

وظیفهٔ Compiler:

```text
۱. هر دو واژگان را فهرست کند.
۲. نگاشت را به عنوان Inferred ثبت کند، با همین دو مشاهده به عنوان شاهد.
۳. در MISSING-FROM-DIST.md بنویسد که Extractor باید نگاشت را
   از AiSemanticV15ExportPostProcessor یا از قاعدهٔ enum پروفایل اثبات کند.
۴. در RECIPES.md از واژگان AiExport استفاده کند (چون artifact واقعی
   همان را نشان می‌دهد) و صریح بگوید که CLR enum چیز دیگری است.
```

اگر Extractor بعداً نگاشت را اثبات کرد، Compiler باید خودکار Verified شود — بدون دست‌کاری دستی.

---

# 11. ماتریس نوع × property

مفیدترین چیز در کل بسته این است:

```text
REPORT-TYPES.md

نوع گزارش      propertyهای مرتبط            propertyهای بی‌معنا
ViewResults    columns, sorting, grid*      matrix, treeAutoOpenLevels
TreeView       treeCondition, treeAuto...   matrix
MatrixView     matrix, sqlGrouping          treeCondition
CalendarView   calendar                     matrix, tree*
...
```

اما **هیچ شاهدی برای این ماتریس در `dist/` نیست.** هیچ جا نگفته `matrix` فقط برای `MatrixView` معنا دارد.

پس قاعده:

```text
Compiler ماتریس را بر اساس تطابق نام تولید می‌کند (matrix↔MatrixView،
tree*↔TreeView، calendar↔CalendarView)، آن را Inferred علامت می‌زند،
و بقیهٔ خانه‌ها را Unknown می‌گذارد — نه «بی‌معنا».
```

«شاهدی ندارم» با «بی‌معناست» یکی نیست. این همان قاعدهٔ §91 در Spec v3 است.

برای اثبات، `MISSING-FROM-DIST.md` باید بخواهد: decompile شدن `AiReportChangeProvider.ApplyReportPatch`، که تنها جایی است که این شرطی‌ها زندگی می‌کنند.

---

# 12. ستون‌ها

شکل واقعی از artifact:

```json
"columns": [
  { "field": "#گیت",      "alias": "گیت" },
  { "field": "#توضیحات",  "alias": "توضیحات" }
]
```

`field` یک selector است، نه id. `alias` عنوان نمایشی ستون.

Compiler باید:

```text
- شکل را از artifact نقل کند (Verified)
- بگوید selector به چه resolve می‌شود (یک FieldDef زیر همان entity)
- فهرست کند چه fieldTypeهایی می‌توانند ستون شوند
- بگوید آیا ستونِ relation مجاز است — و اگر شاهدی نیست، Unknown
```

منبع fieldType:

```text
dist/index/semantic-contract.json → propertyContracts.field
  ۲۴ subtype با propertyهای مخصوص خودشان
```

---

# 13. شرط‌ها

شکل واقعی:

```json
"condition": { "all": [] }
```

و در enumها:

```text
Barsa.Meta.CombinationOperator   0 All, 1 Any
Barsa.Meta.ComparisonOperator    0 AdvancedTextSearch2
```

`all` / `any` دقیقاً با `CombinationOperator` می‌خوانند — این CrossVerified است.

ولی `ComparisonOperator` فقط **یک** عضو دارد (`AdvancedTextSearch2`). این تقریباً قطعاً یعنی enum واقعی عملگرها جای دیگری است و پروفایل فقط همین یکی را نگاشت کرده.

Compiler باید این را به‌عنوان یک شکاف صریح ثبت کند:

```text
عملگرهای مقایسه در شرط: Unknown
شاهد: پروفایل فقط AdvancedTextSearch2 را می‌شناسد، که برای یک
      موتور شرط کامل بسیار کم است.
لازم: یک artifact با شرط غیرخالی، یا decompile شدن سازندهٔ شرط.
```

هر دو artifact موجود `{"all": []}` دارند — یعنی **هیچ شرط واقعی‌ای دیده نشده**. این را باید گفت.

---

# 14. پارامترها

```text
contract:  parameters (writable), parameterEntity (writable),
           parameterPanelHeight (writable), parameterLayout (ReadOnly)
pipeline:  AiRuntimeVerifier.ReportParametersPatchMatches
           AiRuntimeVerifier.BuildReportParameterIdMap
           AiRuntimeVerifier.NormalizeReportParameterReferences
```

وجود `BuildReportParameterIdMap` و `NormalizeReportParameterReferences` در verifier نشان می‌دهد پارامترها **ارجاع‌دار** هستند و هنگام وارسی نرمال می‌شوند.

شکل `parameters` در هیچ artifact موجودی دیده نشده. پس:

```text
وجود: Verified
شکل:  Unknown
```

`PARAMETERS.md` باید همین دو خط باشد، نه یک شکل ساختگی.

---

# 15. جایگاه در navigator

یک گزارش ساخته‌شده اگر جایی نشانده نشود دیده نمی‌شود.

```text
dist/formats/legacy-dataset-schema.md   MET_FOLDER
dist/comparison/match-report.md         ساختار پوشه در نسخهٔ ZIP
dist/index/semantic-contract.json       propertyContracts.folder
```

`Barsa.Meta.FolderType` در پروفایل:

```text
0   MainRoot
3   ReportRoot
9   Report          ← یک placement گزارش
12  ReportFolder    ← پوشهٔ ظرف
```

واقعیت‌ها:

```text
- یک placement گزارش ردیفی با FolderType=Report (9) و ReportId است
- پوشهٔ ظرف FolderType=ReportFolder (12) است
- objectType مربوط در contract: folder (structuralOrder 130)
- پس در یک batch، گزارش (120) قبل از folder (130) ساخته می‌شود
```

Compiler باید نام enum را به کار ببرد نه عدد خام. عدد در `dist/` هست ولی
نامش هم هست، و نامْ خواناتر و کم‌خطاتر است.

این ترتیب از `structuralOrder` می‌آید و Verified است. `PLACEMENT.md` باید recipe دوفرمانی بدهد: اول `report`، بعد `folder` که با selector به آن اشاره می‌کند.

---

# 16. Selectorها

```text
dist/formats/ai-export.md
dist/comparison/match-report.md
```

قواعدی که باید منتقل شوند:

```text
شکل          '#' + نام   (مثل #گیت)
شکل براکتی    '#[...]' وقتی جزء نیاز به escape دارد
codec        SemanticSelectorCodec
دامنه        در AiChangeBatch، selector تنها راه ارجاع به شیء موجود است
ممنوع       id, rowId, sourceId, runtimeId, dependencyKey
tempId      برای اشاره به چیزی که در همان batch ساخته می‌شود
```

نکتهٔ عملی که باید گفته شود: شکل‌های عربی/فارسی حروف (`ي`/`ی`، `ك`/`ک`) در این داده‌ها در هم به کار می‌روند. یک selector که با حرف اشتباه نوشته شود resolve نمی‌شود. `SELECTORS.md` باید هشدار بدهد و بگوید نام را از `selectors.json` کپی کنند، نه تایپ.

---

# 17. Recipeها

`RECIPES.md` قلب بخش authoring است. هر recipe یک `AiChangeBatch` کامل و **lint-clean** است.

حداقل recipeها:

```text
R1  گزارش لیستی ساده روی یک موجودیت موجود
R2  گزارش لیستی + جایگاه در یک پوشهٔ موجود
R3  گزارش لیستی + پوشهٔ جدید + جایگاه   (سه فرمان، با tempId)
R4  update روی یک گزارش موجود (تغییر ستون‌ها)
R5  حذف یک گزارش
R6  گزارش form روی یک typeView
```

قاعدهٔ سخت:

```text
هر recipe باید از tools/lint_change_batch.py با
«۰ error، ۰ warning» رد شود.
```

اگر recipeای warning می‌دهد، یعنی propertyای را به کار برده که contract مجاز نمی‌داند — و آن recipe غلط است، نه linter.

این دقیقاً همان چیزی است که در نسخهٔ قبلی دو اشتباه را در مثال خودم گرفت (`DbName` به جای `dbName`، و `orderNumber` که اصلاً authorable نیست). هر recipe باید در build تست شود.

---

# 18. اعتبارسنجی recipeها در build

```text
tools/report_compiler.py --validate-recipes
```

برای هر recipe:

```text
۱. از schema رد شود                models/ai-change-batch.schema.json
۲. از linter رد شود                ۰ error، ۰ warning
۳. هر selector در recipe در selectors.json باشد (در حالت scope=system)
۴. هر property در گروه‌بندی §7 باشد
```

شکست هر کدام = شکست build. این تنها راهی است که بسته با گذر زمان دروغ نمی‌شود.

---

# 19. انتشار Confidence

هیچ واقعیتی نباید در عبور از Compiler **ارتقا** پیدا کند.

```text
dist/ می‌گوید Verified    →  بسته می‌گوید Verified
dist/ می‌گوید Observed    →  بسته می‌گوید Observed
dist/ می‌گوید Unknown     →  بسته می‌گوید Unknown
Compiler استنباط می‌کند   →  بسته می‌گوید Inferred، با ذکر قاعدهٔ استنباط
```

گروه‌بندی §7 و ماتریس §11 تنها دو جایی هستند که Compiler چیزی اضافه می‌کند، و هر دو Inferred هستند.

Compiler باید در build بررسی کند که هیچ confidence ارتقا نیافته است: برای هر واقعیتی که provenance به `dist/` دارد، سطحش را با منبع مقایسه کند.

---

# 20. Provenance

هر فایل در بسته باید header داشته باشد:

```text
> منبع: dist/index/semantic-contract.json → propertyContracts.report
> dist commit: <sha>
> compiled: <date>
```

و `PROVENANCE.md` یک جدول کامل: هر بخش بسته ← فایل `dist/` ← فایل `source/` یا artifact.

بدون این، بسته از `dist/` جدا می‌افتد و کسی نمی‌فهمد کدام قدیمی است.

---

# 21. ناوابستگی و invalidation

```text
index/report-pack.json
{
  "compiledAt": "...",
  "distCommit": "<sha>",
  "inputs": [
    { "path": "dist/index/semantic-contract.json", "sha256": "..." },
    { "path": "dist/index/ai-export-properties.json", "sha256": "..." },
    ...
  ],
  "scope": "system=1011413550000000100",
  "sizeBytes": 0,
  "budget": { "total": 512000, "largestFile": 153600 }
}
```

اگر hash هر ورودی تغییر کرد، بسته stale است. Compiler باید حالت `--check` داشته باشد که فقط همین را بگوید و خروج غیرصفر بدهد — تا در CI قابل استفاده باشد.

---

# 22. MISSING-FROM-DIST.md

این فایل مرز §1 را قابل اجرا می‌کند. هر چیزی که Compiler برای ساخت گزارش لازم داشت و در `dist/` نبود، اینجا ثبت می‌شود — با آدرس دقیق اینکه Extractor کجا باید دنبالش برود.

ورودی‌های شناخته‌شدهٔ همین حالا:

```text
۱. نگاشت reportType بین واژگان AiExport و ReportTypeEnum
   کجا: AiSemanticV15ExportPostProcessor، یا قاعدهٔ enum در پروفایل

۲. عملگرهای مقایسه در شرط
   کجا: سازندهٔ شرط؛ یا یک artifact با شرط غیرخالی

۳. شکل parameters
   کجا: یک گزارش با پارامتر در یک artifact

۴. اینکه کدام property برای کدام reportType معنا دارد
   کجا: AiReportChangeProvider.ApplyReportPatch (نیاز به decompile)

۵. آیا ReportData در legacy همان اطلاعات AiExport را دارد
   کجا: decoder SerializeReportData که پروفایل نامش را می‌برد ولی اجرا نشده

۶. قالب چاپ (PrintView / Stimulsoft .mrt)
   کجا: هیچ نمونهٔ .mrt در source/ نیست
```

این فهرست باید توسط Compiler **تولید** شود، نه دستی نگه‌داشته شود: هر جا در قالب‌ها یک مقدار Unknown رندر شد، یک سطر اینجا بیفزاید.

---

# 23. چیزی که این بسته نیست

```text
- یک SDK نیست. کد اجرایی ندارد.
- یک UI designer نیست.
- جایگزین dist/ نیست. زیرمجموعهٔ آن است.
- دربارهٔ Stimulsoft چیزی نمی‌داند جز اینکه وجود دارد.
- گزارش اجرا نمی‌کند و SQL تولید نمی‌کند.
```

اگر کسی از بسته انتظار یکی از این‌ها را داشت، `README.md` باید در همان پاراگراف اول ردش کند.

---

# 24. پیاده‌سازی

```text
tools/report_compiler.py

--dist PATH            پیش‌فرض dist/
--out PATH             پیش‌فرض dist-report/
--scope contract|system=<id>
--validate-recipes     recipeها را lint کن، در صورت شکست خروج غیرصفر
--check                فقط stale بودن را بررسی کن
--budget-bytes N       سقف اندازه
```

ماژول‌ها:

```text
report_compiler/
├── load.py        خواندن dist/ با بررسی hash
├── contract.py    استخراج و گروه‌بندی قرارداد گزارش
├── enums.py       انتخاب enumهای گزارش‌محور
├── entities.py    مدل موجودیت در scope
├── recipes.py     ساخت و اعتبارسنجی recipeها
├── render.py      تولید markdown و json
└── audit.py       بودجه، confidence، provenance، MISSING
```

`recipes.py` باید از `barsa_extractor.change_batch` استفاده کند، نه کپی‌اش. یک linter، یک contract.

---

# 25. معیار موفقیت

یک agent که **فقط** `dist-report/` را دارد و `dist/` یا `source/` را ندارد، باید بتواند:

```text
۱. یک AiChangeBatch برای گزارش لیستی بسازد که از linter با ۰ finding رد شود.
۲. بگوید چرا نمی‌تواند موجودیت هدف یک گزارش موجود را عوض کند.
۳. برای یک موجودیت در scope، فهرست فیلدهای قابل ستون‌شدن را بدهد.
۴. ترتیب درست فرمان‌ها را برای «گزارش + پوشهٔ جدید» بگوید و دلیلش را
   از structuralOrder توضیح دهد.
۵. بگوید چه چیزی را نمی‌داند — بدون پر کردن جایش با حدس.
   مخصوصاً: شکل parameters، عملگرهای شرط، چیدمان پنل پارامتر.
۶. selector یک فیلد را درست نقل کند، با شکل حرفی درست.
```

آزمون ۵ مهم‌ترین است. بستهٔ کوچکی که حدس می‌زند بدتر از بستهٔ بزرگی است که ساکت است.

---

# 26. آزمون پذیرش

```text
python3 tools/report_compiler.py --scope system=<id> --validate-recipes
```

باید:

```text
✓ اندازه زیر بودجه
✓ هر ۸۱ property در دقیقاً یک گروه
✓ هر recipe ۰ error و ۰ warning
✓ هیچ confidence ارتقا نیافته
✓ هر فایل provenance دارد
✓ MISSING-FROM-DIST.md غیرخالی است
```

آخری عجیب به نظر می‌رسد ولی نیست: اگر خالی باشد یعنی Compiler Unknownها را قایم کرده.

---

# 27. اصل نهایی

```text
dist/      دربارهٔ Barsa است.
dist-report/ دربارهٔ ساختن یک گزارش در Barsa است.
```

اولی باید کامل باشد. دومی باید **کوچک، درست، و صادق دربارهٔ مرزهای خودش**.

ترتیب اعتبار همان است:

```text
CrossVerified > Verified > Observed > Inferred > Unknown
```

و `Guess` همچنان ممنوع است.

---

# End of Specification
