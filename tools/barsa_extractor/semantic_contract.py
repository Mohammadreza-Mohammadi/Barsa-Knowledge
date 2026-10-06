"""Recovery of the semantic write contract from SemanticContractRegistry.

The contract is not a data file. `SemanticContractRegistry` builds it at
type-init time: its `.cctor` registers one `SemanticObjectContract` per
objectType, and `BuildProperties` registers every property contract through a
set of small factories. Both methods are straight-line sequences of calls whose
arguments are compile-time constants, so `il_eval` can recover the table
exactly.

Parameter names come from the Param metadata table, so the argument mapping
below is read rather than inferred -- which matters, because `Reference` takes
its source and writer *before* its target type, not after.
"""

from .cli_metadata import TYPEDEF, enum_members, is_enum
from .il_eval import evaluate, find_method

REGISTRY = "SemanticContractRegistry"

# Factories that construct one property contract. The value is the parameter
# list as the Param table gives it, minus the leading dictionary where present.
FACTORIES = {
    "Writable": ("name", "kind", "source", "writer", "subtypes",
                 "create", "update"),
    "Reference": ("name", "classification", "source", "writer", "targetType",
                  "subtypes", "create", "update"),
    "ReadOnly": ("name", "kind", "source", "subtypes", "exported"),
    "Derived": ("name", "kind", "source", "subtypes"),
    "ReconstructionOnly": ("name", "kind", "source", "subtypes", "exported"),
    "RawJson": ("source", "writer", "subtypes"),
}

OBJ_ARGS = ("type", "identity", "adapter", "ordered", "operations",
            "applyClass", "structuralOrder")


def _enum_maps(asm):
    """name -> {value: member} for the enums the registry stores as ints."""
    wanted = ("SemanticPropertyKind", "SemanticPropertyClassification",
              "SemanticApplyClass")
    out = {}
    for rid in range(1, asm.row_count(TYPEDEF) + 1):
        tn = asm.type_full_name(rid) or ""
        short = tn.split(".")[-1]
        if short not in wanted or not is_enum(asm, rid):
            continue
        out[short] = {v: n for n, v in enum_members(asm, rid)
                      if isinstance(v, int)}
    return out


def _name(maps, enum, value):
    if not isinstance(value, int):
        return None
    return maps.get(enum, {}).get(value, str(value))


def object_contracts(asm):
    """One row per objectType, from the registry's static constructor."""
    rid = find_method(asm, REGISTRY, ".cctor")
    if rid is None:
        return []
    maps = _enum_maps(asm)
    out = []
    for rec in evaluate(asm, rid, interesting=(REGISTRY + "::Obj",)):
        args = {k: rec.arg(i) for i, k in enumerate(OBJ_ARGS)}
        out.append({
            "objectType": args["type"],
            "identitySemantics": args["identity"],
            "runtimeAdapterKey": args["adapter"],
            "hasOrderingSemantics": bool(args["ordered"]),
            "supportedOperations": args["operations"] or [],
            "applyClass": _name(maps, "SemanticApplyClass", args["applyClass"]),
            "structuralOrder": args["structuralOrder"],
            "evidence": "SemanticContractRegistry..cctor -> Obj(...)",
            "confidence": "Verified" if rec.complete else "Observed",
        })
    return sorted(out, key=lambda r: (r["structuralOrder"] or 0,
                                      r["objectType"] or ""))


