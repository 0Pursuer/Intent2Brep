from __future__ import annotations

import json
from pathlib import Path

import typer

from .models import PartIntent
from .pipeline import run_pipeline

app = typer.Typer(help="Natural-language mechanical intent to analytic B-Rep MVP")


@app.callback()
def main():
    """Intent2BRep command line interface."""
    pass


@app.command()
def build(
    text: str = typer.Argument(..., help="Natural-language part description"),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    parser: str = typer.Option("regex", help="regex or llm"),
    allow_unsupported: bool = typer.Option(False, "--allow-unsupported", help="Build while recording unsupported requests"),
):
    result = run_pipeline(text, output, parser=parser, allow_unsupported=allow_unsupported)
    typer.echo(json.dumps({"validation": result.validation, "outputs": result.outputs}, indent=2, ensure_ascii=False))


@app.command()
def schema():
    """Print the strict Engineering Geometry IR JSON schema."""
    typer.echo(json.dumps(PartIntent.model_json_schema(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
