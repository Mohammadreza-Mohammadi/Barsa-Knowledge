# Package Protocol

مرجع اصلی transport در `EM01 — Package` است. Agent فقط artifact تولید/مصرف می‌کند و HTTP مستقیم نمی‌زند.

## Path convention

- تمام referenceهای عملیاتی به اسناد داخل initial ZIP از **root خود Package** نوشته می‌شوند و با `agent/*`، `skills/*`، `knowledge/*` یا `dataexchange/*` شروع می‌شوند.
- repository-only Source prefix فقط convention مستندات Source repository است و **داخل generated initial ZIP مجاز نیست**. projection باید reference قابل‌مصرف را به package-root path تبدیل کند یا reference Source-only غیرعملیاتی را از routing Agent-facing خارج کند؛ validator هر repository-only Source prefix باقی‌مانده را خطا می‌داند.
- `dataexchange/*` source-backed mirror از `Barsa.Meta.SemanticExchange/Docs/AI/*` است و فقط برای دسترسی EM01 به exact technical contract حمل می‌شود؛ authority مستقل ندارد.
- prefix `artifact:` برای نام artifactهای ورودی/خروجی Role است و document-routing reference نیست؛ filenameهای protocol مانند `request.json` و `change.json` نیز artifact هستند.

## Envelope

فایل command ZIP شامل `barsa-chat-manifest.json` است. protocol جاری دو command سطح‌بالا دارد و `action` اجباری است:

- `context`
  - `system-semantic`
  - `target-semantic`
  - `km-current`
  - `km-previous-invalid`
- `change`
  - `semantic-change`
  - `km-save`
  - `km-invalidate`
  - `km-delete`

`semantic-change` از `change.json` استفاده می‌کند. سایر actionهای protocol v3 از `request.json` استفاده می‌کنند. shape دقیق و capability جاری در generated `chat-protocol.json` هر exchange self-described است؛ Agent schema/action تازه حدس نمی‌زند.

Unknown command/action **protocol error** است و هرگز به Semantic Change fallback نمی‌شود.

## Semantics

- `semantic-change` همان pipeline موجود `Plan → Apply → Runtime Read-back → Verify` را route می‌کند؛ Package transport pipeline دوم نمی‌سازد.
- `semantic-change` **فقط Semantic v15** را می‌پذیرد؛ `change.json.profileVersion` اجباری و دقیقاً `15` است. missing/v14/other version protocol/plan rejection است و Host compatibility fallback نمی‌سازد.
- KM actionها مستقیم به lifecycle/storage `AiKnowledge` route می‌شوند. `AiKnowledge` objectType ساختگی Semantic/Metadata نیست.
- `target-semantic` فقط scopeهای advertised توسط `chat-protocol.json` را استفاده می‌کند. در baseline فعلی فقط `system` و `entity` end-to-end فعال‌اند.
- `km-previous-invalid` پاسخ `ambiguous` و `candidateIds/reuseId` را بدون انتخاب حدسی candidate به Agent منتقل می‌کند؛ Agent در ambiguity به Full Generate fallback می‌کند.

## `km-save` request contract

`km-save` همان action موجود است و دو شکل backward-compatible دارد. شکل single قبلی بدون breaking change معتبر می‌ماند:

```json
{
  "targetType": "entity",
  "targetId": 123,
  "content": "{...KM v1 JSON text...}",
  "isValid": true
}
```

در single form، `id` اختیاری است و pair فنی `relatedObjectTypeDefId + relatedObjectId` نیز برای compatibility قرارداد storage قبلی باقی است. اگر representation typed و compatibility همزمان داده شوند، Host API باید همان target واقعی را resolve کند.

`content` در هر دو form باید JSON معتبر KM Content v1 باشد و representation canonical Agent-facing آن **pretty-formatted JSON با indentation دو space** است. Package Bridge `content` را با JSON parser parse و دوباره `Formatting.Indented` serialize می‌کند؛ string manipulation دستی ندارد. برای object KM، ترتیب preferred top-level `summary → keyPoints → drillDown` حفظ/normalize می‌شود و propertyهای دیگر schema بدون حذف بعد از آنها می‌آیند. whitespace در مقایسه semantic بی‌اهمیت است. این formatting schema را تغییر نمی‌دهد.

Batch form همان `km-save` را در **یک Package exchange** برای چند save مرتب گسترش می‌دهد:

```json
{
  "items": [
    {
      "targetType": "entity",
      "targetId": 123,
      "content": "{...KM v1 JSON text...}",
      "isValid": true
    },
    {
      "targetType": "view",
      "targetId": 456,
      "content": "{...KM v1 JSON text...}",
      "isValid": true
    },
    {
      "targetType": "system",
      "targetId": 789,
      "content": "{...KM v1 JSON text...}",
      "isValid": true
    }
  ]
}
```

