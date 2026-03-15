import fitz
import os
import tempfile
from .models import XoppPage
from .geometry import (
    get_new_pdf_corners, 
    CANONICAL_SHORT_EDGE, 
    CANONICAL_LONG_EDGE
)


def render_page_layout(ghost_page: fitz.Page, page_index: int, src_w: float, src_h: float,is_rotated=False) -> str:
    """Takes a rendered ghost page and fits it to the RM canvas."""
    fd, output_path = tempfile.mkstemp(suffix=f"_layout_{page_index}.pdf")
    os.close(fd)

    out_doc = fitz.open()
    new_page = out_doc.new_page(width=CANONICAL_SHORT_EDGE, height=CANONICAL_LONG_EDGE)

    # Calculate transformation (src_w/src_h are already swapped if landscape)
    p_tl, p_br = get_new_pdf_corners(src_w, src_h)
    target_rect = fitz.Rect(p_tl[0], p_tl[1], p_br[0], p_br[1])

    # rotate=270 is 90 deg CCW
    rot_val = 270 if is_rotated else 0
    new_page.show_pdf_page(target_rect, ghost_page.parent, ghost_page.number, rotate=rot_val)



    # Apply hatching using your existing logic
    _apply_hatching(new_page, p_tl, p_br) 

    out_doc.save(output_path)
    out_doc.close()
    return output_path

def xml_page_to_PDF(page: XoppPage) -> str:
    """
    Creates a single-page PDF with the background correctly positioned 
    and hatched. Returns the path to the temporary PDF file.
    """
    # Create a unique temporary filename
    fd, output_path = tempfile.mkstemp(suffix=f"_bg_{page.index}.pdf")
    os.close(fd)

    out_doc = fitz.open()
    
    # 1. Create the new page at reMarkable canonical size
    new_page = out_doc.new_page(
        width=CANONICAL_SHORT_EDGE, 
        height=CANONICAL_LONG_EDGE
    )

    # 2. If there is a background PDF, place it and hatch margins
    if page.bg_path and os.path.exists(page.bg_path):
        src_doc = fitz.open(page.bg_path)
        
        # Determine placement using the matrix logic
        p_tl, p_br = get_new_pdf_corners(page.width, page.height)
        target_rect = fitz.Rect(p_tl[0], p_tl[1], p_br[0], p_br[1])

        # Place the specific background page
        new_page.show_pdf_page(target_rect, src_doc, page.bg_page_num)
        
        # Draw Invalid Area (Hatching)
        _apply_hatching(new_page, p_tl, p_br)
        
        src_doc.close()
    else:
        # If no background, we just leave it blank (or draw a default grid)
        pass

    out_doc.save(output_path)
    out_doc.close()
    
    return output_path

def _apply_hatching(page, p_tl, p_br):
    """Internal helper to identify and hatch the empty zones."""
    # Zone: Left Margin
    if p_tl[0] > 1:
        _draw_invalid_hatching(page, fitz.Rect(0, 0, p_tl[0], CANONICAL_LONG_EDGE))
    
    # Zone: Top Margin
    if p_tl[1] > 1:
        _draw_invalid_hatching(page, fitz.Rect(p_tl[0], 0, CANONICAL_SHORT_EDGE, p_tl[1]))
        
    # Zone: Bottom Margin
    remaining_y = CANONICAL_LONG_EDGE - p_br[1]
    if remaining_y > 1:
        _draw_invalid_hatching(page, fitz.Rect(p_tl[0], p_br[1], CANONICAL_SHORT_EDGE, CANONICAL_LONG_EDGE))

def _draw_invalid_hatching(page, rect, spacing=15):
    """Draws light gray diagonal lines inside the specified rectangle."""
    if rect.width < 1 or rect.height < 1:
        return

    stroke_color = (0.85, 0.85, 0.85)
    for i in range(-int(rect.height), int(rect.width + rect.height), spacing):
        p1 = fitz.Point(rect.x0 + i, rect.y0)
        p2 = fitz.Point(rect.x0 + i + rect.height, rect.y1)
        
        lp1, lp2 = _clip_line_to_rect(p1, p2, rect)
        if lp1 and lp2:
            page.draw_line(lp1, lp2, color=stroke_color, width=0.5)

def _clip_line_to_rect(p1, p2, rect):
    """Calculates intersection points of a line and a bounding box for hatching."""
    x1, y1 = p1
    x2, y2 = p2
    if max(x1, x2) < rect.x0 or min(x1, x2) > rect.x1: return None, None
    if max(y1, y2) < rect.y0 or min(y1, y2) > rect.y1: return None, None
    
    def get_t(val, start, end):
        if end == start: return None
        return (val - start) / (end - start)

    points = []
    for x in [rect.x0, rect.x1]:
        t = get_t(x, x1, x2)
        if t is not None and 0 <= t <= 1:
            y = y1 + t * (y2 - y1)
            if rect.y0 <= y <= rect.y1: points.append(fitz.Point(x, y))
    for y in [rect.y0, rect.y1]:
        t = get_t(y, y1, y2)
        if t is not None and 0 <= t <= 1:
            x = x1 + t * (x2 - x1)
            if rect.x0 <= x <= rect.x1: points.append(fitz.Point(x, y))

    unique = []
    for p in points:
        if not any(abs(p.x - up.x) < 0.1 and abs(p.y - up.y) < 0.1 for up in unique):
            unique.append(p)
    if len(unique) < 2: return None, None
    return unique[0], unique[1]
