import asyncio
import time
from agent_state import AgentState
from screen_capture import ScreenCapturer
import os
from datetime import datetime

CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

class AgentCore:
    def set_monitor(self, idx: int):
        self.capturer.set_monitor(idx)
        self.state.log(f"monitor_index = {idx}")

    def __init__(self, state: AgentState):
        self.state = state
        self.capturer = ScreenCapturer(monitor_index=1)
        self.latest_frame: bytes | None = None

        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self):
        if self.state.running:
            return
        self.state.running = True
        self._stop.clear()
        self.state.log("Agent started")
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if not self.state.running:
            return
        self.state.log("Stopping agent...")
        self.state.running = False
        self._stop.set()
        if self._task:
            await self._task
        self.state.log("Agent stopped")

    async def _loop(self):
        last = time.time()
        frames = 0

        while not self._stop.is_set():
            try:
                self.latest_frame = self.capturer.grab_jpeg_bytes(quality=55)
                self.state.last_frame_ts = time.time()
                frames += 1
            except Exception as e:
                self.state.log(f"Capture error: {e}")
            if self.state.save_captures:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(CAPTURE_DIR, f"{ts}.jpg")
                with open(path, "wb") as f:
                    f.write(self.latest_frame)

            if self.state.view_only:
                self.state.last_action = "View-only: watching screen"
            else:
                # сюда позже вставим "агент делает что-то"
                self.state.last_action = "Active mode: (logic goes here)"

            now = time.time()
            if now - last >= 1.0:
                self.state.fps = frames / (now - last)
                frames = 0
                last = now

            await asyncio.sleep(0.2)  # ~5 FPS
