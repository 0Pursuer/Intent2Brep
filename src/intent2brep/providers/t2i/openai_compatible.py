from __future__ import annotations

import base64
import os
from pathlib import Path
import httpx
from ...errors import ProviderConfigurationError, ProviderExecutionError


class OpenAICompatibleImageProvider:
    """Text-to-image adapter for OpenAI-compatible `/images/generations` endpoints."""

    name = "openai-compatible-t2i"

    def __init__(self, base_url: str, model: str, api_key: str = "", *, size: str = "1024x1024", timeout: float = 180.0, send_seed: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.size = size
        self.timeout = timeout
        self.send_seed = send_seed
        if not self.base_url or not self.model:
            raise ProviderConfigurationError("T2I base_url and model are required")

    @classmethod
    def from_env(cls) -> "OpenAICompatibleImageProvider":
        base_url = os.getenv("T2I_BASE_URL", "")
        model = os.getenv("T2I_MODEL", "")
        if not base_url or not model:
            raise ProviderConfigurationError("Set T2I_BASE_URL and T2I_MODEL for text2image/text2mesh")
        return cls(base_url, model, os.getenv("T2I_API_KEY", ""), size=os.getenv("T2I_SIZE", "1024x1024"),
                   send_seed=os.getenv("T2I_SEND_SEED", "0").lower() in {"1", "true", "yes"})

    def generate(self, prompt: str, output: Path, *, seed: int = 42) -> Path:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "prompt": prompt, "n": 1, "size": self.size, "response_format": "b64_json"}
        if self.send_seed:
            payload["seed"] = seed
        try:
            r = httpx.post(f"{self.base_url}/images/generations", json=payload, headers=headers, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderExecutionError(f"HTTP {r.status_code}: {r.text[:500]}")
            item = r.json()["data"][0]
            if item.get("b64_json"):
                content = base64.b64decode(item["b64_json"])
            elif item.get("url"):
                image_response = httpx.get(item["url"], timeout=self.timeout)
                image_response.raise_for_status()
                content = image_response.content
            else:
                raise ProviderExecutionError("T2I response contains neither b64_json nor url")
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError(f"T2I request failed: {exc}") from exc
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        return output
