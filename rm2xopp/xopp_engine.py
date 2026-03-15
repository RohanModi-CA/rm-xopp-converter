# FILE: rm2xopp/xopp_engine.py

import xml.etree.ElementTree as ET
from typing import List, Tuple
from libs.rmscene import scene_items as si
from xopp2rm.geometry import DPI_RATIO

def _map_color_to_xopp(color: si.PenColor) -> str:
    """Maps reMarkable PenColor back to Xournal++ hex color."""
    if color == si.PenColor.BLUE: return "#3333ccff"
    if color == si.PenColor.RED: return "#ff0000ff"
    if color == si.PenColor.GREEN: return "#00ff00ff"
    return "#000000ff" # Default to black

def create_xopp_stroke(
    points: List[Tuple[float, float]],
    color: si.PenColor,
    thickness: float
) -> ET.Element:
    """
    Creates an XML <stroke> element for a Xournal++ file.
    """
    stroke_elem = ET.Element("stroke")
    stroke_elem.set("tool", "pen") # For now, assume all new strokes are 'pen'
    stroke_elem.set("color", _map_color_to_xopp(color))
    
    # Inverse of the DPI_RATIO scaling
    xopp_width = thickness / DPI_RATIO
    stroke_elem.set("width", str(xopp_width))

    # Format points into "x1 y1 x2 y2 ..."
    points_str = " ".join(f"{p[0]:.2f} {p[1]:.2f}" for p in points)
    stroke_elem.text = points_str
    
    return stroke_elem
