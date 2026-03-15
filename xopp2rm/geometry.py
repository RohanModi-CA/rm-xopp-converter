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

def get_new_stroke_coordinates(xpp_x, xpp_y, pdf_w, pdf_h):
    point = np.ones(3)
    point[0] = xpp_x
    point[1] = xpp_y

    xpp_to_pdf = xournalpoint_to_pdf_matrix()
    pdf_to_pixel = portrait_pixel_transform_matrix(pdf_w, pdf_h)
    pixel_to_centered = portrait_centre_transform_matrix()
    pixel_scale = points_to_rm_pixels_matrix()
    transform = pixel_scale @ pixel_to_centered @ pdf_to_pixel @ xpp_to_pdf



    npoint = transform @ point
    return (npoint[0], npoint[1])

