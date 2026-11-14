"""Coordinate contract and repeated-cycle checks without task-specific answers."""
from __future__ import annotations
import math

def map_point(x: float, y: float, *, width: int, height: int, input_space: str, clamp: bool) -> tuple[float, float]:
    if not all(math.isfinite(v) for v in (x,y)) or width <= 0 or height <= 0:
        raise ValueError("Non-finite point or invalid viewport")
    if input_space == "normalized_1000":
        x, y = round(x * width / 1000), round(y * height / 1000)
    elif input_space != "viewport_css":
        raise ValueError("Unknown Web point coordinate space")
    if clamp:
        x,y=max(0,min(width-1,x)),max(0,min(height-1,y))
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError("point outside viewport")
    return x,y

def repeated_cycle(history: list[str], *, repeats: int = 3) -> bool:
    """Require repeated identical action+pre-observation cycles; not just repeated tools."""
    for period in (1,2,3):
        if len(history)>=period*repeats:
            window=history[-period*repeats:]
            if all(window[i:i+period]==window[:period] for i in range(0,len(window),period)):
                return True
    return False
