from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx

from ...errors import ProviderConfigurationError, ProviderExecutionError


def _env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""


class OpenAICompatibleImageProvider:
    """Text-to-image adapter for OpenAI-compatible image-generation endpoints.

    The provider intentionally stays vendor-neutral.  It supports the common
    `POST /images/generations` contract, Bearer API keys, URL/base64 responses,
    and a few compatibility switches used by self-hosted gateways and API
    aggregators.
    """

    name = "openai-compatible-t2i"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        *,
        size: str = "1024x1024",
        timeout: float = 180.0,
        send_seed: bool = False,
        response_format: str = "b64_json",
        endpoint_path: str = "/images/generations",
        auth_header: str = "Authorization",
        auth_scheme: str = "Bearer",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.size = size
        self.timeout = timeout
        self.send_seed = send_seed
        self.response_format = response_format.strip().lower()
        self.endpoint_path = endpoint_path.strip() or "/images/generations"
        self.auth_header = auth_header.strip() or "Authorization"
        self.auth_scheme = auth_scheme.strip()

        if not self.base_url or not self.model:
            raise ProviderConfigurationError("T2I base_url and model are required")
        if self.response_format not in {"auto", "b64_json", "url"}:
            raise ProviderConfigurationError(
                "T2I response_format must be one of: auto, b64_json, url"
            )

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        api_key_env: str | None = None,
        size: str | None = None,
        response_format: str | None = None,
        endpoint_path: str | None = None,
        send_seed: bool | None = None,
    ) -> "OpenAICompatibleImageProvider":
        """Build from T2I_* variables with standard OpenAI variable fallbacks.

        Preferred project-specific variables:
          T2I_BASE_URL, T2I_API_KEY, T2I_MODEL

        Standard compatibility fallbacks:
          OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_IMAGE_MODEL

        `api_key_env` lets callers reference a custom secret variable without
        placing the key itself on the command line.
        """

        resolved_base_url = base_url or _env_first("T2I_BASE_URL", "OPENAI_BASE_URL")
        resolved_model = model or _env_first("T2I_MODEL", "OPENAI_IMAGE_MODEL")

        resolved_api_key = api_key or ""
        if not resolved_api_key and api_key_env:
            resolved_api_key = os.getenv(api_key_env, "")
        if not resolved_api_key:
            resolved_api_key = _env_first("T2I_API_KEY", "OPENAI_API_KEY")

        if not resolved_base_url or not resolved_model:
            raise ProviderConfigurationError(
                "Set T2I_BASE_URL/T2I_MODEL (or OPENAI_BASE_URL/OPENAI_IMAGE_MODEL) "
                "for text2image/text2mesh"
            )

        if send_seed is None:
            send_seed = os.getenv("T2I_SEND_SEED", "0").lower() in {"1", "true", "yes"}

        try:
            timeout = float(os.getenv("T2I_TIMEOUT", "180"))
        except ValueError as exc:
            raise ProviderConfigurationError("T2I_TIMEOUT must be a number") from exc

        return cls(
            resolved_base_url,
            resolved_model,
            resolved_api_key,
            size=size or os.getenv("T2I_SIZE", "1024x1024"),
            timeout=timeout,
            send_seed=send_seed,
            response_format=response_format
            or os.getenv("T2I_RESPONSE_FORMAT", "b64_json"),
            endpoint_path=endpoint_path
            or os.getenv("T2I_ENDPOINT_PATH", "/images/generations"),
            auth_header=os.getenv("T2I_AUTH_HEADER", "Authorization"),
            auth_scheme=os.getenv("T2I_AUTH_SCHEME", "Bearer"),
        )

    def _generation_url(self) -> str:
        # Some gateways are configured with the complete endpoint rather than a
        # base URL.  Accept both forms to avoid duplicated /images/generations.
        if self.base_url.endswith("/images/generations"):
            return self.base_url
        if self.endpoint_path.startswith(("http://", "https://")):
            return self.endpoint_path
        return f"{self.base_url}/{self.endpoint_path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            value = f"{self.auth_scheme} {self.api_key}".strip()
            headers[self.auth_header] = value
        return headers

    def generate(self, prompt: str, output: Path, *, seed: int = 42) -> Path:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": self.size,
        }
        # Some OpenAI-compatible gateways reject response_format entirely.
        # "auto" omits it and accepts either URL or base64 in the response.
        if self.response_format != "auto":
            payload["response_format"] = self.response_format
        if self.send_seed:
            payload["seed"] = seed

        try:
            r = httpx.post(
                self._generation_url(),
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            if r.status_code >= 400:
                raise ProviderExecutionError(f"HTTP {r.status_code}: {r.text[:500]}")

            content_type = r.headers.get("content-type", "").lower()
            if content_type.startswith("image/"):
                content = r.content
            else:
                body = r.json()
                data = body.get("data")
                if not isinstance(data, list) or not data:
                    raise ProviderExecutionError("T2I response does not contain data[0]")
                item = data[0]
                if item.get("b64_json"):
                    content = base64.b64decode(item["b64_json"])
                elif item.get("url"):
                    image_response = httpx.get(item["url"], timeout=self.timeout)
                    image_response.raise_for_status()
                    content = image_response.content
                else:
                    raise ProviderExecutionError(
                        "T2I response contains neither b64_json nor url"
                    )
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError(f"T2I request failed: {exc}") from exc

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        return output
