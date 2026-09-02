from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import sqrt

from pydantic import BaseModel, ConfigDict, Field

from .drawing_ir import DrawingViewIR, ViewFrame

Vec2 = tuple[float, float]
Vec3 = tuple[float, float, float]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VertexCandidate(StrictModel):
    id: str
    point: Vec3
    supporting_views: list[str]
    projection_error: float = Field(ge=0)


class WireframeCandidateIR(StrictModel):
    version: str = "0.1"
    units: str = "mm"
    vertices: list[VertexCandidate]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a: Vec3) -> float:
    return sqrt(_dot(a, a))


def _view_point_to_ray(frame: ViewFrame, p: Vec2) -> tuple[Vec3, Vec3]:
    origin = frame.origin_world
    base = _add(
        origin,
        _add(_mul(frame.x_axis_world, p[0]), _mul(frame.y_axis_world, p[1])),
    )
    return base, frame.projection_direction


def _project_world(frame: ViewFrame, p: Vec3) -> Vec2:
    rel = _sub(p, frame.origin_world)
    return (_dot(rel, frame.x_axis_world), _dot(rel, frame.y_axis_world))


def _closest_point_between_rays(a0: Vec3, ad: Vec3, b0: Vec3, bd: Vec3) -> tuple[Vec3, float]:
    w0 = _sub(a0, b0)
    aa = _dot(ad, ad)
    bb = _dot(ad, bd)
    cc = _dot(bd, bd)
    dd = _dot(ad, w0)
    ee = _dot(bd, w0)
    denom = aa * cc - bb * bb
    if abs(denom) < 1e-12:
        raise ValueError("parallel projection rays cannot determine a unique 3D point")
    s = (bb * ee - cc * dd) / denom
    t = (aa * ee - bb * dd) / denom
    pa = _add(a0, _mul(ad, s))
    pb = _add(b0, _mul(bd, t))
    midpoint = _mul(_add(pa, pb), 0.5)
    return midpoint, _norm(_sub(pa, pb))


def _unique_endpoints(view: DrawingViewIR, digits: int = 7) -> list[Vec2]:
    points: dict[tuple[float, float], Vec2] = {}
    for entity in view.entities:
        # Closed curves do not create topological vertices in the projected wireframe.
        if entity.closed:
            continue
        for p in (entity.start, entity.end):
            key = (round(p[0], digits), round(p[1], digits))
            points.setdefault(key, p)
    return list(points.values())


def _nearest_2d_distance(p: Vec2, candidates: list[Vec2]) -> float:
    if not candidates:
        return float("inf")
    return min(sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) for q in candidates)


def reconstruct_vertex_candidates(
    views: list[DrawingViewIR],
    *,
    ray_tolerance: float = 1e-6,
    reprojection_tolerance: float = 1e-5,
    dedupe_tolerance: float = 1e-5,
) -> WireframeCandidateIR:
    """Recover 3D vertex candidates from three or more orthographic DrawingIR views.

    Two matching 2D endpoints define intersecting world-space projection rays. A
    candidate is accepted only if it re-projects onto an endpoint in at least one
    additional view. This is intentionally a conservative first stage: it recovers
    wireframe vertices, not edge correspondences or surfaces.
    """
    if len(views) < 3:
        raise ValueError("at least three views are required for cross-view verification")

    endpoints = {v.frame.name: _unique_endpoints(v) for v in views}
    raw: list[tuple[Vec3, set[str], float]] = []

    for va, vb in combinations(views, 2):
        remaining = [v for v in views if v is not va and v is not vb]
        for pa in endpoints[va.frame.name]:
            a0, ad = _view_point_to_ray(va.frame, pa)
            for pb in endpoints[vb.frame.name]:
                b0, bd = _view_point_to_ray(vb.frame, pb)
                try:
                    point, ray_error = _closest_point_between_rays(a0, ad, b0, bd)
                except ValueError:
                    continue
                if ray_error > ray_tolerance:
                    continue

                support = {va.frame.name, vb.frame.name}
                errors = [ray_error]
                for vc in remaining:
                    p2 = _project_world(vc.frame, point)
                    err = _nearest_2d_distance(p2, endpoints[vc.frame.name])
                    if err <= reprojection_tolerance:
                        support.add(vc.frame.name)
                        errors.append(err)
                if len(support) >= 3:
                    raw.append((point, support, max(errors)))

    merged: list[tuple[Vec3, set[str], float]] = []
    for point, support, err in raw:
        found = None
        for i, (existing, existing_support, existing_err) in enumerate(merged):
            if _norm(_sub(point, existing)) <= dedupe_tolerance:
                found = i
                merged[i] = (
                    tuple((existing[j] + point[j]) / 2.0 for j in range(3)),
                    existing_support | support,
                    min(existing_err, err),
                )
                break
        if found is None:
            merged.append((point, support, err))

    merged.sort(key=lambda item: tuple(round(x, 8) for x in item[0]))
    vertices = [
        VertexCandidate(
            id=f"v{i:04d}",
            point=tuple(float(x) for x in point),
            supporting_views=sorted(support),
            projection_error=float(err),
        )
        for i, (point, support, err) in enumerate(merged)
    ]
    return WireframeCandidateIR(vertices=vertices)
