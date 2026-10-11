"""Regressions for full system data and evidence-backed navigation identity."""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from barsa_extractor import system_index
from barsa_report_compiler import entities, load, render
from report_retrieve import _fold, retrieve


class SystemIndexTests(unittest.TestCase):
    def test_multi_system_rows_are_not_capped_or_misassigned(self):
        def prov():
            return {"source": "fixture.metaexport", "format": "Barsa.LegacyMetaExport"}

        env = {
            "_source": {"file": "fixture.metaexport",
                        "format": "Barsa.LegacyMetaExport"},
            "system": [{"id": "1", "rootFolderId": "100", "_provenance": prov()},
                       {"id": "2", "rootFolderId": "200", "_provenance": prov()}],
            "entities": [{"id": "10", "systemId": "1", "_provenance": prov()},
                         {"id": "20", "systemId": "2", "_provenance": prov()}],
            "fields": [{"id": str(i), "entityId": "10", "_provenance": prov()}
                       for i in range(30)] +
                      [{"id": "99", "entityId": "20", "_provenance": prov()}],
            "navigation": [{"id": "100", "_provenance": prov()},
                           {"id": "101", "parentId": "100", "_provenance": prov()},
                           {"id": "200", "_provenance": prov()}],
        }
        built = system_index.build([env], [])
        self.assertEqual(len(built["1"]["collections"]["fields"]), 30)
        self.assertEqual(built["1"]["collections"]["fields"][29]["id"], "29")
        self.assertEqual(len(built["2"]["collections"]["fields"]), 1)
        self.assertEqual(len(built["1"]["collections"]["navigation"]), 2)

    def test_generated_index_reaches_report_model(self):
        dist = load.Dist(str(ROOT / "dist"))
        barcode = entities.build(dist, "1011413550000000100")
        self.assertEqual(len(barcode["entities"]), 4)
        self.assertEqual(len(barcode["fields"]), 8)
        self.assertTrue(all(f["provenance"] for f in barcode["fields"]))

        push = entities.build(dist, "7097413550000000101")
        self.assertGreater(len(push["fields"]), 25)
        indexed = dist.systems[push["systemId"]]["collections"]["fields"]
        beyond_first_25 = indexed[25]["id"]
        self.assertIn(beyond_first_25, {f["id"] for f in push["fields"]})
        found = retrieve(dist, push["systemId"], "field", beyond_first_25)
        self.assertTrue(any(f["id"] == beyond_first_25 for f in found["rows"]))

        by_source = {}
        for index in dist.systems.values():
            for source in index["sources"]:
                counts = source["counts"]["fields"]
                if not counts["available"]:
                    continue
                row = by_source.setdefault(source["file"],
                                           [counts["artifactRows"], 0])
                row[1] += counts["assignedRows"]
        self.assertEqual(by_source[
            "Push Notification، الگو، پورتال برسانوين‌راي "
            "(05-07-08 13;42).metaexport"], [2285, 2285])
        self.assertTrue(all(total == assigned for total, assigned
                            in by_source.values()))

    def test_barcode_folder_path_has_provenance_without_guessed_selector(self):
        dist = load.Dist(str(ROOT / "dist"))
        barcode = entities.build(dist, "1011413550000000100")
        folders = [f for f in barcode["folders"]
                   if f.get("stableReference") and
                   f["stableReference"].get("path") == "پایه/Test"]
        self.assertEqual(len(folders), 1)
        self.assertIsNone(folders[0]["selector"])
        self.assertTrue(folders[0]["provenance"])
        self.assertFalse(folders[0]["authorableReference"])

        navigation = dist.systems[barcode["systemId"]]["collections"]["navigation"]
        legacy = {n["id"]: n for n in navigation
                  if n.get("id") and
                  (n.get("_provenance") or {}).get("format")
                  == "Barsa.LegacyMetaExport"}
        test = next(n for n in legacy.values() if n.get("name") == "Test")
        parent = legacy[test["parentId"]]
        self.assertEqual(_fold(parent["name"] + "/" + test["name"]),
                         _fold(folders[0]["path"]))

    def test_large_system_uses_bounded_context_projection(self):
        dist = load.Dist(str(ROOT / "dist"))
        sid = "1013413550000000100"
        model = entities.build(dist, sid)
        self.assertGreater(len(model["fields"]), 1000)
        projection = render._bounded_model(model)
        self.assertEqual(projection["counts"]["fields"], len(model["fields"]))
        self.assertEqual(projection["contextProjection"],
                         "summary; full rows are retrieved from dist/")
        field_id = model["fields"][-1]["id"]
        self.assertTrue(retrieve(dist, sid, "field", field_id)["rows"])


if __name__ == "__main__":
    unittest.main()
