# FILE: xopp2rm/session_manager.py

import os
import json
import shutil
from typing import List, Dict, Tuple

SESSIONS_DIR = "sessions"

def create_session(
    doc_uuid: str,
    page_uuids: List[str],
    page_stroke_maps: List[Dict],
    page_dimensions: List[Tuple[float, float]],
    original_xopp_path: str
):
    """
    Creates a sync session directory containing a snapshot of the original
    .xopp and a manifest.json file with all necessary mapping info.
    """
    session_path = os.path.join(SESSIONS_DIR, doc_uuid)
    os.makedirs(session_path, exist_ok=True)
    
    # 1. Copy the original .xopp file for a perfect snapshot
    shutil.copy(original_xopp_path, os.path.join(session_path, "original.xopp"))
    
    # 2. Build the manifest data structure
    manifest_data = {
        "document_uuid": doc_uuid,
        "timestamp_utc": int(os.path.getmtime(original_xopp_path)),
        "original_xopp_path": original_xopp_path,
        "pages": []
    }
    
    for i, rm_page_uuid in enumerate(page_uuids):
        page_info = {
            "rm_page_uuid": rm_page_uuid,
            "xopp_page_index": i,
            "width": page_dimensions[i][0],
            "height": page_dimensions[i][1],
            "strokes": page_stroke_maps[i]
        }
        manifest_data["pages"].append(page_info)
        
    # 3. Write the manifest.json file
    manifest_path = os.path.join(session_path, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
        
    print(f"[+] Sync session created at: {session_path}")
