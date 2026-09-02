import base64

import httpx

from intent2brep.providers.i23d import Hunyuan3D21HttpProvider, Hunyuan3D2MVHttpProvider
from intent2brep.providers.t2i import OpenAICompatibleImageProvider

PNG = b"png-bytes"


def test_hunyuan3d21_request(monkeypatch, tmp_path):
    image = tmp_path / "a.png"
    image.write_bytes(PNG)
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(url=url, payload=kwargs["json"])
        return httpx.Response(200, content=b"mesh")

    monkeypatch.setattr(httpx, "post", fake_post)
    out = Hunyuan3D21HttpProvider("http://model").generate(
        {"front": image}, tmp_path / "m.glb", seed=7
    )
    assert out.read_bytes() == b"mesh" and seen["url"].endswith("/generate")
    assert base64.b64decode(seen["payload"]["image"]) == PNG
    assert seen["payload"]["seed"] == 7


def test_hunyuan3d2mv_request(monkeypatch, tmp_path):
    front = tmp_path / "f.png"
    left = tmp_path / "l.png"
    front.write_bytes(PNG)
    left.write_bytes(PNG)
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(url=url, payload=kwargs["json"])
        return httpx.Response(200, content=b"mesh")

    monkeypatch.setattr(httpx, "post", fake_post)
    Hunyuan3D2MVHttpProvider("http://mv").generate(
        {"front": front, "left": left}, tmp_path / "m.glb"
    )
    assert seen["url"].endswith("/generate-mv")
    assert set(seen["payload"]["images"]) == {"front", "left"}


def test_openai_compatible_t2i_b64(monkeypatch, tmp_path):
    payload = base64.b64encode(PNG).decode()
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(
            url=url,
            payload=kwargs["json"],
            headers=kwargs["headers"],
        )
        return httpx.Response(200, json={"data": [{"b64_json": payload}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = OpenAICompatibleImageProvider(
        "http://t2i/v1",
        "model-x",
        api_key="secret",
        send_seed=True,
    ).generate("prompt", tmp_path / "x.png", seed=9)

    assert out.read_bytes() == PNG
    assert seen["url"] == "http://t2i/v1/images/generations"
    assert seen["payload"]["seed"] == 9
    assert seen["payload"]["response_format"] == "b64_json"
    assert seen["headers"]["Authorization"] == "Bearer secret"


def test_openai_env_fallback_and_auto_response_format(monkeypatch, tmp_path):
    for key in ("T2I_BASE_URL", "T2I_API_KEY", "T2I_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "image-model")

    payload = base64.b64encode(PNG).decode()
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(
            url=url,
            payload=kwargs["json"],
            headers=kwargs["headers"],
        )
        return httpx.Response(200, json={"data": [{"b64_json": payload}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleImageProvider.from_env(response_format="auto")
    provider.generate("prompt", tmp_path / "x.png")

    assert seen["url"] == "https://gateway.example/v1/images/generations"
    assert seen["payload"]["model"] == "image-model"
    assert "response_format" not in seen["payload"]
    assert seen["headers"]["Authorization"] == "Bearer openai-secret"


def test_openai_custom_key_env_and_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("MY_IMAGE_API_KEY", "custom-secret")
    payload = base64.b64encode(PNG).decode()
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(url=url, headers=kwargs["headers"])
        return httpx.Response(200, json={"data": [{"b64_json": payload}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleImageProvider.from_env(
        base_url="https://proxy.example",
        model="custom-image-model",
        api_key_env="MY_IMAGE_API_KEY",
        endpoint_path="/openai/v1/images/generations",
    )
    provider.generate("prompt", tmp_path / "x.png")

    assert seen["url"] == "https://proxy.example/openai/v1/images/generations"
    assert seen["headers"]["Authorization"] == "Bearer custom-secret"


def test_openai_complete_endpoint_is_not_duplicated(monkeypatch, tmp_path):
    payload = base64.b64encode(PNG).decode()
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        return httpx.Response(200, json={"data": [{"b64_json": payload}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleImageProvider(
        "https://gateway.example/v1/images/generations",
        "image-model",
    )
    provider.generate("prompt", tmp_path / "x.png")
    assert seen["url"] == "https://gateway.example/v1/images/generations"
