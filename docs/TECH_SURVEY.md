# Technical survey and MVP decisions (2026-09)

This document maps each stage of the proposed Text -> Engineering Representation -> B-Rep pipeline to mature technologies and open-source references.

| Stage | Problem | Mature/reference technology | MVP choice | Maturity |
|---|---|---|---|---|
| Natural language -> typed intent | extract dimensions, part semantics, relations | Pydantic/JSON Schema; constrained structured LLM outputs; Instructor/Outlines/PydanticAI patterns | Pydantic schema + offline regex parser + optional OpenAI-compatible JSON parser | High for syntax/schema; semantic correctness still requires validation |
| Engineering constraints | centered, perpendicular, tangent, dimensional relations | SolveSpace solver (`slvs` API); FreeCAD Sketcher PlaneGCS | SciPy least-squares adapter now; design interface for replacement by SolveSpace/PlaneGCS | High for 2D sketch constraints |
| Technical drawing generation | exact front/top/right + hidden lines | OpenCASCADE `HLRBRep_Algo`; Ortho2CAD pythonOCC drawing generator | CadQuery `getSVG`, which internally uses exact OCCT HLR | High |
| Vector DrawingIR | lines/arcs/circles/hidden edges/dimensions | SVG/DXF; Ortho2CAD drawing pipeline; 2023 rule-based orthographic reconstruction assumes vectorized SVG | v0.3 stores exact HLR entity-level DrawingIR + SVG; external SVG/DXF import is next | Medium-high |
| Cross-view matching | identify corresponding projected vertices/edges | Zhang et al. 2023 pattern matching: SVG views -> 3D edge network | v0.3 implements conservative vertex-ray intersection; full projected-edge matching is v0.4 | Medium for constrained drawings |
| 3D wireframe -> surfaces | loop detection, planar/cylindrical/etc surface hypotheses | classical CAD reconstruction; analytic geometry; BrepGaussian shows learned multi-view-to-parametric B-Rep direction | v0.3 still compiles solved semantic primitives directly; surface inference begins after full wireframe reconstruction | Medium; hard in ambiguous/general cases |
| B-Rep construction | vertices/edges/wires/faces/shell/solid + booleans | OpenCASCADE/OCP; CadQuery | CadQuery/OCP | Very high |
| Healing / simplification | sewing gaps, same-domain face merge | OCCT `BRepBuilderAPI_Sewing`, `ShapeUpgrade_UnifySameDomain`, ShapeFix packages | BRep validation now; sewing/unify when raw-face assembler lands | Very high |
| Validation | topological/geometric validity | OCCT `BRepCheck_Analyzer`; re-projection via HLR | implemented | Very high |
| STEP output | serialize B-Rep | OCCT `STEPControl_Writer`; CadQuery `exportStep` | implemented | Very high |

## Key references

- Ortho2CAD (2026): https://github.com/AdityaJoglekar/Ortho2CAD
- Ortho2CAD paper: https://arxiv.org/abs/2607.08891
- CadQuery: https://github.com/CadQuery/cadquery
- SolveSpace: https://github.com/solvespace/solvespace
- FreeCAD: https://github.com/FreeCAD/FreeCAD
- pythonOCC-core: https://github.com/tpaviot/pythonocc-core
- Text2CAD via Technical Drawings (2024): https://arxiv.org/abs/2411.06206
- Automatic 3D CAD models reconstruction from 2D orthographic drawings (2023): https://doi.org/10.1016/j.cag.2023.05.021
- Dataset for the 2023 reconstruction work: https://zenodo.org/records/7785223
- BrepGaussian (CVPR 2026): https://openaccess.thecvf.com/content/CVPR2026/html/Yu_BrepGaussian_CAD_reconstruction_from_Multi-View_Images_with_Gaussian_Splatting_CVPR_2026_paper.html

## Architectural conclusion

The low-risk engineering boundary is not `Text -> PNG -> mesh`. It is:

```text
Text -> typed engineering intent -> deterministic geometry/constraint layer -> analytic B-Rep
```

Raster/vector views are valuable as an inspection, interaction and reconstruction representation, but exact dimensions and surface-class priors should remain symbolic. The difficult research module is `Structured DrawingIR -> analytic B-Rep`, not STEP export.
