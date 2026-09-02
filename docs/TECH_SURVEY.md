# Technical survey and MVP decisions (2026-09)

This document records the technical decisions behind the **v0.4 visual-first pivot**.

Intent2Brep now keeps two independent research tracks:

1. **Visual mainline:** text -> image -> image/multi-view-to-3D -> coarse 3D prior -> engineering CADification -> analytic B-Rep.
2. **Parametric baseline:** text -> typed PartIntent -> deterministic CadQuery/OpenCASCADE construction.

The baseline remains useful for controlled comparison, but it is no longer the project's primary hypothesis.

## Current technology map

| Stage | Problem | Current/reference technology | Intent2Brep v0.4 choice | Maturity |
|---|---|---|---|---|
| Text -> visual proposal | turn natural-language shape intent into a reconstruction-friendly image | modern T2I systems such as HunyuanImage / FLUX / hosted image APIs | model-agnostic T2I provider; prompt adds rendering constraints only, not complete geometry JSON | High for visual fidelity; exact engineering dimensions are not guaranteed |
| Single image -> 3D | infer coarse 3D geometry from one image | Hunyuan3D-2.1, TripoSG, TRELLIS-class image-to-3D systems | HTTP adapter for Tencent Hunyuan3D-2.1 official FastAPI server | High enough for experimentation; not CAD-accurate |
| Multi-view -> 3D | reduce hidden-side ambiguity with several named views | Hunyuan3D-2mv; multi-view diffusion/reconstruction | 1-4 named `front/back/left/right` adapter + isolated sidecar service | Medium-high and rapidly improving |
| Visual 3D representation | preserve the model output before CAD assumptions are imposed | mesh / SDF / sparse voxels / learned 3D latent | persist raw GLB plus deterministic mesh statistics | High for graphics; low for direct CAD semantics |
| Mechanical geometry cleanup | preserve holes, thin walls, sharp edges and topology | topology-aware mesh processing; mechanical-part reconstruction research | next milestone: conservative cleanup and feature-preserving segmentation | Medium; domain-specific |
| Analytic primitive recovery | recover plane/cylinder/cone/sphere/torus rather than fragmented freeform patches | robust fitting, region growing, RANSAC/least squares; learned B-Rep reconstruction work such as BrepGaussian/ParaCAD directions | planned primitive hypothesis engine with complexity prior | Medium; difficult under noisy/ambiguous geometry |
| Engineering regularization | impose coplanar/coaxial/symmetric/equal-radius relationships without rebuilding from text | constrained optimization / geometric solvers | planned post-3D optimization over recovered analytic entities | Medium |
| Raw B-Rep assembly | surface intersections, trim loops, faces, shells, solids | OpenCASCADE/OCP | planned after primitive recovery; existing OCC stack retained | High at kernel level, difficult at inference boundary |
| Healing / simplification | sew gaps and merge same-domain fragments | OCCT `BRepBuilderAPI_Sewing`, `ShapeUpgrade_UnifySameDomain`, ShapeFix | planned downstream hardening | Very high |
| Validation | reject invalid geometry and compare reconstructions | OCCT `BRepCheck_Analyzer`; mesh metrics; HLR reprojection | BRep validation already exists; v0.4 adds mesh hard gate; reprojection will be reused downstream | High |
| STEP output | serialize an already-valid B-Rep | OCCT/CadQuery STEP writer | existing implementation retained | Very high |

## Why the model boundary changed

v0.3 effectively concentrated the hard problem at the front:

```text
Natural language
  -> complete typed geometry intent
  -> exact deterministic construction
```

That is useful as a baseline, but it risks becoming another form of text-to-CAD-program generation.

v0.4 instead treats the 3D foundation model as a **geometric prior**:

```text
Natural language
  -> visual proposal
  -> image / consistent views
  -> learned 3D prior
  -> noisy mesh/SDF-like geometry
  -> deterministic engineering regularization
  -> analytic B-Rep
```

The critical rule is that text does **not** secretly regenerate the complete CAD model through a hidden JSON schema. Sparse dimensions or user-confirmed engineering constraints may later regularize a recovered 3D model, but the geometric body of the visual route must originate from 2D-to-3D reconstruction.

## Hunyuan integration decision

### Hunyuan3D-2.1

Tencent exposes an image-to-shape pipeline and an official FastAPI server. Intent2Brep uses the HTTP boundary rather than importing the model into the CadQuery process.

Reasons:

- keeps PyTorch/CUDA dependencies outside the OCC environment;
- makes local/remote GPU execution interchangeable;
- allows future replacement with another image-to-3D model;
- keeps CI deterministic without downloading multi-GB model weights.

### Hunyuan3D-2mv

Tencent's public multi-view path accepts up to four named views (`front/back/left/right`) and sends the image dictionary directly into the shape pipeline. Intent2Brep includes a small optional sidecar that exposes this as `POST /generate-mv`.

This is the first preferred path for controlled mechanical experiments because multiple known views reduce the amount of hidden geometry that the model must hallucinate.

## Existing DrawingIR work

The v0.3 vector path is retained as a **secondary reconstruction/validation track**:

```text
B-Rep -> exact HLR -> DrawingIR -> cross-view candidates
```

It is still useful for:

- generating controlled orthographic benchmark data;
- comparing vector reconstruction with raster foundation-model reconstruction;
- HLR reprojection validation after a B-Rep is rebuilt;
- future hybrid methods where engineering drawings provide extra constraints.

It is no longer the main front end of the project.

## Research gap Intent2Brep should own

T2I and general image-to-3D are increasingly commodity/foundation-model capabilities. STEP writing is already solved once a valid B-Rep exists.

The project-specific research gap is therefore:

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

A successful result should not merely look like the source image. It should recover simple, editable engineering geometry whenever simple analytic surfaces can explain the shape.

## Near-term experimental rule

Before implementing a large CADification stack, benchmark whether modern image-to-3D models preserve the topology of representative mechanical parts.

The first benchmark should measure at least:

- connected-component count;
- watertightness;
- silhouette consistency across controlled cameras;
- Chamfer / Hausdorff distance against a reference mesh;
- hole/opening preservation;
- thin-wall preservation;
- sharp-edge preservation.

If the coarse 3D prior systematically loses holes or changes topology, that failure must be addressed before B-Rep reconstruction.

## Key references

- Tencent Hunyuan3D-2.1: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- Tencent Hunyuan3D-2 / Hunyuan3D-2mv: https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- Tencent HunyuanImage-3.0: https://github.com/Tencent-Hunyuan/HunyuanImage-3.0
- BrepGaussian (CVPR 2026): https://openaccess.thecvf.com/content/CVPR2026/html/Yu_BrepGaussian_CAD_reconstruction_from_Multi-View_Images_with_Gaussian_Splatting_CVPR_2026_paper.html
- Ortho2CAD (2026): https://arxiv.org/abs/2607.08891
- Text2CAD via Technical Drawings (2024): https://arxiv.org/abs/2411.06206
- CadQuery: https://github.com/CadQuery/cadquery
- OpenCASCADE: https://dev.opencascade.org/
