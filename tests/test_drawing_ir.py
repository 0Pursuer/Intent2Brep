import json

from intent2brep.builder import build_brep
from intent2brep.drawing_ir import extract_drawing_view_ir
from intent2brep.parser import RegexIntentParser
from intent2brep.resolver import resolve_constraints


def _bracket_shape():
    text = "100x60x10 mm 底板，中间竖一个宽60mm、厚10mm、高50mm的支撑板，支撑板中心有一个直径20mm通孔。"
    intent = RegexIntentParser().parse(text)
    return build_brep(resolve_constraints(intent))


def test_front_view_preserves_exact_circle():
    view = extract_drawing_view_ir(_bracket_shape(), "front", (0, -1, 0))
    circles = [e for e in view.entities if e.geom_type == "CIRCLE" and e.visibility == "visible"]
    assert len(circles) == 1
    assert circles[0].radius == 10.0
    assert circles[0].closed


def test_view_frame_is_explicit():
    view = extract_drawing_view_ir(_bracket_shape(), "top", (0, 0, 1))
    assert view.frame.projection_direction == (0.0, 0.0, 1.0)
    assert view.frame.x_axis_world == (1.0, 0.0, -0.0)
    assert view.frame.y_axis_world == (-0.0, 1.0, 0.0)


def test_visible_edges_win_over_exact_hidden_duplicates():
    view = extract_drawing_view_ir(_bracket_shape(), "front", (0, -1, 0))
    lines = [e for e in view.entities if e.geom_type == "LINE"]
    keys = []
    for e in lines:
        a, b = sorted((tuple(round(x, 7) for x in e.start), tuple(round(x, 7) for x in e.end)))
        keys.append((a, b))
    assert len(keys) == len(set(keys))


def test_pipeline_writes_drawing_ir(tmp_path):
    from intent2brep.pipeline import run_pipeline

    r = run_pipeline("底板 80x50x8 mm，中间直径12mm通孔。", tmp_path)
    front_json = tmp_path / "views" / "front.json"
    assert front_json.exists()
    data = json.loads(front_json.read_text(encoding="utf-8"))
    assert data["frame"]["name"] == "front"
    assert data["entities"]
    assert r.outputs["view_front_ir"] == str(front_json)
    assert (tmp_path / "views" / "wireframe_vertices.json").exists()
