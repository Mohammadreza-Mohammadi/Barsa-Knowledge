"""`connection.yaml` — the one file that says which Barsa we are pointed at.

Everything about reaching a Barsa installation lives here, in one place, so
that "which database am I about to write to" has a single answer you can read
without running anything.

What this file deliberately does **not** do is open a database connection.
Nothing in this repository speaks to SQL Server: the write path goes through
`Barsa.Ai.Host`, which gets its own connection from Barsa's own config. A
second connection string here would be a second source of truth for the most
dangerous question in the system.

What it holds instead is the *expected* identity of that database. The host
reports what it is actually attached to on `/health`, and the manager compares
the two before it applies anything. A mismatch stops the apply -- that is the
whole point of writing it down.
"""

import os

from . import yamlite
from .store import StoreError

FILENAME = "connection.yaml"

TEMPLATE = """\
# تنها جایی که می‌گوید به کدام بارسا وصل هستیم.
#
# اینجا هیچ connection string دیتابیسی نیست و عمداً نیست: این مخزن هرگز
# مستقیم به SQL وصل نمی‌شود. مسیر نوشتن از Barsa.Ai.Host می‌گذرد و او
# connection خودش را از config خودِ بارسا می‌گیرد. دو جا برای یک حقیقت —
# «روی کدام دیتابیس می‌نویسیم» — خطرناک‌ترین نوع drift است.
#
# چیزی که اینجا می‌نویسی هویت *مورد انتظار* آن دیتابیس است. host در /health
# می‌گوید واقعاً به چه چیزی وصل است، و Manager قبل از هر اعمال این دو را
# مقایسه می‌کند. نخوانند، اعمال انجام نمی‌شود.
schemaVersion: 1

# برچسبی که در هدر کنسول دیده می‌شود. کوتاه و خوانا: «تست»، «پیش‌تولید».
label: "محیط تست"

host:
  prefix: "http://127.0.0.1:17840/"   # AiHost.HttpPrefix
  # نام متغیر محیطی که AiHost.ApiKey در آن است — نه خود کلید.
  apiKeyEnv: BARSA_AI_HOST_KEY
  timeoutSeconds: 180
  maxWaitSeconds: 600
  # اگر host بگوید این plan تمیز اعمال نمی‌شود، اعمال نکن.
  requireCleanPlan: true

database:
  # از خروجی `python tools/manager.py host --health` پر کن. هر کدام را خالی
  # بگذاری، همان یکی مقایسه نمی‌شود.
  server: ""
  name: ""
  instance: ""
  # نخواندنِ هویت دیتابیس با آنچه host می‌گوید، اعمال را متوقف می‌کند.
  # false کردنش یعنی می‌پذیری که ممکن است روی دیتابیس دیگری بنویسی.
  enforce: true
"""


def path(store):
    return os.path.join(store.config_dir, FILENAME)


def load(store):
    """The connection settings, or None when the file is not there yet."""
    full = path(store)
    if not os.path.isfile(full):
        return None
    with open(full, encoding="utf-8") as fh:
        try:
            doc = yamlite.loads(fh.read())
        except yamlite.YamlError as exc:
            raise StoreError("%s خراب است: %s" % (FILENAME, exc))
    if doc.get("schemaVersion") != 1:
        raise StoreError("%s نیازمند schemaVersion: 1 است" % FILENAME)
    host = doc.get("host") or {}
    if "apiKey" in host:
        raise StoreError(
            "%s نباید apiKey داشته باشد. نام متغیر محیطی را در apiKeyEnv "
            "بنویس؛ کلیدی که commit شود کلیدی است که لو می‌رود." % FILENAME)
    return doc


def write_template(store):
    full = path(store)
    if os.path.isfile(full):
        return None
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(TEMPLATE)
    return full


def host_settings(config, connection):
    """Host settings, preferring connection.yaml over the older location."""
    if connection and connection.get("host"):
        return dict(connection["host"])
    return dict((config["repository"].get("integration") or {}).get("host")
                or {})


def check_database(connection, health):
    """Compare the database the host reports with the one we expect.

    Returns (ok, message). Unknown is not agreement: an expected value that
    the host does not report is reported as unverifiable, not as a match.
    """
    expected = (connection or {}).get("database") or {}
    if not expected or expected.get("enforce") is False:
        return True, "مقایسهٔ دیتابیس خاموش است (database.enforce: false)."
    actual = (health or {}).get("database") or {}
    wanted = {k: str(expected.get(k) or "").strip()
              for k in ("server", "name", "instance")}
    if not any(wanted.values()):
        return True, ("هویت دیتابیس در connection.yaml خالی است، پس چیزی "
                      "مقایسه نشد. از خروجی host --health پرش کن.")
    problems = []
    for key, want in wanted.items():
        if not want:
            continue
        got = str(actual.get(key) or "").strip()
        if not got:
            problems.append("%s: انتظار %r، ولی host چیزی نگفت" % (key, want))
        elif got.lower() != want.lower():
            problems.append("%s: انتظار %r، ولی host می‌گوید %r"
                            % (key, want, got))
    if problems:
        return False, "؛ ".join(problems)
    return True, "دیتابیس همان است که انتظار می‌رفت: %s/%s" % (
        actual.get("server"), actual.get("name"))
