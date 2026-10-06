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
    ap.add_argument("--contract", metavar="PATH",
                    help="semantic-contract.json; defaults to the generated "
                         "dist/index/semantic-contract.json when present")
    ap.add_argument("--no-contract", action="store_true",
                    help="skip the property check and apply only the "
                         "SemanticV15Linter rules")
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

    contract = None if args.no_contract else cb.load_contract(args.contract)
    findings = cb.lint(doc, contract)
    errors = [f for f in findings if f.get("severity") != "warning"]
    warnings = [f for f in findings if f.get("severity") == "warning"]

    if contract is None and not args.no_contract:
        print("note: no semantic contract found, so properties were not "
              "checked. Run tools/extract.py to generate it.\n")

    for f in errors + warnings:
        label = "[%s %s]" % (f.get("severity", "error"), f["rule"])
        print("%-46s %s" % (label, f["path"]))
        print("    %s" % f["message"])

    if not findings:
        print("clean: %d command(s), profileVersion %s"
              % (len(doc.get("changes") or []), doc.get("profileVersion")))
        return 0
    print("\n%d error(s), %d warning(s)." % (len(errors), len(warnings)))
    # A warning is a contract-check finding, which the server raises later as
    # unsupportedProperty rather than at lint time, so it does not fail here.
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
