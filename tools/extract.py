#!/usr/bin/env python3
"""Entry point: python3 tools/extract.py [--source DIR] [--dist DIR]"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barsa_extractor.pipeline import Extractor


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=os.path.join(repo, "source"))
    ap.add_argument("--dist", default=os.path.join(repo, "dist"))
    ap.add_argument("--exports", action="append", default=None,
                    help="extra directory of export artifacts; repeatable. "
                         "Defaults to <repo>/exports when that exists.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    extra = args.exports
    if extra is None:
        default_exports = os.path.join(repo, "exports")
        extra = [default_exports] if os.path.isdir(default_exports) else []

    if not os.path.isdir(args.source):
        sys.exit("no such source directory: %s" % args.source)

    log = (lambda *a: None) if args.quiet else \
        (lambda msg: print(msg, flush=True))
    ex = Extractor(args.source, args.dist, log=log, extra_roots=extra)
    report = ex.run()
    log("done in %ss -> %s" % (report["elapsedSeconds"], args.dist))
    return 0 if all(c["pass"] for c in report["validation"]) else 1


if __name__ == "__main__":
    sys.exit(main())