در batch هر item canonical و typed است: `targetType + targetId + content + isValid` اجباری و `id` اختیاری است. compatibility pairهای storage داخل batch Agent-facing استفاده نمی‌شوند. `items` باید non-empty باشد و duplicate target در همان batch ممنوع است. تمام itemها، target type/id، نوع `id/isValid` و parse شدن JSON داخل `content` **قبل از اولین mutation** validate می‌شوند. سپس Bridge availability واقعی AI Knowledge storage را و بعد برای تمام itemها preflight واقعی target mapping/identity را از همان DataExchange production authority اجرا می‌کند؛ اگر storage وجود نداشته باشد batch با `status=unavailable` و **zero mutation** materialize می‌شود. اگر storage موجود باشد ولی mapping یا target واقعی resolve نشود، آن Integration/identity failure است و batch نیز پیش از mutation reject می‌شود. exact storage mapping/availability در `dataexchange/09-knowledge-storage-reference.fa.md` است و این protocol آن را duplicate نمی‌کند. malformed/unresolvable batch هیچ itemی را write نمی‌کند.

Host itemها را دقیقاً به ترتیب request با endpoint موجود `POST /ai-knowledge` اجرا می‌کند؛ public Host API و storage schema عوض نمی‌شوند. اولین HTTP failure یا ambiguity execution را متوقف می‌کند. itemهای موفق قبلی rollback یا پنهان نمی‌شوند و itemهای بعدی `notAttempted` باقی می‌مانند. transaction سراسری تازه‌ای تعریف نشده است.

برای `Full Generate(System)`، selected Child KMها باید قبل از System item قرار گیرند و System item آخر باشد. در نتیجه failure یک Child مانع write شدن System KM جدید می‌شود.

### `knowledge-result.json`

برای single form همان response قبلی `/ai-knowledge` بدون تغییر materialize می‌شود. برای batch، result aggregate machine-readable است:

```json
{
  "status": "succeeded | partiallySucceeded | ambiguous | failed | unavailable",
  "overallStatus": "succeeded | partiallySucceeded | ambiguous | failed | unavailable",
  "succeededCount": 2,
  "failedCount": 1,
  "notAttemptedCount": 1,
  "itemCount": 4,
  "items": [
    {
      "index": 0,
      "targetType": "entity",
      "targetId": 123,
      "status": "succeeded",
      "httpStatus": 200,
      "resultStatus": "succeeded",
      "created": false,
      "reused": true,
      "knowledgeId": 9001
    },
    {
      "index": 1,
      "targetType": "view",
      "targetId": 456,
      "status": "ambiguous",
      "httpStatus": 409,
      "candidateIds": [9010, 9011],
      "reuseId": 9011,
      "error": "..."
    },
    {
      "index": 2,
      "targetType": "system",
      "targetId": 789,
      "status": "notAttempted",
      "httpStatus": null
    }
  ]
}
```

`partiallySucceeded` completion موفق Full Generate نیست. Agent فقط وقتی hierarchy انتخاب‌شده را persisted اعلام می‌کند که aggregate `status=succeeded` باشد و همه itemهای مورد انتظار، با System item آخر، success شده باشند.

`unavailable` فقط وقتی AI Knowledge storage (`Meta02 / دانش ai`) در deployment وجود ندارد به‌کار می‌رود؛ برای batch تمام itemها `notAttempted` می‌مانند و mutation صفر است. این status با defect target mapping یکی نیست. `km-current`/single lifecycle نیز ممکن است HTTP `503` با `status=unavailable` و `failureStage=knowledgeStorage` برگرداند. Agent این وضعیت را `KM=unavailable` گزارش می‌کند؛ success/Verify خود System مستقل است.

## Bootstrap authority

Initial delivery دقیقاً دو artifact هم‌سطح با Exchange ID مشترک دارد:

```text
<EID>-START-HERE.en.md
<EID>-upload-ai-gen.zip
```

Start مستقل و خارج ZIP است. Initial ZIP `00-START-HERE`، bootstrap authority دوم یا `package-manifest.json` Agent-facing ندارد.
## Change reference continuity across exchanges

`tempId` scope فقط همان `semantic-change` logical Batch است. Upload نتیجه می‌تواند `temporaryIds`/`sessionReferenceMap` را برای diagnostics/trace حمل کند، اما در Semantic v15 wave/exchange بعدی object persisted با **Semantic selector/context** دوباره resolve می‌شود؛ typed Runtime `id` fallback semantic نیست. tempId wave قبلی قابل حمل نیست و `sessionReferenceMap` authority جدید نمی‌سازد.

Plan blockerهای Chat از compact diagnostics runtime می‌آیند. Package Bridge صریحاً compact mode را مصرف می‌کند؛ default `/plan` برای clientهای قدیمی Full Plan باقی می‌ماند. `summary` compact همان casing contract Plan اصلی را دارد. `unknownTempId` یعنی reference موقت در Batch جاری owner ندارد. stale/foreign tempId را به Runtime ID rewrite نکن؛ برای object persisted، selector/context canonical را بازسازی/مصرف کن و Runtime read-back را فقط evidence تشخیص بگیر. Host stale tempId را خودکار rewrite نمی‌کند.

Exchange `SESSION+SEQ` بعد از expose immutable است؛ retry/correction همیشه sequence جدید می‌گیرد. Package با همان sequence، حتی با suffix فایل، continuation معتبر جدید محسوب نمی‌شود.
