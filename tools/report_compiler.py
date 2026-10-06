#!/usr/bin/env python3
"""Compile dist/ down to a small, honest report-authoring pack.

    python3 tools/report_compiler.py --scope system=1011413550000000100
    python3 tools/report_compiler.py --scope contract
    python3 tools/report_compiler.py --check

The pack it writes is about one task: building and understanding a Barsa
report. It reads dist/ and never source/ -- the loader's allowlist is what
enforces that. Anything the report task needs and dist/ lacks is recorded in
MISSING-FROM-DIST.md instead of being worked around.

Exits non-zero if any build gate fails: over budget, a property outside its
one group, a recipe with a linter error *or warning*, a promoted confidence, a
file without provenance, or an empty gap register.
"""

import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_extractor import change_batch as cb
from barsa_report_compiler import (
    audit, contract as contract_mod, enums as enums_mod, entities, gaps as
    gaps_mod, load, recipes as recipes_mod, render, shapes as shapes_mod,
)
from barsa_report_compiler import __version__


def parse_scope(value):
    if value in (None, "contract"):
        return None
    if value.startswith("system="):
        sid = value[len("system="):].strip()
        if not sid:
            raise SystemExit("--scope system= needs a system id")
        return sid
    raise SystemExit("--scope takes 'contract' or 'system=<id>', not %r"
                     % value)


def collect(dist, system_id, log):
    """Everything the renderers need, assembled once."""
    parts = {"cb": cb}
    parts["contract"] = contract_mod.build(dist)
    parts["types"] = contract_mod.report_types(dist, parts["contract"])
    parts["pairings"] = contract_mod.report_type_pairings(dist)
    parts["fieldTypes"] = contract_mod.field_types(dist)
    parts["enums"] = enums_mod.build(dist)
    parts["shapes"] = shapes_mod.build(dist, parts["contract"])
    parts["legacyTable"] = shapes_mod.legacy_report_columns(dist)
    parts["recipes"] = recipes_mod.build(dist, None)

    model = None
    if system_id:
        model = entities.build(dist, system_id)
        if model is None:
            known = entities.discover_systems(dist)
            log("system %s is in no artifact dist/ carries." % system_id)
            log("systems dist/ knows about:")
            for s in known:
                log("  %s  %s%s" % (s["systemId"],
                                    (s["captions"] or ["(unnamed)"])[0],
                                    "" if s["authorable"]
                                    else "  [legacy only, not authorable]"))
            log("compiling the contract scope instead, not an empty model.")
    parts["model"] = model
    parts["systemRecipes"] = (recipes_mod.build(dist, model) if model
                              else None)
    return parts


def write_pack(pack, out, log):
    """Write the pack, removing files a previous build left behind."""
    wanted = set(pack.files)
    if os.path.isdir(out):
        for root, _dirs, names in os.walk(out):
            for n in names:
                full = os.path.join(root, n)
                rel = os.path.relpath(full, out)
                if rel not in wanted:
                    os.remove(full)
    for rel, content in sorted(pack.files.items()):
        full = os.path.join(out, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)
    # Drop directories a removed file left empty.
    for root, dirs, names in os.walk(out, topdown=False):
        if not names and not dirs and os.path.abspath(root) != os.path.abspath(out):
            os.rmdir(root)
    log("wrote %d files to %s/" % (len(pack.files), out))


