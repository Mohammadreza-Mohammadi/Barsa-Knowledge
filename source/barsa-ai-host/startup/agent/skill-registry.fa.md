# Skill Registry

Skill capability مستقل است، نه Workflow step. contract کامل SK01..SK10 در `agent/skills.fa.md` است.

BSDN skill guidance به `knowledge/bsdn/00-start.fa.md` route می‌شود؛ Registry فقط Purpose را sync می‌کند.

| Code | Name | Purpose |
|---|---|---|
| `SK01` | Requirement Analysis | Sources → canonical System/Section Requirements + completeness/minimality؛ بدون Design/Change authority |
| `SK02` | System Design | Overall BSDN per System + Detailed BSDN per Section؛ canonical Desired Design، ownership و completeness/minimality مستقل از Apply |
| `SK03` | Semantic Model Read / Generation | actual-state Semantic و Reverse evidence برای BSDN |
| `SK04` | Generate SystemBuilder Actions / Change Construction | Current Build Scope BSDN + relevant Support Mapping + Execution Authorization → exact Actions + expected read-back؛ بدون Design جدید |
| `SK05` | Plan | exact core contract-shape validation + dependency/order فنی قبل از persistence، بدون تصمیم Design |
| `SK06` | Apply | اجرای Plan پذیرفته‌شده بدون semantics جدید |
| `SK07` | Read Actual State | خواندن وضعیت واقعی Runtime/Metadata |
| `SK08` | Verify | Step/Wave → Section → System → Final Delivery verification؛ Runtime ↔ Current Target BSDN scopes |
| `SK09` | AI Work Management / Governance | routing، Solution/Delivery/Build Scope، operational artifacts، continuation، recovery و version evolution |
| `SK10` | KM Generate / Update | KM با مصرف BSDN/Runtime/HK، بدون تبدیل KM به Design authority |
