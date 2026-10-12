#!/usr/bin/env python3
"""Tests for the agent protocol. Run: python3 tools/test_kanban.py

They cover the parts where a silent mistake would be expensive: the YAML
subset the store round-trips through, the state machine's shape, each
verification gate's negative case, and one full walk from a raw request to an
integrated task including both human gates.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_kanban import config as config_mod
from barsa_kanban import connection as connection_mod
from barsa_kanban import states, systems as systems_mod, verify, yamlite
from barsa_kanban.manager import Manager, ManagerError
from barsa_kanban.store import Store, StoreError

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Yamlite(unittest.TestCase):
    def test_round_trip(self):
        doc = {"a": 1, "b": "two", "c": None, "d": True, "e": [1, "x"],
               "f": {"g": -2.5, "h": []}}
        self.assertEqual(yamlite.loads(yamlite.dumps(doc)), doc)

    def test_flow_mapping_rows(self):
        text = 'rows: [{ac: "AC-1", verdict: pass}, {ac: "AC-2", verdict: fail}]'
        self.assertEqual(yamlite.loads(text)["rows"][1],
                         {"ac": "AC-2", "verdict": "fail"})

    def test_comma_inside_quotes_is_not_a_separator(self):
        doc = yamlite.loads('rows: [{basis: "a, b", ac: "AC-1"}]')
        self.assertEqual(doc["rows"][0]["basis"], "a, b")

    def test_hash_inside_a_quoted_string_survives(self):
        self.assertEqual(yamlite.loads('s: "#Value"')["s"], "#Value")

    def test_a_selector_round_trips(self):
        doc = {"scope": {"allow": ["report:#نمای 1", "entity:#BarcodeReader"]}}
        self.assertEqual(yamlite.loads(yamlite.dumps(doc)), doc)

    def test_tabs_are_refused(self):
        with self.assertRaises(yamlite.YamlError):
            yamlite.loads("a:\n\tb: 1\n")

    def test_unbalanced_inline_is_refused(self):
        with self.assertRaises(yamlite.YamlError):
            yamlite.loads('a: [{b: "x]')


class StateMachine(unittest.TestCase):
    def test_every_edge_targets_a_known_state(self):
        known = set(states.TASK_TRANSITIONS) | states.TERMINAL_STATES
        for source, targets in states.TASK_TRANSITIONS.items():
            for target in targets:
                self.assertIn(target, known, "%s → %s" % (source, target))

    def test_terminal_states_have_no_exit(self):
        for state in states.TERMINAL_STATES:
            self.assertNotIn(state, states.TASK_TRANSITIONS)

    def test_every_state_sits_in_a_lane_or_is_terminal(self):
        laned = {s for lane in states.LANES for s in lane["states"]}
        for state in states.TASK_TRANSITIONS:
            if state in ("blocked", "cancelled", "abandoned"):
                continue
            self.assertIn(state, laned, state)

    def test_the_lanes_are_the_six_stages_plus_done(self):
        self.assertEqual([lane["title"] for lane in states.LANES],
                         ["ورودی", "طراحی", "آماده", "پیاده‌سازی", "بازبینی",
                          "آماده اعمال", "تمام"])


class Gates(unittest.TestCase):
    """Each gate's negative case. A gate that cannot fail is not a gate."""

    @classmethod
    def setUpClass(cls):
        cls.contract = verify.load_contract(REPO)
        cls.index = verify.load_selector_index(REPO, "1011413550000000100")
        if cls.contract is None or cls.index is None:
            raise unittest.SkipTest("dist/ or dist-report/ is not built")
        cls.scope = {"allow": ["entity:#BarcodeReader", "report:#X"],
                     "deny": []}

    def batch(self, **properties):
        props = {"name": "X", "reportType": "list"}
        props.update(properties)
        return {"profileVersion": 15,
                "policy": {"errorPolicy": "continueIndependent",
                           "ignoreUnsupported": False},
                "changes": [{"commandId": "c1", "operation": "create",
                             "objectType": "report",
                             "parent": {"objectType": "entity",
                                        "selector": "#BarcodeReader"},
                             "properties": props}]}

    def gates_of(self, findings):
        return {f["gate"] for f in findings}

    def test_a_clean_batch_passes_every_gate(self):
        findings, summary = verify.run(self.batch(), self.contract, self.scope,
                                       self.index)
        self.assertEqual(findings, [])
        self.assertTrue(summary["passed"])

    def test_lint_rejects_a_wrong_profile_version(self):
        batch = self.batch()
        batch["profileVersion"] = 14
        self.assertIn("lint", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))

    def test_selectors_rejects_a_name_not_in_the_index(self):
        batch = self.batch()
        batch["changes"][0]["parent"]["selector"] = "#NotThere"
        self.assertIn("selectors", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))

    def test_selectors_rejects_an_unreplaced_placeholder(self):
        batch = self.batch()
        batch["changes"][0]["parent"]["selector"] = "#<entity>"
        self.assertIn("selectors", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))

    def test_unknowns_rejects_a_populated_condition(self):
        batch = self.batch(condition={"all": [{"field": "#Value",
                                               "operator": "Equals"}]})
        self.assertIn("unknowns", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))

    def test_unknowns_accepts_an_empty_condition(self):
        findings, _ = verify.run(self.batch(condition={"all": []}),
                                 self.contract, self.scope, self.index)
        self.assertEqual(findings, [])

    def test_unknowns_rejects_authored_parameters(self):
        batch = self.batch(parameters=[{"name": "p"}])
        self.assertIn("unknowns", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))

    def test_scope_rejects_an_object_the_task_does_not_hold(self):
        findings, _ = verify.run(self.batch(), self.contract,
                                 {"allow": ["report:#Other"], "deny": []},
                                 self.index)
        self.assertIn("scope", self.gates_of(findings))

    def test_order_rejects_a_child_before_its_parent(self):
        batch = self.batch()
        batch["changes"].insert(0, {
            "commandId": "c0", "operation": "create", "objectType": "folder",
            "parent": {"objectType": "folder", "tempId": "later"},
            "properties": {"name": "F"}})
        self.assertIn("order", self.gates_of(
            verify.run(batch, self.contract,
                       {"allow": ["folder:*", "entity:#BarcodeReader",
                                  "report:#X"], "deny": []},
                       self.index)[0]))

    def test_a_tempId_reference_with_no_creator_is_rejected(self):
        batch = self.batch()
        batch["changes"][0]["parent"] = {"objectType": "entity",
                                         "tempId": "ghost"}
        self.assertIn("selectors", self.gates_of(
            verify.run(batch, self.contract, self.scope, self.index)[0]))