def check_stale(out, dist, log):
    """--check: is the pack on disk still the one dist/ would produce?"""
    manifest = os.path.join(out, "common", "index", "report-pack.json")
    if not os.path.isfile(manifest):
        log("no pack at %s (no common/index/report-pack.json)" % out)
        return 2
    doc = json.load(open(manifest, encoding="utf-8"))
    stale = []
    for row in doc.get("inputs", ()):
        rel = row["path"][len("dist/"):]
        now = dist.hashes.get(rel)
        if now is None:
            stale.append((row["path"], "no longer present in dist/"))
        elif now != row["sha256"]:
            stale.append((row["path"], "changed"))
    for rel in sorted(dist.hashes):
        if not any(r["path"] == "dist/" + rel for r in doc.get("inputs", ())):
            stale.append(("dist/" + rel, "new input, not in the pack"))
    if stale:
        log("the pack is STALE, compiled at %s against dist commit %s:"
            % (doc.get("compiledAt"), doc.get("distCommit")))
        for path, why in stale:
            log("  %-60s %s" % (path, why))
        log("recompile: python3 tools/report_compiler.py --scope %s"
            % doc.get("scope", "contract"))
        return 1
    log("the pack is current: %d inputs, all hashes match."
        % len(doc.get("inputs", ())))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compile dist/ into a report-authoring pack.")
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--out", default="dist-report")
    ap.add_argument("--scope", default="system",
                    help="contract | system=<id> | system (the default: the "
                         "one authorable system, if there is exactly one)")
    ap.add_argument("--validate-recipes", action="store_true",
                    help="lint the recipes and report, writing nothing")
    ap.add_argument("--check", action="store_true",
                    help="only say whether the pack on disk is stale")
    ap.add_argument("--budget-bytes", type=int, default=audit.BUDGET_TOTAL)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    def log(msg):
        if not args.quiet:
            print(msg)

    try:
        dist = load.Dist(args.dist)
    except load.DistError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if dist.missing:
        log("dist/ is missing %d of the inputs this compiler reads: %s"
            % (len(dist.missing), ", ".join(dist.missing)))

    if args.check:
        return check_stale(args.out, dist, log)

    # Default scope is system (decision 1). With no id, take the one
    # authorable system if there is exactly one, and say so.
    scope_arg = args.scope
    if scope_arg == "system":
        authorable = [s for s in entities.discover_systems(dist)
                      if s["authorable"]]
        if len(authorable) == 1:
            scope_arg = "system=" + authorable[0]["systemId"]
            log("scope: %s (the only authorable system dist/ carries)"
                % scope_arg)
        elif not authorable:
            log("no authorable system in dist/ -- no AiExport artifact, so no "
                "selectors. Compiling the contract scope.")
            scope_arg = "contract"
        else:
            print("error: dist/ carries %d authorable systems, so --scope "
                  "system is ambiguous. Pick one:" % len(authorable),
                  file=sys.stderr)
            for s in authorable:
                print("  --scope system=%s   %s"
                      % (s["systemId"], (s["captions"] or ["(unnamed)"])[0]),
                      file=sys.stderr)
            return 2

    system_id = parse_scope(scope_arg)
    parts = collect(dist, system_id, log)
    if system_id and parts["model"] is None:
        system_id = None

    meta = {
        "compiledAt": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%d"),
        "distCommit": dist.dist_commit(),
        "scope": ("system=%s" % system_id) if system_id else "contract",
        "version": __version__,
    }

    if args.validate_recipes and not args.check:
        rc = 0
        for label, built in (("contract", parts["recipes"]),
                             (meta["scope"], parts["systemRecipes"])):
            if built is None:
                continue
            for r in built["recipes"]:
                n_e = len(r["lint"]["errors"])
                n_w = len(r["lint"]["warnings"])
                log("  %-4s %-45s %s  errors=%d warnings=%d  unbound=%s"
                    % (r["id"], r["title"][:45], label, n_e, n_w,
                       ",".join(r["selectorsUnbound"]) or "-"))
                if n_e or n_w:
                    rc = 1
        if rc:
            print("error: a recipe did not lint clean", file=sys.stderr)
            return rc
        log("every recipe lints clean, in every scope.")

    gaps = gaps_mod.Gaps()
    pack = render.build(dist, parts, meta, gaps)
    # The Persian summary quotes the gap count, so it is written once the
    # renderers have finished registering gaps but before the audit runs --
    # otherwise it would escape the provenance and budget checks.
    render.readme_fa(pack, parts, meta, parts["model"],
                     len(gaps) + len(audit.SEEDED))
    findings, results = audit.run(dist, pack, parts, gaps, meta,
                                  args.budget_bytes)

    log("")
    log("  size              %7d bytes of %d  (+%d exempt per-system)"
        % (results["budget"]["totalBytes"], args.budget_bytes,
           results["budget"]["exemptBytes"]))
    log("  grouping          %d of %d writable properties, %d duplicated, "
        "%d drifted" % (results["grouping"]["grouped"],
                        results["grouping"]["writable"],
                        results["grouping"]["duplicated"],
                        results["grouping"]["drift"]))
    for key in ("recipes-contract", "recipes-system"):
        if key in results:
            log("  %-17s %d of %d lint clean"
                % (key, results[key]["clean"], results[key]["recipes"]))
    log("  confidence        published %s, source %s"
        % (results["confidence"]["published"],
           results["confidence"]["sourceLevel"]))
    log("  inference         %d report types carry an affinity, %d grouped "
        "rows" % (results["inference"]["typesWithAffinity"],
                  results["inference"]["groupedRows"]))
    log("  provenance        %d files checked" % results["provenance"]["files"])
    log("  gaps              %d in MISSING-FROM-DIST.md (%d registered by "
        "the renderers, %d seeded)"
        % (results["gaps"]["rendered"], results["gaps"]["gaps"],
           len(audit.SEEDED)))

    if findings:
        print("", file=sys.stderr)
        print("error: %d build gate failure(s); nothing was written."
              % len(findings), file=sys.stderr)
        for f in findings:
            print("  [%s] %s" % (f["check"], f["message"]), file=sys.stderr)
            if f.get("detail"):
                print("        %s" % json.dumps(f["detail"],
                                                ensure_ascii=False)[:400],
                      file=sys.stderr)
        return 1

    write_pack(pack, args.out, log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