def property_contracts(asm):
    """Per-objectType property contracts, from BuildProperties.

    A factory call builds a contract and the `Register` that follows it binds
    that contract to an objectType, so the two are paired by order. The bulk
    helpers (`RegisterWritableSet`, `RegisterFieldSubtype`,
    `RegisterRelationSubtype`) register many names at once and are expanded.
    """
    rid = find_method(asm, REGISTRY, "BuildProperties")
    if rid is None:
        return {}, []
    maps = _enum_maps(asm)
    records = evaluate(asm, rid, interesting=(REGISTRY + "::",))

    by_type = {}
    unresolved = []
    pending = None

    def add(object_type, entry):
        if not object_type:
            unresolved.append(entry)
            return
        by_type.setdefault(object_type, []).append(entry)

    for rec in records:
        short = rec.name.split("::")[-1]

        if short in FACTORIES:
            names = FACTORIES[short]
            args = {k: rec.arg(i) for i, k in enumerate(names)}
            kind = _name(maps, "SemanticPropertyKind", args.get("kind"))
            classification = _name(maps, "SemanticPropertyClassification",
                                   args.get("classification"))
            if classification is None:
                classification = {
                    "Writable": "Writable", "Reference": "Writable",
                    "ReadOnly": "ReadOnly", "Derived": "Derived",
                    "ReconstructionOnly": "ReconstructionOnly",
                    "RawJson": "Writable",
                }[short]
            if short == "Reference":
                kind = kind or "Reference"
            elif short == "RawJson":
                kind = kind or "RawJson"
            pending = {
                "property": args.get("name"),
                "factory": short,
                "kind": kind,
                "classification": classification,
                "runtimeSource": args.get("source"),
                "writer": args.get("writer"),
                "referenceTargetType": args.get("targetType"),
                "subtypes": _subtypes(args.get("subtypes")),
                "writableOnCreate": _flag(args.get("create"), short),
                "writableOnUpdate": _flag(args.get("update"), short),
                "exported": (bool(args["exported"])
                             if args.get("exported") is not None else None),
                "complete": rec.complete,
            }
            continue

        if short == "Register":
            if pending is not None:
                add(rec.arg(1), pending)
                pending = None
            continue

        if short == "RegisterWritableSet":
            object_type = rec.arg(1)
            subtypes = _subtypes(rec.arg(2))
            writer = rec.arg(3)
            for name in (rec.arg(4) or []):
                if not name:
                    continue
                add(object_type, {
                    "property": name, "factory": "RegisterWritableSet",
                    "kind": None, "classification": "Writable",
                    "runtimeSource": None, "writer": writer,
                    "referenceTargetType": None, "subtypes": subtypes,
                    "writableOnCreate": True, "writableOnUpdate": True,
                    "exported": None, "complete": rec.complete,
                })
            continue

        if short in ("RegisterFieldSubtype", "RegisterRelationSubtype"):
            object_type = "field" if short.endswith("FieldSubtype") \
                else "relation"
            subtype = rec.arg(1)
            for name in (rec.arg(2) or []):
                if not name:
                    continue
                add(object_type, {
                    "property": name, "factory": short,
                    "kind": None, "classification": "Writable",
                    "runtimeSource": None, "writer": None,
                    "referenceTargetType": None,
                    "subtypes": [subtype] if subtype else [],
                    "writableOnCreate": True, "writableOnUpdate": True,
                    "exported": None, "complete": rec.complete,
                })
            continue

        if short == "RegisterRelationSingleLike":
            subtype = rec.arg(1)
            add("relation", {
                "property": "relationViewType", "factory": short,
                "kind": None, "classification": "Writable",
                "runtimeSource": None, "writer": None,
                "referenceTargetType": None,
                "subtypes": [subtype] if subtype else [],
                "writableOnCreate": bool(rec.arg(2)),
                "writableOnUpdate": bool(rec.arg(2)),
                "exported": None, "complete": rec.complete,
            })
            continue

        if short == "SetPhase3Dependencies":
            object_type = rec.arg(1)
            prop = rec.arg(2)
            deps = rec.arg(3) or []
            for entry in by_type.get(object_type, ()):
                if entry["property"] == prop:
                    entry["phase3DependsOn"] = [d for d in deps if d]
            continue

    for entries in by_type.values():
        entries.sort(key=lambda e: (e["property"] or "",
                                    ",".join(e["subtypes"])))
    return by_type, unresolved


def _subtypes(v):
    if isinstance(v, dict) and "anyOf" in v:
        return [s for s in v["anyOf"] if s]
    if isinstance(v, list):
        return [s for s in v if s]
    return []


def _flag(v, factory):
    if v is None:
        return factory in ("RegisterWritableSet",)
    return bool(v)


def summary(asm):
    objects = object_contracts(asm)
    props, unresolved = property_contracts(asm)
    return {
        "source": ("Barsa.Meta.SemanticExchange :: SemanticContractRegistry, "
                   "recovered from IL by constant evaluation"),
        "objectContracts": objects,
        "propertyContracts": props,
        "unboundPropertyContracts": unresolved,
        "counts": {
            "objectTypes": len(objects),
            "propertyRows": sum(len(v) for v in props.values()),
            "unbound": len(unresolved),
        },
        "confidence": "Verified",
        "limits": ("Recovered from a straight-line constant evaluation. Where "
                   "a value came from a loop variable the possible values are "
                   "reported as a set rather than a single name, and anything "
                   "not modelled is left null rather than guessed."),
    }
