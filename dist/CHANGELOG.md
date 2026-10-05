# Changelog

## 2.0 — initial knowledge pack

Produced by `tools/barsa_extractor` against the inputs then present in `source/`.

- Pure-Python ECMA-335 reader; 364 managed assemblies parsed,
  12 native PEs identified.
- 219200 types and 386140 methods indexed.
- 2 `.metaexport` packages decoded without executing Barsa code.
- Export/import symmetry established across binary and sample evidence.
- `$IdEmbeddingFields` identified as the package-carried ID remap instruction set.

### Re-running

```
python3 tools/extract.py
```

Incremental state is written to `dist/index/knowledge-index.json`
(`inputHashes`); a later run can compare SHA-256, MVID and assembly version to
re-analyse only what changed.
