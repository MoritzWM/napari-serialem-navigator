from typing import TYPE_CHECKING, List, Optional

import numpy as np
from magicgui.widgets import ComboBox, PushButton, Container, create_widget
from skimage.transform import estimate_transform

if TYPE_CHECKING:
    import napari


class LinkMap(Container):
    def __init__(self, viewer: "napari.viewer.Viewer"):  # type: ignore
        super().__init__()
        self.viewer = viewer

        self.wdg_shapes_layer = create_widget(
            label="Navigator shapes", annotation="napari.layers.Shapes"
        )
        self.wdg_image_layer = create_widget(
            label="Map image", annotation="napari.layers.Image"
        )
        self.wdg_polygon = ComboBox(
            label="Polygon", choices=self.polygon_names
        )
        self.wdg_link = PushButton(text="Link")
        self.wdg_link.clicked.connect(self.link)
        self.wdg_shapes_layer.changed.connect(self.wdg_polygon.reset_choices)  # type: ignore
        self.extend(
            [
                self.wdg_shapes_layer,
                self.wdg_image_layer,
                self.wdg_polygon,
                self.wdg_link,
            ]
        )

    @property
    def shapes_layer(self) -> Optional["napari.layers.Shapes"]:  # type: ignore
        assert isinstance(self.wdg_shapes_layer, ComboBox)
        return self.wdg_shapes_layer.value

    @property
    def image_layer(self) -> Optional["napari.layers.Image"]:  # type: ignore
        assert isinstance(self.wdg_image_layer, ComboBox)
        return self.wdg_image_layer.value

    def polygon_names(self, *args) -> List[str]:
        if self.shapes_layer is None:
            return []
        return list(self.shapes_layer.properties["polygon_name"])

    def link(self):
        if self.shapes_layer is None or self.image_layer is None:
            return
        shape_idx = self.polygon_names().index(self.wdg_polygon.value)
        shape = self.shapes_layer.data[shape_idx]
        image_shape = self.image_layer.data.shape
        image_coords = np.array(
            [
                [image_shape[0], 0],
                [image_shape[0], image_shape[1]],
                [0, image_shape[1]],
                [0, 0],
            ]
        )
        transform = estimate_transform(
            ttype="affine", src=image_coords, dst=shape
        )
        self.image_layer.affine = transform.params
