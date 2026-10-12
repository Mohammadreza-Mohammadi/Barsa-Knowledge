"""Configuration — what belongs to the repository owner, not to the tool.

Two files, both under `.agent-work/config/`, both read strictly:

  repository.yaml    which Barsa systems may be worked on, which verification
                     gates run, and who applies a finished batch
  agent-runtime.yaml which provider runs each role

A missing file is not a silent default: the manager writes a starter pair on
`init` and refuses to run without them.
"""

import os

from . import yamlite
from .store import StoreError

REPOSITORY_FILE = "repository.yaml"
RUNTIME_FILE = "agent-runtime.yaml"

DEFAULT_BUDGET = {
    "intakeRuns": 3,
    "architectRuns": 4,
    "implementerRuns": 6,
    "reviewerRuns": 4,
    "clarifications": 3,
    "attempts": 24,
}

REPOSITORY_TEMPLATE = """\
# چه چیزی مال صاحب مخزن است، نه ابزار. این فایل را دستی ویرایش کن.
schemaVersion: 1

# بستهٔ دانش که هر نقش از آن می‌خواند. Compiler گزارش این‌ها را می‌سازد.
knowledge:
  dist: dist
  pack: dist-report

# سیستم‌هایی که کار روی آن‌ها مجاز است. خالی یعنی «هر سیستمی که در بسته
# هست» — فهرست کامل را با `python tools/manager.py systems` ببین.
# این یک allowlist است، نه یک پیش‌فرض: اگر درخواست سیستمی نگوید، Intake
# باید از متن تشخیصش بدهد و اگر نتوانست سؤال می‌پرسد.
systems:
  allow: []

# گیت‌های verification. هیچ‌کدام را خالی نگذار مگر دلیلش را همین‌جا بنویسی —
# یک گیت غیرفعال در پنل apply-approval هشدار می‌دهد.
verification:
  gates: [lint, selectors, unknowns, scope, order]

budget:
  intakeRuns: {intakeRuns}
  architectRuns: {architectRuns}
  implementerRuns: {implementerRuns}
  reviewerRuns: {reviewerRuns}
  clarifications: {clarifications}
  attempts: {attempts}

integration:
  # چه کسی batch تأییدشده را روی بارسا اعمال می‌کند.
  #   human      → `answer <id> --approve` یعنی «من خودم اعمال کردم». Manager
  #                قبل از بستن تسک مکانیکی اثبات می‌کند batch همان چیزی است
  #                که گیت رویش باز شد و هنوز از همهٔ گیت‌ها رد می‌شود.
  #   barsa-host → تأیید تو یعنی «اعمالش کن». Manager خودش batch را به
  #                Barsa.Ai.Host می‌دهد: POST /plan، بررسی disposition،
  #                POST /apply، و انتظار برای یک حکم واقعی از /apply-status.
  #                تسک فقط با پاسخ خودِ بارسا بسته می‌شود، نه با حرف کسی.
  appliedBy: human

  # فقط وقتی appliedBy: barsa-host معنا دارد.
  host:
    prefix: "http://127.0.0.1:17840/"   # AiHost.HttpPrefix
    # کلید هرگز در این فایل نیست — نام متغیر محیطی است که مقدار
    # AiHost.ApiKey را نگه می‌دارد.
    apiKeyEnv: BARSA_AI_HOST_KEY
    timeoutSeconds: 180
    # اگر host بگوید این plan تمیز اعمال نمی‌شود، اعمال نکن. false کردنش
    # یعنی اعمال نیمه‌کاره را می‌پذیری؛ خط لوله عمداً atomic نیست.
    requireCleanPlan: true
    maxWaitSeconds: 600

  # درست مثل autoMerge در آن workflow: عمداً false. اعتماد باید کسب شود.
  autoApply: false
"""

