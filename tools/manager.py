#!/usr/bin/env python3
"""Manager — the only entry point to the Barsa agent protocol.

A task walks from a raw request to a verified `AiChangeBatch`, through the same
state machine and the same two human gates as the BarsaAgent workflow. The
console speaks to this CLI and never touches `.agent-work/` itself.

    python3 tools/manager.py init --system 1011413550000000100
    python3 tools/manager.py import-issue --file request.json
    python3 tools/manager.py run 0001
    python3 tools/manager.py answer 0001 --approve
    python3 tools/manager.py status --json
    python3 tools/manager.py board

JSON discipline: `capabilities`, `status`, `events` and `verify --json` print
nothing but JSON on stdout. `run` is the exception -- it streams a human log,
and its exit code carries the outcome:

    0 integrated · 10 awaiting a human · 20 stopped · 30 no progress
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_kanban.manager import Manager, ManagerError
from barsa_kanban.states import EXIT_LABELS
from barsa_kanban.store import StoreError


def force_utf8_stdio():
    """Windows pipes default to the ANSI code page; Persian output dies there.

    What this prints is a contract, not decoration: the console reads this
    JSON through a pipe, and on Windows that pipe is cp1252 by default, so
    the first Persian slug raises UnicodeEncodeError and the board never
    loads. `errors="replace"` keeps a console that genuinely cannot render
    Persian from crashing the run over it.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _emit(doc):
    print(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True))


def _read_reason(args):
    """Free text never comes through argv -- always a UTF-8 file.

    A Persian reason pasted into a Windows console arrives as `???`, and a
    reason that lost its text is worse than no reason at all.
    """
    if getattr(args, "reason_file", None):
        with open(args.reason_file, encoding="utf-8") as fh:
            return fh.read().strip()
    if getattr(args, "reason", None):
        text = args.reason
        if "??" in text:
            raise ManagerError(
                "متن دلیل شامل '??' است، یعنی encoding در مسیر شکسته. از "
                "--reason-file با یک فایل UTF-8 استفاده کن.")
        return text.strip()
    return None


