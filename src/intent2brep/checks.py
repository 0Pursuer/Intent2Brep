from __future__ import annotations

from .errors import GeometryDomainError, UnderspecifiedIntentError
from .models import PartIntent

EPS = 1e-9


def _inside(center: float, half_feature: float, half_container: float) -> bool:
    return abs(center) + half_feature <= half_container + EPS


def validate_intent_domain(intent: PartIntent) -> None:
    """Reject impossible/underspecified geometry before touching OpenCASCADE.

    The MVP intentionally prefers a clear error to silently inventing a location.
    """
    b = intent.base

    if intent.web:
        w = intent.web
        if w.centered_on_base:
            wx = 0.0 if w.x is None else w.x
            wy = 0.0 if w.y is None else w.y
        else:
            if w.x is None or w.y is None:
                raise UnderspecifiedIntentError(
                    "web is not centered, so both web.x and web.y must be specified"
                )
            wx, wy = w.x, w.y

        if not _inside(wx, w.width / 2.0, b.length / 2.0):
            raise GeometryDomainError("web width/position extends outside the base length")
        if not _inside(wy, w.thickness / 2.0, b.width / 2.0):
            raise GeometryDomainError("web thickness/position extends outside the base width")

    for idx, h in enumerate(intent.holes):
        if not h.through:
            raise GeometryDomainError(
                f"hole[{idx}] is blind; v0.2 requires a face/direction semantic before blind holes are built"
            )
        if h.target == "web":
            if intent.web is None:
                raise GeometryDomainError(f"hole[{idx}] targets web but no web exists")
            w = intent.web
            if h.centered_on_target:
                x = (0.0 if w.x is None else w.x) if h.x is None else h.x
                z = b.thickness + w.height / 2.0 if h.z is None else h.z
            else:
                if h.x is None or h.z is None:
                    raise UnderspecifiedIntentError(
                        f"hole[{idx}] on web is not centered; x and z must be specified"
                    )
                x, z = h.x, h.z
            web_x = 0.0 if w.x is None else w.x
            if not _inside(x - web_x, h.diameter / 2.0, w.width / 2.0):
                raise GeometryDomainError(f"hole[{idx}] exceeds web width")
            local_z = z - b.thickness
            if local_z - h.diameter / 2.0 < -EPS or local_z + h.diameter / 2.0 > w.height + EPS:
                raise GeometryDomainError(f"hole[{idx}] exceeds web height")
        else:
            if h.centered_on_target:
                x = 0.0 if h.x is None else h.x
                y = 0.0 if h.y is None else h.y
            else:
                if h.x is None or h.y is None:
                    raise UnderspecifiedIntentError(
                        f"hole[{idx}] on base is not centered; x and y must be specified"
                    )
                x, y = h.x, h.y
            if not _inside(x, h.diameter / 2.0, b.length / 2.0):
                raise GeometryDomainError(f"hole[{idx}] exceeds base length")
            if not _inside(y, h.diameter / 2.0, b.width / 2.0):
                raise GeometryDomainError(f"hole[{idx}] exceeds base width")

    for idx, s in enumerate(intent.slots):
        if s.length <= s.width:
            raise GeometryDomainError(f"slot[{idx}] length must be greater than width")
        if not s.through:
            raise GeometryDomainError(f"slot[{idx}] blind slots are not supported in the MVP")
        if s.centered_on_target:
            x = 0.0 if s.x is None else s.x
            y = 0.0 if s.y is None else s.y
        else:
            if s.x is None or s.y is None:
                raise UnderspecifiedIntentError(
                    f"slot[{idx}] is not centered; x and y must be specified"
                )
            x, y = s.x, s.y
        if not _inside(x, s.length / 2.0, b.length / 2.0):
            raise GeometryDomainError(f"slot[{idx}] exceeds base length")
        if not _inside(y, s.width / 2.0, b.width / 2.0):
            raise GeometryDomainError(f"slot[{idx}] exceeds base width")
