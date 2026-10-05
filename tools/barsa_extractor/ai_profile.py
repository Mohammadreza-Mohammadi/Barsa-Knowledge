"""Reader for the embedded Barsa AI Export Profile.

`AiExportProfileLoader.LoadEmbedded` reads a JSON profile shipped as a manifest
resource inside the assembly.  That profile is the authoritative, machine
readable description of the AiExport format: which Barsa record types are
exported, which legacy table each one comes from, how every field is treated,
which enums are spelled out, which binary columns have decoders, and how the
ZIP package is laid out.

Reading it is better evidence than a sample: a sample shows one system, the
profile states the rules.
"""

import json

from .cli_metadata import (
    Assembly, NotManagedError, manifest_resource_blob, manifest_resource_names,
)

PROFILE_MARKER = "ai-export-profile"

# Field rules are either a bare string verb or an object of modifiers.
FIELD_VERBS = ("keep", "omit")


class AiExportProfile:
    """One parsed profile resource."""

    def __init__(self, assembly_name, resource_name, raw):
        self.assembly = assembly_name
        self.resource = resource_name
        self.raw_size = len(raw)
        self.is_schema = resource_name.endswith(".schema.json")
        self.doc = json.loads(raw.decode("utf-8-sig"))
        self.profile_version = self.doc.get("profileVersion")
        if self.is_schema:
            self.profile_version = (
                self.doc.get("properties", {})
                .get("profileVersion", {})
                .get("const", self.profile_version))

    # -- sections -----------------------------------------------------------

    @property
    def engine(self):
        return self.doc.get("engine") or {}

    @property
    def packaging(self):
        return self.doc.get("packaging") or {}

    @property
    def record_types(self):
        return self.doc.get("recordTypes") or {}

    @property
    def serialized_types(self):
        return self.doc.get("serializedTypes") or {}

    @property
    def enums(self):
        return self.doc.get("enums") or {}

    @property
    def binary_decoders(self):
        return self.doc.get("binaryDecoders") or {}

    # -- derived views ------------------------------------------------------

    def record_type_rows(self):
        """One row per exported record type, with its legacy table."""
        out = []
        for name, rule in sorted(self.record_types.items()):
            if not isinstance(rule, dict):
                continue
            fields = rule.get("fields") or {}
            out.append({
                "recordType": name,
                "legacyTable": rule.get("table"),
                "output": rule.get("output"),
                "fieldCount": len(fields),
                "keptFields": sorted(
                    k for k, v in fields.items() if _is_kept(v)),
                "omittedFields": sorted(
                    k for k, v in fields.items() if v == "omit"),
                "referenceFields": sorted(
                    k for k, v in fields.items()
                    if isinstance(v, dict) and "reference" in v),
                "enumFields": sorted(
                    (k, v.get("enum")) for k, v in fields.items()
                    if isinstance(v, dict) and "enum" in v),
                "decoderFields": sorted(
                    (k, v.get("decoder")) for k, v in fields.items()
                    if isinstance(v, dict) and "decoder" in v),
                "transformFields": sorted(
                    (k, v.get("transform")) for k, v in fields.items()
                    if isinstance(v, dict) and "transform" in v),
            })
        return out

    def legacy_table_map(self):
        """recordType -> legacy DataSet table, as the profile declares it."""
        return {name: rule.get("table")
                for name, rule in sorted(self.record_types.items())
                if isinstance(rule, dict) and rule.get("table")}

    def decoder_targets(self):
        """Which (recordType, field) pairs route through a binary decoder."""
        out = []
        for name, rule in sorted(self.record_types.items()):
            if not isinstance(rule, dict):
                continue
            for field, fr in sorted((rule.get("fields") or {}).items()):
                if isinstance(fr, dict) and fr.get("decoder"):
                    out.append({
                        "recordType": name,
                        "field": field,
                        "decoder": fr["decoder"],
                        "implementation": (self.binary_decoders
                                           .get(fr["decoder"], {})
                                           .get("implementation")),
                    })
        return out

    def packaging_rules(self):
        pk = self.packaging
        return {
            "systemRecordFile": pk.get("systemRecordFile"),
            "unmappedRecordsFile": pk.get("unmappedRecordsFile"),
            "includeUnmappedRecords": pk.get("includeUnmappedRecords"),
            "relationGroups": pk.get("relationGroups") or [],
            "relationFiles": pk.get("relationFiles") or [],
            "omitRelations": pk.get("omitRelations") or [],
        }

    def summary(self):
        return {
            "assembly": self.assembly,
            "resource": self.resource,
            "isSchema": self.is_schema,
            "profileVersion": self.profile_version,
            "sizeBytes": self.raw_size,
            "recordTypes": len(self.record_types),
            "serializedTypes": len(self.serialized_types),
            "enums": len(self.enums),
            "binaryDecoders": len(self.binary_decoders),
            "relationGroups": len(self.packaging.get("relationGroups") or []),
        }


def _is_kept(rule):
    if rule == "keep":
        return True
    return isinstance(rule, dict)


def discover_profiles(assembly_paths):
    """Pull every embedded ai-export-profile resource out of the assemblies."""
    found = []
    errors = []
    for path in assembly_paths:
        try:
            asm = Assembly(path)
        except (NotManagedError, Exception):
            continue
        try:
            names = manifest_resource_names(asm)
        except Exception:
            continue
        for name in names:
            if PROFILE_MARKER not in name:
                continue
            try:
                blob = manifest_resource_blob(asm, name)
                if not blob:
                    continue
                info = asm.assembly_info() or {}
                found.append(AiExportProfile(
                    info.get("name") or path.split("/")[-1], name, blob))
            except Exception as exc:
                errors.append({"assembly": path, "resource": name,
                               "error": "%s: %s" % (type(exc).__name__, exc)})
    found.sort(key=lambda p: (p.assembly, p.resource))
    return found, errors


def executable_profile(profiles):
    """The profile the runtime will actually accept.

    `AiExportProfileLoader.Validate` rejects anything but profileVersion 15,
    so among the embedded profiles only the v15 document is executable input.
    The v14 copy is retained in the assembly and is reported as historical.
    """
    live = [p for p in profiles if not p.is_schema and p.profile_version == 15]
    return live[0] if live else None
