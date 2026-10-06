"""Report Designer Knowledge Compiler.

Compiles the general-purpose knowledge pack in `dist/` down to a small pack
aimed at one task: authoring and understanding Barsa reports.

Hard boundary (spec section 1): this compiler reads `dist/` and never
`source/`. Anything the report task needs that `dist/` lacks is a gap in the
Extractor, recorded in MISSING-FROM-DIST.md rather than worked around.
"""

__version__ = "1.0"
