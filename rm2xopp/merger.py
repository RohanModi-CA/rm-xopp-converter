# FILE: rm2xopp/merger.py

import json
import os
import xml.etree.ElementTree as ET
import numpy as np
import gzip
from typing import Dict, List, Any
from .xopp_engine import create_xopp_stroke
from xopp2rm.geometry import get_xopp_coordinates_from_rm

# A small tolerance for floating point comparisons
FIDELITY_EPSILON = 1e-5

def _compare_strokes(original_points_str: str, new_points: List, epsilon: float) -> bool:
    """
    Compares original XOPP stroke points with new, transformed RM points.
    Returns True if they are considered identical.
    """
    try:
        original_coords = [float(p) for p in original_points_str.split()]
        original_points = list(zip(original_coords[::2], original_coords[1::2]))
        
        if len(original_points) != len(new_points):
            return False
            
        dist = np.linalg.norm(np.array(original_points) - np.array(new_points))
        return dist < epsilon
    except (ValueError, IndexError):
        return False # Mismatched format or empty string

def merge_changes(session_path: str, rm_data: Dict[str, Any], output_path: str):
    """
    Merges annotations from a reMarkable bundle into the original .xopp file.
    """
    manifest_path = os.path.join(session_path, "manifest.json")
    original_xopp_path = os.path.join(session_path, "original.xopp")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)



    # Load the original XOPP into an XML tree (handling gzip compression)
    try:
        with gzip.open(original_xopp_path, 'rb') as f:
            tree = ET.parse(f)
    except Exception:
        # Fallback if it's an uncompressed .xoj / .xopp
        tree = ET.parse(original_xopp_path)

    root = tree.getroot()  # <--- ADD THIS LINE HERE

    # Create a fast lookup for page and stroke data from the manifest
    page_manifest_lookup = {p['rm_page_uuid']: p for p in manifest['pages']}
    
    # Process each page from the reMarkable data
    for rm_page_uuid, rm_strokes in rm_data['pages'].items():
        if rm_page_uuid not in page_manifest_lookup:
            print(f"[!] Warning: Page {rm_page_uuid} was created on the tablet. Ignoring for now.")
            continue

        page_manifest = page_manifest_lookup[rm_page_uuid]
        xopp_page_index = page_manifest['xopp_page_index']
        page_width = page_manifest['width']
        page_height = page_manifest['height']
        
        # Find the corresponding <page> and <layer> in the XML tree
        xopp_page_node = root.findall('page')[xopp_page_index]
        # We assume a single layer for simplicity, matching our forward conversion
        xopp_layer_node = xopp_page_node.find('layer')
        if xopp_layer_node is None:
            # If no layer exists, create one
            xopp_layer_node = ET.SubElement(xopp_page_node, 'layer')
            
        original_strokes = xopp_layer_node.findall('stroke')
        
        # Keep track of which original strokes we've seen
        seen_original_stroke_indices = set()

        for rm_stroke in rm_strokes:
            # 1. Convert RM coordinates back to XOPP coordinates
            transformed_points = [
                get_xopp_coordinates_from_rm(p[0], p[1], page_width, page_height)
                for p in rm_stroke['points']
            ]
            
            # 2. Check if this stroke existed in the original file
            stroke_manifest = page_manifest['strokes'].get(rm_stroke['id'])

            if stroke_manifest:
                # Case: The stroke existed before. Check if it was modified.
                original_stroke_idx = stroke_manifest['stroke_idx']
                seen_original_stroke_indices.add(original_stroke_idx)
                
                original_stroke_node = original_strokes[original_stroke_idx]
                
                # Fidelity Check
                if not _compare_strokes(original_stroke_node.text, transformed_points, FIDELITY_EPSILON):
                    print(f"[*] Stroke {original_stroke_idx} on page {xopp_page_index} was modified.")
                    # It's modified. Create a new XML element and replace the old one.
                    new_stroke_node = create_xopp_stroke(
                        transformed_points, rm_stroke['color'], rm_stroke['thickness']
                    )
                    # This is tricky in ET. The easiest way is to overwrite attributes and text.
                    original_stroke_node.attrib = new_stroke_node.attrib
                    original_stroke_node.text = new_stroke_node.text
            else:
                # Case: This is a new stroke created on the tablet.
                print(f"[*] New stroke detected on page {xopp_page_index}.")
                new_stroke_node = create_xopp_stroke(
                    transformed_points, rm_stroke['color'], rm_stroke['thickness']
                )
                xopp_layer_node.append(new_stroke_node)
    
        # 3. Handle deleted strokes
        all_original_indices = set(range(len(original_strokes)))
        deleted_indices = sorted(list(all_original_indices - seen_original_stroke_indices), reverse=True)
        
        if deleted_indices:
            print(f"[*] Deleting {len(deleted_indices)} strokes on page {xopp_page_index}.")
            for idx in deleted_indices:
                xopp_layer_node.remove(original_strokes[idx])


    # Write the modified XML tree back out as a compressed .xopp file
    with gzip.open(output_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)
        
    print(f"[+] Successfully merged changes to {output_path}")
