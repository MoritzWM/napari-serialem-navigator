from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from magicgui import magic_factory
from magicgui.widgets import PushButton
from skimage.transform import estimate_transform

from ._mrc import read_map, resolve_map_path

if TYPE_CHECKING:
    import napari



def _map_items(layer) -> list[tuple[str, int]]:
    """``(label, row)`` choices for items in ``layer`` that have a MapFile.

    ``row`` is the positional row in ``layer.features``, which is also the
    index of the shape in ``layer.data``; the label is ``"<Item>: <Note>"``.
    """
    features = getattr(layer, "features", None)
    if features is None or "MapFile" not in features:
        return []
    has_map = (features["MapFile"].notna() & (features["MapFile"] != "")).to_numpy()
    notes = features["Note"] if "Note" in features else None  # noqa: SIM401
    choices = []
    for row in np.flatnonzero(has_map):
        label = str(features["Item"].iloc[row])
        if notes is not None and pd.notna(notes.iloc[row]) and notes.iloc[row]:
            label += f": {notes.iloc[row]}"
        choices.append((label, int(row)))
    return choices


def _init_load_map(widget) -> None:
    """Keep the ``map_item`` choices in sync with the selected shapes layer."""

    def update_choices(*_):
        widget.map_item.choices = _map_items(widget.shapes_layer.value)

    widget.shapes_layer.changed.connect(update_choices)
    # napari fills the layer dropdown only once the widget is docked in the
    # viewer, so the initial call below may see no layer yet.
    widget.parent_changed.connect(update_choices)
    update_choices()

    refresh = PushButton(text="Refresh list")
    refresh.clicked.connect(update_choices)
    widget.insert(widget.index(widget.map_item) + 1, refresh)


@magic_factory(
    widget_init=_init_load_map,
    map_item={"widget_type": "ComboBox", "choices": []},
    call_button="Load",
)
def load_maps(
    viewer: "napari.viewer.Viewer", # pyright: ignore[reportAttributeAccessIssue]
    shapes_layer: "napari.layers.Shapes", # pyright: ignore[reportAttributeAccessIssue]
    map_item: int,
):
    # map_item is the positional row in shapes_layer.features / index in .data
    row = shapes_layer.features.iloc[map_item]
    path = resolve_map_path(row["MapFile"], shapes_layer.source.path)
    data = read_map(path)
    layer = viewer.add_image(data, name=f"{row['Item']}: {path.name}", interpolation2d="linear")
    layer.affine = _placement_affine(data.shape, shapes_layer.data[map_item])
    # Draw the map beneath the navigator shapes instead of on top of them.
    viewer.layers.move(
        viewer.layers.index(layer), viewer.layers.index(shapes_layer)
    )


def _placement_affine(image_shape, polygon: np.ndarray) -> np.ndarray:
    """Affine mapping the image corners onto the navigator polygon vertices."""
    h, w = image_shape[:2]
    polygon = np.asarray(polygon)
    if len(polygon) == 5 and np.allclose(polygon[0], polygon[-1]):
        polygon = polygon[:-1]  # SerialEM repeats the first vertex to close it
    image_corners = np.array([[h, 0], [h, w], [0, w], [0, 0]])
    if len(polygon) != 4:
        raise ValueError(
            f"Expected a 4-vertex polygon for the map, got {len(polygon)}"
        )
    return estimate_transform("affine", src=image_corners, dst=polygon).params
