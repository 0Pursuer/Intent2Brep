import base64
import httpx
from intent2brep.providers.i23d import Hunyuan3D21HttpProvider, Hunyuan3D2MVHttpProvider
from intent2brep.providers.t2i import OpenAICompatibleImageProvider

PNG=b"png-bytes"

def test_hunyuan3d21_request(monkeypatch,tmp_path):
    image=tmp_path/"a.png"; image.write_bytes(PNG); seen={}
    def fake_post(url,**kwargs):
        seen.update(url=url,payload=kwargs["json"]); return httpx.Response(200,content=b"mesh")
    monkeypatch.setattr(httpx,"post",fake_post)
    out=Hunyuan3D21HttpProvider("http://model").generate({"front":image},tmp_path/"m.glb",seed=7)
    assert out.read_bytes()==b"mesh" and seen["url"].endswith("/generate")
    assert base64.b64decode(seen["payload"]["image"])==PNG and seen["payload"]["seed"]==7

def test_hunyuan3d2mv_request(monkeypatch,tmp_path):
    front=tmp_path/"f.png"; left=tmp_path/"l.png"; front.write_bytes(PNG); left.write_bytes(PNG); seen={}
    def fake_post(url,**kwargs):
        seen.update(url=url,payload=kwargs["json"]); return httpx.Response(200,content=b"mesh")
    monkeypatch.setattr(httpx,"post",fake_post)
    Hunyuan3D2MVHttpProvider("http://mv").generate({"front":front,"left":left},tmp_path/"m.glb")
    assert seen["url"].endswith("/generate-mv") and set(seen["payload"]["images"])=={"front","left"}

def test_openai_compatible_t2i_b64(monkeypatch,tmp_path):
    payload=base64.b64encode(PNG).decode(); seen={}
    def fake_post(url,**kwargs):
        seen.update(url=url,payload=kwargs["json"]); return httpx.Response(200,json={"data":[{"b64_json":payload}]})
    monkeypatch.setattr(httpx,"post",fake_post)
    out=OpenAICompatibleImageProvider("http://t2i/v1","model-x", send_seed=True).generate("prompt",tmp_path/"x.png",seed=9)
    assert out.read_bytes()==PNG and seen["url"]=="http://t2i/v1/images/generations" and seen["payload"]["seed"]==9
