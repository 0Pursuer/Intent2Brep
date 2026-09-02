# Roadmap

## v0.4 — visual pipeline foundation (completed)

- provider/service interfaces for T2I and image-to-3D
- OpenAI-compatible T2I adapter
- Hunyuan3D-2.1 official FastAPI adapter
- Hunyuan3D-2mv 1-4 named-view adapter + optional sidecar
- `text2image`, `image2mesh`, `text2mesh`, `views2mesh`, `mesh-info`
- persistent stage manifests and intermediate artifacts
- trimesh hard gate
- DrawingIR/cross-view utilities retained for validation research

## v0.5 — remove legacy text-to-JSON construction path (completed)

- delete PartIntent schema
- delete regex/LLM geometry parser
- delete constraint resolver and domain checks
- delete direct text-driven CadQuery builder
- delete `parametric`, `build`, and `schema` CLI commands
- remove legacy examples and tests
- remove SciPy dependency that existed only for the old constraint resolver
- make documentation and public API visual-only

## v0.6 — mechanical reconstruction benchmark

- 30-100 STEP reference parts rendered from controlled cameras
- compare single-view Hunyuan3D-2.1 vs multi-view Hunyuan3D-2mv vs remote baselines
- Chamfer/Hausdorff/silhouette metrics
- hole, thin-wall, sharp-edge and component-count preservation scores
- deterministic camera/render manifests
- establish pass/fail thresholds before deep CADification work

## v0.7 — CADification primitives

- mesh cleanup without destroying openings
- face-normal + curvature region growing
- robust plane/cylinder/cone/sphere/torus fitting
- analytic-complexity prior
- adjacency graph and sharp-edge extraction
- symmetry / coaxial / coplanar regularization

## v0.8 — raw B-Rep reconstruction

- primitive surface intersections
- trim-curve and loop construction
- wire -> face -> shell -> solid
- sewing and same-domain unification
- BRepCheck hard gate
- STEP export

## v0.9 — verification + feature layer

- HLR reprojection against source/multi-view masks
- geometry residual optimization
- optional canonical feature recognition after B-Rep quality is stable
- SolidWorks/NX/Creo adapters only after analytic B-Rep reconstruction is reliable
