# FILE: xopp2rm/session_manager.py

import os
import json
import shutil
from typing import List, Dict, Tuple

SESSIONS_DIR = "sessions"


# FILE: xopp2rm/session_manager.py
import os
import json
import shutil
import time
from typing import List, Dict, Tuple

# Locate sessions folder relative to the project root
PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(PROJ_ROOT, "sessions")

def create_session(doc_uuid, page_uuids, page_stroke_maps, page_dimensions, original_xopp_path, rotations):
    session_path = os.path.join(SESSIONS_DIR, doc_uuid)
    os.makedirs(session_path, exist_ok=True)
    
    shutil.copy(original_xopp_path, os.path.join(session_path, "original.xopp"))
    
    manifest_data = {
        "document_uuid": doc_uuid,
        "session_created_at": time.time(), # Record when we pushed
        "original_xopp_path": os.path.abspath(original_xopp_path),
        "pages": []
    }
    
    for i, rm_page_uuid in enumerate(page_uuids):
        manifest_data["pages"].append({
            "rm_page_uuid": rm_page_uuid,
            "xopp_page_index": i,
            "width": page_dimensions[i][0],
            "height": page_dimensions[i][1],
            "is_rotated": rotations[i], 
            "strokes": page_stroke_maps[i]
        })
        
    with open(os.path.join(session_path, "manifest.json"), 'w') as f:
        json.dump(manifest_data, f, indent=2)
    print(f"[+] Sync session created at: {session_path}")
