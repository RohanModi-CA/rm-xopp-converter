#!/usr/bin/env python3
import sys
import argparse
import os
from src.ssh_client import RMClient
from src.core import RMCore

def main():
    parser = argparse.ArgumentParser(description="Push a .zip bundle to the reMarkable tablet")
    parser.add_argument("file", help="Path to the .zip file to upload")
    
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[-] Error: File '{args.file}' not found.")
        sys.exit(1)

    if not args.file.lower().endswith(".zip"):
        print("[-] Error: This tool currently only accepts .zip bundles.")
        sys.exit(1)

    try:
        with RMClient() as client:
            core = RMCore(client)
            core.push_zip(args.file)
            print(f"[+] '{args.file}' has been successfully synced to the tablet.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
