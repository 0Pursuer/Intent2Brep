from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from ..mesh.metrics import inspect_mesh
from ..providers.base import ImageTo3DProvider, TextToImageProvider
from ..vision.prompting import build_visual_prompt


def _provider_name(provider) -> str:
    return str(getattr(provider, "name", provider.__class__.__name__))


@dataclass
class VisualPipelineResult:
    source_image: Path | None
    views: dict[str, Path]
    mesh: Path | None
    manifest: Path
    mesh_report: dict | None = None


def _write_manifest(output_dir: Path, payload: dict) -> Path:
    path = output_dir / "run_manifest.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_text_to_image(text: str, output_dir: str | Path, t2i: TextToImageProvider, *, seed: int = 42) -> VisualPipelineResult:
    out = Path(output_dir); image_dir = out / "01_t2i"; image_dir.mkdir(parents=True, exist_ok=True)
    visual_prompt = build_visual_prompt(text)
    (out / "source_prompt.txt").write_text(text, encoding="utf-8")
    (out / "visual_prompt.txt").write_text(visual_prompt, encoding="utf-8")
    image = t2i.generate(visual_prompt, image_dir / "candidate_00.png", seed=seed)
    manifest = _write_manifest(out, {"pipeline": "text2image", "seed": seed, "t2i_provider": _provider_name(t2i),
                                     "source_prompt": text, "visual_prompt": visual_prompt, "source_image": str(image)})
    return VisualPipelineResult(source_image=image, views={"front": image}, mesh=None, manifest=manifest)


def _copy_source_image(image: Path, output_dir: Path) -> Path:
    dst_dir = output_dir / "02_preprocess"; dst_dir.mkdir(parents=True, exist_ok=True)
    suffix = image.suffix.lower() or ".png"; dst = dst_dir / f"source{suffix}"
    if image.resolve() != dst.resolve(): shutil.copy2(image, dst)
    return dst


def _mesh_stage(images: Mapping[str, Path], out: Path, i23d: ImageTo3DProvider, *, seed: int,
                analyze_mesh: bool) -> tuple[Path, dict | None]:
    mesh_dir = out / "04_mesh"; mesh_dir.mkdir(parents=True, exist_ok=True)
    mesh = i23d.generate(images, mesh_dir / "raw.glb", seed=seed)
    report = inspect_mesh(mesh) if analyze_mesh else None
    if report is not None:
        report_path = mesh_dir / "mesh_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return mesh, report


def run_image_to_mesh(image: str | Path, output_dir: str | Path, i23d: ImageTo3DProvider, *, seed: int = 42,
                      analyze_mesh: bool = True) -> VisualPipelineResult:
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    source = _copy_source_image(Path(image), out)
    views = {"front": source}
    mesh, report = _mesh_stage(views, out, i23d, seed=seed, analyze_mesh=analyze_mesh)
    manifest = _write_manifest(out, {"pipeline": "image2mesh", "seed": seed, "i23d_provider": _provider_name(i23d),
                                     "views": {k: str(v) for k, v in views.items()}, "mesh": str(mesh), "mesh_report": report})
    return VisualPipelineResult(source_image=source, views=views, mesh=mesh, manifest=manifest, mesh_report=report)


def run_views_to_mesh(views: Mapping[str, str | Path], output_dir: str | Path, i23d: ImageTo3DProvider, *,
                      seed: int = 42, analyze_mesh: bool = True) -> VisualPipelineResult:
    out = Path(output_dir); view_dir = out / "03_multiview"; view_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for name, raw in views.items():
        if raw is None: continue
        src = Path(raw); dst = view_dir / f"{name}{src.suffix.lower() or '.png'}"
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        copied[name] = dst
    if not copied: raise ValueError("at least one view must be provided")
    mesh, report = _mesh_stage(copied, out, i23d, seed=seed, analyze_mesh=analyze_mesh)
    manifest = _write_manifest(out, {"pipeline": "views2mesh", "seed": seed, "i23d_provider": _provider_name(i23d),
                                     "views": {k: str(v) for k, v in copied.items()}, "mesh": str(mesh), "mesh_report": report})
    return VisualPipelineResult(source_image=copied.get("front"), views=copied, mesh=mesh, manifest=manifest, mesh_report=report)


def run_text_to_mesh(text: str, output_dir: str | Path, t2i: TextToImageProvider, i23d: ImageTo3DProvider, *,
                     seed: int = 42, analyze_mesh: bool = True) -> VisualPipelineResult:
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    first = run_text_to_image(text, out, t2i, seed=seed)
    image = first.source_image
    if image is None: raise RuntimeError("text-to-image provider produced no image")
    views = {"front": image}
    mesh, report = _mesh_stage(views, out, i23d, seed=seed, analyze_mesh=analyze_mesh)
    manifest = _write_manifest(out, {"pipeline": "text2mesh", "seed": seed, "t2i_provider": _provider_name(t2i),
                                     "i23d_provider": _provider_name(i23d), "source_image": str(image),
                                     "views": {"front": str(image)}, "mesh": str(mesh), "mesh_report": report})
    return VisualPipelineResult(source_image=image, views=views, mesh=mesh, manifest=manifest, mesh_report=report)
