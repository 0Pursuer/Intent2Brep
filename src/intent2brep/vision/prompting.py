from __future__ import annotations


def build_visual_prompt(text: str) -> str:
    """Turn user wording into a reconstruction-friendly visual prompt, not geometry JSON."""
    suffix = (
        "\n\nRender specification: a single isolated mechanical CAD part; neutral matte gray material; "
        "clean white background; isometric three-quarter product view; orthographic-like weak perspective; "
        "sharp hard-surface edges; clearly visible holes, slots, thin walls and openings; no assembly context; "
        "no screws or fasteners unless explicitly requested; no text, labels or dimension annotations; "
        "no dramatic lighting, reflections, depth of field or decorative texture. Preserve mechanical symmetry."
    )
    return text.strip() + suffix
