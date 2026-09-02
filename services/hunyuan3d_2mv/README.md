# Hunyuan3D-2mv sidecar

This sidecar exposes Tencent's 1-4 view `Hunyuan3D-2mv` model as a tiny HTTP service so the CadQuery/OpenCASCADE environment stays isolated from the PyTorch/CUDA model environment.

Use the **Tencent Hunyuan3D-2 repository/model environment**. Copy or mount `server.py` there and run:

```bash
python server.py --port 8082
```

Then in Intent2Brep:

```bash
intent2brep views2mesh --front front.png --left left.png --back back.png -o out
```

The accepted named views are `front`, `back`, `left`, and `right`, matching the public Hunyuan3D-2mv Gradio implementation.
