#!/usr/bin/env python3
"""The config builder: it must carry Barsa's keys across without touching them."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))

import make_host_config as m

# A value with every character that could break a copy or an XML escape.
NASTY = ('Sql:srv\\inst,Db=a "quoted" & <angled> db % V1 % '
         'DD-BA-CF-47-99-F4-91-48')


def write_source(path, settings):
    root = ET.Element("configuration")
    app = ET.SubElement(root, "appSettings")
    for k, v in settings.items():
        ET.SubElement(app, "add", {"key": k, "value": v})
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


class Builder(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = os.path.join(self.dir, "Barsa.App.exe.config")
        self.out = os.path.join(self.dir, "Barsa.Ai.Host.exe.config")

    def build(self, settings, *extra):
        write_source(self.src, settings)
        return m.main(["--from", self.src, "--out", self.out] + list(extra))

    def settings_of(self, path):
        return m.read_app_settings(path)

    def test_a_nasty_connection_string_survives_verbatim(self):
        self.build({"DBProvider": "System.Data.SqlClient",
                    "DBConnectionString": NASTY,
                    "RemotingUsage": "None"})
        self.assertEqual(self.settings_of(self.out)["DBConnectionString"],
                         NASTY)

    def test_the_ai_keys_are_written_and_overridable(self):
        self.build({"DBConnectionString": NASTY}, "--api-key", "k",
                   "--user", "راهبر", "--password", "p&w<d")
        got = self.settings_of(self.out)
        self.assertEqual(got["AiHost.ApiKey"], "k")
        self.assertEqual(got["AiHost.UserName"], "راهبر")
        self.assertEqual(got["AiHost.Password"], "p&w<d")
        self.assertEqual(got["AiHost.HttpPrefix"], "http://127.0.0.1:17840/")

    def test_a_source_without_a_connection_string_is_refused(self):
        """A config that cannot connect is not a source to copy from."""
        with self.assertRaises(SystemExit):
            self.build({"DBProvider": "System.Data.SqlClient"})
        self.assertFalse(os.path.exists(self.out))

    def test_an_empty_connection_string_is_refused(self):
        with self.assertRaises(SystemExit):
            self.build({"DBConnectionString": "   "})

    def test_an_existing_file_is_not_clobbered_without_force(self):
        with open(self.out, "w", encoding="utf-8") as fh:
            fh.write("mine")
        with self.assertRaises(SystemExit):
            self.build({"DBConnectionString": NASTY})
        with open(self.out, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "mine")
        self.build({"DBConnectionString": NASTY}, "--force")
        self.assertIn("appSettings", open(self.out, encoding="utf-8").read())

    def test_keys_barsa_does_not_own_are_not_carried(self):
        self.build({"DBConnectionString": NASTY, "Color": "1",
                    "CompilerVersion": "v2.0"})
        got = self.settings_of(self.out)
        self.assertNotIn("Color", got)
        self.assertNotIn("CompilerVersion", got)

    def test_describe_never_reveals_the_payload(self):
        said = m.describe(NASTY)
        self.assertIn("V1", said)
        self.assertNotIn("DD-BA", said)
        self.assertIn("8 بایت", said)

    def test_describe_says_so_when_the_shape_is_wrong(self):
        self.assertIn("انتظار ۳", m.describe("just-a-string"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
