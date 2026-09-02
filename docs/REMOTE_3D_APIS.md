# Remote 3D API survey (2026-09-02)

This note tracks hosted image-to-3D APIs that can be useful for Intent2Brep benchmarking without running a local GPU service.

The important distinction is **web-app free credits vs API free credits**.  A provider is not treated as a free API merely because its browser UI has a free plan.

## Best current candidates

| Provider | 3D API | Free / trial API status | Useful output | Intent2Brep relevance |
|---|---|---|---|---|
| Stability AI | Stable Fast 3D, SPAR3D | New Google-login accounts currently receive 25 platform credits; SF3D costs 10 credits and SPAR3D 4 credits per successful generation | GLB binary | Excellent first non-Hunyuan baseline. SPAR3D is especially cheap for topology tests. |
| Hi3D / Hitem3D | Sparc3D / Ultra3D image-to-3D | Official API docs expose a test resource package for integration; exact trial amount is account/console dependent | OBJ, GLB, STL, FBX, USDZ, 3MF | Strong domestic alternative; supports geometry-only and multi-view generation. |
| Replicate + TRELLIS | Community TRELLIS deployments | Replicate allows limited free runs on selected models before billing is required; this is not a guaranteed permanent quota | GLB + optional Gaussian PLY / renders | Very useful research baseline because TRELLIS is open and multi-image capable. |
| fal.ai + TRELLIS | TRELLIS single/multi-image API | API is low-cost, but fal free credits/coupons are documented as Sandbox/Playground-only, not API usage | generated mesh file | Cheap fallback, but do not call it a free API. |

## Services that look free in the web UI but are not free APIs

### Meshy

Meshy has a free browser plan, but current API documentation says generation API usage is prepaid and the API product page requires Pro or above for API access.  Do not count the 100 monthly web credits as API credits.

### Tripo

Tripo has a free browser plan, but its API platform uses a separate wallet/billing system.  Current documentation explicitly says web-app and API credits are independent.  No guaranteed free API grant was found in the public API documentation.

### Hyper3D / Rodin

The browser free plan lets users generate before confirmation, but the pricing comparison currently places API access on the Business tier.  Public marketing pages also say "start building for free", so the API-free status is ambiguous; treat it as non-free until the developer console grants API credits.

## Recommended benchmark order

For a provider-neutral benchmark, prefer geometry-only generation and avoid paying for texture/PBR when possible:

1. Local Hunyuan3D-2.1 / 2mv baseline (existing provider).
2. Stability SPAR3D API.
3. Hi3D geometry-only API.
4. TRELLIS via Replicate or fal.ai.
5. Cloud Hunyuan / other commercial providers if needed.

The benchmark should compare the raw generated mesh against the tessellated reference STEP before any CADification stage.  Keep the same canonical render, seed when supported, camera convention, mesh normalization, and metric suite across providers.

## Primary references

- Stability pricing: https://platform.stability.ai/pricing
- Stability API reference: https://platform.stability.ai/docs/api-reference
- Hi3D API docs: https://docs.hi3d.ai/en/api/
- Hi3D API pricing: https://docs.hi3d.ai/en/api/getting-started/pricing
- Replicate billing: https://replicate.com/docs/topics/billing/
- Replicate TRELLIS: https://replicate.com/firtoz/trellis
- fal TRELLIS API: https://fal.ai/models/fal-ai/trellis/api
- fal Sandbox free-credit policy: https://fal.ai/docs/documentation/model-apis/sandbox
- Meshy API pricing: https://docs.meshy.ai/en/api/pricing
- Meshy API access: https://www.meshy.ai/api
- Tripo API FAQ: https://platform.tripo3d.ai/docs/faq
- Tripo API quick start: https://platform.tripo3d.ai/docs/quick-start
- Hyper3D pricing: https://hyper3d.ai/pricing
