#!/usr/bin/env python3
"""Validate an AiChangeBatch document offline.

Applies the rules read out of Barsa.Meta.SemanticExchange's SemanticV15Linter,
so an authored batch can be checked before it is sent to
BixWriteHelper.ValidateBatch. It is a convenience, not a substitute: the server
also resolves selectors and inspects targets, which needs a live system.

    python3 tools/lint_change_batch.py batch.json
    python3 tools/lint_change_batch.py --schema > ai-change-batch.schema.json
    python3 tools/lint_change_batch.py --example > batch.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_extractor import change_batch as cb


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="AiChangeBatch JSON to validate")
    ap.add_argument("--schema", action="store_true",
                    help="print the JSON Schema and exit")
    ap.add_argument("--example", action="store_true",
                    help="print a worked, rule-clean example and exit")
    args = ap.parse_args()

    if args.schema:
        print(json.dumps(cb.json_schema(), indent=2, ensure_ascii=False))
        return 0
    if args.example:
        print(json.dumps(cb.example(), indent=2, ensure_ascii=False))
        return 0
    if not args.file:
        ap.print_help()
        return 2

    try:
        with open(args.file, encoding="utf-8-sig") as fh:
            doc = json.load(fh)
    except json.JSONDecodeError as exc:
        print("JsonParseError: %s" % exc, file=sys.stderr)
        return 1
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    findings = cb.lint(doc)
    if not findings:
        changes = doc.get("changes") or []
        print("clean: %d command(s), profileVersion %s"
              % (len(changes), doc.get("profileVersion")))
        return 0
    for f in findings:
        print("%-38s %s" % ("[%s]" % f["rule"], f["path"]))
        print("    %s" % f["message"])
    print("\n%d finding(s)." % len(findings))
    return 1


if __name__ == "__main__":
    sys.exit(main())
