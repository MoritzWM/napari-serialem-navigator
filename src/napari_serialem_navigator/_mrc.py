"""Reading (montage) MRC maps written by SerialEM."""

from pathlib import Path, PureWindowsPath

import mrcfile
import numpy as np


def resolve_map_path(map_file: str, nav_path: str | Path | None = None) -> Path:
    """Find a navigator ``MapFile`` on this machine.

    The navigator stores the path as seen by the microscope PC (e.g.
    ``X:\\data\\map.mrc``). Try it as-is first, then fall back to the file name
    next to the navigator file.
    """
    direct = Path(map_file)
    if direct.is_file():
        return direct
    name = PureWindowsPath(map_file).name
    if nav_path:
        candidate = Path(nav_path).parent / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Could not find map file {map_file!r}"
        + (f" (also looked for {name!r} next to {nav_path})" if nav_path else "")
    )


def read_mdoc_piece_coords(path: Path) -> tuple[bool, list[tuple[int, ...]]]:
    """Return ``(is_montage, piece_coords)`` from a SerialEM ``.mdoc`` file.

    Aligned piece coordinates are preferred over raw piece coordinates.
    """
    montage = False
    piece_coords: list[tuple[int, ...]] = []
    aligned_coords: list[tuple[int, ...]] = []
    if path.is_file():
        with open(path, errors="replace") as f:
            for line in f:
                if line.startswith("Montage = "):
                    montage = bool(int(line.split()[-1]))
                elif line.startswith("PieceCoordinates = "):
                    piece_coords.append(tuple(map(int, line.split()[-3:])))
                elif line.startswith("AlignedPieceCoords = "):
                    aligned_coords.append(tuple(map(int, line.split()[-3:])))
    return montage, aligned_coords or piece_coords


def read_map(path: str | Path) -> np.ndarray:
    """Read an MRC map, stitching montage pieces using ``<path>.mdoc``."""
    path = Path(path)
    with mrcfile.mmap(path, permissive=True) as mrc:
        data = np.asarray(mrc.data)

    montage, coords = read_mdoc_piece_coords(path.with_name(path.name + ".mdoc"))
    if not (montage and data.ndim == 3 and len(coords) == len(data)):
        return data

    coords = np.array(coords)[:, (1, 0)]  # (x, y, z) -> (y, x)
    coords -= coords.min(axis=0)
    stitched = np.zeros(coords.max(axis=0) + data.shape[1:], dtype=data.dtype)
    for piece, (y, x) in zip(data, coords):
        stitched[y : y + piece.shape[0], x : x + piece.shape[1]] = piece
    return stitched