class WindowsStdio(unittest.TestCase):
    """The CLI's JSON must survive a pipe whose encoding is not UTF-8.

    A Windows console reported this as "خواندن برد ناموفق": Python there
    gives a piped stdout the ANSI code page, so the first Persian slug in
    `status --json` raised UnicodeEncodeError and the board never loaded.
    The reproduction is one environment variable.
    """

    def run_cli(self, *args, encoding="cp1252"):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = encoding
        return subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "manager.py"),
             "--repo", REPO] + list(args),
            capture_output=True, env=env)

    def test_status_json_survives_a_cp1252_pipe(self):
        out = self.run_cli("status")
        self.assertEqual(out.returncode, 0,
                         out.stderr.decode("utf-8", "replace")[-600:])
        doc = json.loads(out.stdout.decode("utf-8"))
        self.assertTrue(any("ورودی" == lane["title"] for lane in doc["lanes"]))

    def test_a_persian_slug_round_trips_through_the_pipe(self):
        out = self.run_cli("status")
        slugs = [t.get("slug") for t in json.loads(
            out.stdout.decode("utf-8"))["tasks"]]
        self.assertTrue(any(s and any("\u0600" <= ch <= "\u06FF" for ch in s)
                            for s in slugs),
                        "no Persian slug in the fixture board: %s" % slugs)

    def test_capabilities_too(self):
        out = self.run_cli("capabilities")
        self.assertEqual(out.returncode, 0)
        self.assertEqual(json.loads(out.stdout.decode("utf-8"))["contract"],
                         "barsa-agent-manager")


