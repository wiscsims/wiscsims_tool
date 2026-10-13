# Vendored from MonkeyNavigator2/tools/globalLocalPlaneQuality.py.
# Source SHA256: cc3bcaedb41840887254d7f69cfb89a5abff9b1abc47950df5a868fb358ed2b2
# Keep the forward GLP calculation identical to MonkeyNavigator2 Export.
"""Global similarity + unweighted local residual plane, without hardware I/O.

No production converter or hardware dependencies. Failed fits never fall back
to a different model. Coordinates and predictions retain full float precision.
"""

import math


GLOBAL_LOCAL_PLANE_NEIGHBOR_COUNT = 12
MIN_LOCAL_REFERENCES = 4
# Relative pivot tolerance on a centered, isotropically scaled normal matrix.
# This rejects ill-conditioned geometry, not errors above a scientific cutoff.
RELATIVE_PIVOT_TOLERANCE = 1e-12


def _finite(values):
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite GLP calculation")


def fit_similarity(canvas, stage):
    """OLS X=a*x-b*y+tx, Y=b*x+a*y+ty, using all training points."""
    if len(canvas) != len(stage) or len(canvas) < 2:
        raise ValueError("Global similarity requires matching training coordinates")
    _finite(v for points in (canvas, stage) for p in points for v in p)
    n = len(canvas)
    center = [math.fsum(p[j] / n for p in canvas) for j in (0, 1)]
    stage_center = [math.fsum(p[j] / n for p in stage) for j in (0, 1)]
    offsets = [(p[0] - center[0], p[1] - center[1]) for p in canvas]
    spread = max(abs(v) for p in offsets for v in p)
    resolution = max(math.ulp(v) for p in canvas for v in p)
    if spread <= 8 * resolution:
        raise ValueError("Degenerate global similarity geometry")
    # Common scaling preserves the centered closed-form OLS solution and avoids
    # squaring large raw map coordinates. Do not adopt production rotation signs.
    normalized = [(x / spread, y / spread) for x, y in offsets]
    residual = [(p[0] - stage_center[0], p[1] - stage_center[1]) for p in stage]
    denominator = math.fsum(x*x + y*y for x, y in normalized)
    a = math.fsum(x*X + y*Y for (x, y), (X, Y) in zip(normalized, residual)) / denominator / spread
    b = math.fsum(x*Y - y*X for (x, y), (X, Y) in zip(normalized, residual)) / denominator / spread
    params = (a, b, stage_center[0] - a*center[0] + b*center[1],
              stage_center[1] - b*center[0] - a*center[1])
    _finite(params)
    return params


def apply_similarity(point, params):
    a, b, tx, ty = params
    x, y = point
    result = (a*x - b*y + tx, b*x + a*y + ty)
    _finite(result)
    return result


def _solve(normal, rhs):
    """Small 3x3 normal-equation solver with partial pivoting, two RHS."""
    matrix = [list(row) + list(values) for row, values in zip(normal, rhs)]
    _finite(v for row in matrix for v in row)
    threshold = RELATIVE_PIVOT_TOLERANCE * max(abs(v) for row in normal for v in row)
    for column in range(3):
        pivot = max(range(column, 3), key=lambda i: abs(matrix[i][column]))
        if abs(matrix[pivot][column]) <= threshold:
            raise ValueError("Singular or nearly collinear local plane geometry")
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        for row in range(column + 1, 3):
            factor = matrix[row][column] / matrix[column][column]
            for j in range(column, 5):
                matrix[row][j] -= factor * matrix[column][j]
    solutions = []
    for axis in (3, 4):
        result = [0.0] * 3
        for row in (2, 1, 0):
            result[row] = (matrix[row][axis] - math.fsum(matrix[row][j]*result[j] for j in range(row+1, 3))) / matrix[row][row]
        _finite(result)
        solutions.append(result)
    return solutions


def local_residual_plane(target, canvas, residuals):
    """Unweighted OLS residual at target, from already selected local points."""
    if len(canvas) != len(residuals) or len(canvas) < MIN_LOCAL_REFERENCES:
        raise ValueError("Local residual plane requires at least four training references")
    _finite(v for points in (canvas, residuals, [target]) for p in points for v in p)
    offsets = [(p[0] - target[0], p[1] - target[1]) for p in canvas]
    # Recenter/scale target-relative columns only as a change of basis. All
    # observations still carry equal weight; recover the intercept at u=v=0.
    n = len(offsets)
    center = [math.fsum(p[j] / n for p in offsets) for j in (0, 1)]
    scale = max(abs(p[j] - center[j]) for p in offsets for j in (0, 1))
    if not math.isfinite(scale) or scale == 0:
        raise ValueError("Degenerate local plane geometry")
    design = [[(p[0]-center[0])/scale, (p[1]-center[1])/scale, 1.0] for p in offsets]
    normal = [[math.fsum(row[i]*row[j] for row in design) for j in range(3)] for i in range(3)]
    rhs = [[math.fsum(row[i]*r[j] for row, r in zip(design, residuals)) for j in (0, 1)] for i in range(3)]
    solutions = _solve(normal, rhs)
    result = tuple(c - p*center[0]/scale - q*center[1]/scale for p, q, c in solutions)
    _finite(result)
    return result


def global_residual_plane_stage_predict(target, canvas, stage):
    """All inputs must be training-only; nearest-12 selection follows global fit."""
    return PreparedGlobalLocalPlane(canvas, stage).predict(target)


class PreparedGlobalLocalPlane:
    """Immutable input snapshot and reusable global fit/residuals.

    LOOCV constructs one instance per training fold. Movement/export use a
    separate full-reference instance, refreshed on alignment changes only.
    """

    def __init__(self, canvas, stage):
        if len(canvas) < MIN_LOCAL_REFERENCES:
            raise ValueError("GLP requires at least four usable references")
        self.canvas = tuple(tuple(p) for p in canvas)
        self.params = fit_similarity(self.canvas, stage)
        self.residuals = tuple(tuple(s[j] - g[j] for j in (0, 1))
                               for s, g in zip(stage, (apply_similarity(p, self.params) for p in self.canvas)))
        _finite(v for p in self.residuals for v in p)

    def predict(self, target):
        _finite(target)
        nearest = sorted(range(len(self.canvas)), key=lambda i: (math.dist(target, self.canvas[i]), i))[:GLOBAL_LOCAL_PLANE_NEIGHBOR_COUNT]
        local = local_residual_plane(target, [self.canvas[i] for i in nearest], [self.residuals[i] for i in nearest])
        global_prediction = apply_similarity(target, self.params)
        result = tuple(global_prediction[j] + local[j] for j in (0, 1))
        _finite(result)
        return result
