"""The Host's own reference docs, read as a primary source.

`Barsa.Ai.Host` writes a startup payload of reference documents, and those
documents state outright several things this extractor could only mark
Unknown from the binaries: the comparison operators a condition may use, the
values `nullBehavior` takes, the folder kinds, the shape of a report
parameter.

That makes them a different kind of evidence from everything else here. A
string in an assembly is a fact about the code; a sentence in the vendor's
own contract document is a statement about the contract. Both are better
than a guess, and neither is the other, so every value extracted here carries
the file, the line and the hash it came from -- and the pack says the source
was a document, not IL.

Nothing is inferred. A section this module cannot find produces no vocabulary
at all, which leaves the consumer's gate exactly as strict as it was before.
"""

import hashlib
import os
import re

# Where the Host writes its startup payload, relative to source/.
ROOT = os.path.join("barsa-ai-host", "startup")

CONDITION_DOC = os.path.join("dataexchange", "10-condition-reference.fa.md")
REPORT_DOC = os.path.join("dataexchange", "05-report-folder-reference.fa.md")
API_DOC = "host-api.fa.md"

_BACKTICKED = re.compile(r"`([A-Za-z][A-Za-z0-9_]*)`")
_KIND = re.compile(r'kind\s*:\s*"([a-zA-Z][a-zA-Z0-9_]*)"')
# "- Page: `kind:"page"` و parent System" -- the kind, then the parent name.
_CHAIN = re.compile(
    r'kind\s*:\s*"([a-zA-Z]+)"`?\s*\S*\s*parent\s+([A-Za-z]+)')
# properties.report={objectType:"report",tempId:"report tempId"}
_TEMPID_REF = re.compile(
    r'objectType\s*:\s*"[a-zA-Z]+"\s*,\s*tempId\s*:')


def available(source_root):
    return os.path.isdir(os.path.join(source_root, ROOT))


