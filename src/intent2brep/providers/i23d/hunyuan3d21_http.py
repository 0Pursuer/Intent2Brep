from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Mapping
import httpx
from ...errors import ProviderConfigurationError, ProviderExecutionError


class Hunyuan3D21HttpProvider:
    """Adapter for the official Hunyuan3D-2.1 FastAPI `/generate` endpoint."""

    name = "hunyuan3d-2.1-http"

    def __init__(self, base_url: str = "http://127.0.0.1:8081", *, timeout: float = 900.0,
                 octree_resolution: int = 256, num_inference_steps: int = 5,
                 guidance_scale: float = 5.0, num_chunks: int = 8000):
        if not base_url:
            raise ProviderConfigurationError("Hunyuan3D base_url is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.octree_resolution = octree_resolution
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale
        self.num_chunks = num_chunks

    @classmethod
    def from_env(cls) -> "Hunyuan3D21HttpProvider":
        return cls(os.getenv("HUNYUAN3D_BASE_URL", "http://127.0.0.1:8081"))

    def generate(self, images: Mapping[str, Path], output: Path, *, seed: int = 42) -> Path:
        if len(images) != 1:
            raise ProviderExecutionError("Hunyuan3D-2.1 official API is single-image; use Hunyuan3D2MVHttpProvider for multiple views")
        image_path = next(iter(images.values()))
        encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        output_type = output.suffix.lower().lstrip(".") or "glb"
        if output_type not in {"glb", "obj"}:
            output_type = "glb"
        payload = {"image": encoded, "remove_background": True, "texture": False, "seed": seed,
                   "octree_resolution": self.octree_resolution, "num_inference_steps": self.num_inference_steps,
                   "guidance_scale": self.guidance_scale, "num_chunks": self.num_chunks, "type": output_type}
        try:
            r = httpx.post(f"{self.base_url}/generate", json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderExecutionError(f"HTTP {r.status_code}: {r.text[:500]}")
            if not r.content:
                raise ProviderExecutionError("Hunyuan3D returned an empty model")
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError(f"Hunyuan3D-2.1 request failed: {exc}") from exc
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(r.content)
        return output
