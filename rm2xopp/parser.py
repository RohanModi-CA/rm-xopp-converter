# FILE: rm2xopp/parser.py

import zipfile
import json
import os
import tempfile
from typing import List, Dict, Any
from libs.rmscene import read_blocks, scene_items as si, CrdtId

def parse_rm_zip(zip_path: str) -> Dict[str, Any]:
    """
    Unzips a reMarkable bundle and parses its contents into a dictionary.
    """
    data = {"doc_uuid": None, "pages": {}}

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Find the document UUID by looking for a .metadata file
        for filename in os.listdir(tmpdir):
            if filename.endswith(".metadata"):
                data["doc_uuid"] = filename.replace(".metadata", "")
                break
        if not data["doc_uuid"]:
            raise FileNotFoundError("Could not find a .metadata file in the zip archive.")
        
        # Parse the .content file to get page order
        with open(os.path.join(tmpdir, f"{data['doc_uuid']}.content"), 'r') as f:
            content = json.load(f)
        
        page_uuids = content.get("pages", [])

        # Parse each .rm file for stroke data
        for page_uuid in page_uuids:
            rm_path = os.path.join(tmpdir, data["doc_uuid"], f"{page_uuid}.rm")
            if os.path.exists(rm_path):
                data["pages"][page_uuid] = _parse_rm_file(rm_path)
    
    return data


def _parse_rm_file(rm_path: str) -> List[Dict]:
    """
    Reads a binary .rm file and extracts stroke data safely.
    """
    strokes = []
    with open(rm_path, "rb") as f:
        for block in read_blocks(f):
            # Safely check if this block has an item and a value
            if hasattr(block, "item") and hasattr(block.item, "value"):
                # Check if the value is actually a Pen stroke (Line)
                if isinstance(block.item.value, si.Line):
                    line = block.item.value
                    rm_id = block.item.item_id
                    
                    strokes.append({
                        "id": f"{rm_id.part1}_{rm_id.part2}",
                        "tool": line.tool,
                        "color": line.color,
                        "thickness": line.thickness_scale,
                        "points": [(p.x, p.y) for p in line.points]
                    })
    return strokes