RUNTIME_TEMPLATE = """\
# انتخاب provider برای هر نقش. برای سوییچ کل workflow فقط defaultProvider را عوض کن.
schemaVersion: 1
defaultProvider: manual

roles:
  intake:
    provider: default
  architect:
    provider: default
  implementer:
    provider: default
  reviewer:
    provider: default

providers:
  # manual: Manager هیچ agent صدا نمی‌زند. گیت‌ها، قفل‌ها و verification را
  # اداره می‌کند و می‌گوید نقش بعدی دقیقاً چه فایلی باید بنویسد. وقتی آن فایل‌ها
  # نوشته شدند، `run` بعدی مصرفشان می‌کند و transition می‌دهد.
  manual:
    enabled: true
  # claude: مثل run-agent.js خودت — هر transition یک agent headless اجرا می‌کند.
  # عمداً خاموش: هر اجرا توکن مصرف می‌کند، و روشن‌کردنش تصمیم صاحب مخزن است.
  claude:
    enabled: false
    command: claude
    # ابزارهایی که نقش دارد. یک نقش بسته را می‌خواند و artifact خودش را
    # می‌نویسد؛ دلیلی ندارد دستور اجرا کند.
    allowedTools: "Read Write Edit Glob Grep"
    permissionMode: acceptEdits
    timeoutSeconds: 900
    # اختیاری، به ازای نقش: مثلاً architect و reviewer روی مدل قوی‌تر.
    model:
      intake: null
      architect: null
      implementer: null
      reviewer: null
"""


def load(store):
    """Both config files, or a StoreError naming what to do about it."""
    repo = _load_one(store, REPOSITORY_FILE)
    runtime = _load_one(store, RUNTIME_FILE)
    _validate_repository(repo)
    _validate_runtime(runtime)
    return {"repository": repo, "runtime": runtime}


def _load_one(store, name):
    path = os.path.join(store.config_dir, name)
    if not os.path.isfile(path):
        raise StoreError(
            "%s is missing. Run: python3 tools/manager.py init"
            % os.path.join(".agent-work", "config", name))
    with open(path, encoding="utf-8") as fh:
        try:
            return yamlite.loads(fh.read())
        except yamlite.YamlError as exc:
            raise StoreError("%s is malformed: %s" % (name, exc))


def _validate_repository(doc):
    if doc.get("schemaVersion") != 1:
        raise StoreError("repository.yaml needs schemaVersion: 1")
    integration = doc.get("integration") or {}
    applied_by = integration.get("appliedBy")
    if applied_by not in ("human", "barsa-host"):
        raise StoreError(
            "integration.appliedBy must be 'human' (you apply the batch and "
            "say so) or 'barsa-host' (the manager hands it to "
            "Barsa.Ai.Host). Got %r." % (applied_by,))
    if applied_by == "barsa-host":
        host = integration.get("host") or {}
        if not host.get("prefix"):
            raise StoreError(
                "integration.host.prefix is required when appliedBy is "
                "barsa-host. The host's default is http://127.0.0.1:17840/ "
                "(AiHost.HttpPrefix).")
        if "apiKey" in host:
            raise StoreError(
                "integration.host.apiKey must not be in this file. Name the "
                "environment variable in apiKeyEnv instead; a key in a "
                "committed config is a key that leaks.")
    gates = ((doc.get("verification") or {}).get("gates")) or []
    from .verify import GATES
    unknown = [g for g in gates if g not in GATES]
    if unknown:
        raise StoreError("repository.yaml names unknown verification gates: %s"
                         % ", ".join(unknown))


def _validate_runtime(doc):
    if doc.get("schemaVersion") != 1:
        raise StoreError("agent-runtime.yaml needs schemaVersion: 1")
    default = doc.get("defaultProvider")
    providers = doc.get("providers") or {}
    if default not in providers:
        raise StoreError("defaultProvider %r is not in providers" % (default,))


def provider_for(config, role):
    """Which provider runs this role, and its settings."""
    runtime = config["runtime"]
    roles = runtime.get("roles") or {}
    name = ((roles.get(role) or {}).get("provider")) or "default"
    if name == "default":
        name = runtime.get("defaultProvider")
    settings = (runtime.get("providers") or {}).get(name) or {}
    if not settings.get("enabled"):
        raise StoreError(
            "provider %r for role %r is not enabled in agent-runtime.yaml. "
            "Enable it there, or leave the role on 'manual'." % (name, role))
    return name, settings


def budget_limits(config):
    out = dict(DEFAULT_BUDGET)
    out.update({k: v for k, v in (config["repository"].get("budget") or
                                  {}).items() if isinstance(v, int)})
    return out


def write_templates(store, system_id):
    """Starter config, written once by `init`; never overwritten."""
    written = []
    for name, text in ((REPOSITORY_FILE,
                        REPOSITORY_TEMPLATE.format(system=system_id or "",
                                                   **DEFAULT_BUDGET)),
                       (RUNTIME_FILE, RUNTIME_TEMPLATE)):
        path = os.path.join(store.config_dir, name)
        if os.path.isfile(path):
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(path)
    return written
