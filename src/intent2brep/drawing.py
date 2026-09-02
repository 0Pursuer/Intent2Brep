from __future__ import annotations

from pathlib import Path
import json

import cadquery as cq


# Camera-to-object directions for orthographic engineering views.
VIEWS = {
    "front": (0, -1, 0),
    "top": (0, 0, 1),
    "right": (1, 0, 0),
    "iso": (-1.75, 1.1, 5),
}


def export_views(shape: cq.Shape, output_dir: Path, show_hidden: bool = True) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    for name, direction in VIEWS.items():
        svg = cq.exporters.getSVG(
            shape,
            {
                "width": 720,
                "height": 520,
                "marginLeft": 35,
                "marginTop": 35,
                "projectionDir": direction,
                "showAxes": False,
                "showHidden": show_hidden,
            },
        )
        p = output_dir / f"{name}.svg"
        p.write_text(svg, encoding="utf-8")
        out[name] = str(p)
    manifest = output_dir / "drawing_manifest.json"
    manifest.write_text(json.dumps({"views": VIEWS, "files": out}, indent=2), encoding="utf-8")
    out["manifest"] = str(manifest)
    return out
