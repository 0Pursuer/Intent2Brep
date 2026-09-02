"""Optional Hunyuan3D-2mv sidecar service.

Run this in the *Hunyuan3D-2* model environment, not in Intent2Brep's CadQuery environment.
"""
from __future__ import annotations

import argparse
import base64
import io
from typing import Dict


def create_app(model_path: str = "tencent/Hunyuan3D-2mv", subfolder: str = "hunyuan3d-dit-v2-mv", device: str = "cuda"):
    import torch
    import trimesh
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response
    from PIL import Image
    from pydantic import BaseModel, Field
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
    from hy3dgen.rembg import BackgroundRemover

    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path, subfolder=subfolder, device=device)
    rembg = BackgroundRemover()
    app = FastAPI(title="Intent2Brep Hunyuan3D-2mv sidecar")

    class MVRequest(BaseModel):
        images: Dict[str, str]
        seed: int = 42
        octree_resolution: int = Field(380, ge=64, le=512)
        num_inference_steps: int = Field(30, ge=1, le=100)
        guidance_scale: float = Field(5.0, gt=0)
        num_chunks: int = Field(20000, ge=1000)
        type: str = "glb"

    @app.get("/health")
    def health(): return {"status": "healthy", "model": model_path}

    @app.post("/generate-mv")
    def generate_mv(req: MVRequest):
        allowed = {k:v for k,v in req.images.items() if k in {"front","back","left","right"}}
        if not allowed: raise HTTPException(422, "front/back/left/right image required")
        images = {}
        for k, v in allowed.items():
            image = Image.open(io.BytesIO(base64.b64decode(v)))
            image = rembg(image) if image.mode == "RGB" else image.convert("RGBA")
            images[k] = image
        generator = torch.manual_seed(req.seed)
        outputs = pipeline(image=images, num_inference_steps=req.num_inference_steps,
                           guidance_scale=req.guidance_scale, generator=generator,
                           octree_resolution=req.octree_resolution, num_chunks=req.num_chunks,
                           output_type="trimesh")
        mesh = outputs[0]
        file_type = "glb" if req.type.lower() not in {"glb","obj","ply","stl"} else req.type.lower()
        blob = mesh.export(file_type=file_type)
        if isinstance(blob, str): blob = blob.encode("utf-8")
        return Response(content=blob, media_type="application/octet-stream")
    return app


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--host",default="0.0.0.0"); parser.add_argument("--port",type=int,default=8082)
    parser.add_argument("--model-path",default="tencent/Hunyuan3D-2mv"); parser.add_argument("--subfolder",default="hunyuan3d-dit-v2-mv")
    parser.add_argument("--device",default="cuda"); args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_app(args.model_path,args.subfolder,args.device),host=args.host,port=args.port)

if __name__ == "__main__": main()
