"""FastAPI bridge smoke tests. Run pytest -q test_server.py"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as mod
client = TestClient(mod.app)

def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] in ("cubism", "reference_preview")
    assert data["aside_default"] is None

def test_no_aside_by_default():
    r = client.post("/api/events", json={"reply":"正常回答"})
    assert r.status_code == 200
    assert not r.json()["aside_shown_candidate"]

def test_optional_aside():
    r = client.post("/api/events", json={"reply":"整理好了","aside":{"text":"这一版还不错。","expression":"tease_smile"}})
    assert r.status_code == 200
    assert r.json()["aside_shown_candidate"]

def test_serious_suppression():
    r = client.post("/api/events",json={"reply":"认真处理","aside":{"text":"不应该出现。"},"context_safety":"serious"})
    assert r.status_code == 200
    assert not r.json()["aside_shown_candidate"]

def test_reject_long_aside():
    r = client.post("/api/events",json={"aside":{"text":"字"*25}})
    assert r.status_code == 422

def test_path_traversal_not_exposed():
    assert client.get("/assets/../../README.md").status_code in (404,400)

def test_chat_requires_user_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    response = client.post("/api/chat", json={"message":"你好"})
    assert response.status_code == 503

def test_chat_mocked_without_real_api_call(monkeypatch):
    import deepseek_client
    monkeypatch.setenv("DEEPSEEK_API_KEY","test-not-a-real-key")
    async def fake_generate(message, allow_aside=True, serious=False):
        return {"reply": "好的，我来处理。", "aside": {"text": "有点意思。", "expression": "tease_smile"}}
    monkeypatch.setattr(deepseek_client, "generate", fake_generate)
    response = client.post("/api/chat",json={"message":"你好","allow_aside":True})
    assert response.status_code == 200
    assert response.json()["event"]["reply"] == "好的，我来处理。"
    assert response.json()["event"]["aside"]["text"] == "有点意思。"

def test_chat_serious_suppresses_model_aside(monkeypatch):
    import deepseek_client
    monkeypatch.setenv("DEEPSEEK_API_KEY","test-not-a-real-key")
    async def fake_generate(message, allow_aside=True, serious=False):
        return {"reply": "认真处理。", "aside": {"text": "这不该显示。"}}
    monkeypatch.setattr(deepseek_client, "generate", fake_generate)
    response = client.post("/api/chat",json={"message":"认真事","context_safety":"serious"})
    assert response.status_code == 200
    assert response.json()["event"]["aside"] is None


def test_integrated_detail_inspector():
    result = client.get("/review")
    assert result.status_code == 200
    assert "图层精修检查器" in result.text
    assert 'id="sourceCanvas"' in result.text
    assert 'id="partCanvas"' in result.text

def test_identity_reference_served_from_original_art():
    result = client.get("/source/identity")
    assert result.status_code == 200
    assert result.headers["content-type"].startswith("image/png")

def test_status_exposes_reference_cutout_url():
    result = client.get("/api/status")
    assert result.status_code == 200
    assert result.json()["subject_url"].startswith("/assets/00_subject_cutout")
