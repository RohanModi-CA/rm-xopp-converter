# FILE: xopp2rm/rm_engine.py

import uuid
import os
import tempfile
from typing import Generator, Tuple, Dict

from .models import XoppPage, Stroke
from .geometry import get_new_stroke_coordinates, DPI_RATIO

# reMarkable scene library imports
from libs.rmscene import (
    write_blocks, CrdtId, LwwValue, SceneLineItemBlock, AuthorIdsBlock, 
    MigrationInfoBlock, PageInfoBlock, SceneTreeBlock, TreeNodeBlock, 
    SceneGroupItemBlock, scene_items as si
)
from libs.rmscene.crdt_sequence import CrdtSequenceItem

def _map_color(hex_color: str) -> si.PenColor:
    """Maps Xournal++ hex colors to reMarkable PenColors."""
    hex_color = hex_color.lower()
    if "#3333cc" in hex_color: return si.PenColor.BLUE
    if "#ff0000" in hex_color: return si.PenColor.RED
    if "#00ff00" in hex_color: return si.PenColor.GREEN
    return si.PenColor.BLACK

def xml_page_to_rm(page: XoppPage) -> Tuple[str, Dict]:
    """
    Converts a single XoppPage model into a reMarkable .rm binary file.
    Returns the path to the generated file AND a map of {rm_id: xopp_id}.
    """
    fd, output_path = tempfile.mkstemp(suffix=f"_page_{page.index}.rm")
    os.close(fd)
    
    # This dictionary will store our critical mapping info
    stroke_map = {}

    def block_generator() -> Generator:
        author_uuid = uuid.uuid4()
        yield AuthorIdsBlock(author_uuids={1: author_uuid})
        yield MigrationInfoBlock(migration_id=CrdtId(1, 1), is_device=True)
        yield PageInfoBlock(loads_count=1, merges_count=0, text_chars_count=0, text_lines_count=0)

        root_id = CrdtId(0, 1)
        layer_id = CrdtId(0, 11)
        yield SceneTreeBlock(tree_id=layer_id, node_id=CrdtId(0, 0), is_update=True, parent_id=root_id)
        yield TreeNodeBlock(si.Group(node_id=root_id))
        yield TreeNodeBlock(si.Group(node_id=layer_id, label=LwwValue(CrdtId(1, 2), "Layer 1")))
        
        yield SceneGroupItemBlock(
            parent_id=root_id, 
            item=CrdtSequenceItem(CrdtId(1, 3), CrdtId(0, 0), CrdtId(0, 0), 0, layer_id)
        )

        last_id = CrdtId(0, 0)
        stroke_counter = 10

        # Enumerate to get the original index of the stroke
        for stroke_idx, stroke in enumerate(page.strokes):
            rm_points = []
            
            for (x_xpp, y_xpp) in stroke.points:
                rm_x, rm_y = get_new_stroke_coordinates(x_xpp, y_xpp, page.width, page.height)
                rm_points.append(si.Point(
                    x=float(rm_x), y=float(rm_y), 
                    speed=20, direction=0, width=4, pressure=128
                ))

            if not rm_points:
                continue

            thickness = stroke.width * DPI_RATIO
            line = si.Line(
                color=_map_color(stroke.color), tool=si.Pen.FINELINER_2,
                points=rm_points, thickness_scale=thickness, starting_length=0.0
            )

            new_id = CrdtId(1, stroke_counter)
            
            # *** KEY CHANGE: Record the mapping ***
            # NOTE: We currently assume all strokes are on layer 0. A future
            # refactor could preserve the original layer structure from XOPP.
            rm_id_str = f"{new_id.part1}_{new_id.part2}"

            stroke_map[rm_id_str] = {
                "layer_idx": 0,
                "stroke_idx": stroke_idx
            }
            # **************************************
            
            yield SceneLineItemBlock(
                parent_id=layer_id,
                item=CrdtSequenceItem(new_id, last_id, CrdtId(0, 0), 0, line)
            )
            last_id = new_id
            stroke_counter += 1

    with open(output_path, "wb") as f:
        write_blocks(f, block_generator(), options={"version": "3.3.2"})
    
    return output_path, stroke_map
