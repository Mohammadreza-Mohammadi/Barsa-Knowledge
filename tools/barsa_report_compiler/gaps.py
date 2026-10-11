"""The gap register behind MISSING-FROM-DIST.md.

Spec section 22: the file is generated, not maintained by hand. Every place a
renderer had to write Unknown adds a row here, so the register cannot drift
from what the pack actually says.
"""


class Gaps:
    def __init__(self):
        self._rows = {}

    def add(self, topic, needed_for, where, evidence, blocks=None):
        """Record one thing the report task needs that dist/ does not carry.

        topic       what is missing, in a few words
        needed_for  which part of the pack had to write Unknown without it
        where       where the Extractor should go looking -- a method, a
                    profile rule, or an artifact that would have to be supplied
        evidence    why we can say it is absent rather than merely unseen
        blocks      what a consumer cannot do until it is filled
        """
        row = self._rows.setdefault(topic, {
            "topic": topic,
            "neededFor": [],
            "whereToLook": where,
            "evidenceOfAbsence": evidence,
            "blocks": blocks,
        })
        if needed_for not in row["neededFor"]:
            row["neededFor"].append(needed_for)
        if blocks and not row["blocks"]:
            row["blocks"] = blocks
        return row

    def rows(self):
        return [self._rows[k] for k in sorted(self._rows)]

    def __len__(self):
        return len(self._rows)
