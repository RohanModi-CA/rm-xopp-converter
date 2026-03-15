# FILE: main.py
import argparse, os, sys, json, glob, shutil
from xopp2rm import XOPP_TO_ZIP
from rm2xopp import ZIP_TO_XOPP
from libs.rm_io_tools import RMClient, RMCore

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(PROJ_ROOT, "sessions")

def _get_latest_session_manifest():
    manifest_files = glob.glob(os.path.join(SESSIONS_DIR, "*", "manifest.json"))
    if not manifest_files: return None
    manifests = []
    for mf in manifest_files:
        with open(mf, 'r') as f: manifests.append(json.load(f))
    # Sort by the time we actually ran the 'push'
    manifests.sort(key=lambda x: x.get('session_created_at', 0), reverse=True)
    return manifests[0]

def _find_session_by_hint(hint):
    manifest_files = glob.glob(os.path.join(SESSIONS_DIR, "*", "manifest.json"))
    for mf in manifest_files:
        with open(mf, 'r') as f:
            m = json.load(f)
            if hint in m['document_uuid'] or hint in m['original_xopp_path']: return m
    return None

def handle_push(args):
    input_file = os.path.abspath(args.input)
    if not os.path.exists(input_file):
        print(f"[-] Error: {input_file} not found"); sys.exit(1)

    temp_zip = os.path.join(PROJ_ROOT, "temp_transfer.zip")
    print(f"[*] Converting {input_file}...")
    try:
        XOPP_TO_ZIP(input_file, temp_zip)
        with RMClient() as client:
            RMCore(client).push_zip(temp_zip)
        print("[+] Push complete!")
    finally:
        if os.path.exists(temp_zip): os.remove(temp_zip)

def handle_pull(args):
    manifest = _find_session_by_hint(args.hint) if args.hint else _get_latest_session_manifest()
    if not manifest:
        print("[-] Error: No active sessions found"); sys.exit(1)

    doc_uuid = manifest["document_uuid"]
    original_path = manifest["original_xopp_path"]
    out_name = os.path.abspath(args.output) if args.output else original_path

    if not args.output and os.path.exists(original_path):
        shutil.copy2(original_path, original_path + ".backup")
        print(f"[*] Safety backup: {original_path}.backup")

    temp_zip = os.path.join(PROJ_ROOT, f"pull_{doc_uuid}.zip")
    try:
        with RMClient() as client:
            core = RMCore(client)
            core.pull_as_zip(doc_uuid, temp_zip)
            ZIP_TO_XOPP(temp_zip, out_name)
            core.delete_document(doc_uuid) # Cleanup Tablet
        print(f"[+] Success!")
    finally:
        if os.path.exists(temp_zip): os.remove(temp_zip)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    psh = subparsers.add_parser("push")
    psh.add_argument("input")
    
    pll = subparsers.add_parser("pull")
    pll.add_argument("hint", nargs='?')
    pll.add_argument("-o", "--output")

    args = parser.parse_args()
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    if args.command == "push": handle_push(args)
    else: handle_pull(args)
