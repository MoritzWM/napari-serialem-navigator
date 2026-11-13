from pathlib import Path

from napari import current_viewer
import numpy as np

from napari_serialem_navigator._widget import load_maps
from napari_serialem_navigator.serialem_navigator import (
    pts_to_arrays,
    read_sem_navigator,
)


def napari_get_reader(path):
    if not isinstance(path, list):
        path = [path]
    if not all(p.endswith(".nav") for p in path):
        return None
    return reader_function


def reader_function(path: str | list[str] | Path):
    if isinstance(path, list):
        path = path[0]
    path = Path(path)
    nav = read_sem_navigator(path)
    point_rows = nav.query('`NumPts` == 1').copy()
    polygon_rows = nav.query('`NumPts` > 1').copy()
    point_coords = pts_to_arrays(point_rows["PtsX"], point_rows["PtsY"])
    point_coords = np.concatenate(point_coords)
    polygon_coords = pts_to_arrays(polygon_rows["PtsX"], polygon_rows["PtsY"])

    viewer = current_viewer()
    if viewer is not None:
        dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget("napari-serialem-navigator", "Load maps")
    return [
        (
            polygon_coords,
            {
                "name": f"{path.stem} polygons",
                "shape_type": "polygon",
                "face_color": "transparent",
                "edge_color": "red",
                "edge_width": 0.1,
                "text": {
                    "string": "{Item}",
                    "anchor": "center",
                    "color": "red",
                },
                "features": polygon_rows,
            },
            "shapes",
        ),
        (
            point_coords,
            {
                "name": f"{path.stem} points",
                "text": "{Item}",
                "size": 1,
                "features": point_rows
            },
            "points",
        ),
    ]
