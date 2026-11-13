import re
from pathlib import Path

import numpy as np
import pandas as pd

section_pattern = re.compile(r'^\[Item\s*=\s*(.+?)\s*\]$')

# Keys whose values are always free text and must not be converted to numbers
STRING_KEYS = {'Note', 'MapFile', 'LastSavedAs'}

Value = str | int | float | tuple[int, ...] | tuple[float, ...]


def _parse_value(key: str, raw: str) -> Value:
    """Convert a raw value into an int/float (single value), a tuple of
    ints/floats (multiple values), or leave it as string."""
    raw = raw.strip()
    if key in STRING_KEYS:
        return raw
    parts = raw.split()
    if not parts:
        return raw
    for conv in (int, float):
        try:
            values = tuple(conv(p) for p in parts)
        except ValueError:
            continue
        return values[0] if len(values) == 1 else values
    return raw


def _parse_line(line: str) -> tuple[str, Value]:
    key, val = line.split('=', maxsplit=1)
    key = key.strip()
    return key, _parse_value(key, val)


def pts_to_arrays(ptsx: pd.Series, ptsy: pd.Series) -> list[np.ndarray]:
    """Convert the ``PtsX``/``PtsY`` columns into one (N, 2) float array per row,
    with columns in (y, x) order as expected by napari. N may differ per row.
    Scalar values (single-point items) give shape (1, 2)."""
    arrays = []
    for x, y in zip(ptsx, ptsy, strict=True):
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        if x.shape != y.shape:
            raise ValueError(f'PtsX and PtsY differ in length: {x.shape} vs {y.shape}')
        arrays.append(np.column_stack([y, x]))
    return arrays


def read_sem_navigator(path: Path) -> pd.DataFrame:
    """Parse a SerialEM navigator file into a DataFrame.

    Each ``[Item = <name>]`` section becomes one row. The item name is stored in
    the ``Item`` column (kept as string, since names can be non-numeric, e.g.
    ``empty``); the index is a default RangeIndex. Keys
    become columns; items lacking a key get NaN. Keys in the file header
    (before the first item) are stored in ``df.attrs['header']``.
    """
    header: dict[str, Value] = {}
    items: dict[str, dict[str, Value]] = {}
    current: dict[str, Value] = header

    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = section_pattern.match(line)
            if m:
                name = m.group(1)
                if name in items:
                    raise ValueError(f'Duplicate navigator item {name!r} in {path}')
                current = items[name] = {}
            elif '=' in line:
                key, val = _parse_line(line)
                current[key] = val

    df = pd.DataFrame.from_dict(items, orient='index')
    df.index.name = 'Item'
    df = df.reset_index()
    df.attrs['header'] = header
    return df
