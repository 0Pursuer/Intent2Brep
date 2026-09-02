# Architecture

## v0.4 architectural pivot

v0.3 made `Text -> Engineering JSON -> B-Rep` the mainline. v0.4 deliberately keeps that route as a **parametric baseline** and introduces an independent **visual mainline**.

```text
                              Natural Language
                               /             \
                              v               v
                      Visual mainline   Parametric baseline
                              |               |
                         T2I provider      PartIntent
                              |               |
                       canonical image      resolver
                              |               |
                   optional view synthesis   CSG/OCC
                              |               |
                       1-4 named views       B-Rep
                              |
                    Image-to-3D provider
                              |
                           raw mesh
                              |
                    mesh quality hard gate
                              |
                      CADification layer
             segmentation / normals / primitives
                              |
          plane/cylinder/cone/sphere/torus/NURBS
                              |
                  global regularization
                              |
                  surface intersections
                              |
                       analytic B-Rep
                              |
                    healing / validation
                              |
                            STEP
                              |
                  HLR reprojection feedback
```

The decisive rule is:

> The visual route must not secretly become text -> complete geometry JSON.

Text conditions image generation. 3D geometry is supplied by the 2D/multi-view reconstruction model. Deterministic geometry code begins after a coarse 3D prior exists.

## Provider boundary

Core contracts live in `providers/base.py`:

- `TextToImageProvider`
- `ImageTo3DProvider`
- `MultiViewProvider` (reserved for view-synthesis adapters)

Current adapters:

- `OpenAICompatibleImageProvider`
- `Hunyuan3D21HttpProvider` for Tencent's official single-image `/generate` API
- `Hunyuan3D2MVHttpProvider` for the included 1-4-view sidecar

PyTorch/diffusers/Hunyuan packages are intentionally not dependencies of the CadQuery core environment.

## Visual artifacts

A visual run preserves stage evidence:

```text
source_prompt.txt
visual_prompt.txt
01_t2i/candidate_00.png
02_preprocess/source.png
03_multiview/*.png
04_mesh/raw.glb
04_mesh/mesh_report.json
run_manifest.json
```

This makes failures attributable: T2I generation, view consistency, I2-3D topology and later CADification errors remain separate.

## What remains from v0.3

`drawing_ir.py`, `cross_view.py`, exact HLR, BRepCheck and STEP export stay. They become downstream validation/research tools rather than evidence that upstream geometry has already been solved.

## Next hard technical boundary

The next implementation milestone is not another language schema:

```text
Hunyuan mesh
  -> topology-preserving cleanup
  -> normal/curvature segmentation
  -> analytic primitive hypotheses
  -> symmetry/coaxial/coplanar regularization
  -> surface intersections
  -> trim loops
  -> face -> shell -> solid
  -> BRepCheck
  -> HLR reprojection residual
```
