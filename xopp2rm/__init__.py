# FILE: xopp2rm/__init__.py

from .parser import xopp_to_xml, xml_tree_to_pages, get_ghost_xml
from .renderer import generate_ghost_pdf
from .pdf_engine import render_page_layout
from .rm_engine import xml_page_to_rm
from .packager import rms_and_pdfs_paths_to_zip
from . import session_manager # Import the new module
import fitz
import os

def XOPP_TO_ZIP(xopp_path: str, out_zip_path: str):
    # 1. Parse Data
    root = xopp_to_xml(xopp_path)
    pages = xml_tree_to_pages(root)
    
    # 2. Create Background Scaffolding
    ghost_xml = get_ghost_xml(root, xopp_path)
    ghost_pdf_path = generate_ghost_pdf(ghost_xml)
    ghost_doc = fitz.open(ghost_pdf_path)

    processed_pages = []
    all_stroke_maps = [] # To collect stroke maps for each page

    # 3. Processing Loop
    for i, page_data in enumerate(pages):
        ghost_page = ghost_doc[i]
        pdf_path = render_page_layout(ghost_page, i, page_data.width, page_data.height)
        
        # Capture both the path and the stroke map
        rm_path, stroke_map = xml_page_to_rm(page_data)
        all_stroke_maps.append(stroke_map)
        
        processed_pages.append({
            "page_RM_path": rm_path, 
            "page_PDF_path": pdf_path
        })

    # 4. Final Bundle (now returns UUIDs)
    ZIP_path, doc_uuid, page_uuids = rms_and_pdfs_paths_to_zip(
        processed_pages, 
        out_zip_path,
        visible_name=os.path.basename(xopp_path).replace(".xopp", "")
    )
    
    # 5. Create the Sync Session
    session_manager.create_session(
        doc_uuid=doc_uuid,
        page_uuids=page_uuids,
        page_stroke_maps=all_stroke_maps,
        page_dimensions=[(p.width, p.height) for p in pages],
        original_xopp_path=xopp_path
    )
    
    # 6. Cleanup
    ghost_doc.close()
    os.remove(ghost_pdf_path)
    # (Consider cleanup of individual temp files)
    
    return ZIP_path