class SystemCatalogue(unittest.TestCase):
    def setUp(self):
        self.rows = systems_mod.catalogue(REPO)
        if not self.rows:
            raise unittest.SkipTest("dist/index/systems is not built")

    def test_every_system_in_the_pack_is_listed(self):
        ids = {row["id"] for row in self.rows}
        with open(os.path.join(REPO, "dist", "index", "systems",
                               "manifest.json"), encoding="utf-8") as fh:
            self.assertEqual(ids, set(json.load(fh)["systemIds"]))

    def test_a_system_without_a_selector_pack_says_why(self):
        for row in self.rows:
            if not row["authorable"]:
                self.assertIn("report_compiler", row["notAuthorableBecause"])
                break
        else:
            self.skipTest("every system has a pack here")

    def test_authorable_systems_come_first(self):
        flags = [row["authorable"] for row in self.rows]
        self.assertEqual(flags, sorted(flags, reverse=True))

    def test_a_caption_resolves_whichever_yeh_was_typed(self):
        row, _ = systems_mod.find(REPO, "بارکد")     # Farsi yeh/kaf
        other, _ = systems_mod.find(REPO, "باركد")   # Arabic yeh/kaf
        self.assertIsNotNone(row)
        self.assertEqual(row["id"], other["id"])

    def test_an_id_resolves_to_itself(self):
        row, _ = systems_mod.find(REPO, "1011413550000000100")
        self.assertEqual(row["id"], "1011413550000000100")

    def test_an_ambiguous_name_resolves_to_nothing_and_offers_candidates(self):
        row, candidates = systems_mod.find(REPO, "Meta")
        self.assertIsNone(row)
        self.assertGreater(len(candidates), 1)


class DatabaseGuard(unittest.TestCase):
    """connection.yaml names the database; the host says what it really is."""

    def check(self, expected, actual):
        return connection_mod.check_database(
            {"database": expected}, {"database": actual})

    def test_a_different_database_is_refused(self):
        ok, message = self.check({"server": "SQL01", "name": "BarsaTest"},
                                 {"server": "SQL01", "name": "BarsaProd"})
        self.assertFalse(ok)
        self.assertIn("BarsaProd", message)

    def test_the_same_database_passes(self):
        ok, _ = self.check({"server": "SQL01", "name": "BarsaTest"},
                           {"server": "sql01", "name": "barsatest"})
        self.assertTrue(ok)

    def test_a_host_that_does_not_say_is_not_a_match(self):
        ok, message = self.check({"name": "BarsaTest"}, {})
        self.assertFalse(ok)
        self.assertIn("host چیزی نگفت", message)

    def test_an_empty_expectation_compares_nothing_and_says_so(self):
        ok, message = self.check({"server": "", "name": ""},
                                 {"server": "X", "name": "Y"})
        self.assertTrue(ok)
        self.assertIn("خالی", message)

    def test_it_can_be_turned_off_explicitly(self):
        ok, message = self.check(
            {"server": "A", "name": "B", "enforce": False},
            {"server": "C", "name": "D"})
        self.assertTrue(ok)
        self.assertIn("خاموش", message)

    def test_a_committed_key_is_refused(self):
        root = tempfile.mkdtemp(prefix="kanban-conn-")
        try:
            store = Store(root)
            store.ensure()
            with open(os.path.join(store.config_dir, "connection.yaml"), "w",
                      encoding="utf-8") as fh:
                fh.write('schemaVersion: 1\nhost:\n  apiKey: "secret"\n')
            with self.assertRaises(StoreError) as cm:
                connection_mod.load(store)
            self.assertIn("apiKeyEnv", str(cm.exception))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class StoreRules(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="kanban-store-")
        self.store = Store(self.root)
        self.store.ensure()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_artifact_paths_cannot_escape_the_task(self):
        task_dir = self.store.create_task_dir("0001", "x")
        for bad in ("../../etc/passwd", "/etc/passwd", "a/../../b"):
            with self.assertRaises(StoreError):
                self.store.resolve_in_task(task_dir, bad)

    def test_a_slug_with_a_separator_is_refused(self):
        with self.assertRaises(StoreError):
            self.store.create_task_dir("0002", "a/b")

    def test_scope_conflict_sees_a_live_task_only(self):
        task_dir = self.store.create_task_dir("0001", "x")
        self.store.write_manifest(task_dir, {
            "schemaVersion": 1, "id": "0001", "state": "implementing",
            "scope": {"allow": ["report:#A"], "deny": []}})
        self.assertIsNotNone(self.store.scope_conflict("0002", ["report:#A"]))
        self.store.write_manifest(task_dir, {
            "schemaVersion": 1, "id": "0001", "state": "integrated",
            "scope": {"allow": ["report:#A"], "deny": []}})
        self.assertIsNone(self.store.scope_conflict("0002", ["report:#A"]))


