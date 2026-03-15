#!/usr/bin/env python3
import sys
import argparse
from src.ssh_client import RMClient
from src.core import RMCore

def main():
    parser = argparse.ArgumentParser(description="Pull a reMarkable document as a .zip bundle")
    parser.add_argument("identifier", help="The Visible Name or UUID of the document")
    parser.add_argument("-o", "--output", help="Output filename (defaults to identifier.zip)")
    
    args = parser.parse_args()
    
    output_filename = args.output if args.output else f"{args.identifier}.zip"
    if not output_filename.endswith(".zip"):
        output_filename += ".zip"

    try:
        # Use context manager to handle SSH connection lifecycle
        with RMClient() as client:
            core = RMCore(client)
            core.pull_as_zip(args.identifier, output_filename)
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
