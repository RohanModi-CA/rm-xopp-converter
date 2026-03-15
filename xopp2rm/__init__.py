from .parser import xopp_to_xml, xml_tree_to_pages, get_ghost_xml
from .renderer import generate_ghost_pdf
from .pdf_engine import render_page_layout
from .rm_engine import xml_page_to_rm
from .packager import rms_and_pdfs_paths_to_zip
import fitz
import os


def XOPP_TO_ZIP(xopp_path: str, out_zip_path: str):
    # 1. Parse Data
    root = xopp_to_xml(xopp_path)
    pages = xml_tree_to_pages(root) # Extracts strokes
    
    # 2. Create Background Scaffolding
    ghost_xml = get_ghost_xml(root, xopp_path)
    ghost_pdf_path = generate_ghost_pdf(ghost_xml)
    ghost_doc = fitz.open(ghost_pdf_path)

    processed_pages = []

    # 3. Processing Loop
    for i, page_data in enumerate(pages):
        # A. Get the visual page from our Ghost PDF
        ghost_page = ghost_doc[i]
        
        # B. Transform PDF (Ghost PDF -> RM Sized PDF)
        pdf_path = render_page_layout(ghost_page, i, page_data.width, page_data.height)
        
        # C. Transform Strokes (XPP Coords -> RM Coords)
        rm_path = xml_page_to_rm(page_data)
        
        processed_pages.append({
            "page_RM_path": rm_path, 
            "page_PDF_path": pdf_path
        })

    # 4. Final Bundle
    ZIP_path = rms_and_pdfs_paths_to_zip(processed_pages, out_zip_path)
    
    # 5. Cleanup
    ghost_doc.close()
    os.remove(ghost_pdf_path)
    # (Optional: loop and remove individual temp pdf/rm files)
    
    return ZIP_path
