from __future__ import annotations

import json
from pathlib import Path
import typer
from .mesh.metrics import inspect_mesh
from .models import PartIntent
from .pipelines.parametric import run_parametric_pipeline
from .pipelines.visual import run_image_to_mesh, run_text_to_image, run_text_to_mesh, run_views_to_mesh
from .providers.i23d import Hunyuan3D21HttpProvider, Hunyuan3D2MVHttpProvider
from .providers.t2i import OpenAICompatibleImageProvider

app = typer.Typer(help="Intent2Brep: visual-first Text/Image-to-3D research pipeline with a parametric baseline")

@app.callback()
def main(): pass

def _dump(result):
    payload = {"manifest": str(result.manifest), "source_image": str(result.source_image) if result.source_image else None,
               "mesh": str(result.mesh) if result.mesh else None, "views": {k: str(v) for k,v in result.views.items()},
               "mesh_report": result.mesh_report}
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))

@app.command()
def parametric(text: str = typer.Argument(...), output: Path = typer.Option(Path("out"), "--output", "-o"),
               parser: str = typer.Option("regex"), allow_unsupported: bool = typer.Option(False, "--allow-unsupported")):
    r = run_parametric_pipeline(text, output, parser=parser, allow_unsupported=allow_unsupported)
    typer.echo(json.dumps({"validation": r.validation, "outputs": r.outputs}, indent=2, ensure_ascii=False))

@app.command()
def build(text: str = typer.Argument(...), output: Path = typer.Option(Path("out"), "--output", "-o"),
          parser: str = typer.Option("regex"), allow_unsupported: bool = typer.Option(False, "--allow-unsupported")):
    """Backward-compatible alias for `parametric`."""
    return parametric(text, output, parser, allow_unsupported)

@app.command("text2image")
def text2image_cmd(text: str = typer.Argument(...), output: Path = typer.Option(Path("out"), "--output", "-o"),
                   seed: int = typer.Option(42)):
    _dump(run_text_to_image(text, output, OpenAICompatibleImageProvider.from_env(), seed=seed))

@app.command("image2mesh")
def image2mesh_cmd(image: Path = typer.Argument(..., exists=True, readable=True),
                   output: Path = typer.Option(Path("out"), "--output", "-o"), seed: int = typer.Option(42),
                   hunyuan_url: str = typer.Option("http://127.0.0.1:8081", "--hunyuan-url"),
                   analyze: bool = typer.Option(True, "--analyze/--no-analyze")):
    _dump(run_image_to_mesh(image, output, Hunyuan3D21HttpProvider(hunyuan_url), seed=seed, analyze_mesh=analyze))

@app.command("views2mesh")
def views2mesh_cmd(front: Path | None = typer.Option(None, exists=True), back: Path | None = typer.Option(None, exists=True),
                   left: Path | None = typer.Option(None, exists=True), right: Path | None = typer.Option(None, exists=True),
                   output: Path = typer.Option(Path("out"), "--output", "-o"), seed: int = typer.Option(42),
                   hunyuan_url: str = typer.Option("http://127.0.0.1:8082", "--hunyuan-url"),
                   analyze: bool = typer.Option(True, "--analyze/--no-analyze")):
    views = {k:v for k,v in {"front":front,"back":back,"left":left,"right":right}.items() if v is not None}
    _dump(run_views_to_mesh(views, output, Hunyuan3D2MVHttpProvider(hunyuan_url), seed=seed, analyze_mesh=analyze))

@app.command("text2mesh")
def text2mesh_cmd(text: str = typer.Argument(...), output: Path = typer.Option(Path("out"), "--output", "-o"),
                  seed: int = typer.Option(42), hunyuan_url: str = typer.Option("http://127.0.0.1:8081", "--hunyuan-url"),
                  analyze: bool = typer.Option(True, "--analyze/--no-analyze")):
    _dump(run_text_to_mesh(text, output, OpenAICompatibleImageProvider.from_env(), Hunyuan3D21HttpProvider(hunyuan_url),
                           seed=seed, analyze_mesh=analyze))

@app.command("mesh-info")
def mesh_info(mesh: Path = typer.Argument(..., exists=True, readable=True)):
    typer.echo(json.dumps(inspect_mesh(mesh), indent=2, ensure_ascii=False))

@app.command()
def schema():
    typer.echo(json.dumps(PartIntent.model_json_schema(), indent=2, ensure_ascii=False))

if __name__ == "__main__": app()