class FullWalk(unittest.TestCase):
    """One task from a raw request to integrated, through both gates."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="kanban-walk-")
        # The knowledge pack is read, never written, so it is linked in.
        for name in ("dist", "dist-report", "tools"):
            os.symlink(os.path.join(REPO, name),
                       os.path.join(self.root, name))
        self.m = Manager(self.root)
        self.m.init("1011413550000000100")
        self.log = []

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def say(self, line):
        self.log.append(line)

    def task_dir(self, task_id="0001"):
        return self.m.store.task_dir_or_fail(task_id)

    def write(self, rel, text):
        path = os.path.join(self.task_dir(), rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def state(self):
        return self.m.store.read_manifest(self.task_dir())["state"]

    def test_walk(self):
        self.m.create_task({"slug": "گزارش-تست", "kind": "report.create",
                            "requestText": "یک گزارش لیستی روی BarcodeReader."})
        self.assertEqual(self.state(), "new")

        # intake
        self.assertEqual(self.m.run("0001", self.say), states.EXIT_AWAITING_HUMAN)
        self.write("proposed-task.md", "# t\n\n- AC-1 یک گزارش ساخته می‌شود.\n")
        self.write("release-note.md",
                   '---\nuserVisible: true\nheadline: "گزارش تازه"\n---\n\nمتن.\n')
        self.write("attempts/001/result.yaml",
                   "role: intake\noutcome: completed\n"
                   "requestedTransition: architecture\n")
        self.assertEqual(self.m.run("0001", self.say), states.EXIT_AWAITING_HUMAN)
        manifest = self.m.store.read_manifest(self.task_dir())
        self.assertEqual(manifest["awaitingHuman"]["kind"], "spec-approval")

        # the spec gate stamps task.md -- and only the manager may write it
        self.m.answer("0001", approve=True, log=self.say)
        self.assertTrue(os.path.isfile(os.path.join(self.task_dir(), "task.md")))
        self.assertEqual(self.state(), "architecture")

        # architect
        self.m.run("0001", self.say)
        self.write("plan.md", "plan")
        self.write("tests.md", "- T-1")
        self.write("handoff.md", "handoff")
        self.write("attempts/002/result.yaml",
                   "role: architect\noutcome: completed\n"
                   "requestedTransition: ready\nproposal:\n"
                   '  system: "1011413550000000100"\n  scope:\n'
                   '    allow: ["entity:#BarcodeReader", "report:#گزارش تست"]\n'
                   "    deny: []\n")
        self.m.run("0001", self.say)
        self.assertEqual(self.state(), "implementing")

        # implementer, first attempt: a batch that breaks the unknowns gate
        self.write("change-batch.json", json.dumps({
            "profileVersion": 15,
            "policy": {"errorPolicy": "continueIndependent",
                       "ignoreUnsupported": False},
            "changes": [{"commandId": "c1", "operation": "create",
                         "objectType": "report",
                         "parent": {"objectType": "entity",
                                    "selector": "#BarcodeReader"},
                         "properties": {"name": "گزارش تست",
                                        "reportType": "list",
                                        "parameters": [{"name": "p"}]}}]},
            ensure_ascii=False))
        self.write("implementation-report.md", "report")
        self.write("attempts/003/result.yaml",
                   "role: implementer\noutcome: completed\n"
                   "requestedTransition: review\n")
        self.m.run("0001", self.say)
        # The role claimed completed; the manager's own gates disagreed, so
        # the task did not advance.
        self.assertEqual(self.state(), "implementing")
        rejection = os.path.join(self.task_dir(), ".last-rejection-implementer.md")
        self.assertTrue(os.path.isfile(rejection))
        with open(rejection, encoding="utf-8") as fh:
            self.assertIn("unknowns", fh.read())

        # second attempt: the same batch without the Unknown property
        self.write("change-batch.json", json.dumps({
            "profileVersion": 15,
            "policy": {"errorPolicy": "continueIndependent",
                       "ignoreUnsupported": False},
            "changes": [{"commandId": "c1", "operation": "create",
                         "objectType": "report",
                         "parent": {"objectType": "entity",
                                    "selector": "#BarcodeReader"},
                         "properties": {"name": "گزارش تست",
                                        "reportType": "list",
                                        "condition": {"all": []}}}]},
            ensure_ascii=False))
        self.m.run("0001", self.say)          # opens attempt 004
        self.write("attempts/004/result.yaml",
                   "role: implementer\noutcome: completed\n"
                   "requestedTransition: review\n")
        self.m.run("0001", self.say)
        self.assertEqual(self.state(), "review")
        # the previous rejection reached the new attempt
        self.assertTrue(os.path.isfile(
            os.path.join(self.task_dir(), "attempts", "004",
                         "previous-rejection.md")))

        # reviewer: an evidence table missing an AC is refused
        self.write("review.md", "review")
        self.write("attempts/005/result.yaml",
                   "role: reviewer\noutcome: completed\n"
                   "requestedTransition: approved\ndecision: approved\n"
                   "evidence:\n  acceptance: [{ac: \"AC-9\", verdict: pass, "
                   "basis: \"x\"}]\n")
        self.m.run("0001", self.say)
        self.assertEqual(self.state(), "review")

        self.m.run("0001", self.say)          # opens attempt 006
        self.write("attempts/006/result.yaml",
                   "role: reviewer\noutcome: completed\n"
                   "requestedTransition: approved\ndecision: approved\n"
                   "evidence:\n  acceptance: [{ac: \"AC-1\", verdict: pass, "
                   "basis: \"changes[0].properties.name\"}]\n")
        self.m.run("0001", self.say)
        manifest = self.m.store.read_manifest(self.task_dir())
        self.assertEqual(manifest["state"], "integrating")
        self.assertEqual(manifest["awaitingHuman"]["kind"], "apply-approval")

        # the last gate proves the batch has not moved since it opened
        with open(os.path.join(self.task_dir(), "change-batch.json"),
                  encoding="utf-8") as fh:
            keep = fh.read()
        self.write("change-batch.json", keep.replace('"list"', '"form"'))
        with self.assertRaises(ManagerError):
            self.m.answer("0001", approve=True, log=self.say)
        self.write("change-batch.json", keep)
        self.m.answer("0001", approve=True, log=self.say)
        self.assertEqual(self.state(), "integrated")

        # and the scope lock is released only now
        self.assertIsNone(self.m.store.scope_conflict(
            "0002", ["entity:#BarcodeReader"]))

    def test_budget_exhaustion_blocks_rather_than_looping(self):
        self.m.create_task({"slug": "بودجه", "kind": "report.create",
                            "requestText": "x"})
        limits = config_mod.budget_limits(self.m.config)
        for _ in range(limits["intakeRuns"] + 1):
            manifest = self.m.store.read_manifest(self.task_dir())
            if manifest["state"] == "blocked":
                break
            # Each run opens an attempt the role never answers; clearing the
            # gate and the attempt marker makes the next run spend budget
            # again, which is what exhaustion needs to be reachable at all.
            self.m.run("0001", self.say)
            manifest = self.m.store.read_manifest(self.task_dir())
            self.m._set(self.task_dir(), manifest, awaitingHuman=None)
            for name in self.m.store.attempts(self.task_dir()):
                meta = os.path.join(self.task_dir(), "attempts", name,
                                    "attempt.json")
                if os.path.isfile(meta):
                    os.remove(meta)
        self.assertEqual(self.m.store.read_manifest(self.task_dir())["state"],
                         "blocked")
        self.assertEqual(
            self.m.store.read_manifest(self.task_dir())["blocker"]["kind"],
            "budget-exhausted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
