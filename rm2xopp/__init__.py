# FILE: rm2xopp/__init__.py
import os
import shutil
from .parser import parse_rm_zip
from .merger import merge_changes

PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(PROJ_ROOT, "sessions")

def ZIP_TO_XOPP(zip_path: str, output_xopp_path: str):
    rm_data = parse_rm_zip(zip_path)
    doc_uuid = rm_data["doc_uuid"]
    
    session_path = os.path.join(SESSIONS_DIR, doc_uuid)
    if not os.path.isdir(session_path):
        raise FileNotFoundError(f"No active session for UUID: {doc_uuid}")

    print(f"[+] Found sync session at: {session_path}")
    merge_changes(session_path, rm_data, output_xopp_path)
    
    # Cleanup local session
    shutil.rmtree(session_path)
    print(f"[*] Cleaned up session: {session_path}")
    return output_xopp_path
