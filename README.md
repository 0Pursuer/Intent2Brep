# Intent2Brep

**Intent2Brep** is a research/engineering MVP for converting constrained natural-language mechanical intent into an **analytic OpenCASCADE B-Rep**, without asking an LLM to emit a long CAD feature-command sequence.

The hypothesis is simple:

> let the model describe **geometry, dimensions and constraints**; let deterministic CAD algorithms own exact geometry.

## Current pipeline (v0.3)

```text
Natural language
   -> strict Engineering Geometry IR (Pydantic / JSON Schema)
   -> semantic/domain validation
   -> constraint resolution
   -> analytic primitives + boolean construction
   -> OpenCASCADE B-Rep
   -> BRepCheck validation
   -> STEP + native BREP
   -> exact HLR front/top/right/isometric SVGs
   -> Structured DrawingIR (visible/hidden analytic projected entities)
   -> cross-view 3D vertex candidates
```

The orthographic views and DrawingIR are currently generated **from** the B-Rep. The new cross-view module deliberately reconstructs candidate 3D vertices from the projected views rather than reading original B-Rep vertex coordinates. This is a round-trip validation/dataset-generation step; a true external `DrawingIR -> 3D wireframe -> analytic surfaces -> B-Rep` path remains the next major research module.

## Supported subset

- rectangular base plate
- optional centered vertical web/support plate
- circular through holes on base or web
- through slot on base
- centered/perpendicular relations represented explicitly in the IR
- explicit `x/y/z` hole placement for the constrained offline grammar
- Chinese constrained natural-language parser for reproducible demos
- optional OpenAI-compatible LLM parser
- exact STEP/BREP export via CadQuery/OCP/OpenCASCADE
- exact hidden-line-removal orthographic SVG generation
- per-view DrawingIR JSON with projector frame, visibility, edge class and curve type
- exact circle center/radius preservation where OCCT returns a circular projected edge
- three-view ray-intersection + reprojection filtering for 3D vertex candidates
- OpenCASCADE `BRepCheck_Analyzer` validation

### Fail-closed behavior

The pipeline deliberately refuses to silently invent missing engineering information:

- a non-centered hole without a complete location is rejected;
- a hole/slot that extends outside its target body is rejected before OCCT construction;
- unsupported requests such as fillet/chamfer fail by default instead of producing a STEP that quietly omits them;
- `--allow-unsupported` must be explicitly supplied to override that behavior during experiments.

Blind-hole data exists in the schema, but v0.3 rejects it until face/direction semantics are explicit enough to avoid guessing the drilling side.

## Installation

CadQuery officially supports both pip and conda; conda/mamba is the better-tested route because of the OCCT/OCP binary dependency stack.

### Recommended: mamba / conda

```bash
mamba env create -f environment.yml
conda activate intent2brep
python -m pip install -e . --no-deps --no-build-isolation
```

### Pip

```bash
python -m venv .venv
# activate the environment
python -m pip install -U pip
python -m pip install -e .
```

## Run

```bash
intent2brep build \
  '100x60x10 mm 底板，中间竖一个宽60mm、厚10mm、高50mm的支撑板，支撑板中心有一个直径20mm通孔。' \
  -o out
```

Outputs:

```text
out/
  01_intent.json
  02_resolved_geometry.json
  03_model.brep
  03_model.step
  04_validation.json
  views/
    front.svg
    top.svg
    right.svg
    iso.svg
    front.json
    top.json
    right.json
    iso.json
    wireframe_vertices.json
    drawing_manifest.json
```

Example explicit placement:

```bash
intent2brep build '底板 80x50x8 mm，直径12mm通孔，x=10 y=5。' -o out
```

Print the exact IR schema:

```bash
intent2brep schema
```

## Optional LLM parser

```bash
python -m pip install -e '.[llm]'
export LLM_BASE_URL=https://your-provider.example/v1
export LLM_API_KEY=...
export LLM_MODEL=...
intent2brep build 'your freer-form description' --parser llm -o out
```

The geometry backend does not depend on the provider. The model is only an **intent provider**; the schema/domain validator, constraint layer, B-Rep builder and validation remain deterministic.

## Tests

```bash
pytest -q
```

The test suite covers end-to-end B-Rep generation, explicit placement, schema CLI output, geometry-domain rejection, fail-closed unsupported-feature behavior, exact HLR DrawingIR extraction, and three-view reconstruction of box vertices.

## Design principles

1. **Model proposes intent; kernel owns geometry.**
2. **Never use pixels as the authoritative dimension source.**
3. **Prefer analytic primitives over fitted NURBS whenever possible.**
4. **Make uncertainty/underspecification explicit instead of inventing dimensions.**
5. **Reject impossible geometry before calling the CAD kernel.**
6. **Validate every generated B-Rep before export.**
7. **Use HLR re-projection as the geometry feedback loop.**

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/TECH_SURVEY.md`](docs/TECH_SURVEY.md), and [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Status

This is intentionally a narrow MVP, not a general Text-to-CAD system. v0.3 establishes a structured HLR DrawingIR and the first cross-view reconstruction primitive. The next meaningful milestone is **projected-edge correspondence + 3D wireframe reconstruction**, not more regex patterns.

## License

MIT.
