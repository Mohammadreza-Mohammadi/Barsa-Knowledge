"""Reader for Barsa.AiExport artifacts (spec v3 sections 23-38).

Handles both observed physical variants:

  AiExport.SingleJson      one JSON document: { "tree": [...], "manifest": {...} }
  AiExport.ZipJsonPackage  a ZIP of manifest.json plus a JSON file hierarchy

Both are reduced to the same in-memory shape so the normalizer downstream does
not care which one it was given.
"""

import io
import json
import os
import re
import zipfile

from .format_detect import (
    LOGICAL_AI, VARIANT_AI_SINGLE, VARIANT_AI_ZIP, detect, normalize_manifest,
)

# A semantic selector as SemanticSelectorCodec writes it: one or more leading
# '#' then a bracketed, escape-aware key list.
SELECTOR_RE = re.compile(r"^#+\[")

RESERVED_KEYS = ("$type", "$caption", "id", "selector", "output")


class AiExportArtifact:
    """A parsed AiExport document or package."""

    def __init__(self, path, fmt=None):
        self.path = path
        self.format = fmt or detect(path)
        self.variant = self.format.get("variant")
        self.manifest = normalize_manifest(self.format)
        self.errors = list(self.format.get("errors") or [])
        self.files = {}      # published path -> parsed JSON
        self.tree = None
        self.unmapped = None
        if self.format.get("logicalFormat") != LOGICAL_AI:
            return
        try:
            if self.variant == VARIANT_AI_SINGLE:
                self._load_single()
            elif self.variant == VARIANT_AI_ZIP:
                self._load_zip()
        except Exception as exc:
            self.errors.append({"kind": "JsonParseError",
                                "message": "%s: %s" % (type(exc).__name__, exc)})

    def _load_single(self):
        raw = open(self.path, "rb").read()
        doc = json.loads(raw.decode("utf-8-sig"))
        self.files["<root>"] = doc
        self.tree = doc.get("tree")
        self.unmapped = doc.get("unmappedRecords")

    def _load_zip(self):
        zf = zipfile.ZipFile(io.BytesIO(open(self.path, "rb").read()))
        nodes = []
        assets = []
        for name in sorted(zf.namelist()):
            if name.endswith("/"):
                continue
            if not name.lower().endswith(".json"):
                # Code and asset payloads are externalized by the writer's
                # large-code rule; recorded by path, not parsed.
                assets.append(name)
                continue
            try:
                doc = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception as exc:
                self.errors.append({"kind": "JsonParseError",
                                    "message": "%s: %s" % (name, exc)})
                continue
            self.files[name] = doc
            if os.path.basename(name).lower() == "manifest.json":
                continue
            nodes.append(doc)
        if assets:
            self.files["_assets"] = assets
        self.tree = nodes

    # -- schema discovery ---------------------------------------------------

    def json_paths(self):
        """Every observed JSON path with its observed types and frequency."""
        acc = {}
        for src, doc in self.files.items():
            if src == "_assets":
                continue
            _walk_paths(doc, "$", acc, src)
        out = []
        for path, info in sorted(acc.items()):
            out.append({
                "path": path,
                "observedTypes": sorted(info["types"]),
                "occurrences": info["count"],
                "sampleFiles": sorted(info["files"])[:5],
                "nullable": info["nulls"] > 0,
            })
        return out

    def type_catalog(self):
        """Spec section 30: observed "$type" values only."""
        counts = {}
        props = {}
        for src, doc in self.files.items():
            if src == "_assets":
                continue
            for obj in _iter_objects(doc):
                t = obj.get("$type")
                if not isinstance(t, str):
                    continue
                counts[t] = counts.get(t, 0) + 1
                props.setdefault(t, set()).update(
                    k for k in obj if k != "$type")
        return [{"type": t, "count": counts[t],
                 "properties": sorted(props.get(t, ()))}
                for t in sorted(counts)]

    def selectors(self):
        """Observed selector strings, for section 31."""
        found = {}
        for src, doc in self.files.items():
            if src == "_assets":
                continue
            for obj in _iter_objects(doc):
                for key in ("selector", "target"):
                    v = obj.get(key)
                    if isinstance(v, str) and SELECTOR_RE.match(v):
                        found.setdefault(v, set()).add(key)
        return [{"selector": s, "seenAs": sorted(k)}
                for s, k in sorted(found.items())]

    def summary(self):
        return {
            "file": os.path.basename(self.path),
            "sha256": self.format.get("sha256"),
            "size": self.format.get("size"),
            "variant": self.variant,
            "manifest": self.manifest,
            "jsonFiles": len([k for k in self.files if k != "_assets"]),
            "assetFiles": len(self.files.get("_assets") or []),
            "typeCatalog": len(self.type_catalog()),
            "errors": self.errors,
        }


def _walk_paths(node, path, acc, src, depth=0):
    if depth > 40:
        return
    entry = acc.setdefault(path, {"types": set(), "count": 0,
                                  "files": set(), "nulls": 0})
    entry["count"] += 1
    entry["files"].add(src)
    if node is None:
        entry["types"].add("null")
        entry["nulls"] += 1
    elif isinstance(node, dict):
        entry["types"].add("object")
        for k, v in node.items():
            _walk_paths(v, "%s.%s" % (path, k), acc, src, depth + 1)
    elif isinstance(node, list):
        entry["types"].add("array")
        for v in node:
            _walk_paths(v, path + "[*]", acc, src, depth + 1)
    elif isinstance(node, bool):
        entry["types"].add("boolean")
    elif isinstance(node, (int, float)):
        entry["types"].add("number")
    else:
        entry["types"].add("string")


def _iter_objects(node, depth=0):
    if depth > 40:
        return
    if isinstance(node, dict):
        yield node
        for v in node.values():
            for x in _iter_objects(v, depth + 1):
                yield x
    elif isinstance(node, list):
        for v in node:
            for x in _iter_objects(v, depth + 1):
                yield x
