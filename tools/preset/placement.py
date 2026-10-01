"""Spot placement in map coordinates, independent of Qt and QGIS.

Spacing is specified in micrometers. ``scale`` converts it to map units.
Fixed-step lines include only positions at multiples of the requested step.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LinePlacement:
    points: list
    length: float
    step: float


def line_positions(start, end, scale=1, *, step=None, count=None, limit=5000):
    """Use either fixed spacing or a point count that includes both endpoints.

    Raise ValueError with a UI-ready explanation before allocating too many points.
    """
    if scale <= 0:
        raise ValueError("Pixel size must be positive.")
    length = math.hypot(end[0] - start[0], end[1] - start[1]) / scale
    if length <= 0:
        raise ValueError("Choose a different end point.")
    if (step is None) == (count is None):
        raise ValueError("Choose either step size or spot count.")
    if step is not None:
        if step <= 0:
            raise ValueError("Step size must be positive.")
        count = math.floor(length / step) + 1
    else:
        if count < 2:
            raise ValueError("Choose at least two spots.")
        step = length / (count - 1)
    if count > limit:
        raise ValueError(f"Maximum {limit} spots.")

    points = []
    for index in range(count):
        fraction = index * step / length
        points.append([
            start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction,
        ])
    return LinePlacement(points, length, step)


def grid_positions(start, step, count, order, scale=1, rotation=0, limit=5000):
    """Return row-major (order 0) or column-major positions, rotated around start.

    Negative steps reverse an axis. Rotation is in degrees, with the same
    coordinate convention as the canvas rotation used by the plugin.
    """
    n_x, n_y = count
    if n_x < 1 or n_y < 1:
        raise ValueError("Choose at least one spot per axis.")
    if n_x * n_y > limit:
        raise ValueError(f"Maximum {limit} spots.")
    if (n_x > 1 and step[0] == 0) or (n_y > 1 and step[1] == 0):
        raise ValueError("Step size must be nonzero when using multiple spots.")
    if scale <= 0:
        raise ValueError("Pixel size must be positive.")

    if order == 0:
        indices = ((x, y) for y in range(n_y) for x in range(n_x))
    else:
        indices = ((x, y) for x in range(n_x) for y in range(n_y))
    angle = math.radians(rotation)
    cosine, sine = math.cos(angle), math.sin(angle)
    points = []
    for x, y in indices:
        dx, dy = x * step[0] * scale, y * step[1] * scale
        points.append([
            start[0] + dx * cosine - dy * sine,
            start[1] + dx * sine + dy * cosine,
        ])
    return points
