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

# Arabic and Persian forms of the same letter are used interchangeably in this
# data: the AI export profile itself maps both "فرآيند" and "فرآیند" to one
# folder. Comparing names without folding them reports the same object as two.
_LETTER_FOLD = str.maketrans({
    "\u064a": "\u06cc",  # Arabic yeh    -> Persian yeh
    "\u0649": "\u06cc",  # alef maksura  -> Persian yeh
    "\u0643": "\u06a9",  # Arabic kaf    -> Persian keheh
    "\u0624": "\u0648",  # waw with hamza
    "\u0623": "\u0627",  # alef variants
    "\u0625": "\u0627",
    "\u0622": "\u0627",
    "\u200c": " ",       # zero-width non-joiner
    "\u200f": "",
    "\u200e": "",
})

# Export file names end in a timestamp the exporter itself appends:
# ApplicationExportForm.btnSelectFile_Click formats it as "(yy-MM-dd HH;mm)".
# Two exports of one selection taken at different times differ only in that
# suffix, so it is stripped before names are compared for candidacy.
_EXPORT_STAMP = re.compile(r"\s*\(\s*\d{2}-\d{2}-\d{2}[^)]*\)\s*$")


def _stem(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    return _norm_name(_EXPORT_STAMP.sub("", base))


def _norm_name(v):
    """Case-, whitespace- and letter-form-insensitive key.

    Callers keep the original value; this is only ever a comparison key.
    """
    if v is None:
        return None
    folded = str(v).translate(_LETTER_FOLD)
    return _WS.sub(" ", folded).strip().lower()


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


# In both supplied legacy samples every $RootSelection row carries
# ObjectTypeLocalId 41355, the MetaSystem type. Selection roots are therefore
# systems, which is what the AiExport side must be matched on.
AI_ROOT_TYPE = "system"


def ai_selection_roots(artifact):
    """The systems an AiExport artifact covers.

    For the single-document variant the roots are the top-level `tree` entries;
    for the ZIP variant each record is its own file, so the top-level file list
    is not a root list -- taking it as one would compare a legacy selection of
    systems against a mixture of entities, views and reports. Both variants are
    therefore reduced to their `$type: "system"` records.
    """
    roots = []
    seen = set()
    for src, doc in artifact.files.items():
        if src == "_assets":
            continue
        for obj in _iter_objects(doc):
            if obj.get("$type") != AI_ROOT_TYPE:
                continue
            oid = obj.get("id")
            if oid in seen:
                continue
            seen.add(oid)
            roots.append({
                "objectId": oid,
                "title": (obj.get("$caption") or obj.get("Caption")
                          or obj.get("caption")),
                "selector": obj.get("selector"),
                "type": obj.get("$type"),
                "source": src,
            })
    if roots:
        return roots
    tree = artifact.tree
    if not isinstance(tree, list):
        return None
    for node in tree:
        if isinstance(node, dict):
            roots.append({
                "objectId": node.get("id"),
                "title": node.get("$caption") or node.get("caption"),
                "selector": node.get("selector"),
                "type": node.get("$type"),
                "source": "<tree>",
            })
    return roots


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


def temporal_distance(pkg, artifact):
    """How far apart in time two artifacts were produced.

    Equal selection ids do not make two artifacts comparable if the system
    changed between exports: a value difference would then be a real change,
    not an export defect. This is reported so bug classification can account
    for it.
    """
    legacy_time = (pkg.header or {}).get("Export Time")
    legacy_core = (pkg.header or {}).get("Core Version")
    man = artifact.manifest or {}
    return {
        "legacyExportTime": legacy_time,
        "legacyCoreVersion": legacy_core,
        "aiProducerVersion": man.get("producerVersion"),
        "aiBuildId": man.get("buildId"),
        "sameBuild": (bool(legacy_core) and bool(man.get("producerVersion"))
                      and man["producerVersion"].startswith(legacy_core)),
    }


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
        lstem = _stem(lname)
        for art in ai_artifacts:
            aname = os.path.basename(art.path)
            astem = _stem(aname)
            if not lstem or not astem:
                continue
            if lstem == astem:
                how = "nameExactAfterStampStrip"
            elif lstem.startswith(astem) or astem.startswith(lstem):
                how = "namePrefix"
            elif lstem in astem or astem in lstem:
                how = "nameSubstring"
            else:
                how = None
            key = (lname, aname)
            if how is None and key not in declared:
                continue
            pairs.append({
                "legacy": lname,
                "aiExport": aname,
                "pairedBy": "declared" if key in declared else how,
                "declaredScope": declared.get(key),
                "note": ("Filename candidacy only. Scope is decided by the "
                         "structural check, never by the name."),
            })
    return pairs


# --- semantic comparison --------------------------------------------------

# Identity keys in descending strength. Order matters twice: it decides which
# key wins for one node, and it decides the order of the global passes below.
_KEY_ORDER = ("selector", "id", "codeTarget", "dbNameScoped", "name",
              "caption")

_KEY_STRENGTH = {
    "selector": MATCH_EXACT_IDENTITY,
    "id": MATCH_EXACT_IDENTITY,
    "codeTarget": MATCH_EXACT_IDENTITY,
    "dbNameScoped": MATCH_STRONG,
    "name": MATCH_STRONG,
    "caption": MATCH_WEAK,
}

# Keys strong enough that failing to find a counterpart means the object really
# is absent, rather than merely unmatchable.
_DECISIVE_KEYS = ("selector", "id", "codeTarget")


def _identity_keys(node):
    """Identity candidates for one node, keyed by strength.

    `dbName` is deliberately *not* a bare key. A field's dbName is "F1", "F2",
    "F3" within its own entity and repeats across every other entity, so a bare
    dbName match pairs unrelated fields. It is only used when the owning entity
    is known, as `dbNameScoped`.
    """
    keys = {}
    if node.get("selector"):
        keys["selector"] = str(node["selector"])
    if node.get("id"):
        keys["id"] = str(node["id"])
    # A MetaCode record is identified by what it is attached to: the legacy
    # row carries TargetObjectId, and AiExport keeps the same code inline on
    # the target object itself.
    if node.get("targetObjectId"):
        keys["codeTarget"] = str(node["targetObjectId"])
    owner = node.get("entityId") or node.get("_ownerId")
    if node.get("dbName") and owner:
        keys["dbNameScoped"] = "%s/%s" % (owner, _norm_name(node["dbName"]))
    if node.get("name"):
        keys["name"] = _norm_name(node["name"])
    if node.get("caption"):
        keys["caption"] = _norm_name(node["caption"])
    return keys


def match_collection(legacy_nodes, ai_nodes):
    """Match two normalized collections, strongest key first.

    The passes are global: every pair that agrees on selector or id is matched
    before any weaker key is consulted. A single-pass, per-node loop lets a weak
    key consume a node that had an exact identity match with a different node,
    which silently reports a present object as missing.
    """
    if legacy_nodes is None or ai_nodes is None:
        return None

    l_keys = [(_identity_keys(n), n) for n in legacy_nodes]
    a_keys = [(_identity_keys(n), n) for n in ai_nodes]

    matched = []
    used_l, used_a = set(), set()

    for key in _KEY_ORDER:
        index = {}
        for i, (keys, node) in enumerate(a_keys):
            if i in used_a or key not in keys:
                continue
            index.setdefault(keys[key], []).append(i)
        for j, (keys, lnode) in enumerate(l_keys):
            if j in used_l or key not in keys:
                continue
            bucket = index.get(keys[key])
            if not bucket:
                continue
            # An ambiguous key matches nothing: pairing one of several
            # candidates arbitrarily would invent a difference for the rest.
            free = [i for i in bucket if i not in used_a]
            if len(free) != 1:
                continue
            i = free[0]
            used_l.add(j)
            used_a.add(i)
            matched.append({
                "legacy": _brief(lnode),
                "aiExport": _brief(a_keys[i][1]),
                "matchedOn": key,
                "strength": _KEY_STRENGTH[key],
            })

    # Which decisive keys each side actually populated. An object reported
    # missing is only trustworthy if the key used to look for it existed on the
    # other side too; otherwise the collections were never comparable by it.
    coverage = {}
    for key in _DECISIVE_KEYS:
        coverage[key] = {
            "legacy": sum(1 for k, _n in l_keys if key in k),
            "aiExport": sum(1 for k, _n in a_keys if key in k),
        }

    for j, (keys, lnode) in enumerate(l_keys):
        if j not in used_l:
            matched.append({
                "legacy": _brief(lnode), "aiExport": None,
                "matchedOn": None, "strength": MATCH_UNMATCHED,
                "searchedBy": sorted(k for k in _DECISIVE_KEYS if k in keys),
                "keyComparable": any(
                    k in keys and coverage[k]["aiExport"] > 0
                    for k in _DECISIVE_KEYS),
            })
    for i, (keys, anode) in enumerate(a_keys):
        if i not in used_a:
            matched.append({
                "legacy": None, "aiExport": _brief(anode),
                "matchedOn": None, "strength": MATCH_UNMATCHED,
                "searchedBy": sorted(k for k in _DECISIVE_KEYS if k in keys),
                "keyComparable": any(
                    k in keys and coverage[k]["legacy"] > 0
                    for k in _DECISIVE_KEYS),
            })
    return matched


def _brief(node):
    out = {k: node.get(k) for k in ("id", "selector", "name", "caption")
           if node.get(k) is not None}
    if node.get("dataType"):
        out["dataType"] = node["dataType"]
    if node.get("_aiType"):
        out["$type"] = node["_aiType"]
    return out


# Legacy MET_FIELDDEF carries plain fields *and* relation fields in one table,
# while AiExport splits them into "field" and "relation" record types. Comparing
# the two collections separately therefore reports every relation field as
# missing on one side and extra on the other. These collections are compared as
# a union instead.
UNIONED_COLLECTIONS = {"fields": ("fields", "relationDefs")}


def comparable_pairs(legacy_env, ai_env):
    """Yield (label, legacy nodes, ai nodes) honouring the union rule."""
    done = set()
    for label, parts in UNIONED_COLLECTIONS.items():
        l_nodes, a_nodes = [], []
        l_any = a_any = False
        for part in parts:
            lv, av = legacy_env.get(part), ai_env.get(part)
            if lv is not None:
                l_nodes.extend(lv)
                l_any = True
            if av is not None:
                a_nodes.extend(av)
                a_any = True
            done.add(part)
        yield ("%s (incl. relation fields)" % label,
               l_nodes if l_any else None,
               a_nodes if a_any else None)
    for coll in sorted(set(legacy_env) | set(ai_env)):
        if coll in done or coll.startswith("_"):
            continue
        if coll in ("schemaVersion", "extensions"):
            continue
        yield coll, legacy_env.get(coll), ai_env.get(coll)


def classify_difference(match, scope_level, importer_reads=None,
                        temporal=None):
    """Turn an unmatched or mismatched entry into a typed difference.

    Section 52: a difference is only a BugCandidate when scope is equivalent,
    the semantic match is strong, and the concept matters to the importer.
    Everything else is a Difference.
    """
    if match["strength"] == MATCH_UNMATCHED:
        kind = DIFF_MISSING_IN_AI if match["legacy"] else DIFF_EXTRA_IN_AI
    else:
        kind = DIFF_REPRESENTATION

    if match["strength"] == MATCH_UNMATCHED:
        # An absent object has no match strength. What matters instead is
        # whether it was looked for by a decisive key that the other side also
        # populated: only then does "not found" mean "not there".
        strong = bool(match.get("keyComparable"))
    else:
        strong = match["strength"] in (MATCH_EXACT_IDENTITY, MATCH_STRONG)
    scope_ok = scope_level == SCOPE_EXACT
    matters = True if importer_reads is None else bool(importer_reads)

    verdict = "BugCandidate" if (scope_ok and strong and matters
                                 and kind == DIFF_MISSING_IN_AI) \
        else "Difference"
    caveat = None
    if verdict == "BugCandidate" and temporal and not temporal.get("sameBuild"):
        # Equal selection ids do not make two artifacts contemporaneous. If the
        # exports come from different builds, a missing object may have been
        # deleted between them, so the finding is held at a lower confidence
        # rather than asserted as a defect.
        verdict = "BugCandidate (unconfirmed: artifacts are not from one build)"
        caveat = ("Legacy core %s exported %s; AiExport producer %s. A "
                  "same-build pair is needed to separate an export defect from "
                  "a change made between the two exports."
                  % (temporal.get("legacyCoreVersion"),
                     (temporal.get("legacyExportTime") or "?")[:10],
                     temporal.get("aiProducerVersion")))
    return {
        "differenceType": kind,
        "verdict": verdict,
        "scopeLevel": scope_level,
        "matchStrength": match["strength"],
        "legacy": match["legacy"],
        "aiExport": match["aiExport"],
        "temporalCaveat": caveat,
        "whyNotBug": None if verdict.startswith("BugCandidate") else _why(
            scope_ok, strong, matters, kind),
    }


def _why(scope_ok, strong, matters, kind):
    if not scope_ok:
        return "scope is not proven Exact, so a missing object may simply be out of scope"
    if not strong:
        return ("the object could not be looked for by a decisive key that the "
                "other side also carries, so its absence is not evidence")
    if not matters:
        return "no importer read-set entry shows this concept is consumed"
    if kind == DIFF_EXTRA_IN_AI:
        return "present only in AiExport, which may be a new capability rather than a defect"
    return "difference is in representation, not in semantics"


def coverage(legacy_env, ai_env, scope, per_concept=None):
    """Per-concept coverage table (section 53).

    A percentage is produced only under the section 54 conditions: scope Exact
    and identity matching strong enough to trust. Where it is produced, the
    denominator is stated, because "percent compatible" means nothing without
    one.
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

    computable = scope.get("level") == SCOPE_EXACT and bool(per_concept)
    pct = None
    breakdown = []
    if computable:
        total_l = total_m = 0
        weak = False
        for label, info in sorted(per_concept.items()):
            if not isinstance(info, dict):
                continue
            lc, mc = info["legacyCount"], info["matched"]
            total_l += lc
            total_m += mc
            by = info.get("byKey") or {}
            # A concept matched mostly on caption is too weak to count toward a
            # headline number.
            if by.get("caption", 0) > mc / 2 and mc:
                weak = True
            breakdown.append({
                "concept": label, "legacyObjects": lc, "matched": mc,
                "percent": round(100.0 * mc / lc, 1) if lc else None,
                "byKey": by,
            })
        if weak:
            computable = False
        elif total_l:
            pct = round(100.0 * total_m / total_l, 1)

    if pct is not None:
        note = ("Computable: scope is Exact and matches are on decisive keys. "
                "The figure is the share of legacy objects, across the "
                "comparable collections, that found a counterpart in the "
                "AiExport artifact. It is not a statement about data fidelity "
                "within a matched object.")
    elif scope.get("level") != SCOPE_EXACT:
        note = ("Not computable: spec section 54 requires scope Exact. Scope "
                "here is %s, so a percentage would measure the selection "
                "difference rather than format compatibility."
                % scope.get("level"))
    elif not per_concept:
        note = "Not computable: no collection was comparable."
    else:
        note = ("Not computable: too much of the matching rests on captions, "
                "which section 48 treats as a weak key.")

    return {
        "rows": rows,
        "compatibilityPercentage": pct,
        "percentageComputable": computable,
        "percentageNote": note,
        "percentageBreakdown": breakdown,
    }
