# Intent2Brep

**Intent2Brep** is a visual-first Text/Image-to-3D research pipeline toward analytic CAD B-Rep.

The project has one primary path:

```text
Natural language
      |
      v
Text-to-Image provider
      |
      v
canonical mechanical image
      |
      +------ optional view synthesis / known multi-view inputs
      |
      v
Image-to-3D foundation model
      |
      v
raw 3D geometry (mesh today)
      |
      v
mesh quality hard gate
      |
      v
CADification
  - topology-preserving cleanup
  - plane/cylinder/cone/sphere/torus recovery
  - symmetry/coaxial/coplanar regularization
  - surface intersections and trim loops
      |
      v
analytic B-Rep
      |
      v
STEP
```

The removed legacy path `Text -> PartIntent JSON -> resolver -> CadQuery construction` is no longer part of the package, CLI, tests, or documentation architecture. Text is used to condition visual generation; the geometric body must come from 2D/multi-view-to-3D reconstruction.

## Current status

Implemented:

- model-agnostic text-to-image provider
- Hunyuan3D-2.1 single-image HTTP provider
- Hunyuan3D-2mv 1-4 named-view HTTP provider and optional sidecar
- `text2image`, `image2mesh`, `text2mesh`, `views2mesh`
- deterministic `mesh-info` quality report
- retained OpenCASCADE HLR / DrawingIR / cross-view utilities for downstream validation and benchmark generation

Not implemented yet:

- robust mechanical mesh cleanup
- analytic primitive segmentation/fitting
- global engineering regularization
- raw B-Rep reconstruction from recovered surfaces
- STEP export from the visual reconstruction path

## Why model services are isolated

The CadQuery/OpenCASCADE utilities and GPU foundation models have different Python/CUDA dependency stacks. Intent2Brep keeps GPU models behind provider/service interfaces:

```text
Intent2Brep core
   |
   +---- HTTP ----> Text-to-image service
   |
   +---- HTTP ----> Hunyuan3D service
```

This keeps the visual pipeline replaceable and avoids coupling the repository to a specific torch/CUDA environment.

## Install core

```bash
mamba env create -f environment.yml
conda activate intent2brep
python -m pip install -e . --no-deps --no-build-isolation
pytest -q
```

## Image -> Hunyuan3D-2.1 -> mesh

Run Tencent's Hunyuan3D-2.1 FastAPI service separately, then:

```bash
intent2brep image2mesh part.png \
  --hunyuan-url http://127.0.0.1:8081 \
  -o out_visual
```

Outputs include:

```text
out_visual/
  02_preprocess/source.png
  04_mesh/raw.glb
  04_mesh/mesh_report.json
  run_manifest.json
```

## Text -> image

Configure an OpenAI-compatible image-generation endpoint:

```bash
export T2I_BASE_URL=https://provider.example/v1
export T2I_API_KEY=...
export T2I_MODEL=...
```

Then:

```bash
intent2brep text2image '一个机械双耳支架...' -o out_t2i
```

CLI overrides are also supported:

```bash
intent2brep text2image '一个机械双耳支架...' \
  --t2i-base-url https://provider.example/v1 \
  --t2i-model your-image-model \
  --t2i-api-key-env MY_IMAGE_GATEWAY_KEY \
  --t2i-response-format auto \
  -o out_t2i
```

The prompt adapter adds rendering constraints only: isolated mechanical part, neutral material, clean background, visible holes/openings and reconstruction-friendly viewing. It does **not** emit CAD feature commands or a complete geometry JSON.

## Text -> image -> Hunyuan3D -> mesh

```bash
intent2brep text2mesh '一个机械双耳支架...' \
  --t2i-base-url https://provider.example/v1 \
  --t2i-model your-image-model \
  --t2i-api-key-env MY_IMAGE_GATEWAY_KEY \
  --hunyuan-url http://127.0.0.1:8081 \
  -o out_visual
```

## Multi-view -> Hunyuan3D-2mv -> mesh

The included sidecar accepts up to four named views: `front/back/left/right`.

```bash
intent2brep views2mesh \
  --front front.png \
  --left left.png \
  --back back.png \
  --right right.png \
  --hunyuan-url http://127.0.0.1:8082 \
  -o out_mv
```

## Mesh hard gate

```bash
intent2brep mesh-info model.glb
```

The report records vertex/face counts, connected components, watertightness, winding consistency, Euler number, area, volume when valid, bounds and extents.

## Repository layout

```text
src/intent2brep/
  pipelines/
    visual.py
  providers/
    t2i/
    i23d/
  vision/
    prompting.py
  mesh/
    metrics.py
  drawing.py
  drawing_ir.py
  cross_view.py
  validation.py

services/
  hunyuan3d_2mv/
```

See `docs/ARCHITECTURE.md`, `docs/HUNYUAN_INTEGRATION.md`, `docs/REMOTE_3D_APIS.md`, and `docs/ROADMAP.md`.
