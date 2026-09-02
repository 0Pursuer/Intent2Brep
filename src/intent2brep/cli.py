from __future__ import annotations

import json
from pathlib import Path

import typer

from .mesh.metrics import inspect_mesh
from .pipelines.visual import (
    run_image_to_mesh,
    run_text_to_image,
    run_text_to_mesh,
    run_views_to_mesh,
)
from .providers.i23d import Hunyuan3D21HttpProvider, Hunyuan3D2MVHttpProvider
from .providers.t2i import OpenAICompatibleImageProvider

app = typer.Typer(
    help="Intent2Brep: visual-first Text/Image-to-3D research pipeline toward analytic B-Rep"
)


@app.callback()
def main():
    pass


def _dump(result):
    payload = {
        "manifest": str(result.manifest),
        "source_image": str(result.source_image) if result.source_image else None,
        "mesh": str(result.mesh) if result.mesh else None,
        "views": {k: str(v) for k, v in result.views.items()},
        "mesh_report": result.mesh_report,
    }
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


def _openai_t2i(
    base_url: str | None,
    model: str | None,
    api_key_env: str | None,
    size: str | None,
    response_format: str | None,
    endpoint_path: str | None,
) -> OpenAICompatibleImageProvider:
    return OpenAICompatibleImageProvider.from_env(
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        size=size,
        response_format=response_format,
        endpoint_path=endpoint_path,
    )


@app.command("text2image")
def text2image_cmd(
    text: str = typer.Argument(...),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    seed: int = typer.Option(42),
    t2i_base_url: str | None = typer.Option(
        None,
        "--t2i-base-url",
        help="OpenAI-compatible base URL; overrides T2I_BASE_URL/OPENAI_BASE_URL.",
    ),
    t2i_model: str | None = typer.Option(
        None,
        "--t2i-model",
        help="Image model name; overrides T2I_MODEL/OPENAI_IMAGE_MODEL.",
    ),
    t2i_api_key_env: str | None = typer.Option(
        None,
        "--t2i-api-key-env",
        help="Read the API key from this environment variable instead of putting the secret on the command line.",
    ),
    t2i_size: str | None = typer.Option(None, "--t2i-size"),
    t2i_response_format: str | None = typer.Option(
        None,
        "--t2i-response-format",
        help="b64_json, url, or auto. 'auto' omits response_format for stricter gateways.",
    ),
    t2i_endpoint_path: str | None = typer.Option(
        None,
        "--t2i-endpoint-path",
        help="Generation path, default /images/generations.",
    ),
):
    provider = _openai_t2i(
        t2i_base_url,
        t2i_model,
        t2i_api_key_env,
        t2i_size,
        t2i_response_format,
        t2i_endpoint_path,
    )
    _dump(run_text_to_image(text, output, provider, seed=seed))


@app.command("image2mesh")
def image2mesh_cmd(
    image: Path = typer.Argument(..., exists=True, readable=True),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    seed: int = typer.Option(42),
    hunyuan_url: str = typer.Option("http://127.0.0.1:8081", "--hunyuan-url"),
    analyze: bool = typer.Option(True, "--analyze/--no-analyze"),
):
    _dump(
        run_image_to_mesh(
            image,
            output,
            Hunyuan3D21HttpProvider(hunyuan_url),
            seed=seed,
            analyze_mesh=analyze,
        )
    )


@app.command("views2mesh")
def views2mesh_cmd(
    front: Path | None = typer.Option(None, exists=True),
    back: Path | None = typer.Option(None, exists=True),
    left: Path | None = typer.Option(None, exists=True),
    right: Path | None = typer.Option(None, exists=True),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    seed: int = typer.Option(42),
    hunyuan_url: str = typer.Option("http://127.0.0.1:8082", "--hunyuan-url"),
    analyze: bool = typer.Option(True, "--analyze/--no-analyze"),
):
    views = {
        k: v
        for k, v in {"front": front, "back": back, "left": left, "right": right}.items()
        if v is not None
    }
    _dump(
        run_views_to_mesh(
            views,
            output,
            Hunyuan3D2MVHttpProvider(hunyuan_url),
            seed=seed,
            analyze_mesh=analyze,
        )
    )


@app.command("text2mesh")
def text2mesh_cmd(
    text: str = typer.Argument(...),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    seed: int = typer.Option(42),
    hunyuan_url: str = typer.Option("http://127.0.0.1:8081", "--hunyuan-url"),
    analyze: bool = typer.Option(True, "--analyze/--no-analyze"),
    t2i_base_url: str | None = typer.Option(
        None,
        "--t2i-base-url",
        help="OpenAI-compatible base URL; overrides T2I_BASE_URL/OPENAI_BASE_URL.",
    ),
    t2i_model: str | None = typer.Option(
        None,
        "--t2i-model",
        help="Image model name; overrides T2I_MODEL/OPENAI_IMAGE_MODEL.",
    ),
    t2i_api_key_env: str | None = typer.Option(
        None,
        "--t2i-api-key-env",
        help="Read the API key from this environment variable instead of putting the secret on the command line.",
    ),
    t2i_size: str | None = typer.Option(None, "--t2i-size"),
    t2i_response_format: str | None = typer.Option(
        None,
        "--t2i-response-format",
        help="b64_json, url, or auto. 'auto' omits response_format for stricter gateways.",
    ),
    t2i_endpoint_path: str | None = typer.Option(
        None,
        "--t2i-endpoint-path",
        help="Generation path, default /images/generations.",
    ),
):
    t2i = _openai_t2i(
        t2i_base_url,
        t2i_model,
        t2i_api_key_env,
        t2i_size,
        t2i_response_format,
        t2i_endpoint_path,
    )
    _dump(
        run_text_to_mesh(
            text,
            output,
            t2i,
            Hunyuan3D21HttpProvider(hunyuan_url),
            seed=seed,
            analyze_mesh=analyze,
        )
    )


@app.command("mesh-info")
def mesh_info(mesh: Path = typer.Argument(..., exists=True, readable=True)):
    typer.echo(json.dumps(inspect_mesh(mesh), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
