"""Backward-compatible shim for the v0.3 parametric pipeline.

New code should import `run_parametric_pipeline` from `intent2brep.pipelines` or use
`run_text_to_mesh` / `run_image_to_mesh` for the visual mainline.
"""
from .pipelines.parametric import PipelineResult, run_parametric_pipeline


def run_pipeline(*args, **kwargs):
    return run_parametric_pipeline(*args, **kwargs)


__all__ = ["PipelineResult", "run_pipeline", "run_parametric_pipeline"]
