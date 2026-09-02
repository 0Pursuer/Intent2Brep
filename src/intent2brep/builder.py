from __future__ import annotations

from pathlib import Path

import cadquery as cq

from .resolver import ResolvedPart


def build_brep(part: ResolvedPart) -> cq.Shape:
    b = part.intent.base
    base = cq.Workplane("XY").box(b.length, b.width, b.thickness, centered=(True, True, False)).val()
    result = base

    if part.web:
        w = part.web
        web = (
            cq.Workplane("XY")
            .box(w.width, w.thickness, w.height, centered=(True, True, False))
            .translate((w.x, w.y, w.z0))
            .val()
        )
        result = result.fuse(web)

    for h in part.holes:
        r = h.diameter / 2.0
        x, y, z = h.center
        if h.axis == "Y":
            start = cq.Vector(x, y - h.length / 2.0, z)
            cutter = cq.Solid.makeCylinder(r, h.length, start, cq.Vector(0, 1, 0))
        else:
            start = cq.Vector(x, y, z - h.length / 2.0)
            cutter = cq.Solid.makeCylinder(r, h.length, start, cq.Vector(0, 0, 1))
        result = result.cut(cutter)

    # Slots are represented as a 2D capsule extruded through the base.
    for s in part.slots:
        bth = part.intent.base.thickness
        x, y = s.center
        if s.length <= s.width:
            raise ValueError("slot length must be greater than slot width")
        straight = s.length - s.width
        slot2d = (
            cq.Workplane("XY", origin=(x, y, -1.0))
            .moveTo(-straight / 2.0, -s.width / 2.0)
            .lineTo(straight / 2.0, -s.width / 2.0)
            .threePointArc((s.length / 2.0, 0.0), (straight / 2.0, s.width / 2.0))
            .lineTo(-straight / 2.0, s.width / 2.0)
            .threePointArc((-s.length / 2.0, 0.0), (-straight / 2.0, -s.width / 2.0))
            .close()
            .extrude(bth + 2.0)
            .val()
        )
        result = result.cut(slot2d)

    result = result.clean()
    if not result.isValid():
        raise ValueError("OpenCASCADE produced an invalid B-Rep")
    return result


def export_shape(shape: cq.Shape, output_dir: Path, stem: str = "model") -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    step = output_dir / f"{stem}.step"
    brep = output_dir / f"{stem}.brep"
    shape.exportStep(str(step))
    shape.exportBrep(str(brep))
    return {"step": str(step), "brep": str(brep)}
