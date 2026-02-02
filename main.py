import time
from pathlib import Path
from datetime import datetime

import numpy as np
import cv2
import mss

from config import Config


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


def get_capture_box(sct: mss.mss, region):
    if region is None:
        # основной монитор
        return sct.monitors[1]
    left, top, width, height = region
    return {"left": left, "top": top, "width": width, "height": height}


def main():
    cfg = Config()

    # ВАЖНО: пути всегда относительно main.py, а не текущей папки запуска
    base_dir = Path(__file__).resolve().parent
    captures_dir = base_dir / "captures"
    debug_dir = base_dir / "debug"
    captures_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    print("Screen Watcher started ✅")
    print("Project dir:", base_dir)
    print("Captures dir:", captures_dir)
    print("Region:", cfg.region if cfg.region else "FULL SCREEN (monitor 1)")
    print("FPS:", cfg.fps, "| Save every:", cfg.save_every_n_frames, "frames")
    print("Stop: Ctrl+C", "| Preview:", cfg.show_preview)

    frame_interval = 1.0 / max(1, cfg.fps)
    frame_count = 0
    saved_count = 0
    last_status_print = 0

    with mss.mss() as sct:
        box = get_capture_box(sct, cfg.region)

        while True:
            t0 = time.time()

            # Захват
            shot = sct.grab(box)
            frame = np.array(shot)  # BGRA
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            frame_count += 1

            # Сохранение
            if frame_count % max(1, cfg.save_every_n_frames) == 0:
                saved_count += 1
                file_path = captures_dir / f"{stamp()}.jpg"

                ok = cv2.imwrite(
                    str(file_path),
                    frame_bgr,
                    [int(cv2.IMWRITE_JPEG_QUALITY), int(cfg.jpeg_quality)]
                )

                # Если вдруг не записалось — сохраняем debug png
                if not ok:
                    dbg = debug_dir / f"FAILED_{stamp()}.png"
                    cv2.imwrite(str(dbg), frame_bgr)
                    print("⚠️ Save failed, wrote debug frame to:", dbg)
                else:
                    if saved_count % cfg.print_status_every_n_saves == 0:
                        print(f"Saved {saved_count} frames. Last:", file_path.name)

            # Превью (лучше держать False, чтобы не было матрёшки)
            if cfg.show_preview:
                preview = frame_bgr.copy()
                cv2.putText(
                    preview,
                    f"saved={saved_count} fps={cfg.fps} every={cfg.save_every_n_frames}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("Screen Watcher", preview)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Держим FPS
            dt = time.time() - t0
            sleep_for = frame_interval - dt
            if sleep_for > 0:
                time.sleep(sleep_for)

    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("\nStopped by Ctrl+C.")
