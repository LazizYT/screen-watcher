from dataclasses import dataclass

@dataclass
class Config:
    # None = весь основной монитор
    # (left, top, width, height) = область
    region = None  # например (0, 0, 1280, 720)

    fps: int = 2
    save_every_n_frames: int = 2

    # ВАЖНО: если show_preview=True и захват = весь экран,
    # будет "матрёшка". Для стабильности поставь False.
    show_preview: bool = False

    jpeg_quality: int = 85

    # Диагностика
    print_status_every_n_saves: int = 5  # печатать прогресс каждые N сохранений
