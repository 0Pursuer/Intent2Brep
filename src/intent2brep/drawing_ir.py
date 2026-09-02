from __future__ import annotations

from typing import Literal

import cadquery as cq
from cadquery.occ_impl.shapes import Shape, TOLERANCE
from OCP.BRepLib import BRepLib
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ViewFrame(StrictModel):
    name: str
    origin_world: tuple[float, float, float] = (0.0, 0.0, 0.0)
    projection_direction: tuple[float, float, float]
    x_axis_world: tuple[float, float, float]
    y_axis_world: tuple[float, float, float]


class ProjectedEntity(StrictModel):
    id: str
    visibility: Literal["visible", "hidden"]
    edge_class: Literal["sharp", "smooth", "outline"]
    geom_type: str
    closed: bool
    start: tuple[float, float]
    end: tuple[float, float]
    length: float = Field(ge=0)
    center: tuple[float, float] | None = None
    radius: float | None = Field(default=None, gt=0)
    samples: list[tuple[float, float]] = Field(default_factory=list)


class DrawingViewIR(StrictModel):
    version: Literal["0.1"] = "0.1"
    units: Literal["mm"] = "mm"
    frame: ViewFrame
    entities: list[ProjectedEntity]


def _v3(v) -> tuple[float, float, float]:
    return (float(v.X()), float(v.Y()), float(v.Z()))


def _p2(v) -> tuple[float, float]:
    return (float(v.x), float(v.y))


def _sample_edge(edge: cq.Edge, count: int = 24) -> list[tuple[float, float]]:
    if edge.geomType() == "LINE":
        return [_p2(edge.startPoint()), _p2(edge.endPoint())]
    try:
        pts, _ = edge.sample(count)
        return [_p2(p) for p in pts]
    except Exception:
        return [_p2(edge.startPoint()), _p2(edge.endPoint())]


def _entity_signature(entity: ProjectedEntity, digits: int = 7) -> tuple:
    def r2(p: tuple[float, float]) -> tuple[float, float]:
        return (round(p[0], digits), round(p[1], digits))

    if entity.geom_type == "LINE":
        a, b = sorted((r2(entity.start), r2(entity.end)))
        return ("LINE", a, b)
    if entity.geom_type == "CIRCLE" and entity.center is not None and entity.radius is not None:
        return ("CIRCLE", r2(entity.center), round(entity.radius, digits), entity.closed)
    sampled = tuple(r2(p) for p in entity.samples[:: max(1, len(entity.samples) // 8)])
    reversed_sampled = tuple(reversed(sampled))
    return (entity.geom_type, min(sampled, reversed_sampled), round(entity.length, digits), entity.closed)


def _collect_group(compound, visibility: str, edge_class: str, start_index: int) -> list[ProjectedEntity]:
    if compound.IsNull():
        return []
    BRepLib.BuildCurves3d_s(compound, TOLERANCE)
    out: list[ProjectedEntity] = []
    for i, edge in enumerate(Shape(compound).Edges(), start=start_index):
        geom_type = edge.geomType()
        center = None
        radius = None
        if geom_type == "CIRCLE":
            try:
                center = _p2(edge.arcCenter())
                radius = float(edge.radius())
            except Exception:
                center = None
                radius = None
        out.append(
            ProjectedEntity(
                id=f"e{i:04d}",
                visibility=visibility,
                edge_class=edge_class,
                geom_type=geom_type,
                closed=bool(edge.IsClosed()),
                start=_p2(edge.startPoint()),
                end=_p2(edge.endPoint()),
                length=float(edge.Length()),
                center=center,
                radius=radius,
                samples=_sample_edge(edge),
            )
        )
    return out


def extract_drawing_view_ir(
    shape: cq.Shape,
    name: str,
    direction: tuple[float, float, float],
    *,
    include_hidden: bool = True,
    prefer_visible_on_overlap: bool = True,
) -> DrawingViewIR:
    """Extract structured projected entities from OpenCASCADE exact HLR output.

    The resulting coordinates are in the HLR projector's 2D plane. The world-space
    basis vectors used by that projector are stored in ``frame`` so the 2D entities
    can later participate in cross-view reconstruction.
    """
    axis = gp_Ax2(gp_Pnt(), gp_Dir(*direction))
    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)
    hlr.Projector(HLRAlgo_Projector(axis))
    hlr.Update()
    hlr.Hide()
    h = HLRBRep_HLRToShape(hlr)

    groups: list[tuple[object, str, str]] = [
        (h.VCompound(), "visible", "sharp"),
        (h.Rg1LineVCompound(), "visible", "smooth"),
        (h.OutLineVCompound(), "visible", "outline"),
    ]
    if include_hidden:
        groups.extend(
            [
                (h.HCompound(), "hidden", "sharp"),
                (h.Rg1LineHCompound(), "hidden", "smooth"),
                (h.OutLineHCompound(), "hidden", "outline"),
            ]
        )

    entities: list[ProjectedEntity] = []
    next_id = 0
    for compound, visibility, edge_class in groups:
        current = _collect_group(compound, visibility, edge_class, next_id)
        entities.extend(current)
        next_id += len(current)

    if prefer_visible_on_overlap:
        deduped: dict[tuple, ProjectedEntity] = {}
        for entity in entities:
            sig = _entity_signature(entity)
            previous = deduped.get(sig)
            if previous is None or (
                previous.visibility == "hidden" and entity.visibility == "visible"
            ):
                deduped[sig] = entity
        entities = list(deduped.values())

    entities = [e.model_copy(update={"id": f"e{i:04d}"}) for i, e in enumerate(entities)]

    frame = ViewFrame(
        name=name,
        origin_world=_v3(axis.Location()),
        projection_direction=_v3(axis.Direction()),
        x_axis_world=_v3(axis.XDirection()),
        y_axis_world=_v3(axis.YDirection()),
    )
    return DrawingViewIR(frame=frame, entities=entities)
