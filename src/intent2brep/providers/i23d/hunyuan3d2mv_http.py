from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Mapping
import httpx
from ...errors import ProviderConfigurationError, ProviderExecutionError

_ALLOWED = ("front", "back", "left", "right")


class Hunyuan3D2MVHttpProvider:
    """Adapter for the lightweight sidecar in `services/hunyuan3d_2mv/server.py`."""

    name = "hunyuan3d-2mv-http"

    def __init__(self, base_url: str = "http://127.0.0.1:8082", *, timeout: float = 900.0,
                 octree_resolution: int = 380, num_inference_steps: int = 30,
                 guidance_scale: float = 5.0, num_chunks: int = 20000):
        if not base_url:
            raise ProviderConfigurationError("Hunyuan3D-2mv base_url is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.octree_resolution = octree_resolution
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale
        self.num_chunks = num_chunks

    @classmethod
    def from_env(cls) -> "Hunyuan3D2MVHttpProvider":
        return cls(os.getenv("HUNYUAN3D_MV_BASE_URL", "http://127.0.0.1:8082"))

    def generate(self, images: Mapping[str, Path], output: Path, *, seed: int = 42) -> Path:
        selected = {k: Path(v) for k, v in images.items() if k in _ALLOWED and v is not None}
        if not selected:
            raise ProviderExecutionError("At least one of front/back/left/right views is required")
        if len(selected) > 4:
            raise ProviderExecutionError("Hunyuan3D-2mv supports up to four named views")
        payload = {
            "images": {k: base64.b64encode(v.read_bytes()).decode("ascii") for k, v in selected.items()},
            "seed": seed,
            "octree_resolution": self.octree_resolution,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "num_chunks": self.num_chunks,
            "type": output.suffix.lower().lstrip(".") or "glb",
        }
        try:
            r = httpx.post(f"{self.base_url}/generate-mv", json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderExecutionError(f"HTTP {r.status_code}: {r.text[:500]}")
            if not r.content:
                raise ProviderExecutionError("Hunyuan3D-2mv returned an empty model")
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError(f"Hunyuan3D-2mv request failed: {exc}") from exc
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(r.content)
        return output