def build(source_root):
    """Every vocabulary these documents state, with where each one came from."""
    base = os.path.join(source_root, ROOT)
    if not os.path.isdir(base):
        return None

    docs = {}
    for rel in (CONDITION_DOC, REPORT_DOC, API_DOC):
        path = os.path.join(base, rel)
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                raw = fh.read()
            docs[rel] = {
                "path": os.path.join(ROOT, rel).replace(os.sep, "/"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "lines": raw.decode("utf-8", "replace").splitlines(),
            }

    out = {
        "schemaVersion": 1,
        "source": "Barsa.Ai.Host startup payload, under source/%s"
                  % ROOT.replace(os.sep, "/"),
        "sourceKind": "VendorDocument",
        "confidence": "Documented",
        "note": ("These values are stated by the Host's own reference "
                 "documents. That is a different kind of evidence from a "
                 "string recovered out of IL: it is the vendor describing "
                 "the contract rather than this tool inferring it. Treat a "
                 "disagreement between the two as a finding, not as a tie."),
        "documents": [{"path": d["path"], "sha256": d["sha256"]}
                      for d in docs.values()],
    }

    condition = docs.get(CONDITION_DOC)
    if condition:
        out["comparisonOperators"] = _comparison_operators(condition)
        out["nullBehaviors"] = _null_behaviors(condition)
        out["conditionCombinators"] = _combinators(condition)
    report = docs.get(REPORT_DOC)
    if report:
        out["folderKinds"] = _folder_kinds(report)
        out["reportParameterKeys"] = _parameter_keys(report)
        out["navigationChain"] = _navigation_chain(report)
        out["tempIdReferenceEncoding"] = _tempid_encoding(report)
    api = docs.get(API_DOC)
    if api:
        out["applyStates"] = _apply_states(api)
    return out


def _section(doc, heading):
    """The lines under a '## heading', up to the next heading of any level."""
    lines = doc["lines"]
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## ") \
                and heading.lower() in line.lower():
            start = i + 1
            break
    if start is None:
        return None, None
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return lines[start:end], start + 1


def _sourced(doc, values, line):
    return {"values": values, "document": doc["path"], "line": line,
            "sha256": doc["sha256"]}


def _comparison_operators(doc):
    """The operator list, and only the list.

    It is one paragraph of backticked tokens. The prose after it mentions a
    token that is explicitly *not* part of the contract -- "typo داخلی مثل
    `DoseNotContain` وارد contract AI نمی‌شود" -- so reading to the end of
    the section would hand a consumer the one name the document warns
    against. Collection stops at the blank line that ends the paragraph.
    """
    body, line = _section(doc, "Comparison operators")
    if not body:
        return None
    values = []
    for row in body:
        if row.startswith("#"):
            break
        if not row.strip():
            if values:
                break          # the list ended; what follows is commentary
            continue           # leading blank line
        for token in _BACKTICKED.findall(row):
            if token not in values:
                values.append(token)
    return _sourced(doc, values, line) if values else None


def _null_behaviors(doc):
    for i, row in enumerate(doc["lines"], 1):
        if "nullBehavior" in row:
            continue
        if "ignoreCondition" in row and "|" in row:
            values = [t.strip() for t in
                      row.replace("`", "").split("|") if t.strip()]
            if values:
                return _sourced(doc, values, i)
    return None


def _combinators(doc):
    """`all` / `any`, confirmed by the document as well as by the profile."""
    found = []
    for row in doc["lines"]:
        for key in ("all", "any"):
            if '"%s":[' % key in row.replace(" ", "") and key not in found:
                found.append(key)
    return _sourced(doc, found, None) if found else None


def _folder_kinds(doc):
    values, first = [], None
    for i, row in enumerate(doc["lines"], 1):
        for kind in _KIND.findall(row):
            if kind not in values:
                values.append(kind)
                first = first or i
    return _sourced(doc, values, first) if values else None


def _navigation_chain(doc):
    """The canonical Page -> Group -> Report placement chain.

    The document gives it as three bullets, each naming a kind and the parent
    that kind hangs under. All three or nothing: a partial chain would let a
    consumer build half a navigation path and believe it was the documented
    one.
    """
    wanted = (("page", "system"), ("group", "page"), ("report", "group"))
    found, first = {}, None
    for i, row in enumerate(doc["lines"], 1):
        m = _CHAIN.search(row)
        if not m:
            continue
        kind, parent = m.group(1).lower(), m.group(2).lower()
        if kind not in found:
            found[kind] = {"kind": kind, "parent": parent, "line": i}
            first = first or i
    chain = []
    for kind, parent in wanted:
        row = found.get(kind)
        if not row or row["parent"] != parent:
            return None
        chain.append({"kind": kind, "parent": parent})
    out = _sourced(doc, chain, first)
    out["note"] = ("The report placement is a folder of kind `report` whose "
                   "`report` property points at the report. Page and Group "
                   "are both FolderType.ReportFolder at runtime; the "
                   "hierarchy, not the runtime type, carries the semantics.")
    return out


def _tempid_encoding(doc):
    """Whether the document shows a same-batch reference carrying objectType.

    A literal-presence check, not a reading of the prose: either the document
    writes the encoding out or this returns nothing.
    """
    for i, row in enumerate(doc["lines"], 1):
        if _TEMPID_REF.search(row):
            out = _sourced(doc, ["objectType", "tempId"], i)
            out["note"] = ("A reference to an object created earlier in the "
                           "same batch is written as an object carrying both "
                           "`objectType` and `tempId`. A bare `{\"tempId\": "
                           "...}` is not the documented shape.")
            return out
    return None


def _parameter_keys(doc):
    """The keys of a report parameter, from the document's own example."""
    text = "\n".join(doc["lines"])
    match = re.search(r'"parameters"\s*:\s*\[\s*\{(.+?)\}', text, re.S)
    if not match:
        return None
    keys = re.findall(r'"([A-Za-z][A-Za-z0-9_]*)"\s*:', match.group(1))
    line = text[:match.start()].count("\n") + 1
    return _sourced(doc, keys, line) if keys else None


def _apply_states(doc):
    body, line = _section(doc, "/apply-status")
    if not body:
        return None
    inside, values = False, []
    for row in body:
        stripped = row.strip()
        if stripped.startswith("```"):
            if inside:
                break
            inside = True
            continue
        if inside and stripped:
            values.append(stripped)
    return _sourced(doc, values, line) if values else None
