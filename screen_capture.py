import io
from mss import mss
from PIL import Image

class ScreenCapturer:
    def __init__(self, monitor_index: int = 1):
        self.sct = mss()
        self.monitor_index = monitor_index

    def grab_jpeg_bytes(self, quality: int = 55) -> bytes:
        monitor = self.sct.monitors[self.monitor_index]
        img = self.sct.grab(monitor)
        pil = Image.frombytes("RGB", img.size, img.rgb)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    
    def set_monitor(self, monitor_index: int):
        self.monitor_index = monitor_index
