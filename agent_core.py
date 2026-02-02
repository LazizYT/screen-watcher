import asyncio
import time
import os
from datetime import datetime

from agent_state import AgentState
from screen_capture import ScreenCapturer

CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)


class AgentCore:
    def __init__(self, state: AgentState):
        self.state = state
        self.capturer = ScreenCapturer(monitor_index=state.monitor_index)
        self.latest_frame: bytes | None = None

        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

        self._last_saved = 0.0

    def set_monitor(self, idx: int):
        self.state.monitor_index = idx
        self.capturer.set_monitor(idx)
        self.state.log(f"monitor_index = {idx}")

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
        self.latest_frame = None
        self.state.log("Agent stopped")

    async def _loop(self):
        last_fps_ts = time.time()
        frames = 0

        # частота обновления кадра: 1 / fps (если fps=0 → дефолт 5 fps)
        def loop_sleep():
            # UI fps ≠ capture fps, но пока держим простое управление
            # хочешь — добавим отдельный state.capture_fps
            return 0.2

        while not self._stop.is_set():
            try:
                self.latest_frame = self.capturer.grab_jpeg_bytes(
                    quality=int(self.state.jpeg_quality)
                )
                self.state.last_frame_ts = time.time()
                frames += 1
            except Exception as e:
                self.state.log(f"Capture error: {e}")

            # сохранение: строго по интервалу
            now = time.time()
            if (
                self.state.save_captures
                and self.latest_frame
                and (now - self._last_saved) >= max(0.2, float(self.state.capture_interval_sec))
            ):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(CAPTURE_DIR, f"{ts}.jpg")
                try:
                    with open(path, "wb") as f:
                        f.write(self.latest_frame)
                    self._last_saved = now
                except Exception as e:
                    self.state.log(f"Save error: {e}")

            self.state.last_action = (
                "View-only: watching screen" if self.state.view_only
                else "Active mode: (logic goes here)"
            )

            # FPS метрика
            if now - last_fps_ts >= 1.0:
                self.state.fps = frames / (now - last_fps_ts)
                frames = 0
                last_fps_ts = now

            await asyncio.sleep(loop_sleep())
