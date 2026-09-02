# Technical survey and project decisions (2026-09)

Intent2Brep is now exclusively a **visual-first 2D/multi-view -> 3D -> engineering CAD** project.

The package no longer contains a route where a language model or regex parser emits complete geometry JSON and a CAD builder executes it.

## Current technology map

| Stage | Problem | Current/reference technology | Intent2Brep choice | Maturity |
|---|---|---|---|---|
| Text -> visual proposal | turn natural-language shape intent into a reconstruction-friendly image | modern T2I systems such as HunyuanImage / FLUX / hosted image APIs | model-agnostic T2I provider; rendering prompt only | High for visual fidelity |
| Single image -> 3D | infer coarse 3D geometry from one image | Hunyuan3D-2.1, TripoSG, TRELLIS-class systems | HTTP adapter for Hunyuan3D-2.1 | High enough for experiments; not CAD-accurate |
| Multi-view -> 3D | reduce hidden-side ambiguity | Hunyuan3D-2mv and related multi-view reconstruction | 1-4 named-view adapter + isolated sidecar | Medium-high and rapidly improving |
| Visual 3D representation | preserve model output before CAD assumptions | mesh / SDF / sparse voxels / learned 3D latent | persist raw GLB plus deterministic mesh statistics | High for graphics |
| Mechanical cleanup | preserve holes, thin walls, sharp edges and topology | topology-aware mesh processing | next milestone | Medium |
| Analytic primitive recovery | recover plane/cylinder/cone/sphere/torus rather than fragmented freeform patches | robust fitting, region growing, RANSAC/least squares; learned B-Rep research | planned primitive hypothesis engine with complexity prior | Medium |
| Engineering regularization | impose coplanar/coaxial/symmetric/equal-radius relations on recovered geometry | constrained geometric optimization | planned post-3D optimization | Medium |
| Raw B-Rep assembly | intersections, trim loops, faces, shells, solids | OpenCASCADE/OCP | planned after primitive recovery | Kernel mature; inference boundary hard |
| Healing / simplification | sew gaps and merge same-domain fragments | OCCT ShapeFix/Sewing/UnifySameDomain | planned downstream hardening | Very high |
| Validation | reject invalid geometry and compare reconstructions | mesh metrics, BRepCheck, HLR reprojection | mesh hard gate implemented; B-Rep validation retained | High |
| STEP output | serialize a valid B-Rep | OCCT/CadQuery STEP writer | downstream after visual CADification | Very high |

## Model boundary

The intended path is:

```text
Natural language
  -> visual proposal
  -> image / consistent views
  -> learned 3D prior
  -> noisy mesh / geometric representation
  -> deterministic engineering regularization
  -> analytic B-Rep
```

The project must not recreate the removed path by introducing another complete text-generated geometry schema. Sparse user-confirmed dimensions may later act as optimization constraints, but the geometric body must originate from 2D-to-3D reconstruction.

## Hunyuan integration

### Hunyuan3D-2.1

The model runs behind an HTTP boundary instead of being imported into the core environment. This avoids PyTorch/CUDA/OpenCASCADE dependency coupling and makes model replacement easier.

### Hunyuan3D-2mv

The public multi-view path accepts up to four named views (`front/back/left/right`). Intent2Brep includes an optional sidecar exposing this as `POST /generate-mv`.

## DrawingIR role

DrawingIR is retained only as a geometry/validation research utility:

```text
reference B-Rep -> exact HLR -> DrawingIR -> cross-view candidates
```

It can support controlled datasets, vector reconstruction comparisons, and later reprojection checks. It is not a text-to-CAD construction route.

## Research gap Intent2Brep should own

```text
visual 3D prior
   -> topology-preserving cleanup
   -> sharp/thin/hole-aware segmentation
   -> analytic primitive recovery
   -> engineering regularization
   -> surface intersection + trimming
   -> valid B-Rep
   -> HLR / geometry verification
```

Before implementing a large B-Rep assembler, benchmark whether the coarse 3D prior preserves mechanical topology.

Minimum metrics:

- connected-component count
- watertightness
- silhouette consistency
- Chamfer / Hausdorff distance
- hole/opening preservation
- thin-wall preservation
- sharp-edge preservation

## Key references

- Tencent Hunyuan3D-2.1: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- Tencent Hunyuan3D-2 / Hunyuan3D-2mv: https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- Tencent HunyuanImage-3.0: https://github.com/Tencent-Hunyuan/HunyuanImage-3.0
- BrepGaussian (CVPR 2026): https://openaccess.thecvf.com/content/CVPR2026/html/Yu_BrepGaussian_CAD_reconstruction_from_Multi-View_Images_with_Gaussian_Splatting_CVPR_2026_paper.html
- Ortho2CAD (2026): https://arxiv.org/abs/2607.08891
- Text2CAD via Technical Drawings (2024): https://arxiv.org/abs/2411.06206
- CadQuery: https://github.com/CadQuery/cadquery
- OpenCASCADE: https://dev.opencascade.org/
