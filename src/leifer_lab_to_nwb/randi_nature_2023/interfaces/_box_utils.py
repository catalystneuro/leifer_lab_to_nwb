"""
Adapted from https://github.com/leiferlab/wormdatamodel/blob/2ab956199e3931de41a190d2b9985e961df3810c/wormdatamodel/signal/extraction.py#L12
"""

import pathlib
import json
import math
from typing import Literal

import numpy


def _calculate_voxel_mask(
    centroid_zyx: tuple[int, int, int],
    box_shape: tuple[int, int, int],
    method: Literal["box"] = "box",
) -> tuple[tuple[int, int, int, float], ...]:
    """Generate indices used for slicing of an image array to extract the pixels in the specified box."""
    if method not in ("box"):
        message = f"`method` must be either 'box'. Received '{method}'."
        raise ValueError(message)

    # Only applying to a single Z-frame but assuming ~28 for lower bound on Z-frames
    frame_shape = (max(28, centroid_zyx[0]), 512, 512)

    box_size_to_array_file_path = pathlib.Path(__file__).parent / "box_size_to_array.json"
    with open(file=box_size_to_array_file_path, mode="r") as io:
        box_size_to_array = json.load(fp=io)

    full_box = None
    match {"method": method, "box_shape": box_shape}:
        case {"method": "box", "box_shape": (1, 3, 3)}:
            full_box = numpy.array(box_size_to_array["(1,3,3)"])
        case {"method": "box", "box_shape": (3, 5, 5)}:
            full_box = numpy.array(box_size_to_array["(3,5,5)"])
        case {"method": "box", "box_shape": (5, 5, 5)}:
            full_box = numpy.array(box_size_to_array["(5,5,5)"])

    total_number_of_elements = math.prod(box_shape)

    center_repeated = numpy.repeat(centroid_zyx, repeats=total_number_of_elements).reshape(
        (3, total_number_of_elements)
    )

    center_adjusted_by_box = center_repeated.copy()
    for _ in range(3):
        center_adjusted_by_box += full_box[:, :]

    indices = center_adjusted_by_box.copy()
    for coordinate_index in range(3):
        numpy.clip(indices[coordinate_index], 0, frame_shape[coordinate_index] - 1, indices[coordinate_index])

    voxel_mask = tuple(
        (indices[2, index], indices[1, index], indices[0, index], 1.0) for index in range(total_number_of_elements)
    )
    return voxel_mask
