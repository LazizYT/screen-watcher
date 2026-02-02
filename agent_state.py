from dataclasses import dataclass, field
from typing import List
import time


@dataclass
class AgentState:
    running: bool = False
    view_only: bool = True

    # telemetry
    fps: float = 0.0
    last_action: str = "—"
    last_frame_ts: float = 0.0

    # logs
    logs: List[str] = field(default_factory=list)

    # capture controls (UI-controlled)
    save_captures: bool = False
    capture_interval_sec: float = 1.0
    monitor_index: int = 1
    jpeg_quality: int = 85  # подружим с Config по умолчанию
    
    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {msg}")
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]
