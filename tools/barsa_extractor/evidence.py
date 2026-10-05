"""Evidence ledger: stable IDs, sources and confidence levels (spec sections 4, 5, 51)."""

CONFIDENCE_ORDER = ["CrossVerified", "Verified", "Observed", "Inferred", "Unknown"]

SOURCES = {
    "AssemblyMetadata", "IL", "DecompiledCode", "StringLiteral", "CallGraph",
    "SQLLiteral", "ConfigLiteral", "ExportSample", "ExporterCode",
    "ImporterCode", "MRTSample", "UserProvided", "Inference",
}

_PREFIX = {
    "AssemblyMetadata": "DLL", "IL": "DLL", "CallGraph": "DLL",
    "StringLiteral": "DLL", "SQLLiteral": "DLL", "ConfigLiteral": "CFG",
    "ExportSample": "EXP", "ExporterCode": "EXR", "ImporterCode": "IMP",
    "DecompiledCode": "DEC", "MRTSample": "MRT", "UserProvided": "USR",
    "Inference": "INF",
}


class Ledger:
    """Allocates deterministic EVID-* identifiers and keeps them addressable."""

    def __init__(self):
        self._items = {}
        self._counters = {}
        self._by_key = {}

    def add(self, source, detail, locator=None):
        if source not in SOURCES:
            raise ValueError("unknown evidence source: %s" % source)
        key = (source, detail, locator)
        if key in self._by_key:
            return self._by_key[key]
        prefix = _PREFIX[source]
        n = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = n
        eid = "EVID-%s-%06d" % (prefix, n)
        self._items[eid] = {
            "id": eid,
            "source": source,
            "detail": detail,
            "locator": locator,
        }
        self._by_key[key] = eid
        return eid

    def get(self, eid):
        return self._items.get(eid)

    def all(self):
        return [self._items[k] for k in sorted(self._items)]


def combine(*confidences):
    """Weakest-link rule for a fact resting on several sub-facts."""
    worst = "CrossVerified"
    for c in confidences:
        if c not in CONFIDENCE_ORDER:
            c = "Unknown"
        if CONFIDENCE_ORDER.index(c) > CONFIDENCE_ORDER.index(worst):
            worst = c
    return worst


def from_source_count(sources):
    """Two or more independent source families -> CrossVerified (spec 4)."""
    families = set()
    for s in sources:
        if s in ("AssemblyMetadata", "IL", "CallGraph", "StringLiteral",
                 "SQLLiteral", "DecompiledCode"):
            families.add("binary")
        elif s in ("ExportSample", "MRTSample"):
            families.add("sample")
        elif s in ("ExporterCode", "ImporterCode"):
            families.add("exchangeCode")
        elif s == "ConfigLiteral":
            families.add("config")
        elif s == "Inference":
            families.add("inference")
    if "inference" in families and len(families) == 1:
        return "Inferred"
    families.discard("inference")
    if len(families) >= 2:
        return "CrossVerified"
    if families:
        return "Verified"
    return "Unknown"
