from __future__ import annotations

from dataclasses import dataclass, field

from scipy.optimize import least_squares

from .errors import UnderspecifiedIntentError
from .models import PartIntent


@dataclass
class ResolvedWeb:
    width: float
    thickness: float
    height: float
    x: float
    y: float
    z0: float


@dataclass
class ResolvedHole:
    diameter: float
    target: str
    axis: str
    center: tuple[float, float, float]
    length: float


@dataclass
class ResolvedSlot:
    length: float
    width: float
    center: tuple[float, float]


@dataclass
class ResolvedPart:
    intent: PartIntent
    web: ResolvedWeb | None = None
    holes: list[ResolvedHole] = field(default_factory=list)
    slots: list[ResolvedSlot] = field(default_factory=list)
    residual_norm: float = 0.0


def resolve_constraints(intent: PartIntent) -> ResolvedPart:
    """Resolve a small set of geometric constraints numerically.

    This deliberately uses a generic least-squares formulation so the MVP has a
    clear migration path to SolveSpace/FreeCAD's full sketch solver later.
    """
    b = intent.base
    web = None
    residual_norm = 0.0
    if intent.web:
        w = intent.web
        if not w.centered_on_base and (w.x is None or w.y is None):
            raise UnderspecifiedIntentError("non-centered web requires x and y")
        x0 = 0.0 if w.x is None else w.x
        y0 = 0.0 if w.y is None else w.y

        def residual(v):
            x, y = v
            r = []
            if w.centered_on_base:
                r.extend([x, y])
            if w.x is not None:
                r.append((x - w.x) * 10.0)
            if w.y is not None:
                r.append((y - w.y) * 10.0)
            return r or [0.0]

        sol = least_squares(residual, [x0, y0])
        residual_norm = float((sol.fun @ sol.fun) ** 0.5)
        web = ResolvedWeb(w.width, w.thickness, w.height, float(sol.x[0]), float(sol.x[1]), b.thickness)

    holes: list[ResolvedHole] = []
    for h in intent.holes:
        if h.target == "web":
            if web is None:
                raise ValueError("hole targets web but no web exists")
            if not h.centered_on_target and (h.x is None or h.z is None):
                raise UnderspecifiedIntentError("non-centered web hole requires x and z")
            x = web.x if h.x is None else h.x
            z = web.z0 + web.height / 2 if h.z is None else h.z
            y = web.y if h.y is None else h.y
            length = web.thickness + 4.0 if h.through else float(h.depth)
            holes.append(ResolvedHole(h.diameter, "web", "Y", (x, y, z), length))
        else:
            if not h.centered_on_target and (h.x is None or h.y is None):
                raise UnderspecifiedIntentError("non-centered base hole requires x and y")
            x = 0.0 if h.x is None else h.x
            y = 0.0 if h.y is None else h.y
            z = b.thickness / 2 if h.z is None else h.z
            length = b.thickness + 4.0 if h.through else float(h.depth)
            holes.append(ResolvedHole(h.diameter, "base", "Z", (x, y, z), length))

    slots: list[ResolvedSlot] = []
    for s in intent.slots:
        if not s.centered_on_target and (s.x is None or s.y is None):
            raise UnderspecifiedIntentError("non-centered slot requires x and y")
        x = 0.0 if s.x is None else s.x
        y = 0.0 if s.y is None else s.y
        slots.append(ResolvedSlot(s.length, s.width, (x, y)))

    return ResolvedPart(intent=intent, web=web, holes=holes, slots=slots, residual_norm=residual_norm)
