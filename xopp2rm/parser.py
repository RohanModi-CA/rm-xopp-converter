import gzip
import xml.etree.ElementTree as ET
from typing import List
from .models import XoppPage, Stroke
import os


def get_ghost_xml(root: ET.Element, xopp_path: str) -> str:
    """Returns an XML string with strokes removed and paths normalized."""
    base_dir = os.path.dirname(os.path.abspath(xopp_path))
    
        # 1. Remove all strokes
    for page in root.findall('page'):
        for layer in page.findall('layer'):
            for stroke in layer.findall('stroke'):
                layer.remove(stroke)
        # If using standard ET, iterate through layers and remove:
        # for layer in page.findall('layer'): 
        #    for s in layer.findall('stroke'): layer.remove(s)

    # 2. Fix relative paths for backgrounds and images
    for bg in root.findall(".//background"):
        fname = bg.get("filename")
        if fname and not os.path.isabs(fname):
            bg.set("filename", os.path.join(base_dir, fname))
            
    for img in root.findall(".//image"):
        fname = img.get("filename")
        if fname and not os.path.isabs(fname):
            img.set("filename", os.path.join(base_dir, fname))

    return ET.tostring(root, encoding="unicode")


def xopp_to_xml(filepath: str) -> ET.Element:
    """Decompresses a .xopp file and returns the XML root element."""
    try:
        with gzip.open(filepath, 'rb') as f:
            tree = ET.parse(f)
    except Exception:
        # Fallback for uncompressed .xoj or .xopp files
        tree = ET.parse(filepath)
    return tree.getroot()


def xml_tree_to_pages(root: ET.Element) -> List[XoppPage]:
    pages = []
    for i, page_node in enumerate(root.findall('page')):
        w = float(page_node.get('width'))
        h = float(page_node.get('height'))
        
        is_rotated = w > h
        # If landscape, swap dimensions for the internal pipeline
        internal_w = h if is_rotated else w
        internal_h = w if is_rotated else h
        
        strokes = []
        for layer in page_node.findall('layer'):
            for stroke_node in layer.findall('stroke'):
                strokes.append(_parse_stroke_node(stroke_node))
        
        pages.append(XoppPage(
            index=i,
            width=internal_w,   # Engine sees the "tall" version
            height=internal_h,  # Engine sees the "tall" version
            strokes=strokes,
            is_rotated=is_rotated
        ))
    return pages

def _parse_stroke_node(node: ET.Element) -> Stroke:
    """Helper to convert a <stroke> XML element into a Stroke model."""
    raw_points_str = node.text if node.text else ""
    coords = [float(x) for x in raw_points_str.split()]
    
    # Convert flat list [x1, y1, x2, y2] to [(x1, y1), (x2, y2)]
    points = list(zip(coords[::2], coords[1::2]))
    
    return Stroke(
        tool=node.get('tool', 'pen'),
        color=node.get('color', '#000000ff'),
        width=float(node.get('width', '1.0')),
        points=points
    )

