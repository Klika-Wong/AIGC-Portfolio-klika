"""FastAPI bridge smoke tests. Run pytest -q test_server.py"""
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location("klika_bridge", Path(__file__).with_name("server.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
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
