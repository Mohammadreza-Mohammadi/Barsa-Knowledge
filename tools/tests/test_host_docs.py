#!/usr/bin/env python3
"""The Host documents say what the pack claims they say.

A vocabulary extracted from prose is only trustworthy while the prose has
not moved. These tests re-read the documents in source/ and check both the
values and the one trap in them.
"""

import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))

from barsa_extractor import host_docs


class HostDocuments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = os.path.join(REPO, "source")
        if not host_docs.available(cls.source):
            raise unittest.SkipTest("no Host startup payload under source/")
        cls.vocab = host_docs.build(cls.source)

    def values(self, name):
        row = self.vocab.get(name) or {}
        return row.get("values") or []

    def test_the_operator_list_is_the_list_and_not_the_prose(self):
        values = self.values("comparisonOperators")
        self.assertIn("equal", values)
        self.assertIn("advancedTextSearch2", values)
        # The document names this one as a typo that does NOT enter the
        # contract. Reading to the end of the section would swallow it.
        self.assertNotIn("DoseNotContain", values)

    def test_every_operator_looks_like_one(self):
        for value in self.values("comparisonOperators"):
            self.assertRegex(value, r"^[a-z][A-Za-z0-9]*$", value)

    def test_null_behaviors(self):
        self.assertEqual(sorted(self.values("nullBehaviors")),
                         ["checkNullValue", "dontIgnore", "ignoreCondition"])

    def test_folder_kinds(self):
        self.assertEqual(sorted(self.values("folderKinds")),
                         ["group", "page", "report"])

    def test_apply_states_match_what_the_client_expects(self):
        from barsa_kanban import barsa_host
        states = self.values("applyStates")
        self.assertEqual(sorted(states),
                         ["applied", "applying", "faulted", "ready",
                          "unknown"])
        known = set(barsa_host.NON_TERMINAL_STATES) \
            | set(barsa_host.SUCCESS_STATES) \
            | set(barsa_host.FAILURE_STATES) \
            | set(barsa_host.UNPROVABLE_STATES)
        self.assertEqual(set(states), known,
                         "the client and the Host reference disagree")

    def test_every_vocabulary_carries_its_source(self):
        for name, row in self.vocab.items():
            if isinstance(row, dict) and "values" in row:
                self.assertTrue(row.get("document"), name)
                self.assertTrue(row.get("sha256"), name)

    def test_the_navigation_chain_is_the_canonical_one(self):
        self.assertEqual(
            self.values("navigationChain"),
            [{"kind": "page", "parent": "system"},
             {"kind": "group", "parent": "page"},
             {"kind": "report", "parent": "group"}])

    def test_a_same_batch_reference_needs_its_object_type(self):
        """The document writes the encoding out; a bare tempId is not it."""
        self.assertEqual(sorted(self.values("tempIdReferenceEncoding")),
                         ["objectType", "tempId"])

    def test_the_gate_rejects_a_bare_temp_id(self):
        from barsa_kanban import verify
        vocab = {"tempIdReferenceEncoding":
                 {"values": ["objectType", "tempId"]}}
        bare = {"changes": [{"objectType": "folder",
                             "properties": {"report": {"tempId": "x"}}}]}
        full = {"changes": [{"objectType": "folder",
                             "properties": {"report": {
                                 "objectType": "report", "tempId": "x"}}}]}
        self.assertEqual(len(verify.gate_unknowns(bare, vocab)), 1)
        self.assertEqual(verify.gate_unknowns(full, vocab), [])
        # Without the evidence the gate stays silent rather than guessing.
        self.assertEqual(verify.gate_unknowns(bare, {}), [])

    def test_a_missing_payload_yields_nothing_rather_than_a_guess(self):
        self.assertIsNone(host_docs.build(os.path.join(REPO, "tools")))

class ObservedHealth(unittest.TestCase):
    """The first real /health, from a live Barsa.Ai.Host 4.1.203.

    Recorded verbatim from a run against D:\\Barsa\\4.1.203\\WinDesign on
    2026-10-12. Until this, every field name here was reconstructed from IL;
    this payload is what the host actually answered, so it is the evidence
    the rest of the client is checked against. Trimmed to the keys the client
    reads, with the database identity kept because the whole point is that
    those three names were right.
    """

    PAYLOAD = {
        "connectionKey": "<server>-<instance>-<database>",
        "database": {"instance": "<instance>", "name": "<database>",
                     "server": "<server>"},
        "httpPrefix": "http://127.0.0.1:17840/",
        "processId": 36256,
        "runtimeFingerprint": {
            "semanticProfileVersion": 15,
            "socContractRevision": "v15-qtr-v217",
            "socContractHash": None,
            "host": {"assemblyVersion": "4.1.203.0",
                     "file": "Barsa.Ai.Host.exe"},
        },
        "startedAt": "2026-10-12T13:36:50.3111546Z",
        "status": "ready",
    }

    def test_the_database_identity_keys_are_the_ones_we_reconstructed(self):
        from barsa_kanban import connection
        db = self.PAYLOAD["database"]
        self.assertEqual(sorted(db), ["instance", "name", "server"])
        ok, said = connection.check_database(
            {"database": {"server": "<server>", "name": "<database>",
                          "instance": "<instance>", "enforce": True}},
            self.PAYLOAD)
        self.assertTrue(ok, said)

    def test_a_different_database_stops_the_apply(self):
        from barsa_kanban import connection
        ok, said = connection.check_database(
            {"database": {"server": "<server>", "name": "production",
                          "enforce": True}},
            self.PAYLOAD)
        self.assertFalse(ok)
        self.assertIn("production", said)

    def test_the_status_the_client_waits_for(self):
        self.assertEqual(self.PAYLOAD["status"], "ready")

    def test_the_host_profile_matches_the_one_we_author_for(self):
        from barsa_kanban.barsa_host import HostClient
        self.assertIsNone(HostClient.profile_mismatch(self.PAYLOAD))

    def test_a_profile_the_host_moved_past_is_caught(self):
        from barsa_kanban.barsa_host import HostClient
        from barsa_extractor.change_batch import PROFILE_VERSION
        moved = dict(self.PAYLOAD)
        moved["runtimeFingerprint"] = dict(self.PAYLOAD["runtimeFingerprint"],
                                           semanticProfileVersion=16)
        self.assertEqual(HostClient.profile_mismatch(moved),
                         (PROFILE_VERSION, 16))

    def test_a_system_id_never_leaves_as_a_number(self):
        """Observed: /systems answers id as a JSON number past 2**53.

        1011413550000000100 is a real id from a live host. Read as a double
        it becomes ...128 -- a different system, silently. The client coerces
        every id to a string at the one door they come through.
        """
        real = 1011413550000000100
        self.assertGreater(real, 2 ** 53)
        self.assertNotEqual(int(float(real)), real)   # the corruption

        from barsa_kanban.barsa_host import HostClient
        client = HostClient.__new__(HostClient)
        client._call = lambda *a, **k: {
            "status": "succeeded",
            "systems": [{"id": real, "name": "باركد"},
                        {"id": 7097413550000000101, "name": "Push"}]}
        rows = client.systems()["systems"]
        self.assertEqual([r["id"] for r in rows],
                         ["1011413550000000100", "7097413550000000101"])
        for row in rows:
            self.assertIsInstance(row["id"], str)

    def test_an_unreported_profile_is_not_a_disagreement(self):
        from barsa_kanban.barsa_host import HostClient
        quiet = dict(self.PAYLOAD, runtimeFingerprint={})
        self.assertIsNone(HostClient.profile_mismatch(quiet))

if __name__ == "__main__":
    unittest.main(verbosity=2)
