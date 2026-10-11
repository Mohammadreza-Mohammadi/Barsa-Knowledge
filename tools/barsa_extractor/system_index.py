"""Full, evidence-preserving per-system indexes from normalized exports.

An export may contain several systems. Rows without a proven owner are left out
of a system index and counted as unassigned; they must never be attached by
caption or by the first 25 rows of an artifact.
"""

from .normalize import EMPTY_ENVELOPE_KEYS


def build(legacy, ai):
    indexes = {}
    for env in [*legacy, *ai]:
        systems = {str(s["id"]): s for s in env.get("system") or ()
                   if s.get("id")}
        if not systems:
            continue
        single = len(systems) == 1
        entities = env.get("entities") or []
        entity_system = {str(e["id"]): str(e["systemId"])
                         for e in entities if e.get("id") and e.get("systemId")}
        if single:
            only = next(iter(systems))
            entity_system.update({str(e["id"]): only for e in entities
                                  if e.get("id")})
        folder_system = _folder_owners(env.get("navigation") or [], systems)
        source = env.get("_source") or {}

        for sid, system in systems.items():
            index = indexes.setdefault(sid, {
                "schemaVersion": "1.0", "systemId": sid,
                "systems": [], "sources": [],
                "collections": {k: [] for k in EMPTY_ENVELOPE_KEYS
                                if k != "system"},
            })
            index["systems"].append(system)
            counts = {}
            for coll in index["collections"]:
                rows = env.get(coll)
                if rows is None:
                    counts[coll] = {"available": False, "artifactRows": None,
                                    "assignedRows": None}
                    continue
                selected = [r for r in rows if _belongs(
                    coll, r, sid, single, entity_system, folder_system)]
                index["collections"][coll].extend(selected)
                counts[coll] = {"available": True,
                                "artifactRows": len(rows),
                                "assignedRows": len(selected)}
            index["sources"].append({
                "file": source.get("file"), "format": source.get("format"),
                "sha256": source.get("sha256"), "counts": counts,
            })
    for index in indexes.values():
        index["counts"] = {k: len(v) for k, v in index["collections"].items()}
        index["completeFromAvailableEvidence"] = True
        index["note"] = ("Every assignable normalized row is retained. A "
                         "multi-system artifact can also contain rows whose "
                         "owner is not evidenced; source counts expose that "
                         "limit instead of assigning them by name.")
    return indexes


def _folder_owners(rows, systems):
    """Legacy navigation belongs to the system whose rootFolderId reaches it."""
    owners = {str(s["rootFolderId"]): sid for sid, s in systems.items()
              if s.get("rootFolderId")}
    pending = {str(r["id"]): r for r in rows if r.get("id")}
    changed = True
    while changed:
        changed = False
        for fid, row in pending.items():
            parent = owners.get(str(row.get("parentId")))
            if parent and owners.get(fid) != parent:
                owners[fid] = parent
                changed = True
    return owners


def _belongs(coll, row, sid, single, entity_system, folder_system):
    if single:
        return True
    if row.get("systemId") is not None:
        return str(row["systemId"]) == sid
    if coll == "entities":
        return entity_system.get(str(row.get("id"))) == sid
    if coll in ("fields", "views", "businessRules", "workflows"):
        owner = row.get("entityId") or row.get("_ownerId")
        return entity_system.get(str(owner)) == sid
    if coll == "relationDefs":
        owners = (row.get("sourceEntity"), row.get("targetEntity"),
                  row.get("entityId"), row.get("_ownerId"))
        return any(entity_system.get(str(o)) == sid for o in owners if o)
    if coll == "navigation":
        return folder_system.get(str(row.get("id"))) == sid
    if coll in ("code", "commands", "webServices"):
        return entity_system.get(str(row.get("targetObjectId") or
                                     row.get("targetId") or
                                     row.get("_ownerId"))) == sid
    return False
