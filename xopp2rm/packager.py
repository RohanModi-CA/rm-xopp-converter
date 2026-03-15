# FILE: xopp2rm/packager.py

import uuid
import json
import time
import zipfile
import os
import fitz
from typing import List, Dict, Tuple

def rms_and_pdfs_paths_to_zip(
    pages_paths: List[Dict[str, str]], 
    output_zip_path: str, 
    visible_name: str = "Converted Document"
) -> Tuple[str, str, List[str]]:
    """
    Packages all assets into a reMarkable .zip and returns the path,
    the document UUID, and the list of page UUIDs.
    """
    doc_uuid = str(uuid.uuid4())
    timestamp = str(int(time.time() * 1000))
    
    master_pdf_doc = fitz.open()
    page_uuids = []
    
    for entry in pages_paths:
        page_pdf = fitz.open(entry['page_PDF_path'])
        master_pdf_doc.insert_pdf(page_pdf)
        page_pdf.close()
        page_uuids.append(str(uuid.uuid4()))

    master_pdf_bytes = master_pdf_doc.tobytes()
    master_pdf_doc.close()

    doc_metadata = {
        "deleted": False, "lastModified": timestamp, "metadatamodified": False,
        "modified": False, "parent": "", "pinned": False, "synced": False,
        "type": "DocumentType", "version": 1, "visibleName": visible_name
    }
    doc_content = {
        "extraMetadata": {}, "fileType": "pdf", "pageCount": len(pages_paths),
        "pages": page_uuids, "orientation": "portrait",
        "customZoomOrientation": "portrait", "transform": {}
    }

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as rm_zip:
        rm_zip.writestr(f"{doc_uuid}.pdf", master_pdf_bytes)
        rm_zip.writestr(f"{doc_uuid}.metadata", json.dumps(doc_metadata, indent=4))
        rm_zip.writestr(f"{doc_uuid}.content", json.dumps(doc_content, indent=4))

        for i, entry in enumerate(pages_paths):
            p_uuid = page_uuids[i]
            with open(entry['page_RM_path'], 'rb') as f:
                rm_data = f.read()
            page_metadata = {"layers": [{"name": "Layer 1"}]}
            rm_zip.writestr(f"{doc_uuid}/{p_uuid}.rm", rm_data)
            rm_zip.writestr(f"{doc_uuid}/{p_uuid}-metadata.json", json.dumps(page_metadata, indent=4))

    return output_zip_path, doc_uuid, page_uuids
