from __future__ import annotations

import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer


def validate_shape(shape: cq.Shape) -> dict:
    analyzer = BRepCheck_Analyzer(shape.wrapped, True)
    bb = shape.BoundingBox()
    solids = shape.Solids()
    faces = shape.Faces()
    edges = shape.Edges()
    volume = sum(s.Volume() for s in solids)
    return {
        "valid": bool(analyzer.IsValid()) and shape.isValid(),
        "solid_count": len(solids),
        "face_count": len(faces),
        "edge_count": len(edges),
        "volume_mm3": volume,
        "bounding_box_mm": {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen},
    }
