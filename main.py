# FILE: main.py

import argparse
import os
import sys
import json
import glob
from pathlib import Path

# Import our converters
from xopp2rm import XOPP_TO_ZIP
from rm2xopp import ZIP_TO_XOPP

# Import the tablet SSH tools
from libs.rm_io_tools import RMClient, RMCore

SESSIONS_DIR = "sessions"

def _get_latest_session_manifest() -> dict:
    """Finds the most recently created session manifest."""
    manifest_files = glob.glob(os.path.join(SESSIONS_DIR, "*", "manifest.json"))
    if not manifest_files:
        return None
    
    manifests = []
    for mf in manifest_files:
        with open(mf, 'r') as f:
            manifests.append(json.load(f))
            
    # Sort by the timestamp we saved during 'push'
    manifests.sort(key=lambda x: x.get('timestamp_utc', 0), reverse=True)
    return manifests[0]

def _find_session_by_hint(hint: str) -> dict:
    """Finds a session based on the original filename."""
    manifest_files = glob.glob(os.path.join(SESSIONS_DIR, "*", "manifest.json"))
    for mf in manifest_files:
        with open(mf, 'r') as f:
            manifest = json.load(f)
            # Check if the hint matches the document UUID or the original XOPP filename
            if hint in manifest.get('document_uuid', '') or hint in manifest.get('original_xopp_path', ''):
                return manifest
    return None

def handle_push(args):
    """Converts XOPP and sends it to the tablet."""
    input_file = args.input
    if not os.path.exists(input_file):
        print(f"[-] Error: Input file '{input_file}' not found.")
        sys.exit(1)

    temp_zip = "temp_transfer.zip"
    
    print(f"[*] Starting conversion of {input_file}...")
    try:
        # 1. Convert to ZIP (This also generates the Sync Session)
        XOPP_TO_ZIP(input_file, temp_zip)
        
        # 2. Push to Tablet
        print("[*] Connecting to reMarkable...")
        with RMClient() as client:
            core = RMCore(client)
            core.push_zip(temp_zip)
            
        print("[+] Push complete! You can now edit the file on your tablet.")
        
    except Exception as e:
        print(f"[-] Push failed: {e}")
    finally:
        # Clean up the transport ZIP
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

def handle_pull(args):
    """Pulls the document from the tablet and merges annotations."""
    # 1. Figure out which session we are pulling
    manifest = None
    if args.hint:
        manifest = _find_session_by_hint(args.hint)
        if not manifest:
            print(f"[-] Error: Could not find an active session matching '{args.hint}'.")
            sys.exit(1)
    else:
        manifest = _get_latest_session_manifest()
        if not manifest:
            print("[-] Error: No active sessions found. Have you pushed a file yet?")
            sys.exit(1)

    doc_uuid = manifest["document_uuid"]
    # We don't save original_xopp_path in manifest yet, so let's derive output name from session folder
    # Or just use a default naming scheme. Let's find the original.xopp in the session folder.
    session_path = os.path.join(SESSIONS_DIR, doc_uuid)
    
    # We'll name the output based on the original file, if we can deduce it, otherwise default.
    out_name = args.output if args.output else "annotated_document.xopp"
    if not args.output and args.hint and args.hint.endswith('.xopp'):
        out_name = args.hint.replace(".xopp", "_annotated.xopp")

    temp_zip = f"pull_{doc_uuid}.zip"
    
    print(f"[*] Found Session. Pulling document UUID: {doc_uuid}...")
    try:
        # 2. Pull from Tablet
        with RMClient() as client:
            core = RMCore(client)
            # Because we know the exact UUID, pull_as_zip works perfectly
            core.pull_as_zip(doc_uuid, temp_zip)
        
        # 3. Merge changes into a new XOPP
        print(f"[*] Merging tablet annotations into {out_name}...")
        ZIP_TO_XOPP(temp_zip, out_name)
        print(f"[+] Pull complete! Your annotated file is at: {out_name}")
        
    except Exception as e:
        print(f"[-] Pull failed: {e}")
    finally:
        # Clean up the pulled ZIP
        if os.path.exists(temp_zip):
            os.remove(temp_zip)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bidirectional Xournal++ <-> reMarkable sync tool.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    # Push Command
    push_parser = subparsers.add_parser("push", help="Convert a .xopp file and push it to the tablet.")
    push_parser.add_argument("input", help="Path to the local .xopp file")

    # Pull Command
    pull_parser = subparsers.add_parser("pull", help="Pull annotations from the tablet and merge them back.")
    pull_parser.add_argument("hint", nargs='?', help="(Optional) The name of the original .xopp file or UUID to pull. Defaults to most recent.")
    pull_parser.add_argument("-o", "--output", help="(Optional) Name of the resulting merged .xopp file.")

    args = parser.parse_args()

    # Ensure sessions directory exists
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    if args.command == "push":
        handle_push(args)
    elif args.command == "pull":
        handle_pull(args)
