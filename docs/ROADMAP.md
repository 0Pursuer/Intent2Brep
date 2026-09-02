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

## v0.2 — reliability boundary
- fail closed on unsupported requests
- no silent centering of underspecified holes
- explicit `x/y/z` placement in constrained grammar
- pre-kernel geometry-domain checks
- explicit centered/perpendicular constraints in the IR
- schema CLI
- end-to-end CLI smoke test
- regression suite
- conda environment + GitHub Actions CI

## v0.3 — Structured DrawingIR + first cross-view primitive (implemented)
- exact OCCT HLR projected edges exposed as JSON entities
- projector world frame persisted per view
- visible/hidden semantics
- sharp/smooth/outline categories
- analytic curve type preservation (`LINE`, `CIRCLE`, `BSPLINE`, ...)
- exact circle center/radius when available
- sampled fallback for generic curves
- exact visible/hidden overlap de-duplication
- three-view projection-ray intersection
- third-view reprojection verification
- 3D vertex candidate JSON output
- 13-test regression suite

## v0.4 — projected-edge correspondence -> 3D wireframe
- candidate 3D edge generation from reconstructed vertices
- compatibility scoring against all projected entities
- line/arc/circle correspondence rules
- hidden-line-aware matching
- branch-and-bound / graph search for globally consistent edge sets
- ambiguity score instead of forced single answers
- external DrawingIR loader independent of generated B-Rep
- benchmark adapter for the Zhang et al. 2023 SVG/STEP dataset

## v0.5 — surface hypothesis engine
- loop detection
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
