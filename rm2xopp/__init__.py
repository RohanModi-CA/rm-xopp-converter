# FILE: rm2xopp/__init__.py

import os
from .parser import parse_rm_zip
from .merger import merge_changes

SESSIONS_DIR = "sessions"

def ZIP_TO_XOPP(zip_path: str, output_xopp_path: str):
    """
    Main orchestrator for converting a reMarkable zip bundle back to a .xopp file.
    
    1. Parses the reMarkable zip.
    2. Finds the corresponding sync session.
    3. Merges the changes into the original .xopp snapshot.
    4. Saves the result to the specified output path.
    """
    # 1. Parse the reMarkable zip to get stroke data and the document UUID
    print(f"[*] Parsing reMarkable bundle: {zip_path}")
    rm_data = parse_rm_zip(zip_path)
    doc_uuid = rm_data["doc_uuid"]
    
    # 2. Find the corresponding sync session
    session_path = os.path.join(SESSIONS_DIR, doc_uuid)
    if not os.path.isdir(session_path):
        raise FileNotFoundError(
            f"No active sync session found for document UUID: {doc_uuid}. "
            "Was this file converted using this tool?"
        )
    print(f"[+] Found sync session at: {session_path}")
    
    # 3. Merge changes and save to the final output path
    merge_changes(session_path, rm_data, output_xopp_path)
    
    # Optional: Clean up the session folder after a successful merge
    # import shutil
    # shutil.rmtree(session_path)
    # print(f"[*] Cleaned up session: {session_path}")
    
    return output_xopp_path
