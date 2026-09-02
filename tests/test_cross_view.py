from intent2brep.builder import build_brep
from intent2brep.cross_view import reconstruct_vertex_candidates
from intent2brep.drawing_ir import extract_drawing_view_ir
from intent2brep.models import BasePlate, PartIntent
from intent2brep.resolver import resolve_constraints


def _box_views():
    intent = PartIntent(base=BasePlate(length=80, width=50, thickness=8))
    shape = build_brep(resolve_constraints(intent))
    return [
        extract_drawing_view_ir(shape, "front", (0, -1, 0), include_hidden=False),
        extract_drawing_view_ir(shape, "top", (0, 0, 1), include_hidden=False),
        extract_drawing_view_ir(shape, "right", (1, 0, 0), include_hidden=False),
    ]


def test_three_views_recover_box_vertices():
    result = reconstruct_vertex_candidates(_box_views())
    assert len(result.vertices) == 8
    actual = {
        tuple(round(x, 6) for x in v.point)
        for v in result.vertices
    }
    expected = {
        (x, y, z)
        for x in (-40.0, 40.0)
        for y in (-25.0, 25.0)
        for z in (0.0, 8.0)
    }
    assert actual == expected
    assert all(len(v.supporting_views) == 3 for v in result.vertices)
