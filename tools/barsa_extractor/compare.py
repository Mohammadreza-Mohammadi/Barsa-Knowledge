"""Scope equivalence and semantic comparison (spec v3 sections 39-54).

The governing rule from section 39: two exports are only compared in full when
their selection scope is equivalent.  Equal filenames prove nothing.  When
scope cannot be established, no compatibility percentage is produced at all
(section 54).
"""

import os
import re

SCOPE_EXACT = "Exact"
SCOPE_PARTIAL = "Partial"
SCOPE_CANDIDATE = "Candidate"
SCOPE_DIFFERENT = "Different"
SCOPE_UNKNOWN = "Unknown"

MATCH_EXACT_IDENTITY = "ExactIdentity"
MATCH_STRONG = "StrongMatch"
MATCH_WEAK = "WeakMatch"
MATCH_UNMATCHED = "Unmatched"

DIFF_MISSING_IN_AI = "MissingInAiExport"
DIFF_EXTRA_IN_AI = "ExtraInAiExport"
DIFF_VALUE = "ValueMismatch"
DIFF_TYPE = "TypeMismatch"
DIFF_REFERENCE = "ReferenceMismatch"
DIFF_ORDERING = "OrderingOnly"
DIFF_CASING = "CasingOnly"
DIFF_REPRESENTATION = "RepresentationDifference"
DIFF_UNKNOWN_MAPPING = "UnknownMapping"

_WS = re.compile(r"\s+")


def _norm_name(v):
    """Case- and whitespace-insensitive key, original value kept by callers."""
    if v is None:
        return None
    return _WS.sub(" ", str(v)).strip().lower()


# --- scope ----------------------------------------------------------------

def legacy_selection_roots(pkg):
    """The roots the operator actually picked, from $RootSelection."""
    if "$RootSelection" not in pkg.tables:
        return None
    roots = []
    for r in pkg.rows_of("$RootSelection"):
        roots.append({
            "objectId": r.get("ObjectId"),
            "title": r.get("ObjectTitle"),
            "typeLocalId": r.get("ObjectTypeLocalId"),
            "parentObjectId": r.get("ParentObjectId"),
        })
    return roots


def ai_selection_roots(artifact):
    """Top-level tree nodes, which are the AiExport equivalent of roots."""
    tree = artifact.tree
    if not isinstance(tree, list):
        return None
    roots = []
    for node in tree:
        if not isinstance(node, dict):
            continue
        roots.append({
            "objectId": node.get("id"),
            "title": node.get("$caption") or node.get("caption"),
            "selector": node.get("selector"),
            "type": node.get("$type"),
        })
    return roots


def scope_equivalence(legacy_roots, ai_roots, declared=None):
    """Classify two artifacts' selection scope (sections 39-41).

    `declared` is an optional user assertion from pairs.json.  It is recorded
    but never trusted on its own: the structural check still runs, and a
    declared "exact" that the structure contradicts is reported as a conflict.
    """
    rec = {
        "level": SCOPE_UNKNOWN,
        "reason": None,
        "declared": declared,
        "declaredAgrees": None,
        "legacyRootCount": None if legacy_roots is None else len(legacy_roots),
        "aiRootCount": None if ai_roots is None else len(ai_roots),
        "sharedIds": [],
        "legacyOnlyIds": [],
        "aiOnlyIds": [],
        "confidence": "Unknown",
    }
    if legacy_roots is None or ai_roots is None:
        rec["reason"] = ("one side exposes no selection roots, so scope cannot "
                         "be established")
        return rec

    lids = {str(r["objectId"]) for r in legacy_roots if r.get("objectId")}
    aids = {str(r["objectId"]) for r in ai_roots if r.get("objectId")}
    shared = sorted(lids & aids)
    rec["sharedIds"] = shared
    rec["legacyOnlyIds"] = sorted(lids - aids)
    rec["aiOnlyIds"] = sorted(aids - lids)

    if lids and aids:
        if lids == aids:
            rec["level"] = SCOPE_EXACT
            rec["reason"] = "both artifacts declare the same selected object ids"
            rec["confidence"] = "Verified"
        elif shared:
            rec["level"] = SCOPE_PARTIAL
            rec["reason"] = ("%d object ids are shared; each side also carries "
                             "ids the other does not" % len(shared))
            rec["confidence"] = "Verified"
        else:
            rec["level"] = SCOPE_DIFFERENT
            rec["reason"] = "no selected object id appears on both sides"
            rec["confidence"] = "Verified"
    else:
        # Fall back to titles, which section 48 calls a weak key.
        ltitles = {_norm_name(r.get("title")) for r in legacy_roots} - {None}
        atitles = {_norm_name(r.get("title")) for r in ai_roots} - {None}
        if ltitles and atitles and ltitles & atitles:
            rec["level"] = SCOPE_CANDIDATE
            rec["reason"] = ("ids are unavailable on at least one side; root "
                             "captions overlap, which resembles but does not "
                             "prove the same selection")
            rec["confidence"] = "Inferred"
        else:
            rec["reason"] = "no usable ids and no overlapping root captions"

    if declared:
        rec["declaredAgrees"] = (declared.lower() == rec["level"].lower())
    return rec


