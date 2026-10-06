#!/usr/bin/env python3
"""Retrieve bounded report context from a full dist/ system index.

Search returns candidates, never an asserted semantic identity. Copy a
selector from a returned row only after checking its owner and provenance.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_report_compiler import entities, load

COLLECTIONS = {
    "entity": "entities", "field": "fields", "report": "reports",
    "view": "views", "folder": "folders", "relation": "relationDefs",
}


def _fold(value):
    return str(value or "").replace("ي", "ی").replace("ك", "ک").casefold()


def retrieve(dist, system_id, kind, query=None, offset=0, limit=25):
    model = entities.build(dist, system_id)
    if model is None:
        raise ValueError("unknown system: %s" % system_id)
    rows = model[COLLECTIONS[kind]]
    if query:
        needle = _fold(query)
        keys = ("id", "selector", "caption", "name", "dbName", "path",
                "entityCaption")
        exact = [r for r in rows if any(needle == _fold(r.get(k)) for k in keys)]
        rows = exact or [r for r in rows
                         if any(needle in _fold(r.get(k)) for k in keys)]
    return {
        "systemId": system_id, "kind": kind, "query": query,
        "matchSemantics": "candidate search; verify owner and provenance",
        "totalMatches": len(rows), "offset": offset, "limit": limit,
        "rows": rows[offset:offset + limit],
        "source": "dist/index/systems/%s/semantic.json" % system_id,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--system", required=True)
    ap.add_argument("--kind", choices=sorted(COLLECTIONS), required=True)
    ap.add_argument("--query")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args(argv)
    if args.offset < 0 or not 1 <= args.limit <= 100:
        ap.error("offset must be nonnegative and limit must be 1..100")
    try:
        result = retrieve(load.Dist(args.dist), args.system, args.kind,
                          args.query, args.offset, args.limit)
    except (load.DistError, ValueError) as exc:
        ap.error(str(exc))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
