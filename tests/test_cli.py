from typer.testing import CliRunner

from intent2brep.cli import app


def test_cli_exposes_only_visual_pipeline_commands():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("text2image", "image2mesh", "text2mesh", "views2mesh", "mesh-info"):
        assert command in result.stdout
    for removed in ("parametric", "schema", "build"):
        assert removed not in result.stdout
