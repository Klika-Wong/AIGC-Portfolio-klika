"""Local avatar HTTP/WebSocket bridge for private AI assistant.
Run: python -m uvicorn server:app --app-dir ... --host 127.0.0.1 --port 8765
Do NOT bind publicly without authentication, TLS and origin restrictions.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict

HERE = Path(__file__).resolve().parent
PARTS = HERE.parent / "04-资产生成" / "output"
MODEL = HERE / "model"
ENTRY = os.environ.get("KLIKA_MODEL_ENTRY", "character.model3.json")
app = FastAPI(title="Klika Avatar Bridge", version="0.1.0")

class Aside(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=24)
    expression: Literal["neutral", "tease_smile", "tease_brow", "tease_sideeye"] = "neutral"

class AvatarEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["assistant.reply", "avatar.state", "avatar.audio_level"] = "assistant.reply"
    reply: str = Field(default="", max_length=4000)
    aside: Aside | None = None
    expression: str = Field(default="neutral", max_length=40)
    context_safety: Literal["normal", "serious", "sensitive", "crisis"] = "normal"
    audio_level: float = Field(default=0, ge=0, le=1)

    def clean(self) -> dict:
        data = self.model_dump()
        if data["context_safety"] != "normal":
            data["aside"] = None
        return data

clients: set[WebSocket] = set()

@app.get("/")
async def index():
    return FileResponse(HERE / "viewer.html")

@app.get("/api/status")
async def status():
    valid = (MODEL / ENTRY).is_file()
    return {"connected": True, "mode": "cubism" if valid else "reference_preview",
            "model_url": "/model/" + ENTRY if valid else None,
            "parts_available": (PARTS / "00_subject_cutout.png").exists(),
            "aside_default": None}

def safe_file(root: Path, filepath: str) -> Path:
    base = root.resolve()
    target = (base / filepath).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return target

@app.get("/assets/{filepath:path}")
async def assets(filepath: str):
    return FileResponse(safe_file(PARTS, filepath))

@app.get("/model/{filepath:path}")
async def models(filepath: str):
    return FileResponse(safe_file(MODEL, filepath))

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            # Client sends keepalive or preferences, not arbitrary broadcast.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)

@app.post("/api/events")
async def publish(event: AvatarEvent):
    # A model chooses aside or null. This server only validates its shape.
    payload = event.clean()
    for ws in list(clients):
        try:
            await ws.send_json(payload)
        except Exception:
            clients.discard(ws)
    return {"ok": True, "listeners": len(clients), "aside_shown_candidate": payload["aside"] is not None}

@app.get("/api/demo")
async def demo():
    # Demo ONLY, not autonomous AI behavior.
    return {"type": "assistant.reply", "reply": "这次已经整理好了。", "aside": None,
            "expression": "neutral", "context_safety": "normal", "audio_level": 0}
