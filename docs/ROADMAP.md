# Roadmap

## v0.1 — deterministic proof of concept
- strict `PartIntent` schema
- constrained Chinese parser
- optional OpenAI-compatible parser
- base/web analytic solids
- circular cuts + base slot
- B-Rep validation
- STEP/BREP export
- exact HLR SVG output

## v0.2 — reliability boundary (implemented)
- fail closed on unsupported requests
- no silent centering of underspecified holes
- explicit `x/y/z` placement in constrained grammar
- pre-kernel geometry-domain checks
- explicit centered/perpendicular constraints in the IR
- schema CLI
- end-to-end CLI smoke test
- 8-test regression suite
- conda environment + GitHub Actions CI

## v0.3 — Structured DrawingIR
- exact projected entity representation, not just raw SVG paths
- line/arc/circle/ellipse/spline entity types
- visible/hidden semantics
- dimension entities + value binding
- view coordinate frames
- cross-view correspondence IDs where known
- import adapter for vectorized SVG engineering drawings
- benchmark adapter for the Zhang et al. 2023 SVG/STEP dataset

## v0.4 — DrawingIR -> 3D wireframe
- candidate 3D vertices from coordinate consistency
- projected-edge compatibility matrix
- graph/branch-and-bound matching
- ambiguity score instead of forced single answers
- human correction hooks

## v0.5 — surface hypothesis engine
- plane first
- cylinder/cone/sphere/torus
- extrusion/revolution surfaces
- NURBS only as fallback
- complexity penalty + projection residual

## v0.6 — raw B-Rep assembler
- loops -> wires -> faces
- surface intersection/trimming
- sewing
- same-domain unification
- topology validation
- HLR back-projection scoring

## v0.7 — human-in-the-loop UI
- text + IR + orthographic views side by side
- edit dimensions/constraints directly
- highlight unresolved/ambiguous entities
- regenerate only affected geometry
