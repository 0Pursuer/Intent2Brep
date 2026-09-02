# Hunyuan integration

## Hunyuan3D-2.1 single-image service

Intent2Brep targets Tencent's official FastAPI contract instead of importing Hunyuan into the CadQuery process. The public server exposes `POST /generate`, taking a base64 image and returning GLB/OBJ bytes.

Recommended deployment split:

```text
conda env: intent2brep   Python 3.11 + CadQuery/OCC
conda env: hunyuan3d     Tencent's tested Python/PyTorch/CUDA stack
```

Start Hunyuan's server from its repository, normally on port 8081. Then:

```bash
intent2brep image2mesh input.png --hunyuan-url http://127.0.0.1:8081 -o out
```

The core provider sends `texture=false`: geometry is the research signal; texture synthesis is unnecessary for CADification.

## Hunyuan3D-2mv

Tencent's public v2 model exposes a multi-view mode with 1-4 named `front/back/left/right` views. Its public Gradio path passes a dictionary of these images directly to the shape pipeline.

The included `services/hunyuan3d_2mv/server.py` wraps that interface as `POST /generate-mv` so the main project can remain model-agnostic.

Use it inside the Hunyuan3D-2 environment:

```bash
python services/hunyuan3d_2mv/server.py --port 8082
```

Or copy the file into that checkout if the model package is not installed globally.

Then:

```bash
intent2brep views2mesh --front f.png --left l.png --right r.png --hunyuan-url http://127.0.0.1:8082 -o out
```

## Text-to-image

The core currently implements an OpenAI-compatible `/images/generations` adapter. This is intentional: a local HunyuanImage/FLUX service or a remote image provider can be swapped without changing the visual pipeline.

Environment variables:

```text
T2I_BASE_URL
T2I_API_KEY
T2I_MODEL
T2I_SIZE (optional, default 1024x1024)
T2I_SEND_SEED (optional; enable only if the provider supports a seed field)
```

The visual prompt adds rendering constraints only. It must not infer exact CAD coordinates, feature IDs or hidden dimensions.

## Production note

Do not combine Hunyuan model dependencies with CadQuery/OCP in one environment unless you have a tested lockfile. Independent services avoid Python/CUDA/torch conflicts and make model benchmarking reproducible.
