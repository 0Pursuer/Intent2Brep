import json

import pytest
from typer.testing import CliRunner

from intent2brep.cli import app
from intent2brep.errors import GeometryDomainError, UnsupportedIntentError
from intent2brep.models import BasePlate, Hole, PartIntent
from intent2brep.parser import RegexIntentParser
from intent2brep.pipeline import run_pipeline
from intent2brep.checks import validate_intent_domain


def test_base_web_hole(tmp_path):
    text = "100x60x10 mm 底板，中间竖一个宽60mm、厚10mm、高50mm的支撑板，支撑板中心有一个直径20mm通孔。"
    r = run_pipeline(text, tmp_path)
    assert r.validation["valid"]
    assert r.validation["solid_count"] == 1
    assert r.intent.web is not None
    assert len(r.intent.holes) == 1
    assert any(c.type == "perpendicular" for c in r.intent.constraints)
    assert (tmp_path / "03_model.step").exists()
    assert (tmp_path / "views" / "front.svg").exists()


def test_base_hole(tmp_path):
    text = "底板 80x50x8 mm，中间直径12mm通孔。"
    r = run_pipeline(text, tmp_path)
    assert r.validation["valid"]
    assert len(r.intent.holes) == 1
    assert r.intent.holes[0].target == "base"
    assert r.intent.holes[0].centered_on_target


def test_parser_does_not_silently_center_unspecified_hole():
    intent = RegexIntentParser().parse("底板 80x50x8 mm，直径12mm通孔。")
    assert not intent.holes[0].centered_on_target
    with pytest.raises(Exception, match="not centered"):
        validate_intent_domain(intent)


def test_explicit_hole_coordinates_are_preserved(tmp_path):
    text = "底板 80x50x8 mm，直径12mm通孔，x=10 y=5。"
    r = run_pipeline(text, tmp_path)
    assert r.resolved.holes[0].center[:2] == (10.0, 5.0)


def test_oversized_hole_rejected():
    intent = PartIntent(
        base=BasePlate(length=20, width=20, thickness=5),
        holes=[Hole(diameter=30, target="base", centered_on_target=True)],
    )
    with pytest.raises(GeometryDomainError, match="exceeds base"):
        validate_intent_domain(intent)


def test_unsupported_features_fail_closed(tmp_path):
    text = "100x60x10 mm 底板，四周R5圆角。"
    with pytest.raises(UnsupportedIntentError):
        run_pipeline(text, tmp_path)


def test_unsupported_features_can_be_explicitly_allowed(tmp_path):
    text = "100x60x10 mm 底板，四周R5圆角。"
    r = run_pipeline(text, tmp_path, allow_unsupported=True)
    assert r.validation["valid"]
    assert r.intent.unsupported_requests


def test_schema_cli():
    runner = CliRunner()
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    schema = json.loads(result.stdout)
    assert schema["title"] == "PartIntent"
