"""Invert MonkeyNavigator2's forward GLP, without Qt or optional packages.

Each fixed nearest-12 reference set gives an affine forward map. Solve those
maps, then verify candidates using the original forward model and its own
canvas-space neighbor selection. Swapping canvas/stage and refitting is not
the inverse of the exported model.
"""

import math
from collections import deque

from .globalLocalPlane import (
    GLOBAL_LOCAL_PLANE_NEIGHBOR_COUNT, RELATIVE_PIVOT_TOLERANCE,
    PreparedGlobalLocalPlane, _solve, apply_similarity,
)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _coordinate(value):
    try:
        pair = tuple(value)
        return len(pair) == 2 and all(_number(v) and v != -999999999 for v in pair)
    except TypeError:
        return False


class AmbiguousGLPInverse(ValueError):
    """A verified stage point has more than one discovered canvas solution."""


def reference_snapshot(records):
    """Match MN2 referenceValidation.is_usable_reference, including beam validity.

    Beam values do not enter GLP, but affect which references MN2 fits. Keep
    its current 1392 x 1040 FOV bounds and enabled states 1/2 consistent here.
    """
    result = []
    for record in records:
        used = record.get("used")
        beam = record.get("beam")
        if not isinstance(used, int) or isinstance(used, bool) or used not in (1, 2):
            continue
        if not _coordinate(record.get("canvas")) or not _coordinate(record.get("stage")):
            continue
        if not isinstance(beam, dict) or not _coordinate(beam.get("position")):
            continue
        if not all(_number(beam.get(key)) and beam[key] > 0 for key in ("size", "eccentricity")):
            continue
        if not (0 <= beam["position"][0] <= 1392 and 0 <= beam["position"][1] <= 1040):
            continue
        result.append((record["r"], tuple(record["canvas"]), tuple(record["stage"])))
    return tuple(result)


def _invert_affine(matrix, displacement):
    magnitude = max(abs(value) for row in matrix for value in row)
    if magnitude == 0 or not math.isfinite(magnitude):
        raise ValueError("GLP inverse has a singular local transform.")
    a, b = (value / magnitude for value in matrix[0])
    c, d = (value / magnitude for value in matrix[1])
    determinant = a * d - b * c
    if not math.isfinite(determinant) or abs(determinant) <= RELATIVE_PIVOT_TOLERANCE:
        raise ValueError("GLP inverse has a singular or ill-conditioned local transform.")
    x, y = (value / magnitude for value in displacement)
    result = ((d*x - b*y) / determinant, (a*y - c*x) / determinant)
    if not all(math.isfinite(v) for v in result):
        raise ValueError("Non-finite GLP inverse result.")
    return result


class PreparedGLPInverse:
    """Cache the global forward fit and local affine maps for a batch import."""

    def __init__(self, canvas, stage):
        self.forward = PreparedGlobalLocalPlane(canvas, stage)
        self.stage = tuple(tuple(p) for p in stage)
        self._local_models = {}

    def _neighbors(self, canvas):
        return tuple(sorted(
            range(len(self.forward.canvas)),
            key=lambda i: (math.dist(canvas, self.forward.canvas[i]), i),
        )[:GLOBAL_LOCAL_PLANE_NEIGHBOR_COUNT])

    def _local_model(self, neighbors):
        # Sort indices for a stable cache key; observations have equal weight.
        key = tuple(sorted(neighbors))
        if key not in self._local_models:
            points = [self.forward.canvas[i] for i in key]
            residuals = [self.forward.residuals[i] for i in key]
            origin = tuple(math.fsum(p[j] / len(points) for p in points) for j in (0, 1))
            scale = max(abs(p[j] - origin[j]) for p in points for j in (0, 1))
            if scale == 0:
                raise ValueError("Degenerate GLP local reference geometry.")
            design = [[(p[j] - origin[j]) / scale for j in (0, 1)] + [1.0] for p in points]
            normal = [[math.fsum(row[i]*row[j] for row in design) for j in range(3)] for i in range(3)]
            rhs = [[math.fsum(row[i]*r[j] for row, r in zip(design, residuals)) for j in (0, 1)] for i in range(3)]
            x, y = _solve(normal, rhs)
            a, b, _, _ = self.forward.params
            matrix = ((a + x[0]/scale, -b + x[1]/scale), (b + y[0]/scale, a + y[1]/scale))
            global_origin = apply_similarity(origin, self.forward.params)
            stage_origin = (global_origin[0] + x[2], global_origin[1] + y[2])
            self._local_models[key] = (origin, stage_origin, matrix)
        return self._local_models[key]

    def predict(self, target):
        if not _coordinate(target):
            raise ValueError("GLP inverse requires finite stage X/Y coordinates.")
        tolerance = max(1e-6, 64 * max(math.ulp(v) for v in target))  # stage µm
        a, b, tx, ty = self.forward.params
        initial = _invert_affine(((a, -b), (b, a)), (target[0] - tx, target[1] - ty))
        # Alternate starting neighborhoods handle changes across nearest-12
        # boundaries; validate all discovered solutions rather than trusting a seed.
        seeds = [initial] + [self.forward.canvas[i] for i in sorted(
            range(len(self.stage)), key=lambda i: (math.dist(target, self.stage[i]), i)
        )[:GLOBAL_LOCAL_PLANE_NEIGHBOR_COUNT]]
        pending = deque(self._neighbors(seed) for seed in seeds)
        visited = set()
        solutions = []
        solution_tolerance = 0
        attempted = []
        errors = []
        while pending:
            neighbors = pending.popleft()
            key = tuple(sorted(neighbors))
            if key in visited:
                continue
            if len(visited) >= 128:
                raise ValueError("GLP inverse did not converge across reference neighborhoods.")
            visited.add(key)
            try:
                origin, stage_origin, matrix = self._local_model(neighbors)
                offset = _invert_affine(matrix, tuple(target[j] - stage_origin[j] for j in (0, 1)))
                candidate = tuple(origin[j] + offset[j] for j in (0, 1))
                attempted.append(candidate)
                actual_neighbors = self._neighbors(candidate)
                if tuple(sorted(actual_neighbors)) != key:
                    pending.append(actual_neighbors)
                    continue
                prediction = self.forward.predict(candidate)
                if math.dist(prediction, target) > tolerance:
                    continue
                # Distinct roots of a folded/discontinuous GLP map must not
                # silently select a different sample location.
                canvas_tolerance = max(
                    math.hypot(*_invert_affine(matrix, (tolerance, 0)))
                    + math.hypot(*_invert_affine(matrix, (0, tolerance))),
                    64 * max(math.ulp(v) for v in candidate),
                )
                if solutions and math.dist(solutions[0], candidate) > max(solution_tolerance, canvas_tolerance):
                    raise AmbiguousGLPInverse("GLP inverse is ambiguous: multiple canvas positions match this stage point.")
                solutions.append(candidate)
                solution_tolerance = max(solution_tolerance, canvas_tolerance)
            except AmbiguousGLPInverse:
                raise
            except ValueError as error:
                errors.append(str(error))
        if not solutions:
            detail = errors[0] if errors else "No consistent nearest-12 neighborhood was found."
            residuals = []
            for candidate in attempted:
                try:
                    residuals.append(math.dist(self.forward.predict(candidate), target))
                except (ValueError, OverflowError):
                    continue
            if residuals:
                detail += f" Best attempted forward residual: {min(residuals):.6g} µm."
            raise ValueError(f"GLP inverse could not find a verified canvas position. {detail}")
        return solutions[0]
