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
    p.add_argument("--system")
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
    client, settings = barsa_host.from_config(manager.config)
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
