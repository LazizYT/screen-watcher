import asyncio
import base64
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from agent_state import AgentState
from agent_core import AgentCore
from fastapi.responses import FileResponse
from fastapi import Body

app = FastAPI()
state = AgentState()
agent = AgentCore(state)

@app.post("/api/set_monitor")
def set_monitor(payload: dict = Body(...)):
    idx = int(payload.get("monitor_index", 1))
    agent.set_monitor(idx)
    return {"monitor_index": idx}

@app.get("/favicon.ico")
def favicon():
    return FileResponse("ui/favicon.ico")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/")
def root():
    return {"open": "http://127.0.0.1:8000/ui"}

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
            })

            await asyncio.sleep(0.25)
    except Exception:
        state.log("UI disconnected")