def main(argv=None):
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="repository root")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold .agent-work/ and its config")
    p.add_argument("--system", help="the Barsa system id to allow")

    sub.add_parser("capabilities", help="the contract handshake")

    p = sub.add_parser("status", help="the board, or one task")
    p.add_argument("--task")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("events", help="a task's event log")
    p.add_argument("task")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("artifact", help="print one artifact of a task")
    p.add_argument("task")
    p.add_argument("--path", required=True)

    p = sub.add_parser("import-issue", help="create a task from a request")
    p.add_argument("--file", help="JSON payload")
    p.add_argument("--slug")
    p.add_argument("--kind")
    p.add_argument("--system",
                   help="id یا نام سیستم. ندهی، Intake باید از متن درخواست "
                        "تشخیصش بدهد و اگر نتوانست سؤال می‌پرسد.")
    p.add_argument("--request-file")
    p.add_argument("request", nargs="?")

    p = sub.add_parser("run", help="advance the task until it needs someone")
    p.add_argument("task")

    p = sub.add_parser("verify", help="run the verification gates now")
    p.add_argument("task")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("answer", help="answer a human gate")
    p.add_argument("task")
    p.add_argument("--approve", action="store_true")
    p.add_argument("--reject", action="store_true")
    p.add_argument("--clarify", action="store_true")
    p.add_argument("--file", help="clarification answer, UTF-8")
    p.add_argument("--reason-file")
    p.add_argument("--reason")
    p.add_argument("--respec", action="store_true")
    p.add_argument("--route", choices=["implementer", "architect"])

    for name, helptext in (("cancel", "close a task"),
                           ("abandon", "close a task as abandoned"),
                           ("void", "undo the last transition"),
                           ("unlock", "release a stale transition lock")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("task")
        p.add_argument("--reason-file")
        p.add_argument("--reason")
        if name == "unlock":
            p.add_argument("--force", action="store_true")

    p = sub.add_parser("host", help="talk to Barsa.Ai.Host without applying")
    p.add_argument("--health", action="store_true")
    p.add_argument("--systems", action="store_true")
    p.add_argument("--lint", metavar="TASK")
    p.add_argument("--plan", metavar="TASK",
                   help="build a plan for the task's batch and print the "
                        "host's disposition; applies nothing")
    p.add_argument("--preflight", metavar="TASK",
                   help="every read-only check in order, against the real "
                        "host, before the first apply. Applies nothing.")

    p = sub.add_parser("systems", help="the systems a request can be about")
    p.add_argument("--json", action="store_true")

    sub.add_parser("board", help="regenerate BOARD.md")

    args = ap.parse_args(argv)
    manager = Manager(args.repo)

    try:
        return _dispatch(manager, args)
    except (ManagerError, StoreError) as exc:
        print("خطا: %s" % exc, file=sys.stderr)
        return 1


def _dispatch(manager, args):
    cmd = args.cmd

    if cmd == "init":
        written = manager.init(args.system)
        for path in written:
            print("نوشته شد: %s" % os.path.relpath(path, manager.repo_root))
        if not written:
            print(".agent-work/ از قبل آماده بود؛ هیچ فایلی بازنویسی نشد.")
        return 0

    if cmd == "capabilities":
        _emit(manager.capabilities())
        return 0

    if cmd == "status":
        # status is JSON only, per the contract's JSON discipline; --json is
        # accepted for symmetry with the other verbs.
        _emit(manager.status(args.task))
        return 0

    if cmd == "events":
        task_dir = manager.store.task_dir_or_fail(args.task)
        _emit({"task": str(args.task),
               "events": manager.store.read_events(task_dir)})
        return 0

    if cmd == "artifact":
        task_dir = manager.store.task_dir_or_fail(args.task)
        path = manager.store.resolve_in_task(task_dir, args.path)
        if not os.path.isfile(path):
            raise ManagerError("artifact وجود ندارد: %s" % args.path)
        with open(path, encoding="utf-8") as fh:
            sys.stdout.write(fh.read())
        return 0

    if cmd == "import-issue":
        payload = _import_payload(args)
        result = manager.create_task(payload)
        _emit(result)
        return 0

    if cmd == "run":
        code = manager.run(args.task)
        label = EXIT_LABELS.get(code)
        if label:
            print("[%d] %s" % (code, label))
        return code

    if cmd == "verify":
        report = manager.verify_task(args.task)
        if args.json:
            _emit(report)
        else:
            print("batch: %s" % (report.get("batch") or {}).get("path"))
            summary = report.get("summary") or {}
            for gate in (report.get("gates") or ()):
                row = summary.get(gate) or {}
                print("  %-10s %s  (errors=%s warnings=%s)"
                      % (gate, "پاس" if row.get("passed") else "رد",
                         row.get("errors"), row.get("warnings")))
            for f in report.get("findings") or ():
                print("  - [%s] %s" % (f["gate"], f["message"]))
                if f.get("where"):
                    print("      %s" % f["where"])
                if f.get("hint"):
                    print("      %s" % f["hint"])
        return 0 if report.get("ok") else 1

    if cmd == "answer":
        clarify = None
        if args.clarify:
            if not args.file:
                raise ManagerError("--clarify نیازمند --file است.")
            with open(args.file, encoding="utf-8") as fh:
                clarify = fh.read()
        manager.answer(args.task, approve=args.approve, reject=args.reject,
                       clarify=clarify, reason=_read_reason(args),
                       respec=args.respec, route=args.route)
        return 0

    if cmd in ("cancel", "abandon"):
        manager.cancel(args.task, _read_reason(args), abandon=cmd == "abandon")
        return 0

    if cmd == "void":
        manager.void(args.task, _read_reason(args))
        return 0

    if cmd == "unlock":
        manager.unlock(args.task, _read_reason(args), force=args.force)
        return 0

    if cmd == "systems":
        rows = manager.systems()
        if args.json:
            _emit({"systems": rows})
            return 0
        if not rows:
            print("هیچ سیستمی در بسته نیست. اول tools/extract.py را اجرا کن.")
            return 1
        print("%-22s %-28s %8s %8s  %s"
              % ("id", "نام", "موجودیت", "گزارش", "قابل authoring"))
        for row in rows:
            print("%-22s %-28s %8s %8s  %s"
                  % (row["id"], (row["caption"] or "—")[:28],
                     row["entities"], row["reports"],
                     "بله (%s selector)" % row["selectorCount"]
                     if row["authorable"] else "نه"))
        missing = [r for r in rows if not r["authorable"]]
        if missing:
            print("")
            print("برای اینکه سیستمی قابل authoring شود، بستهٔ گزارشش را "
                  "بساز:")
            print("  python3 tools/report_compiler.py --scope system=%s"
                  % missing[0]["id"])
        return 0

    if cmd == "host":
        return _host_command(manager, args)

    if cmd == "board":
        path = manager.render_board()
        print("نوشته شد: %s" % os.path.relpath(path, manager.repo_root))
        return 0

    raise ManagerError("فرمان ناشناس: %s" % cmd)


def _host_command(manager, args):
    """A dry run against the host: nothing here can change anything."""
    from barsa_kanban import barsa_host
    client, settings = manager.host_client()
    if args.preflight:
        return _preflight(manager, client, settings, args.preflight)
    print("host: %s" % client.prefix)
    if not client.api_key:
        print("  هشدار: کلیدی در محیط نیست (%s). اگر host کلید می‌خواهد، "
              "پاسخ 401 می‌گیری."
              % ((settings.get("apiKeyEnv")) or "BARSA_AI_HOST_KEY"))
    try:
        if args.health or not (args.systems or args.lint or args.plan):
            _emit(client.health())
        if args.systems:
            _emit(client.systems())
        for task_id, call in ((args.lint, client.lint),
                              (args.plan, client.plan)):
            if not task_id:
                continue
            task_dir = manager.store.task_dir_or_fail(task_id)
            raw = manager.store.read_text(task_dir, "change-batch.json")
            if raw is None:
                raise ManagerError("تسک %s هنوز change-batch.json ندارد."
                                   % task_id)
            _emit(call(json.loads(raw)))
    except barsa_host.HostError as exc:
        print(exc.detail(), file=sys.stderr)
        return 1
    return 0


def _preflight(manager, client, settings, task_id):
    """Everything that can be checked without writing anything.

    Deliberately ordered so the cheapest failure comes first: a wrong prefix
    should not be discovered after a plan has been built. Nothing here calls
    /apply, so the worst outcome is a plan left in the host's memory.
    """
    from barsa_kanban import barsa_host

    integration = (manager.config["repository"].get("integration") or {})
    expected = (manager.connection or {}).get("database") or {}
    checks = []

    def record(name, ok, detail):
        checks.append((name, ok, detail))
        print("  %-22s %s  %s" % (name, "✓" if ok else "✗", detail))

    print("preflight برای تسک %s" % task_id)
    print("host: %s" % client.prefix)

    applied_by = integration.get("appliedBy")
    record("appliedBy", applied_by == "barsa-host",
           applied_by + ("" if applied_by == "barsa-host"
                         else " — تأیید فعلاً چیزی را اعمال نمی‌کند"))
    key_env = settings.get("apiKeyEnv") or "BARSA_AI_HOST_KEY"
    record("کلید", True,
           "از %s خوانده شد" % key_env if client.api_key
           else "تنظیم نشده — اگر host هم کلید ندارد، درش برای هر برنامه‌ای "
                "روی این ماشین باز است")

    task_dir = manager.store.task_dir_or_fail(task_id)
    manifest = manager.store.read_manifest(task_dir)
    raw = manager.store.read_text(task_dir, "change-batch.json")
    if raw is None:
        record("batch", False, "تسک هنوز change-batch.json ندارد")
        return 1
    batch = json.loads(raw)
    record("batch", True, "%d فرمان" % len(batch.get("changes") or ()))

    report = manager.verify_task(task_id)
    record("پنج گیت محلی", report["ok"],
           "پاس" if report["ok"] else "رد — اول verify را درست کن")
    if not report["ok"]:
        return 1

    try:
        health = client.health()
    except barsa_host.HostError as exc:
        record("health", False, str(exc))
        print(exc.detail(), file=sys.stderr)
        return 1
    database = health.get("database") or {}
    # An older host, or a stub, may answer a bare string here.
    finger = health.get("runtimeFingerprint")
    finger = finger if isinstance(finger, dict) else {}
    record("health", str(health.get("status")) == "ready",
           "%s · دیتابیس %s/%s · پروفایل %s · قرارداد %s"
           % (health.get("status"), database.get("server"),
              database.get("name"),
              finger.get("semanticProfileVersion"),
              finger.get("socContractRevision")))

    mismatch = barsa_host.HostClient.profile_mismatch(health)
    record("نسخهٔ پروفایل", mismatch is None,
           "هر دو %s" % finger.get("semanticProfileVersion")
           if mismatch is None else
           "ما برای %s می‌نویسیم و host %s را اجرا می‌کند — هر batch به "
           "قراردادی آدرس دارد که host دیگر صحبت نمی‌کند"
           % mismatch)

    from barsa_kanban import connection as connection_mod
    db_ok, db_message = connection_mod.check_database(manager.connection,
                                                      health)
    record("دیتابیس مورد انتظار", db_ok, db_message)

    system_id = str((manifest.get("need") or {}).get("system") or "")
    try:
        systems = client.systems()
        ids = {str(row.get("id")) for row in (systems.get("systems") or ())}
        record("سیستم تسک", system_id in ids,
               "%s %s %d سیستم"
               % (system_id, "در" if system_id in ids else "نیست در", len(ids)))
    except barsa_host.HostError as exc:
        record("سیستم تسک", False, str(exc))

    try:
        lint = client.lint(batch)
        record("lint سمت سرور", str(lint.get("status")) == "succeeded",
               json.dumps(lint, ensure_ascii=False)[:140])
    except barsa_host.HostError as exc:
        record("lint سمت سرور", False, str(exc))
        print(exc.detail(), file=sys.stderr)
        return 1

    try:
        plan = client.plan(batch)
    except barsa_host.HostError as exc:
        record("plan", False, str(exc))
        print(exc.detail(), file=sys.stderr)
        return 1
    clean = plan.get("isValid") is not False and \
        plan.get("canApplyCleanly") is not False
    record("plan", clean,
           "planId=%s valid=%s clean=%s فرمان=%s خطا=%s"
           % (plan.get("planId"), plan.get("isValid"),
              plan.get("canApplyCleanly"), plan.get("commandCount"),
              plan.get("errorCount")))
    if plan.get("summary"):
        print("\n%s" % plan["summary"])
    diagnostics = (plan.get("diagnostics") or {}).get("items") or []
    for row in diagnostics[:20]:
        print("  · %s" % json.dumps(row, ensure_ascii=False)[:200])

    failed = [name for name, ok, _ in checks if not ok]
    print("")
    print("هیچ چیزی اعمال نشد — این دستور فقط می‌خواند.")
    if failed:
        print("ناموفق: %s" % "، ".join(failed))
        return 1
    print("همه سبز. برای اعمال واقعی: python3 tools/manager.py answer %s "
          "--approve" % task_id)
    return 0


def _import_payload(args):
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            payload = json.load(fh)
    else:
        text = args.request
        if args.request_file:
            with open(args.request_file, encoding="utf-8") as fh:
                text = fh.read()
        if not text:
            raise ManagerError(
                "متن درخواست لازم است: --file <json> یا --request-file <txt> "
                "یا متن به‌عنوان آرگومان آخر.")
        payload = {"requestText": text}
    for name in ("slug", "kind", "system"):
        value = getattr(args, name, None)
        if value:
            payload[name] = value
    if not payload.get("slug"):
        raise ManagerError("slug لازم است: --slug <نام-کوتاه>")
    return payload


if __name__ == "__main__":
    sys.exit(main())
