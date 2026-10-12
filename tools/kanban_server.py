#!/usr/bin/env python3
"""The local console behind the kanban board.

It is the BarsaAgent server for this protocol, with the same ownership
boundary and the same route names:

    browser  →  this server (127.0.0.1)  →  tools/manager.py  →  .agent-work/

This server never reads or writes `.agent-work/` itself and never decides a
transition. Every answer it gives came out of a manager command, so the board
cannot disagree with the store.

    python3 tools/kanban_server.py --port 4310

Then open http://127.0.0.1:4310/. No npm, no build step: the UI is one file.
"""

import argparse
import json
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(HERE, "kanban_ui")
MANAGER = os.path.join(HERE, "manager.py")

# Anything that looks like a token or a key is masked before it reaches the
# log stream, the same rule the console it mirrors applies.
_SECRET = re.compile(
    r"(?i)(token|secret|password|api[-_]?key|authorization)([\"'\s:=]+)"
    r"([^\s\"',}]{6,})")


def mask(text):
    return _SECRET.sub(lambda m: m.group(1) + m.group(2) + "***", text or "")


class RunQueue:
    """One active run per task, `maxConcurrent` overall.

    A second run of the same task is refused rather than queued twice: two
    managers writing one manifest is the failure this exists to prevent.
    """

    def __init__(self, repo_root, max_concurrent=2, log_lines=400):
        self.repo_root = repo_root
        self.max_concurrent = max_concurrent
        self.lock = threading.Lock()
        self.state = {}          # taskId -> row
        self.logs = {}           # taskId -> [lines]
        self.listeners = {}      # taskId -> [queue]
        self.pending = []
        self.active = 0
        self.log_lines = log_lines

    # -- public ------------------------------------------------------------

    def enqueue(self, task_id):
        with self.lock:
            row = self.state.get(task_id)
            if row and (row.get("running") or row.get("queued")):
                return False, row
            row = {"taskId": task_id, "queuedAt": _now(), "startedAt": None,
                   "finishedAt": None, "queued": True, "running": False,
                   "exitCode": None}
            self.state[task_id] = row
            self.pending.append(task_id)
            self._positions()
        self._pump()
        return True, row

    def snapshot(self):
        with self.lock:
            return {k: dict(v) for k, v in self.state.items()}

    def tail(self, task_id):
        with self.lock:
            return list(self.logs.get(task_id) or ())

    def subscribe(self, task_id):
        q = queue.Queue()
        with self.lock:
            self.listeners.setdefault(task_id, []).append(q)
            for line in self.logs.get(task_id) or ():
                q.put(line)
        return q

    def unsubscribe(self, task_id, q):
        with self.lock:
            rows = self.listeners.get(task_id) or []
            if q in rows:
                rows.remove(q)

    # -- internals ---------------------------------------------------------

    def _positions(self):
        for i, task_id in enumerate(self.pending):
            self.state[task_id]["queuePosition"] = i + 1

    def _pump(self):
        with self.lock:
            if self.active >= self.max_concurrent or not self.pending:
                return
            task_id = self.pending.pop(0)
            self._positions()
            row = self.state[task_id]
            row.update({"queued": False, "running": True,
                        "startedAt": _now(), "queuePosition": None})
            self.active += 1
        threading.Thread(target=self._run, args=(task_id,),
                         daemon=True).start()

    def _run(self, task_id):
        self._emit(task_id, "$ manager.py run %s" % task_id)
        code = 1
        try:
            proc = subprocess.Popen(
                [sys.executable, MANAGER, "--repo", self.repo_root, "run",
                 task_id],
                cwd=self.repo_root, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                self._emit(task_id, line.rstrip("\n"))
            proc.wait()
            code = proc.returncode
        except OSError as exc:
            self._emit(task_id, "خطای اجرا: %s" % exc)
        finally:
            with self.lock:
                row = self.state.get(task_id) or {}
                row.update({"running": False, "finishedAt": _now(),
                            "exitCode": code})
                self.active -= 1
            self._emit(task_id, "[exit %s]" % code)
            self._pump()

    def _emit(self, task_id, line):
        line = mask(line)
        with self.lock:
            rows = self.logs.setdefault(task_id, [])
            rows.append(line)
            del rows[:-self.log_lines]
            listeners = list(self.listeners.get(task_id) or ())
        for q in listeners:
            q.put(line)


class Console:
    def __init__(self, repo_root, run_queue, auto_start=True,
                 auto_resume=True):
        self.repo_root = repo_root
        self.runs = run_queue
        self.auto_start = auto_start
        self.auto_resume = auto_resume

    def manager(self, *args, text=None):
        """Call the manager CLI. The only way this console touches state."""
        argv = [sys.executable, MANAGER, "--repo", self.repo_root] + list(args)
        proc = subprocess.run(argv, cwd=self.repo_root, capture_output=True,
                              text=True, input=text)
        return proc.returncode, proc.stdout, proc.stderr

    def manager_json(self, *args):
        code, out, err = self.manager(*args)
        if code != 0:
            raise ConsoleError(err.strip() or out.strip() or
                               "manager exited %d" % code)
        try:
            return json.loads(out)
        except ValueError:
            raise ConsoleError("manager did not return JSON: %s" % out[:300])


class ConsoleError(Exception):
    pass


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


ROUTES = [
    ("GET", r"^/api/repos$", "repos"),
    ("GET", r"^/api/repos/([^/]+)/board$", "board"),
    ("GET", r"^/api/repos/([^/]+)/running$", "running"),
    ("GET", r"^/api/repos/([^/]+)/health$", "health"),
    ("GET", r"^/api/repos/([^/]+)/tasks/([^/]+)$", "task"),
    ("GET", r"^/api/repos/([^/]+)/tasks/([^/]+)/events$", "events"),
    ("GET", r"^/api/repos/([^/]+)/tasks/([^/]+)/artifact$", "artifact"),
    ("GET", r"^/api/repos/([^/]+)/tasks/([^/]+)/stream$", "stream"),
    ("POST", r"^/api/repos/([^/]+)/tasks/([^/]+)/run$", "run"),
    ("POST", r"^/api/repos/([^/]+)/tasks/([^/]+)/answer$", "answer"),
    ("POST", r"^/api/repos/([^/]+)/tasks/([^/]+)/(void|cancel|unlock)$",
     "side"),
    ("POST", r"^/api/tasks/create$", "create"),
]


class Handler(BaseHTTPRequestHandler):
    console = None
    server_version = "BarsaKanban/1.0"

    # -- plumbing ----------------------------------------------------------

    def log_message(self, fmt, *args):
        pass  # the run log is the interesting one; access logs are noise

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        for verb, pattern, name in ROUTES:
            if verb != method:
                continue
            m = re.match(pattern, parsed.path)
            if not m:
                continue
            try:
                getattr(self, "_h_" + name)(parsed, *m.groups())
            except ConsoleError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:  # never take the console down
                self._json(500, {"error": "%s: %s" % (type(exc).__name__, exc)})
            return
        if parsed.path.startswith("/api/"):
            self._json(404, {"error": "مسیر API پیدا نشد."})
            return
        if method == "GET":
            self._static(parsed.path)
        else:
            self._json(405, {"error": "method not allowed"})

    def _json(self, code, doc):
        body = json.dumps(doc, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except ValueError:
            raise ConsoleError("بدنهٔ درخواست JSON معتبر نیست.")

    def _static(self, path):
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.normpath(os.path.join(UI_DIR, name))
        if not full.startswith(UI_DIR) or not os.path.isfile(full):
            self._json(404, {"error": "not found"})
            return
        ctype = {".html": "text/html; charset=utf-8",
                 ".css": "text/css; charset=utf-8",
                 ".js": "application/javascript; charset=utf-8"}.get(
                     os.path.splitext(full)[1], "application/octet-stream")
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- handlers ----------------------------------------------------------

    @property
    def repo_id(self):
        return os.path.basename(self.console.repo_root)

    def _h_repos(self, parsed):
        caps = self.console.manager_json("capabilities")
        self._json(200, [{
            "id": self.repo_id,
            "path": self.console.repo_root,
            "manager": {"ok": True, "contract": caps.get("contract"),
                        "contractVersion": caps.get("contractVersion"),
                        "managerVersion": caps.get("managerVersion"),
                        "protocolVersion": caps.get("protocolVersion"),
                        "capabilities": caps.get("capabilities"),
                        "needKinds": caps.get("needKinds")},
            "run": {"maxConcurrent": self.console.runs.max_concurrent,
                    "autoStartOnCreate": self.console.auto_start,
                    "autoResumeAfterAnswer": self.console.auto_resume},
        }])

    def _h_board(self, parsed, repo):
        self._json(200, self.console.manager_json("status"))

    def _h_task(self, parsed, repo, task_id):
        doc = self.console.manager_json("status", "--task", task_id)
        tasks = doc.get("tasks") or []
        self._json(200, tasks[0] if tasks else {"error": "not found"})

    def _h_events(self, parsed, repo, task_id):
        self._json(200, self.console.manager_json("events", task_id))

    def _h_artifact(self, parsed, repo, task_id):
        path = (parse_qs(parsed.query).get("path") or [""])[0]
        if not path:
            raise ConsoleError("پارامتر path لازم است.")
        code, out, err = self.console.manager("artifact", task_id,
                                              "--path", path)
        if code != 0:
            raise ConsoleError(err.strip() or "artifact پیدا نشد.")
        body = out.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _h_running(self, parsed, repo):
        self._json(200, self.console.runs.snapshot())

    def _h_health(self, parsed, repo):
        """The status bar: the manager's own read-only check."""
        code, out, err = self.console.manager("verify", "--help")
        ok = code == 0
        caps_ok = True
        try:
            self.console.manager_json("capabilities")
        except ConsoleError:
            caps_ok = False
        self._json(200, {"ok": ok and caps_ok, "checkedAt": _now(),
                         "code": code, "output": mask(out + err)})

    def _h_run(self, parsed, repo, task_id):
        started, row = self.console.runs.enqueue(task_id)
        if not started:
            self._json(409, {"error": "این تسک از قبل در صف یا در اجراست.",
                             "running": row})
            return
        self._json(202, {"ok": True, "running": row})

    def _h_answer(self, parsed, repo, task_id):
        body = self._body()
        args = ["answer", task_id]
        text = None
        if body.get("approve"):
            args.append("--approve")
        elif body.get("reject"):
            args.append("--reject")
            text = body.get("reason")
            if not text:
                raise ConsoleError("رد کردن دلیل اجباری دارد.")
            args += ["--reason-file", self._temp(task_id, text)]
            if body.get("route"):
                args += ["--route", body["route"]]
        elif body.get("clarify") is not None:
            args.append("--clarify")
            args += ["--file", self._temp(task_id, body.get("clarify") or "")]
            if body.get("respec"):
                args.append("--respec")
        else:
            raise ConsoleError("یکی از approve/reject/clarify لازم است.")
        code, out, err = self.console.manager(*args)
        if code != 0:
            raise ConsoleError(err.strip() or out.strip())
        resumed = False
        if self.console.auto_resume:
            resumed, _ = self.console.runs.enqueue(task_id)
        self._json(200, {"ok": True, "output": out.strip(),
                         "resumed": resumed})

    def _h_side(self, parsed, repo, task_id, verb):
        body = self._body()
        reason = body.get("reason")
        if verb in ("void", "cancel", "unlock") and not reason:
            raise ConsoleError("دلیل اجباری است.")
        args = [verb, task_id, "--reason-file", self._temp(task_id, reason)]
        if verb == "unlock" and body.get("force"):
            args.append("--force")
        code, out, err = self.console.manager(*args)
        if code != 0:
            raise ConsoleError(err.strip() or out.strip())
        self._json(200, {"ok": True, "output": out.strip()})

    def _temp(self, task_id, text):
        """Free text always travels as a UTF-8 file, never as an argument.

        The reason the workflow this mirrors insists on it: a Persian string
        pasted into a console arrives as `???`, and a reason that lost its
        text is worse than no reason.
        """
        import tempfile
        fd, path = tempfile.mkstemp(prefix="barsa-kanban-%s-" % task_id,
                                    suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text or "")
        return path

    def _h_create(self, parsed):
        body = self._body()
        drafts = body.get("drafts") or [body]
        results = []
        for draft in drafts:
            payload = {k: draft[k] for k in ("requestText", "slug", "kind",
                                             "system", "type", "source")
                       if draft.get(k)}
            path = self._temp("create", json.dumps(payload, ensure_ascii=False))
            code, out, err = self.console.manager("import-issue", "--file",
                                                  path)
            if code != 0:
                results.append({"ok": False, "slug": draft.get("slug"),
                                "message": (err.strip() or out.strip())})
                continue
            created = json.loads(out)
            row = {"ok": True, "taskId": created["taskId"],
                   "slug": draft.get("slug"), "queued": False}
            if self.console.auto_start and draft.get("start", True):
                row["queued"], _ = self.console.runs.enqueue(created["taskId"])
            results.append(row)
        self._json(200, {"succeeded": sum(1 for r in results if r["ok"]),
                         "failed": sum(1 for r in results if not r["ok"]),
                         "results": results})

    def _h_stream(self, parsed, repo, task_id):
        """Server-sent events: the live run log, replayed from the buffer."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        q = self.console.runs.subscribe(task_id)
        try:
            while True:
                try:
                    line = q.get(timeout=20)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue
                payload = "data: %s\n\n" % json.dumps({"line": line},
                                                      ensure_ascii=False)
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.console.runs.unsubscribe(task_id, q)


class Server(ThreadingHTTPServer):
    # Python's HTTPServer sets SO_REUSEADDR, which on Windows lets a second
    # process bind a port another one is already serving. Two consoles on one
    # port, and the browser talks to whichever the OS picks -- exactly the
    # confusion this check exists to prevent.
    allow_reuse_address = os.name != "nt"


def port_is_taken(host, port):
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(1.0)
    try:
        return probe.connect_ex((host, port)) == 0
    finally:
        probe.close()


def who_is_there(host, port):
    """A one-line guess at what already answers on that port."""
    import urllib.error
    import urllib.request
    url = "http://%s:%d/api/repos" % (host, port)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=2) as response:
            body = response.read(400).decode("utf-8", "replace")
        if "barsa-agent-manager" in body:
            return "یک کنسول کانبان (همین برنامه) از قبل اینجاست."
        return "یک سرویس دیگر با /api/repos جواب می‌دهد: %s" % body[:120]
    except urllib.error.HTTPError as exc:
        return "چیزی اینجا هست و با HTTP %s جواب می‌دهد." % exc.code
    except Exception:
        return "چیزی روی این پورت گوش می‌دهد ولی /api/repos را نمی‌شناسد."


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4310)
    ap.add_argument("--max-concurrent", type=int, default=2)
    ap.add_argument("--no-auto-start", action="store_true")
    ap.add_argument("--no-auto-resume", action="store_true")
    args = ap.parse_args(argv)

    repo_root = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo_root, ".agent-work")):
        print("در %s هیچ .agent-work/ نیست. اول: python tools/manager.py init "
              "--system <id>" % repo_root, file=sys.stderr)
        return 2
    if port_is_taken(args.host, args.port):
        print("پورت %d از قبل گرفته شده است." % args.port, file=sys.stderr)
        print("  %s" % who_is_there(args.host, args.port), file=sys.stderr)
        print("  اگر BarsaAgent روی همین پورت بالاست (پیش‌فرض خودش هم 4310 "
              "است)، این کنسول را روی پورت دیگری بیاور:", file=sys.stderr)
        print("  python tools/kanban_server.py --port %d" % (args.port + 1),
              file=sys.stderr)
        return 2

    runs = RunQueue(repo_root, args.max_concurrent)
    Handler.console = Console(repo_root, runs,
                              auto_start=not args.no_auto_start,
                              auto_resume=not args.no_auto_resume)
    try:
        server = Server((args.host, args.port), Handler)
    except OSError as exc:
        print("نمی‌توان روی %s:%d گوش داد: %s"
              % (args.host, args.port, exc), file=sys.stderr)
        return 2
    print("کنسول کانبان: http://%s:%d/" % (args.host, args.port))
    print("مخزن: %s" % repo_root)
    print("manager: %s" % MANAGER)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nبسته شد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
