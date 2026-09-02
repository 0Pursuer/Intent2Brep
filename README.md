# Intent2Brep

**Intent2Brep** is a visual-first Text/Image-to-3D research pipeline toward analytic CAD B-Rep.

v0.4 keeps two hypotheses side by side:

1. **Visual mainline** — natural language -> text-to-image -> image/multi-view-to-3D -> measured mesh -> CADification -> B-Rep.
2. **Parametric baseline** — natural language -> strict engineering JSON -> CadQuery/OpenCASCADE B-Rep (the original v0.3 path).

The main research question is no longer only "can an LLM emit the whole feature history?". It is:

> Can a modern image-to-3D foundation model provide a useful geometric prior, then can engineering regularization project that noisy result back into analytic CAD space?

## v0.4 architecture

```text
                         Natural language
                         /              \
                        v                v
               Visual mainline    Parametric baseline
                        |                |
                  T2I provider       PartIntent JSON
                        |                |
                 canonical image     resolver / CSG
                        |                |
               optional multi-view     B-Rep / STEP
                        |
              Hunyuan3D provider
                        |
                    raw mesh
                        |
                 mesh hard gate
                        |
             CADification (next)
                        |
                 analytic B-Rep
                        |
                      STEP
```

**Important:** v0.4 does not pretend that a Hunyuan mesh is already CAD. The visual path deliberately stops at a measured mesh boundary. Surface segmentation, analytic primitive fitting, global regularization and B-Rep assembly are the next milestones.

## Why provider/services

CadQuery/OpenCASCADE and GPU foundation models have different Python/CUDA stacks. The core package stays lightweight and calls model services over HTTP.

```text
Intent2Brep core (Python 3.11 + OCC)
          |
          +---- HTTP ----> Text-to-image service
          |
          +---- HTTP ----> Hunyuan3D service
```

This also makes models replaceable: HunyuanImage/FLUX/remote T2I APIs can implement the T2I provider; Hunyuan3D-2.1, Hunyuan3D-2mv, cloud HY-3D or future models can implement image-to-3D.

## Install core

```bash
mamba env create -f environment.yml
conda activate intent2brep
python -m pip install -e . --no-deps --no-build-isolation
pytest -q
```

## Parametric baseline

```bash
intent2brep parametric \
  '100x60x10 mm 底板，中间竖一个宽60mm、厚10mm、高50mm的支撑板，支撑板中心有一个直径20mm通孔。' \
  -o out_parametric
```

`intent2brep build ...` remains a backward-compatible alias.

## Image -> Hunyuan3D-2.1 -> mesh

Run Tencent's Hunyuan3D-2.1 FastAPI server in its own environment (normally port 8081), then:

```bash
intent2brep image2mesh part.png --hunyuan-url http://127.0.0.1:8081 -o out_visual
```

Outputs include:

```text
out_visual/
  02_preprocess/source.png
  04_mesh/raw.glb
  04_mesh/mesh_report.json
  run_manifest.json
```

## Text -> image with a custom OpenAI-compatible API

The T2I provider accepts the common OpenAI-compatible `POST /images/generations` contract.

Project-specific variables are preferred:

```bash
export T2I_BASE_URL=https://provider.example/v1
export T2I_API_KEY=your-secret
export T2I_MODEL=your-image-model
```

Standard OpenAI-style variables also work:

```bash
export OPENAI_BASE_URL=https://provider.example/v1
export OPENAI_API_KEY=your-secret
export OPENAI_IMAGE_MODEL=your-image-model
```

Do not commit API keys. Prefer environment variables rather than passing a secret as a command-line argument.

If the gateway uses a custom secret variable, keep the value in that variable and tell the CLI which variable to read:

```bash
export MY_IMAGE_GATEWAY_KEY=your-secret

intent2brep text2image '一个机械双耳支架...' \
  --t2i-base-url https://provider.example/v1 \
  --t2i-model your-image-model \
  --t2i-api-key-env MY_IMAGE_GATEWAY_KEY \
  -o out_t2i
```

Some OpenAI-compatible gateways reject `response_format`. Use `auto` to omit it while still accepting either `url` or `b64_json` responses:

```bash
intent2brep text2image '一个机械双耳支架...' \
  --t2i-base-url https://provider.example/v1 \
  --t2i-model your-image-model \
  --t2i-response-format auto \
  -o out_t2i
```

A non-standard endpoint path can also be configured:

```bash
intent2brep text2image '一个机械双耳支架...' \
  --t2i-base-url https://provider.example \
  --t2i-endpoint-path /openai/v1/images/generations \
  --t2i-model your-image-model \
  -o out_t2i
```

Equivalent environment switches are:

```text
T2I_SIZE
T2I_TIMEOUT
T2I_SEND_SEED
T2I_RESPONSE_FORMAT   # b64_json | url | auto
T2I_ENDPOINT_PATH
T2I_AUTH_HEADER       # default: Authorization
T2I_AUTH_SCHEME       # default: Bearer
```

Then:

```bash
intent2brep text2image '一个机械双耳支架...' -o out_t2i

intent2brep text2mesh '一个机械双耳支架...' \
  --t2i-base-url https://provider.example/v1 \
  --t2i-model your-image-model \
  --t2i-api-key-env MY_IMAGE_GATEWAY_KEY \
  --hunyuan-url http://127.0.0.1:8081 \
  -o out_visual
```

The prompt adapter adds only rendering constraints (isolated matte CAD part, white background, visible openings, weak perspective). It does **not** emit hidden geometry JSON or CAD feature commands.

## Multi-view -> Hunyuan3D-2mv -> mesh

The public Hunyuan3D-2mv path accepts up to four named views: `front/back/left/right`. The repository includes an optional sidecar under `services/hunyuan3d_2mv/` so its PyTorch environment stays isolated.

```bash
intent2brep views2mesh \
  --front front.png \
  --left left.png \
  --back back.png \
  --hunyuan-url http://127.0.0.1:8082 \
  -o out_mv
```

## Mesh hard gate

```bash
intent2brep mesh-info model.glb
```

The report records vertex/face counts, connected components, watertightness, winding consistency, Euler number, area, volume (when valid), bounds and extents. These are the first deterministic checks before CADification.

## Repository layout

```text
src/intent2brep/
  pipelines/
    parametric.py       # deterministic v0.3 baseline
    visual.py           # visual-first mainline
  providers/
    t2i/
    i23d/
  vision/
    prompting.py
  mesh/
    metrics.py
  drawing_ir.py         # retained for HLR/reprojection validation
  cross_view.py         # retained vector reconstruction research

services/
  hunyuan3d_2mv/        # optional GPU sidecar
```

See `docs/ARCHITECTURE.md`, `docs/HUNYUAN_INTEGRATION.md`, and `docs/ROADMAP.md`.
