"""The catalogue of Barsa systems a request can be about.

Read from the knowledge pack, not typed by hand: `dist/index/systems/` lists
every system the extractor saw, and `dist-report/systems/<id>/` says which of
them has a selector index -- the thing that decides whether a batch can refer
to that system's objects at all.

A system without a selector index is still listed, and still refused for
authoring, with the reason said out loud. Hiding it would turn "we have no
evidence for this system" into "this system does not exist".
"""

import json
import os


def catalogue(repo_root, dist="dist", pack="dist-report"):
    """Every system in the pack, with what can and cannot be done with it."""
    manifest_path = os.path.join(repo_root, dist, "index", "systems",
                                 "manifest.json")
    if not os.path.isfile(manifest_path):
        return []
    with open(manifest_path, encoding="utf-8") as fh:
        ids = (json.load(fh).get("systemIds") or [])

    rows = []
    for sid in ids:
        path = os.path.join(repo_root, dist, "index", "systems", sid,
                            "semantic.json")
        captions, counts, complete = [], {}, None
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            for row in (doc.get("systems") or ()):
                caption = row.get("caption") or row.get("name")
                if caption and caption not in captions:
                    captions.append(caption)
            counts = doc.get("counts") or {}
            complete = doc.get("completeFromAvailableEvidence")
        index = os.path.join(repo_root, pack, "systems", sid, "index",
                             "selectors.json")
        authorable = os.path.isfile(index)
        selectors = None
        if authorable:
            with open(index, encoding="utf-8") as fh:
                selectors = (json.load(fh).get("count"))
        rows.append({
            "id": sid,
            "caption": captions[0] if captions else None,
            "captions": captions,
            "entities": counts.get("entities"),
            "reports": counts.get("reports"),
            "fields": counts.get("fields"),
            "completeFromAvailableEvidence": complete,
            "authorable": authorable,
            "selectorCount": selectors,
            "notAuthorableBecause": None if authorable else (
                "بستهٔ گزارش برای این سیستم ساخته نشده، پس هیچ selectorی قابل "
                "اثبات نیست. اول: tools/report_compiler.py --scope system=%s"
                % sid),
        })
    rows.sort(key=lambda r: (not r["authorable"], r["caption"] or r["id"]))
    return rows


def find(repo_root, needle, dist="dist", pack="dist-report"):
    """Resolve an id or a caption to one system, or None when it is not one.

    Returns (row, candidates). A caption that matches several systems returns
    (None, [those systems]) -- an ambiguous name is a question for a human,
    never a pick made quietly.
    """
    rows = catalogue(repo_root, dist, pack)
    if not needle:
        return None, rows
    needle = str(needle).strip()
    for row in rows:
        if row["id"] == needle:
            return row, [row]
    folded = _fold(needle)
    hits = [row for row in rows
            if any(_fold(c) == folded for c in row["captions"])]
    if len(hits) == 1:
        return hits[0], hits
    if hits:
        return None, hits
    partial = [row for row in rows
               if any(folded in _fold(c) for c in row["captions"])]
    if len(partial) == 1:
        return partial[0], partial
    return None, partial or rows


# Arabic and Persian letter forms are mixed in this data; a caption typed with
# the other yeh must still match.
_FOLD = {"ي": "ی", "ك": "ک", "‌": " ", "ي": "ی",
         "ك": "ک"}


def _fold(text):
    out = str(text or "").strip().lower()
    for src, dst in _FOLD.items():
        out = out.replace(src, dst)
    return " ".join(out.split())
