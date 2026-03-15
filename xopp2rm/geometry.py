import numpy as np

CANONICAL_LONG_EDGE: float = 596.39 
CANONICAL_SHORT_EDGE: float = 447.29
DPI_RATIO: float = 226/72


def xournalpoint_to_pdf_matrix():
    """
    Xournalpp Points are defined in points (1/72 inch) (ew). 
    We want to convert these to the units of the PDF.
    Apparently, these are the same as the PDF. Not sure.
    """
    transform = np.eye(3)
    return transform


def portrait_pixel_transform_matrix(pdf_w:float, pdf_h:float):
    """
    This gives us the matrix that comes from taking the portrait, scaling it and sending to the right.
    """
    transform = np.zeros((3,3))
    transform[2,2] = 1 # the translation coord


    assert(pdf_h >= pdf_w and 0 not in (pdf_w, pdf_h))
    normalization_factor:float = (CANONICAL_LONG_EDGE/pdf_h)

    new_width:float = normalization_factor*pdf_w
    # Or if the aspect ratio is wonky, we fix it.
    if new_width > CANONICAL_SHORT_EDGE:
        normalization_factor:float = (CANONICAL_SHORT_EDGE/pdf_w)
        new_width = normalization_factor * pdf_w

    # All pixels then get diagonally scaled in accordance with this.
    transform[0,0] = normalization_factor
    transform[1,1] = normalization_factor

    # And we have to send to the right edge.
    empty_left_edge: float = CANONICAL_SHORT_EDGE - new_width
    transform[0,2] = empty_left_edge # translate in x

    return transform


def portrait_centre_transform_matrix():
    """
    THIS ASSUMES WE HAVE ALREADY DONE A PORTRAIT PIXEL TRANSFORM IN CANONICAL LENGTHS.
    This returns the matrix responsible for shiting coordines such that the vertical top 
    and horizontal centre is (0,0).
    """
    transform = np.eye(3)
    transform[0,2] = -1 * (CANONICAL_SHORT_EDGE/2) 
    return transform
    

def points_to_rm_pixels_matrix():
    """
    Converts Canonical PDF Points up to reMarkable Screen Pixels.
    Multiply by 226/72 (~3.138).
    """
    transform = np.eye(3)
    transform[0, 0] = DPI_RATIO
    transform[1, 1] = DPI_RATIO
    return transform


def get_new_pdf_corners(pdf_w, pdf_h):
    """
    This function takes the height and width of a PDF in whichever unit the PDF analysis wishes to use??
    It then computes the TL and BR that this PDF page should be placed in. It should be placed in a
    containing PDF starting at (0,0) and ending at BR.
    """
    
    transform = portrait_pixel_transform_matrix(pdf_w, pdf_h)
    TL = np.zeros(3)
    TL[2] = 1
    BR = np.zeros(3)
    BR[2] = 1
    BR[0] = pdf_w
    BR[1] = pdf_h

    nTL = transform @ TL
    nBR = transform @ BR

    return ((nTL[0], nTL[1]), (nBR[0], nBR[1]))


def get_total_forward_matrix(pdf_w: float, pdf_h: float):
    """Combines the 4 steps into a single transformation matrix."""
    m1 = xournalpoint_to_pdf_matrix()
    m2 = portrait_pixel_transform_matrix(pdf_w, pdf_h)
    m3 = portrait_centre_transform_matrix()
    m4 = points_to_rm_pixels_matrix()
    
    # Order of application: m4(m3(m2(m1(point))))
    return m4 @ m3 @ m2 @ m1

def get_total_inverse_matrix(pdf_w: float, pdf_h: float):
    """Returns the mathematical inverse of the full forward pipeline."""
    forward = get_total_forward_matrix(pdf_w, pdf_h)
    return np.linalg.inv(forward)


def get_new_stroke_coordinates(xpp_x, xpp_y, pdf_w, pdf_h, is_rotated=False):
    """Forward: XOPP Points -> RM Pixels."""
    if is_rotated:
        # 90 deg CCW: (x, y) -> (y, OrigWidth - x)
        # Note: pdf_h is the Original Width because we swapped them in parser.py
        orig_w = pdf_h 
        new_x = xpp_y
        new_y = orig_w - xpp_x
    else:
        new_x, new_y = xpp_x, xpp_y

    point = np.array([new_x, new_y, 1])
    transform = get_total_forward_matrix(pdf_w, pdf_h)
    npoint = transform @ point
    return (npoint[0], npoint[1])

def get_xopp_coordinates_from_rm(rm_x, rm_y, pdf_w, pdf_h, is_rotated=False):
    """Backward: RM Pixels -> XOPP Points."""
    point = np.array([rm_x, rm_y, 1])
    transform = get_total_inverse_matrix(pdf_w, pdf_h)
    npoint = transform @ point
    
    inv_x, inv_y = npoint[0], npoint[1]
    
    if is_rotated:
        # 90 deg CW: (x, y) -> (OrigWidth - y, x)
        orig_w = pdf_h
        final_x = orig_w - inv_y
        final_y = inv_x
        return (final_x, final_y)
    
    return (inv_x, inv_y)

