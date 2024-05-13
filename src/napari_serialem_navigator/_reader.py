from pathlib import Path

import numpy as np
from .serialem_navigator import SEMNavigator

def napari_get_reader(path):
    if not isinstance(path, list):
        path = [path]
    if not all(p.endswith('.nav') for p in path):
        return None
    return reader_function


def reader_function(path):
    if isinstance(path, list):
        path = path[0]
    path = Path(path)
    nav = SEMNavigator.read(path)
    # For polygon layers
    polygon_coords = list()
    polygon_names = list()
    # For point layers
    point_coords = list()
    point_names = list()
    for item in nav.items:
        ptsx_str, ptsy_str = item.get('PtsX'), item.get('PtsY')
        if ptsx_str is None or ptsy_str is None:
            continue
        ptsx = [float(x) for x in ptsx_str.split()]
        ptsy = [float(y) for y in ptsy_str.split()]
        if len(ptsx) != len(ptsy):
            raise AttributeError(f'PtsX and PtsY have unequal length in item {item.id}')
        if len(ptsx) == 1:
            point_coords.append((ptsy[0], ptsx[0]))
            point_names.append(str(item))
        elif len(ptsx) > 2:
            # last and first point in list are always equal (that's also why im testing for len(ptsx) > 2)
            ptsx.pop(), ptsy.pop()
            polygon_coords.append(np.array(list(zip(ptsy, ptsx))))
            polygon_names.append(str(item))
    point_coords = np.array(point_coords)
    return [(polygon_coords, dict(name=f'{path.stem} polygons',
                            shape_type='polygon',
                            face_color='transparent',
                            text=dict(
                                string='{polygon_name}',
                                anchor='upper_right',
                            ),
                            properties=dict(polygon_name=polygon_names)), 'shapes'),
            (point_coords, dict(name=f'{path.stem} points',
                          text='{point_name}',
                          properties=dict(point_name=point_names)), 'points')]