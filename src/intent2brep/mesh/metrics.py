from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import trimesh
from ..errors import MeshValidationError


def _as_mesh(loaded) -> trimesh.Trimesh:
    if isinstance(loaded, trimesh.Trimesh):
        return loaded
    if isinstance(loaded, trimesh.Scene):
        geometries = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not geometries:
            raise MeshValidationError("mesh scene contains no triangle geometry")
        return trimesh.util.concatenate(geometries)
    raise MeshValidationError(f"unsupported trimesh object: {type(loaded).__name__}")


def inspect_mesh(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    try:
        mesh = _as_mesh(trimesh.load(path, force=None, process=False))
    except MeshValidationError:
        raise
    except Exception as exc:
        raise MeshValidationError(f"failed to load mesh {path}: {exc}") from exc
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise MeshValidationError("generated mesh has no vertices/faces")
    bounds = np.asarray(mesh.bounds, dtype=float)
    extents = np.asarray(mesh.extents, dtype=float)
    components = mesh.split(only_watertight=False)
    return {
        "path": str(path),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
        "component_count": int(len(components)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "surface_area": float(mesh.area),
        "volume": float(mesh.volume) if mesh.is_volume else None,
        "bounds": bounds.tolist(),
        "extents": extents.tolist(),
    }
