# Selectors

> **Source:** dist/formats/ai-export.md · dist/formats/ai-change-batch.md · dist/comparison/match-report.md
> **dist commit:** 427c93cf67edea701b8874a816924f4c31a8d2bb
> **compiled:** 2026-10-06 · **scope:** system=1011413550000000100

In an `AiChangeBatch`, a selector is the **only** way to refer to an object that already exists. Runtime identity is forbidden.

## The form

```text
#Name                a single '#' followed by the object's name
#[Name]              bracketed, when a component needs escaping
```

Written and read by `SemanticSelectorCodec`. The bracketed form is the codec's escape path, not the normal case: in the supplied artifacts every selector is the plain `#Name` form.

## Keys that are forbidden

`id`, `rowId`, `sourceId`, `runtimeId`, `dependencyKey`. A batch carrying any of them is rejected by the linter before anything else happens -- this is a structural rule, not a convention.

## Referring to something created in the same batch

Use `tempId` on the creating command and `{"tempId": "..."}` where the reference is needed. The planner collects temp references into its dependency graph and sorts commands accordingly.

## The letter trap

This is the most common way a correct-looking selector fails to resolve.

Arabic and Persian letter forms are mixed in this data. `ي` (U+064A, Arabic yeh) and `ی` (U+06CC, Farsi yeh) look nearly identical in most fonts, as do `ك` (U+0643) and `ک` (U+06A9). The same object is spelled one way in a legacy export and the other in an AiExport -- the Extractor has to fold these letters before it can match an object across the two families.

A selector is matched by name. A selector typed with the wrong yeh will not resolve, and the failure says the object does not exist.

**So: copy selectors, never type them.** In a system-scoped pack, `systems/<id>/index/selectors.json` carries them verbatim. Copy the string.

## Scope

A selector is resolved within a scope -- a field selector under its entity, a report selector under its system. The same name under a different entity is a different object, so a selector is not globally unique.
