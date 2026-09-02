# Architecture

## Visual-first architecture

Intent2Brep has a single primary reconstruction path:

```text
Natural Language
      |
      v
Text-to-Image Provider
      |
      v
Canonical Image
      |
      +---------------------------+
      |                           |
      v                           v
single image              optional multi-view
      |                           |
      +-------------+-------------+
                    |
                    v
            Image-to-3D Provider
                    |
                    v
                Raw Mesh
                    |
                    v
            Mesh Quality Gate
                    |
                    v
              CADification
       normal/curvature segmentation
       primitive surface hypotheses
       symmetry/coaxial/coplanar rules
                    |
                    v
          Analytic Surface Patches
                    |
                    v
       Intersections + Trim Loops
                    |
                    v
              Analytic B-Rep
                    |
                    v
         Healing / BRepCheck / STEP
                    |
                    v
           HLR Reprojection Check
```

The architecture deliberately excludes a text-to-complete-geometry intermediate representation. Text conditions visual generation; the 3D body originates from image/multi-view reconstruction.

## Provider boundary

Core contracts live in `providers/base.py`:

- `TextToImageProvider`
- `ImageTo3DProvider`
- `MultiViewProvider`

Current adapters:

- `OpenAICompatibleImageProvider`
- `Hunyuan3D21HttpProvider`
- `Hunyuan3D2MVHttpProvider`

GPU model packages are intentionally isolated from the core OpenCASCADE/CadQuery environment.

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

This makes failures attributable to image generation, multi-view consistency, image-to-3D topology, or later CADification.

## DrawingIR and cross-view utilities

`drawing.py`, `drawing_ir.py`, and `cross_view.py` remain because they are useful downstream, not because the project reconstructs CAD from text parameters.

They support:

- exact HLR projection from known B-Rep fixtures/reference parts;
- benchmark generation;
- vector-view reconstruction experiments;
- future B-Rep reprojection validation.

## Next hard boundary

```text
Hunyuan/raw mesh
  -> topology-preserving cleanup
  -> normal/curvature segmentation
  -> analytic primitive hypotheses
  -> engineering regularization
  -> surface intersections
  -> trim loops
  -> face -> shell -> solid
  -> BRepCheck
  -> HLR reprojection residual
```
