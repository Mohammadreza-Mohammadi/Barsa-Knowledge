"""Reading dist/, with hashes, and refusing to read anything else."""

import hashlib
import json
import os
import re

# Every dist/ file this compiler is permitted to read. The allowlist is the
# enforcement point for spec section 1: a path not named here is not opened,
# so the compiler cannot quietly grow a dependency on source/ or on an
# unrelated corner of dist/.
INPUTS = {
    "semanticContract": "index/semantic-contract.json",
    "aiExportProperties": "index/ai-export-properties.json",
    "exportFormats": "index/export-formats.json",
    "writePipeline": "index/write-pipeline.json",
    "knowledgeIndex": "index/knowledge-index.json",
    "changeBatchSchema": "models/ai-change-batch.schema.json",
}

# Generated dist/ documents read for their tables rather than as JSON. The
# observed-path table in the AiExport document is the only place in dist/ that
# records the JSON shape of a report's `columns`, `condition` and `parameters`
# payloads -- the semantic contract names those properties but states no value
# shape, and the normalized samples drop them.
INPUT_DOCS = {
    "aiExportPaths": "formats/ai-export-single-json.md",
    "legacyReportTable": "formats/report-format.md",
}

# `| `$.a.b` | string, null | 12 | yes |` from an observed-path table.
_PATH_ROW = re.compile(
    r"^\|\s*`(\$[^`]*)`\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(yes|no)\s*\|\s*$")

# Directories read as a set rather than a single file.
INPUT_DIRS = {
    "normalizedSamples": "models/normalized-samples",
    "systemIndexes": "index/systems",
}


class DistError(Exception):
    """dist/ is missing, incomplete, or not a knowledge pack."""


class Dist:
    """A loaded, hashed view of the parts of dist/ this compiler may read."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        if not os.path.isdir(self.root):
            raise DistError("no such dist directory: %s" % self.root)
        self.docs = {}
        self.hashes = {}
        self.missing = []
        for key, rel in sorted(INPUTS.items()):
            path = os.path.join(self.root, rel)
            if not os.path.isfile(path):
                self.missing.append(rel)
                self.docs[key] = None
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
            self.hashes[rel] = hashlib.sha256(raw).hexdigest()
            try:
                self.docs[key] = json.loads(raw.decode("utf-8"))
            except ValueError as exc:
                raise DistError("%s is not valid JSON: %s" % (rel, exc))

        self.text = {}
        for key, rel in sorted(INPUT_DOCS.items()):
            path = os.path.join(self.root, rel)
            if not os.path.isfile(path):
                self.missing.append(rel)
                self.text[key] = None
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
            self.hashes[rel] = hashlib.sha256(raw).hexdigest()
            self.text[key] = raw.decode("utf-8")

        self.samples = []
        sample_dir = os.path.join(self.root, INPUT_DIRS["normalizedSamples"])
        if os.path.isdir(sample_dir):
            for name in sorted(os.listdir(sample_dir)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(sample_dir, name)
                with open(path, "rb") as fh:
                    raw = fh.read()
                rel = os.path.join(INPUT_DIRS["normalizedSamples"], name)
                self.hashes[rel] = hashlib.sha256(raw).hexdigest()
                try:
                    self.samples.append((name, json.loads(raw.decode("utf-8"))))
                except ValueError as exc:
                    raise DistError("%s is not valid JSON: %s" % (rel, exc))
        else:
            self.missing.append(INPUT_DIRS["normalizedSamples"])

        self.systems = {}
        systems_dir = os.path.join(self.root, INPUT_DIRS["systemIndexes"])
        manifest_path = os.path.join(systems_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            manifest = self._read_system_json(manifest_path)
            for sid in manifest.get("systemIds", []):
                if not re.fullmatch(r"[0-9]+", sid):
                    raise DistError("invalid system id in index manifest: %r" % sid)
                path = os.path.join(systems_dir, sid, "semantic.json")
                if not os.path.isfile(path):
                    raise DistError("system index missing: %s" % path)
                self.systems[sid] = self._read_system_json(path)
        else:
            raise DistError(
                "index/systems/manifest.json is required for full system "
                "scope. Run tools/extract.py first.")

        if self.docs.get("semanticContract") is None:
            raise DistError(
                "index/semantic-contract.json is required and missing. "
                "Run tools/extract.py first.")

    # -- convenience accessors ---------------------------------------------

    def _read_system_json(self, path):
        with open(path, "rb") as fh:
            raw = fh.read()
        rel = os.path.relpath(path, self.root).replace("\\", "/")
        self.hashes[rel] = hashlib.sha256(raw).hexdigest()
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise DistError("%s is not valid JSON: %s" % (rel, exc))

    @property
    def contract(self):
        return self.docs["semanticContract"]

    @property
    def enums(self):
        doc = self.docs.get("aiExportProperties") or {}
        return doc.get("enums") or {}

    def object_contract(self, object_type):
        for o in self.contract.get("objectContracts", ()):
            if o.get("objectType") == object_type:
                return o
        return None

    def property_contracts(self, object_type):
        return (self.contract.get("propertyContracts") or {}).get(
            object_type, [])

    def observed_paths(self, prefix=None):
        """Rows of the AiExport observed-path table, optionally by prefix.

        Each row is {path, types, occurrences, nullable}. A path is evidence
        that the key was seen in a supplied artifact; the table records keys
        and types, never values, so a value vocabulary is never recoverable
        from here.
        """
        doc = self.text.get("aiExportPaths")
        if not doc:
            return []
        out = []
        for line in doc.splitlines():
            m = _PATH_ROW.match(line)
            if not m:
                continue
            path, types, count, nullable = m.groups()
            if prefix is not None and not path.startswith(prefix):
                continue
            out.append({
                "path": path,
                "types": [t.strip() for t in types.split(",") if t.strip()],
                "occurrences": int(count),
                "nullable": nullable == "yes",
            })
        return out

    def dist_commit(self):
        """The commit dist/ was generated at, if the repo can say."""
        import subprocess
        try:
            out = subprocess.run(
                ["git", "-C", os.path.dirname(self.root), "log", "-1",
                 "--format=%H", "--", "dist"],
                capture_output=True, text=True, timeout=20, check=False)
            sha = out.stdout.strip()
            return sha or None
        except (OSError, subprocess.SubprocessError):
            return None
