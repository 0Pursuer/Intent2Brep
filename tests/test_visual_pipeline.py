import json
from pathlib import Path
import trimesh
from intent2brep.pipelines.visual import run_image_to_mesh, run_text_to_image, run_text_to_mesh, run_views_to_mesh

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c63606060f80f0001040100b51c0c020000000049454e44ae426082")

class FakeT2I:
    name="fake-t2i"
    def generate(self,prompt,output,*,seed=42):
        assert "mechanical CAD part" in prompt; output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(PNG); return output
class FakeI23D:
    name="fake-i23d"
    def generate(self,images,output,*,seed=42):
        assert images; output.parent.mkdir(parents=True,exist_ok=True); trimesh.creation.box(extents=(1,2,3)).export(output); return output

def test_text_to_image_manifest(tmp_path):
    r=run_text_to_image("simple bracket",tmp_path,FakeT2I()); assert r.source_image.exists() and r.manifest.exists()
    data=json.loads(r.manifest.read_text()); assert data["t2i_provider"]=="fake-t2i"
def test_text_to_mesh_end_to_end(tmp_path):
    r=run_text_to_mesh("simple bracket",tmp_path,FakeT2I(),FakeI23D()); assert r.mesh.exists() and r.mesh_report["face_count"]>0
    assert r.mesh_report["watertight"] is True; assert json.loads(r.manifest.read_text())["pipeline"]=="text2mesh"
def test_image_to_mesh_copies_source(tmp_path):
    image=tmp_path/"in.png"; image.write_bytes(PNG); out=tmp_path/"run"
    r=run_image_to_mesh(image,out,FakeI23D()); assert r.source_image != image and r.source_image.exists() and r.mesh.exists()
def test_views_to_mesh_preserves_named_views(tmp_path):
    front=tmp_path/"front.png"; left=tmp_path/"left.png"; front.write_bytes(PNG); left.write_bytes(PNG)
    r=run_views_to_mesh({"front":front,"left":left},tmp_path/"run",FakeI23D()); assert set(r.views)=={"front","left"}; assert r.mesh_report["vertex_count"]==8
