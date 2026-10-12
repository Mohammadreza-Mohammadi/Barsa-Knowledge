# AR04 — reference-reconstruction-evaluator

## Purpose
ارزیابی Integration با بازسازی Target مرجع و تولید BSDN بازسازی‌شده از evidence واقعی، بدون تغییر Target اصلی و بدون تبدیل خودکار Legacy به Best Practice.

## Select / do not select
- انتخاب: Target واقعی/فایل/DB مرجع داده شده و هدف reconstruction، Plan/Apply/Read/Verify یا کشف gap است.
- انتخاب نکن: طراحی بهتر Target، mutation Target اصلی یا patch مستقیم Integration هدف اصلی است.

## Reverse evidence workflow
```text
read-only Target
→ Runtime Semantic first
→ referenced Report/Workflow only when needed
→ Code last, only when prior evidence is insufficient
→ Reconstructed BSDN / draft
→ reconstruction review
→ Reconstructed BSDN / approved when evidence is sufficient
→ test reconstruction actions as mission requires
```

**Source Priority:** `Semantic → Report/Workflow when needed → Code last`. **Stop Condition:** وقتی evidence معتبر موجود پاسخ لازم را داده، cross-check اضافی متوقف می‌شود. External Binding حل‌نشده با مقصد منطقی روشن ثبت می‌شود و جست‌وجوی بی‌پایان برای ID/System واقعی انجام نمی‌شود. intent نامعلوم می‌تواند به‌صورت observed/suspicious باقی بماند.

`بازسازی‌شده + مصوب` فقط reconstruction تأییدشده است و **Build design authority نیست**. Target evidence oracle بازسازی است، نه Best Practice عمومی. Runtime IDهای اجرای جاری در reference action تثبیت نشوند؛ `tempId`/reference پایدار استفاده شود. normative Reverse lifecycle در `knowledge/bsdn/lifecycle.fa.md` است.

## Main Skills
`SK03, SK04, SK05, SK06, SK07, SK08, SK09`؛ `SK01/SK02` فقط برای فهم action/lesson یا تبدیل reconstruction به Target Design جداگانه، نه redesign بی‌صدا.

## Outputs
- Reconstructed BSDN و evidence/uncertainty آن
- `artifact:stage1-result.fa.md`
- `reference-actions.json` فقط مسیر نهایی
- `artifact:stage2-lessons.fa.md` همیشه، با `Stage1Status/ReadyForStage2`
- در صورت نیاز `artifact:rule-updates/*` یا `artifact:bug-report.md`

## Boundaries
Target موجود mutate نمی‌شود. failure ابتدا به Skill/contract مسئول route می‌شود. Rule/case-specific workaround تولید نشود. Reconstructed BSDN بدون Design Review جداگانه به Target BSDN تبدیل نمی‌شود.

Alias مهاجرتی: `azmoongar-1`.
