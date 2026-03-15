from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Stroke:
    tool: str
    color: str
    width: float
    points: List[Tuple[float, float]]

@dataclass
class XoppPage:
    index: int
    width: float
    height: float
    strokes: List[Stroke]
