import os
import json
import zipfile
import tempfile
import shutil
from pathlib import Path

class RMCore:
    def __init__(self, client):
        """
        :param client: An instance of RMClient
        """
        self.client = client

    def find_uuid_by_name(self, visible_name):
        """
        Finds the UUID of a document based on its visible name.
        Uses grep on the tablet for efficiency.
        """
        # Search for the visibleName inside all .metadata files
        # grep -l returns the filename of matching files
        cmd = f"grep -l '\"visibleName\": \"{visible_name}\"' {self.client.BASE_PATH}/*.metadata"
        status, stdout, stderr = self.client.execute(cmd)

        if status != 0 or not stdout:
            return None

        # stdout will be something like: /path/to/xochitl/<uuid>.metadata
        # We need just the <uuid>
        metadata_filename = os.path.basename(stdout.splitlines()[0])
        return metadata_filename.replace(".metadata", "")

    def pull_as_zip(self, identifier, output_path):
        """
        identifier: Can be a UUID or a Visible Name.
        output_path: Local path to save the .zip file.
        """
        # 1. Resolve identifier to UUID
        uuid_str = identifier
        if "-" not in identifier or len(identifier) < 30: # Simple check if it's not a UUID
            print(f"[*] Searching for document: {identifier}...")
            uuid_str = self.find_uuid_by_name(identifier)
            if not uuid_str:
                raise FileNotFoundError(f"Could not find document named '{identifier}'")

        print(f"[+] Found UUID: {uuid_str}. Starting download...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # 2. Download .metadata and .content
            for ext in [".metadata", ".content"]:
                filename = f"{uuid_str}{ext}"
                print(f"[*] Downloading {filename}...")
                self.client.download(filename, str(tmp_path / filename))

            # 3. Download the stroke directory (v2 format)
            stroke_dir = uuid_str
            local_stroke_dir = tmp_path / stroke_dir
            os.makedirs(local_stroke_dir, exist_ok=True)
            
            remote_files = self.client.list_dir(stroke_dir)
            if remote_files:
                print(f"[*] Downloading {len(remote_files)} stroke files...")
                for f in remote_files:
                    self.client.download(f"{stroke_dir}/{f}", str(local_stroke_dir / f))

            # 4. Create ZIP bundle
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(tmp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Archive should be flat or maintain relative structure
                        arcname = os.path.relpath(file_path, tmp_dir)
                        zipf.write(file_path, arcname)

        print(f"[+] Successfully bundled document into: {output_path}")
        return output_path

    def push_zip(self, zip_path):
        """
        Uploads a zip and extracts it on the tablet.
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Local zip not found: {zip_path}")

        remote_zip_name = "transfer_bundle.zip"
        
        try:
            print("[*] Stopping UI...")
            self.client.stop_xochitl()

            print(f"[*] Uploading {zip_path}...")
            self.client.upload(zip_path, remote_zip_name)

            print("[*] Extracting on tablet...")
            # -o overwrites, -d specifies destination
            cmd = f"unzip -o {self.client.BASE_PATH}/{remote_zip_name} -d {self.client.BASE_PATH}/"
            status, stdout, stderr = self.client.execute(cmd)
            
            if status != 0:
                print(f"[-] Unzip error: {stderr}")
            else:
                print("[+] Extraction complete.")

        finally:
            print("[*] Cleaning up and restarting UI...")
            self.client.execute(f"rm {self.client.BASE_PATH}/{remote_zip_name}")
            self.client.start_xochitl()

    def list_all_items(self):
        """
        Returns a list of (visibleName, uuid) for all documents on the device.
        Useful for a quick library view.
        """
        cmd = f"grep -h '\"visibleName\"' {self.client.BASE_PATH}/*.metadata"
        # This returns lines like: "visibleName": "My Notebook",
        status, stdout, stderr = self.client.execute(cmd)
        
        # This is a bit of a hack to get names quickly without full JSON parsing
        names = []
        for line in stdout.splitlines():
            parts = line.split('"')
            if len(parts) >= 4:
                names.append(parts[3])
        return names

    def delete_document(self, uuid_str):
            """Permanently deletes a document and its data folder from the tablet."""
            print(f"[*] Deleting {uuid_str} from tablet...")
            self.client.stop_xochitl()
            base = self.client.BASE_PATH
            cmd = f"rm -f {base}/{uuid_str}.metadata {base}/{uuid_str}.content {base}/{uuid_str}.pdf && rm -rf {base}/{uuid_str}/"
            self.client.execute(cmd)
            self.client.start_xochitl()
