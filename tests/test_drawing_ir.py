import json

import cadquery as cq

from intent2brep.drawing import export_views
from intent2brep.drawing_ir import extract_drawing_view_ir


def _bracket_shape():
    base = cq.Workplane("XY").box(100, 60, 10, centered=(True, True, False)).val()
    web = (
        cq.Workplane("XY")
        .box(60, 10, 50, centered=(True, True, False))
        .translate((0, 0, 10))
        .val()
    )
    shape = base.fuse(web)
    cutter = cq.Solid.makeCylinder(
        10,
        14,
        cq.Vector(0, -7, 35),
        cq.Vector(0, 1, 0),
    )
    return shape.cut(cutter).clean()


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


def test_export_views_writes_drawing_ir(tmp_path):
    outputs = export_views(_bracket_shape(), tmp_path / "views")
    front_json = tmp_path / "views" / "front.json"
    assert front_json.exists()
    data = json.loads(front_json.read_text(encoding="utf-8"))
    assert data["frame"]["name"] == "front"
    assert data["entities"]
    assert outputs["front_ir"] == str(front_json)
    assert (tmp_path / "views" / "drawing_manifest.json").exists()
