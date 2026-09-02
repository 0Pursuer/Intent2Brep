from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from ..builder import build_brep, export_shape
from ..checks import validate_intent_domain
from ..errors import UnsupportedIntentError
from ..drawing import export_views
from ..drawing_ir import DrawingViewIR
from ..cross_view import reconstruct_vertex_candidates
from ..models import PartIntent
from ..parser import IntentParser, OpenAICompatibleIntentParser, RegexIntentParser
from ..resolver import ResolvedPart, resolve_constraints
from ..validation import validate_shape


@dataclass
class PipelineResult:
    intent: PartIntent
    resolved: ResolvedPart
    outputs: dict[str, str]
    validation: dict


def run_parametric_pipeline(text: str, output_dir: str | Path, parser: str | IntentParser = "regex", *,
                            allow_unsupported: bool = False) -> PipelineResult:
    """Legacy deterministic baseline: text -> PartIntent -> analytic CSG/B-Rep."""
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    if isinstance(parser, str):
        parser_obj = RegexIntentParser() if parser == "regex" else OpenAICompatibleIntentParser() if parser == "llm" else None
        if parser_obj is None: raise ValueError(f"unknown parser: {parser}")
    else: parser_obj = parser
    intent = parser_obj.parse(text)
    (out / "01_intent.json").write_text(intent.model_dump_json(indent=2), encoding="utf-8")
    if intent.unsupported_requests and not allow_unsupported:
        raise UnsupportedIntentError("; ".join(intent.unsupported_requests))
    validate_intent_domain(intent)
    resolved = resolve_constraints(intent)
    resolved_json = {"web": vars(resolved.web) if resolved.web else None,
                     "holes": [vars(x) for x in resolved.holes], "slots": [vars(x) for x in resolved.slots],
                     "constraint_residual_norm": resolved.residual_norm}
    (out / "02_resolved_geometry.json").write_text(json.dumps(resolved_json, indent=2), encoding="utf-8")
    shape = build_brep(resolved)
    outputs = export_shape(shape, out, "03_model")
    outputs.update({f"view_{k}": v for k, v in export_views(shape, out / "views").items()})
    ortho_views = [DrawingViewIR.model_validate_json((out / "views" / f"{name}.json").read_text(encoding="utf-8"))
                   for name in ("front", "top", "right")]
    wireframe = reconstruct_vertex_candidates(ortho_views)
    wireframe_path = out / "views" / "wireframe_vertices.json"
    wireframe_path.write_text(wireframe.model_dump_json(indent=2), encoding="utf-8")
    outputs["wireframe_vertices"] = str(wireframe_path)
    validation = validate_shape(shape)
    (out / "04_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    outputs.update({"intent": str(out / "01_intent.json"), "resolved": str(out / "02_resolved_geometry.json"),
                    "validation": str(out / "04_validation.json")})
    return PipelineResult(intent, resolved, outputs, validation)