def candidate_pairs(legacy_packages, ai_artifacts, declared_pairs=None):
    """Pair artifacts by name only as a *candidate*, never as proven scope."""
    declared = {}
    for d in (declared_pairs or []):
        key = (os.path.basename(d.get("legacy", "")),
               os.path.basename(d.get("aiExport", "")))
        declared[key] = d.get("scope")
    pairs = []
    for pkg in legacy_packages:
        lname = os.path.basename(pkg.path)
        lstem = _norm_name(os.path.splitext(lname)[0])
        for art in ai_artifacts:
            aname = os.path.basename(art.path)
            astem = _norm_name(os.path.splitext(aname)[0])
            if not lstem or not astem:
                continue
            related = (lstem == astem or lstem in astem or astem in lstem)
            key = (lname, aname)
            if not related and key not in declared:
                continue
            pairs.append({
                "legacy": lname,
                "aiExport": aname,
                "pairedBy": "declared" if key in declared else "filename",
                "declaredScope": declared.get(key),
            })
    return pairs


# --- semantic comparison --------------------------------------------------

def _identity_keys(node):
    """Ordered identity candidates, strongest first (section 48)."""
    keys = []
    if node.get("selector"):
        keys.append(("selector", str(node["selector"])))
    if node.get("id"):
        keys.append(("id", str(node["id"])))
    if node.get("dbName"):
        keys.append(("dbName", _norm_name(node["dbName"])))
    if node.get("name"):
        keys.append(("name", _norm_name(node["name"])))
    if node.get("caption"):
        keys.append(("caption", _norm_name(node["caption"])))
    return keys


_KEY_STRENGTH = {
    "selector": MATCH_EXACT_IDENTITY,
    "id": MATCH_EXACT_IDENTITY,
    "dbName": MATCH_STRONG,
    "name": MATCH_STRONG,
    "caption": MATCH_WEAK,
}


def match_collection(legacy_nodes, ai_nodes):
    """Match two normalized collections, reporting per-match strength."""
    if legacy_nodes is None or ai_nodes is None:
        return None
    ai_index = {}
    for node in ai_nodes:
        for kind, val in _identity_keys(node):
            ai_index.setdefault((kind, val), []).append(node)

    matches = []
    used = set()
    for lnode in legacy_nodes:
        hit = None
        for kind, val in _identity_keys(lnode):
            bucket = ai_index.get((kind, val))
            if not bucket:
                continue
            for cand in bucket:
                if id(cand) in used:
                    continue
                hit = (kind, cand)
                break
            if hit:
                break
        if hit:
            kind, cand = hit
            used.add(id(cand))
            matches.append({
                "legacy": _brief(lnode),
                "aiExport": _brief(cand),
                "matchedOn": kind,
                "strength": _KEY_STRENGTH.get(kind, MATCH_WEAK),
            })
        else:
            matches.append({
                "legacy": _brief(lnode),
                "aiExport": None,
                "matchedOn": None,
                "strength": MATCH_UNMATCHED,
            })
    for node in ai_nodes:
        if id(node) not in used:
            matches.append({
                "legacy": None,
                "aiExport": _brief(node),
                "matchedOn": None,
                "strength": MATCH_UNMATCHED,
            })
    return matches


def _brief(node):
    return {k: node.get(k) for k in ("id", "selector", "name", "caption")
            if node.get(k) is not None}


def classify_difference(match, scope_level, importer_reads=None):
    """Turn an unmatched or mismatched entry into a typed difference.

    Section 52: a difference is only a BugCandidate when scope is equivalent,
    the semantic match is strong, and the concept matters to the importer.
    Everything else is a Difference.
    """
    if match["strength"] == MATCH_UNMATCHED:
        kind = DIFF_MISSING_IN_AI if match["legacy"] else DIFF_EXTRA_IN_AI
    else:
        kind = DIFF_REPRESENTATION

    strong = match["strength"] in (MATCH_EXACT_IDENTITY, MATCH_STRONG)
    scope_ok = scope_level == SCOPE_EXACT
    matters = True if importer_reads is None else bool(importer_reads)

    verdict = "BugCandidate" if (scope_ok and strong and matters
                                 and kind == DIFF_MISSING_IN_AI) \
        else "Difference"
    return {
        "differenceType": kind,
        "verdict": verdict,
        "scopeLevel": scope_level,
        "matchStrength": match["strength"],
        "legacy": match["legacy"],
        "aiExport": match["aiExport"],
        "whyNotBug": None if verdict == "BugCandidate" else _why(
            scope_ok, strong, matters, kind),
    }


def _why(scope_ok, strong, matters, kind):
    if not scope_ok:
        return "scope is not proven Exact, so a missing object may simply be out of scope"
    if not strong:
        return "identity match is weak, so the objects may not correspond"
    if not matters:
        return "no importer read-set entry shows this concept is consumed"
    if kind == DIFF_EXTRA_IN_AI:
        return "present only in AiExport, which may be a new capability rather than a defect"
    return "difference is in representation, not in semantics"


def coverage(legacy_env, ai_env, scope):
    """Per-concept coverage table (section 53).

    A percentage is produced only under the section 54 conditions.
    """
    rows = []
    for coll in sorted(set(legacy_env) | set(ai_env)):
        if coll.startswith("_") or coll in ("schemaVersion", "extensions"):
            continue
        lv, av = legacy_env.get(coll), ai_env.get(coll)
        rows.append({
            "concept": coll,
            "legacy": "yes" if lv else ("no" if lv == [] else "unknown"),
            "aiExport": "yes" if av else ("no" if av == [] else "unknown"),
            "legacyCount": len(lv) if isinstance(lv, list) else None,
            "aiCount": len(av) if isinstance(av, list) else None,
        })
    computable = scope.get("level") == SCOPE_EXACT
    return {
        "rows": rows,
        "compatibilityPercentage": None,
        "percentageComputable": computable,
        "percentageNote": (
            "Computable: scope is Exact." if computable else
            "Not computable: spec section 54 requires scope Exact plus "
            "sufficiently strong identity matching. Scope here is %s."
            % scope.get("level")),
    }
