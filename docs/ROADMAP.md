# Roadmap

## v0.1-v0.3 — parametric baseline + DrawingIR (completed)

- strict PartIntent schema and constrained parser
- deterministic CadQuery/OpenCASCADE construction
- BRepCheck + STEP/BREP export
- exact HLR views and DrawingIR
- three-view projection-ray 3D vertex candidates

## v0.4 — visual-first architectural pivot (implemented)

- retain v0.3 as `parametric` baseline
- provider/service interfaces for T2I and image-to-3D
- OpenAI-compatible T2I adapter
- Hunyuan3D-2.1 official FastAPI adapter
- Hunyuan3D-2mv 1-4 named-view adapter + optional sidecar
- `text2image`, `image2mesh`, `text2mesh`, `views2mesh`, `mesh-info` CLI
- reconstruction-friendly mechanical visual prompt
- persistent stage manifest/intermediate outputs
- trimesh hard gate: topology, watertightness, extents, area, volume
- fake-provider regression tests; no GPU model required by CI

## v0.5 — mechanical reconstruction benchmark

- 30-100 STEP reference parts rendered from controlled cameras
- compare single-view Hunyuan3D-2.1 vs 1-4-view Hunyuan3D-2mv vs cloud model
- Chamfer/Hausdorff/silhouette metrics
- hole, thin-wall, sharp-edge and component-count preservation scores
- deterministic camera/render manifest
- establish a pass/fail threshold before investing in CADification

## v0.6 — CADification primitives

- mesh cleanup without destroying openings
- face-normal + curvature region growing
- robust plane/cylinder/cone/sphere/torus fitting
- analytic-complexity prior (simple primitives before freeform)
- adjacency graph and sharp-edge extraction
- engineering symmetry / coaxial / coplanar regularization

## v0.7 — raw B-Rep reconstruction

- primitive surface intersections
- trim-curve and loop construction
- wire -> face -> shell -> solid
- sewing and same-domain unification
- BRepCheck hard gate
- STEP export

## v0.8 — verification + feature layer

- HLR reprojection against source/multi-view masks
- geometry residual optimization
- canonical feature recognition/reconstruction as an optional final layer
- SolidWorks/NX/Creo adapters only after analytic B-Rep quality is stable
