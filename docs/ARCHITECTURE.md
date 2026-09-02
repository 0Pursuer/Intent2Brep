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

## What v0.3 implements

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
  -> exact HLR Front/Top/Right/ISO projections
  -> DrawingIR JSON
       * projector world basis
       * visible/hidden
       * sharp/smooth/outline
       * LINE/CIRCLE/BSPLINE/... geometry class
       * endpoints, curve length, circle center/radius, sampled fallback
  -> three-view projection-ray intersection
  -> verified 3D vertex candidates
```

The DrawingIR is currently generated *from* the resulting B-Rep. This gives a controlled round-trip benchmark and a dataset-generation path. It does **not** mean general engineering drawings can already be reconstructed into B-Rep.

## Safety boundary for geometry generation

The system separates three failure classes:

1. **Underspecified intent** — e.g. a non-centered hole with no coordinates. Reject rather than assume center.
2. **Unsupported intent** — e.g. fillet/chamfer in the current subset. Reject by default rather than omit silently.
3. **Impossible domain geometry** — e.g. a hole larger than the plate. Reject before OpenCASCADE.

This boundary becomes more important after an LLM is connected: syntactically valid JSON is not equivalent to engineering-valid geometry.

## DrawingIR design

The HLR projector defines an orthographic 2D coordinate frame. Every view stores:

- `origin_world`
- `projection_direction`
- `x_axis_world`
- `y_axis_world`

A 2D point `(u, v)` therefore represents the world-space projection ray:

```text
P(t) = origin + u*x_axis + v*y_axis + t*projection_direction
```

This explicit frame avoids hard-coding assumptions such as "front means XZ". It also makes cross-view reconstruction generic for any orthographic view direction.

HLR result categories are converted into structured entities. Exact coincident visible/hidden duplicates are de-duplicated with visible geometry taking precedence.

## Cross-view vertex reconstruction in v0.3

For each non-closed projected entity endpoint:

1. form its world-space projection ray;
2. intersect rays from two views;
3. reject pairs whose closest-point distance exceeds tolerance;
4. re-project the candidate into a third view;
5. accept only candidates landing on a third-view endpoint;
6. merge spatial duplicates.

For a simple rectangular box, this recovers exactly the eight true 3D corners without reading original B-Rep vertex positions.

This stage reconstructs **vertices only**. It does not yet determine which projected edges correspond to which 3D edges.

## Why not PNG-first

Raster views are useful for human/VLM inspection, but are not authoritative geometry. Exact engineering entities should live in vector/symbolic form because dimensions, tangency, concentricity and hidden-line semantics are not reliably preserved by pixels.

## Next reconstruction architecture

```text
External Front/Top/Right DrawingIR
        -> projected entity graph
        -> cross-view vertex candidates        [v0.3 primitive exists]
        -> projected-edge compatibility matrix [next]
        -> ambiguity-aware edge graph search
        -> 3D wireframe
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

The key research question remains reliable `DrawingIR -> analytic B-Rep` under ambiguity.
