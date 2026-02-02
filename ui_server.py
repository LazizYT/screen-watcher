import asyncio
import base64
import os

from fastapi import FastAPI, WebSocket, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from agent_state import AgentState
from agent_core import AgentCore

app = FastAPI()

state = AgentState()
agent = AgentCore(state)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")


@app.get("/")
def root():
    return {"open": "http://127.0.0.1:8000/ui"}


@app.get("/favicon.ico")
def favicon():
    # чтобы не было 404/ошибок даже без файла
    return Response(status_code=204)


@app.post("/api/start")
async def api_start():
    await agent.start()
    return {"ok": True}


@app.post("/api/stop")
async def api_stop():
    await agent.stop()
    return {"ok": True}


@app.post("/api/toggle_view_only")
def toggle_view_only():
    state.view_only = not state.view_only
    state.log(f"view_only = {state.view_only}")
    return {"view_only": state.view_only}


@app.post("/api/set_monitor")
def set_monitor(payload: dict = Body(...)):
    idx = int(payload.get("monitor_index", 1))
    agent.set_monitor(idx)
    return {"monitor_index": idx}


@app.post("/api/set_save")
def set_save(payload: dict = Body(...)):
    state.save_captures = bool(payload.get("save_captures", False))
    state.capture_interval_sec = float(payload.get("capture_interval_sec", state.capture_interval_sec))
    state.log(f"save_captures = {state.save_captures}, interval = {state.capture_interval_sec}s")
    return {"save_captures": state.save_captures, "capture_interval_sec": state.capture_interval_sec}


@app.post("/api/set_quality")
def set_quality(payload: dict = Body(...)):
    q = int(payload.get("jpeg_quality", state.jpeg_quality))
    q = max(20, min(95, q))
    state.jpeg_quality = q
    state.log(f"jpeg_quality = {q}")
    return {"jpeg_quality": q}


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    state.log("UI connected")
    try:
        while True:
            frame_b64 = None
            if agent.latest_frame:
                frame_b64 = base64.b64encode(agent.latest_frame).decode("utf-8")

            await ws.send_json({
                "running": state.running,
                "view_only": state.view_only,
                "fps": state.fps,
                "last_action": state.last_action,
                "logs": state.logs[-120:],
                "frame_b64": frame_b64,

                # controls state
                "save_captures": state.save_captures,
                "capture_interval_sec": state.capture_interval_sec,
                "monitor_index": state.monitor_index,
                "jpeg_quality": state.jpeg_quality,
            })

            await asyncio.sleep(0.25)
    except Exception:
        state.log("UI disconnected")
