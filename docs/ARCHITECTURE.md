# Architecture

## Target architecture

```text
Natural Language
    -> Geometry Intent Model
    -> Engineering Geometry IR (Pydantic / JSON Schema)
    -> Semantic + domain validation
    -> Constraint Solver
    -> Structured Drawing IR
    -> Cross-view matching
    -> 3D wireframe + surface hypotheses
    -> Analytic B-Rep construction (OpenCASCADE)
    -> Healing / validation
    -> STEP
            ^
            |
      HLR re-projection
      + discrepancy score
```

## What v0.2 implements

v0.2 proves the deterministic half first:

```text
Text
  -> constrained regex parser OR optional OpenAI-compatible LLM parser
  -> strict PartIntent JSON
  -> fail-closed semantic/domain checks
  -> numeric constraint resolver
  -> analytic box/cylinder/slot CSG
  -> OpenCASCADE B-Rep
  -> BRepCheck validation
  -> STEP + native .brep
  -> exact HLR Front/Top/Right/ISO SVG views
```

The orthographic views are generated *from* the resulting B-Rep. They are a validation/inspection interface and a future dataset source, not yet the authoritative input used to reconstruct the B-Rep.

## Safety boundary for geometry generation

The system separates three failure classes:

1. **Underspecified intent** — e.g. a non-centered hole with no coordinates. Reject rather than assume center.
2. **Unsupported intent** — e.g. fillet/chamfer in the current subset. Reject by default rather than omit silently.
3. **Impossible domain geometry** — e.g. a hole larger than the plate. Reject before OpenCASCADE.

This boundary becomes more important after an LLM is connected: syntactically valid JSON is not equivalent to engineering-valid geometry.

## Why not PNG-first

Raster views are useful for human/VLM inspection, but are not authoritative geometry. Exact engineering entities should live in vector/symbolic form because dimensions, tangency, concentricity and hidden-line semantics are not reliably preserved by pixels.

## Planned reconstruction architecture

```text
Front/Top/Right DrawingIR
        -> projected entity graph
        -> cross-view correspondence candidates
        -> 3D vertex/edge hypotheses
        -> ambiguity-aware graph search
        -> loops
        -> surface hypotheses
             plane
             cylinder
             cone
             sphere/torus
             extrusion/revolution
             NURBS fallback only
        -> trim/intersection
        -> wire -> face -> shell -> solid
        -> sewing + same-domain unification
        -> BRepCheck
        -> HLR re-projection score
```

The key research question is not STEP serialization; it is reliable `DrawingIR -> analytic B-Rep` under ambiguity.
