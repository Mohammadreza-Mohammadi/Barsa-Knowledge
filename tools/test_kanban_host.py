#!/usr/bin/env python3
"""Tests for the Barsa.Ai.Host path. Run: python3 tools/test_kanban_host.py

These run against a stub host that implements the contract recovered from
`Barsa.Ai.Host.exe`: the same routes, the same `X-Barsa-Ai-Key` header, the
same response keys. That makes the client and the manager wiring testable
without a Barsa installation -- and it is also the limit of what these tests
prove. They cannot prove the reconstruction matches the real server; they
prove the client behaves correctly against the contract as read from the
binary.

What they do pin down is the part that matters most: every way the host can
say no leaves the task open, with the host's own words written down.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_kanban import barsa_host
from barsa_kanban.manager import Manager, ManagerError

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = "test-key"


class StubHost(BaseHTTPRequestHandler):
    """Barsa.Ai.Host as its own IL describes it. Behaviour is scripted."""

    script = {}

    def log_message(self, *a):
        pass

    def _send(self, code, doc):
        body = json.dumps(doc, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        if self.headers.get(barsa_host.API_KEY_HEADER) != API_KEY:
            self._send(401, {"status": "unauthorized",
                             "error": "Invalid or missing X-Barsa-Ai-Key."})
            return False
        return True

    def do_GET(self):
        if not self._auth():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"status": "ready", "processId": 4242,
                             "runtimeFingerprint": "stub-fingerprint",
                             "database": {"server": "SQL01",
                                          "name": "BarsaTest"}})
        elif parsed.path == "/systems":
            self._send(200, {"status": "succeeded", "count": 1, "systems": [
                {"id": "1011413550000000100", "caption": "بارکد",
                 "name": "Barcode", "isInactive": False}]})
        elif parsed.path == "/apply-status":
            plan_id = (parse_qs(parsed.query).get("planId") or [""])[0]
            states = self.script.get("states") or ["applied"]
            calls = self.script.setdefault("statusCalls", 0)
            state = states[min(calls, len(states) - 1)]
            self.script["statusCalls"] = calls + 1
            self._send(200, {"status": "succeeded", "planId": plan_id,
                             "state": state, "source": "persistedResult",
                             "result": {"commands": 1},
                             "error": self.script.get("statusError")})
        else:
            self._send(404, {"error": "no route"})

    def do_POST(self):
        if not self._auth():
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        route = urlparse(self.path).path
        if route == "/lint":
            self._send(200, {"status": "succeeded",
                             "profileVersion": body.get("profileVersion")})
        elif route == "/plan":
            self.script["lastBatch"] = body
            self._send(200, dict({
                "planId": "plan-001", "isValid": True,
                "canApplyCleanly": True, "canApplyAny": True,
                "canApplyAll": True, "hasBatchFatalError": False,
                "hasCommandLocalErrors": False,
                "commandCount": len(body.get("changes") or ()),
                "errorCount": 0, "summary": "Plan: ok",
                "diagnostics": {"count": 0, "items": []},
            }, **(self.script.get("plan") or {})))
        elif route == "/apply":
            self.script["appliedPlanId"] = body.get("planId")
            self._send(200, dict({"status": "succeeded",
                                  "planId": body.get("planId"),
                                  "results": [{"commandId": "c1",
                                               "status": "succeeded"}],
                                  "runtimeFingerprint": "stub-fingerprint"},
                                 **(self.script.get("apply") or {})))
        else:
            self._send(404, {"error": "no route"})


class HostHarness(unittest.TestCase):
    def setUp(self):
        StubHost.script = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), StubHost)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.prefix = "http://127.0.0.1:%d/" % self.port
        self.client = barsa_host.HostClient(self.prefix, API_KEY, timeout=10)

    def stop_host(self):
        """Really stop it.

        `shutdown()` only ends the serve_forever loop; the listening socket
        stays open, so a client still connects and then waits for a reply
        that never comes. Closing the socket is what makes the host look
        down, which is the case the test is about.
        """
        self.server.shutdown()
        self.server.server_close()

    def tearDown(self):
        self.stop_host()


class Client(HostHarness):
    BATCH = {"profileVersion": 15, "changes": [{"commandId": "c1"}]}

    def test_health_reaches_the_host(self):
        self.assertEqual(self.client.health()["status"], "ready")

    def test_a_wrong_key_is_a_clear_refusal(self):
        bad = barsa_host.HostClient(self.prefix, "nope", timeout=10)
        with self.assertRaises(barsa_host.HostError) as cm:
            bad.health()
        self.assertEqual(cm.exception.status, 401)
        self.assertIn("apiKeyEnv", str(cm.exception))

    def test_an_unreachable_host_names_the_prefix(self):
        dead = barsa_host.HostClient("http://127.0.0.1:1/", API_KEY, timeout=2)
        with self.assertRaises(barsa_host.HostError) as cm:
            dead.health()
        self.assertIn("127.0.0.1:1", str(cm.exception))

    def test_plan_and_apply_walks_the_whole_sequence(self):
        out = self.client.plan_and_apply(self.BATCH)
        self.assertTrue(out["applied"])
        self.assertEqual(out["plan"]["planId"], "plan-001")
        self.assertEqual(StubHost.script["appliedPlanId"], "plan-001")
        self.assertEqual(StubHost.script["lastBatch"], self.BATCH)

    def test_an_invalid_plan_is_never_applied(self):
        StubHost.script["plan"] = {"isValid": False, "errorCount": 2,
                                   "diagnostics": {"items": ["bad selector"]}}
        with self.assertRaises(barsa_host.HostError):
            self.client.plan_and_apply(self.BATCH)
        self.assertNotIn("appliedPlanId", StubHost.script)

    def test_a_plan_that_cannot_apply_cleanly_is_refused_by_default(self):
        StubHost.script["plan"] = {"canApplyCleanly": False,
                                   "canApplyAny": True, "canApplyAll": False}
        with self.assertRaises(barsa_host.HostError) as cm:
            self.client.plan_and_apply(self.BATCH)
        self.assertIn("cleanly", str(cm.exception))
        self.assertNotIn("appliedPlanId", StubHost.script)

    def test_a_partial_apply_can_be_opted_into(self):
        StubHost.script["plan"] = {"canApplyCleanly": False,
                                   "canApplyAny": True}
        out = self.client.plan_and_apply(self.BATCH, require_clean=False)
        self.assertTrue(out["applied"])

    def test_a_rejected_apply_raises(self):
        StubHost.script["apply"] = {"status": "rejected",
                                    "error": "plan expired"}
        with self.assertRaises(barsa_host.HostError):
            self.client.plan_and_apply(self.BATCH)

    def test_a_failed_state_is_not_success(self):
        StubHost.script["states"] = ["running", "failed"]
        with self.assertRaises(barsa_host.HostError) as cm:
            self.client.plan_and_apply(self.BATCH, poll_seconds=0.01)
        self.assertIn("failed", str(cm.exception))

    def test_it_waits_for_a_terminal_state(self):
        StubHost.script["states"] = ["running", "running", "applied"]
        out = self.client.plan_and_apply(self.BATCH, poll_seconds=0.01)
        self.assertEqual(out["status"]["state"], "applied")

    def test_a_host_that_never_finishes_is_an_error_not_a_hang(self):
        StubHost.script["states"] = ["running"]
        with self.assertRaises(barsa_host.HostError) as cm:
            self.client.plan_and_apply(self.BATCH, poll_seconds=0.01,
                                       max_wait=0.05)
        self.assertIn("terminal state", str(cm.exception))


class ThroughTheManager(HostHarness):
    """The gate itself: approve means apply, and a refusal closes nothing."""

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="kanban-host-")
        for name in ("dist", "dist-report", "tools"):
            os.symlink(os.path.join(REPO, name), os.path.join(self.root, name))
        self.m = Manager(self.root)
        self.m.init("1011413550000000100")
        self._configure_host()
        os.environ["BARSA_AI_HOST_KEY"] = API_KEY
        self._task_to_the_gate()

    def tearDown(self):
        try:
            super().tearDown()
        except OSError:
            pass  # the test may have stopped the host already
        shutil.rmtree(self.root, ignore_errors=True)
        os.environ.pop("BARSA_AI_HOST_KEY", None)

    def _configure_host(self):
        path = os.path.join(self.root, ".agent-work", "config",
                            "repository.yaml")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace("  appliedBy: human", "  appliedBy: barsa-host")
        text = text.replace('    prefix: "http://127.0.0.1:17840/"',
                            '    prefix: "%s"' % self.prefix)
        # A test must never be able to wait three minutes on a socket.
        text = text.replace("    timeoutSeconds: 180", "    timeoutSeconds: 5")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def task_dir(self):
        return self.m.store.task_dir_or_fail("0001")

    def write(self, rel, text):
        path = os.path.join(self.task_dir(), rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def state(self):
        return self.m.store.read_manifest(self.task_dir())["state"]

    def _task_to_the_gate(self):
        quiet = lambda _m: None
        self.m.create_task({"slug": "میزبان", "kind": "report.create",
                            "requestText": "یک گزارش لیستی."})
        self.m.run("0001", quiet)
        self.write("proposed-task.md", "# t\n\n- AC-1 ساخته می‌شود.\n")
        self.write("release-note.md",
                   '---\nuserVisible: true\nheadline: "x"\n---\n\nمتن.\n')
        self.write("attempts/001/result.yaml",
                   "role: intake\noutcome: completed\n"
                   "requestedTransition: architecture\n")
        self.m.run("0001", quiet)
        self.m.answer("0001", approve=True, log=quiet)
        self.m.run("0001", quiet)
        self.write("plan.md", "p")
        self.write("tests.md", "- T-1")
        self.write("handoff.md", "h")
        self.write("attempts/002/result.yaml",
                   "role: architect\noutcome: completed\n"
                   "requestedTransition: ready\nproposal:\n"
                   '  system: "1011413550000000100"\n  scope:\n'
                   '    allow: ["entity:#BarcodeReader", "report:#میزبان"]\n'
                   "    deny: []\n")
        self.m.run("0001", quiet)
        self.write("change-batch.json", json.dumps({
            "profileVersion": 15,
            "policy": {"errorPolicy": "continueIndependent",
                       "ignoreUnsupported": False},
            "changes": [{"commandId": "c1", "operation": "create",
                         "objectType": "report",
                         "parent": {"objectType": "entity",
                                    "selector": "#BarcodeReader"},
                         "properties": {"name": "میزبان",
                                        "reportType": "list",
                                        "condition": {"all": []}}}]},
            ensure_ascii=False))
        self.write("implementation-report.md", "r")
        self.write("attempts/003/result.yaml",
                   "role: implementer\noutcome: completed\n"
                   "requestedTransition: review\n")
        self.m.run("0001", quiet)
        self.write("review.md", "ok")
        self.write("attempts/004/result.yaml",
                   "role: reviewer\noutcome: completed\n"
                   "requestedTransition: approved\ndecision: approved\n"
                   "evidence:\n  acceptance: [{ac: \"AC-1\", verdict: pass, "
                   "basis: \"properties.name\"}]\n")
        self.m.run("0001", quiet)
        self.assertEqual(self.state(), "integrating")

    def test_preflight_reads_everything_and_applies_nothing(self):
        """The command someone runs before trusting this path at all."""
        import subprocess
        out = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "manager.py"),
             "--repo", self.root, "host", "--preflight", "0001"],
            capture_output=True, text=True, env=dict(os.environ))
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("هیچ چیزی اعمال نشد", out.stdout)
        self.assertIn("plan-001", out.stdout)
        # read-only means read-only: the host was planned against, not applied
        self.assertNotIn("appliedPlanId", StubHost.script)
        self.assertEqual(self.state(), "integrating")

    def test_approve_sends_the_batch_and_closes_on_the_host_verdict(self):
        self.m.answer("0001", approve=True, log=lambda _m: None)
        self.assertEqual(self.state(), "integrated")
        manifest = self.m.store.read_manifest(self.task_dir())
        batch = manifest["batch"]
        self.assertEqual(batch["appliedBy"], "barsa-host")
        self.assertEqual(batch["planId"], "plan-001")
        self.assertEqual(batch["hostState"], "applied")
        self.assertEqual(batch["runtimeFingerprint"], "stub-fingerprint")
        # the host saw the real batch, not a summary of it
        sent = StubHost.script["lastBatch"]
        self.assertEqual(sent["changes"][0]["properties"]["name"], "میزبان")
        result = json.load(open(os.path.join(self.task_dir(),
                                             "apply-result.json"),
                                encoding="utf-8"))
        self.assertTrue(result["applied"])

    def test_a_host_refusal_leaves_the_task_open(self):
        StubHost.script["plan"] = {"isValid": False, "errorCount": 1,
                                   "diagnostics": {"items": ["nope"]}}
        with self.assertRaises(ManagerError):
            self.m.answer("0001", approve=True, log=lambda _m: None)
        self.assertEqual(self.state(), "integrating")
        manifest = self.m.store.read_manifest(self.task_dir())
        self.assertEqual(manifest["awaitingHuman"]["kind"], "apply-approval")
        self.assertTrue(os.path.isfile(
            os.path.join(self.task_dir(), "apply-failure.md")))
        # and the next implementer attempt is handed the host's own words
        with open(os.path.join(self.task_dir(),
                               ".last-rejection-implementer.md"),
                  encoding="utf-8") as fh:
            self.assertIn("host", fh.read().lower())

    def test_an_unreachable_host_does_not_close_the_task(self):
        self.stop_host()
        with self.assertRaises(ManagerError) as cm:
            self.m.answer("0001", approve=True, log=lambda _m: None)
        self.assertIn("host", str(cm.exception).lower())
        self.assertEqual(self.state(), "integrating")

    def test_a_tampered_batch_is_refused_before_the_host_is_called(self):
        path = os.path.join(self.task_dir(), "change-batch.json")
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["changes"][0]["properties"]["name"] = "چیز دیگری"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False)
        with self.assertRaises(ManagerError):
            self.m.answer("0001", approve=True, log=lambda _m: None)
        self.assertNotIn("lastBatch", StubHost.script)
        self.assertEqual(self.state(), "integrating")


if __name__ == "__main__":
    unittest.main(verbosity=2)
