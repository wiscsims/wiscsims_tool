"""GLP export parity and verified inverse coordinates, independent of QGIS."""

import math
import pathlib
import sys
import types
import unittest

PACKAGE = "glp_under_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "tools/imports")]
sys.modules[PACKAGE] = package
from glp_under_test.globalLocalPlane import PreparedGlobalLocalPlane
from glp_under_test.glpInverse import PreparedGLPInverse, reference_snapshot


def warped_grid():
    canvas = [(x*1000, y*1000) for x in range(5) for y in range(5)]
    stage = [(1.2*x - .15*y + 120 + 1e-6*x*y,
              .15*x + 1.2*y - 50 + 2e-6*x*x) for x, y in canvas]
    return canvas, stage


class GLPInverseTests(unittest.TestCase):
    def test_forward_matches_monkeynavigator2_export_predictions(self):
        # Generated directly with MN2/tools/globalLocalPlaneQuality.py, whose
        # SHA256 is recorded in the vendored forward module. No QGIS/hardware I/O.
        forward = PreparedGlobalLocalPlane(*warped_grid())
        fixtures = [
            ((350.2, 870.8), (409.67489360100376, 1047.944347302384)),
            ((2000.3, 1700.7), (2268.6568500000003, 2300.2207333333336)),
            ((4100.1, -300.2), (5085.224355272728, 236.3054916363637)),
        ]
        for canvas, expected in fixtures:
            self.assertLess(math.dist(forward.predict(canvas), expected), 1e-10)

    def test_warped_glp_roundtrip_inverts_export_instead_of_refitting_reversed_data(self):
        canvas, stage = warped_grid()
        inverse = PreparedGLPInverse(canvas, stage)
        reversed_fit = PreparedGlobalLocalPlane(stage, canvas)
        for point in ((350.2, 870.8), (2000.3, 1700.7), (4100.1, -300.2)):
            target = inverse.forward.predict(point)
            returned = inverse.predict(target)
            self.assertLess(math.dist(point, returned), 1e-8)
            self.assertLess(math.dist(inverse.forward.predict(returned), target), 1e-6)
            self.assertGreater(math.dist(reversed_fit.predict(target), point), 1e-5)

    def test_large_map_origins_rotation_and_affine_residual_keep_fractional_coordinates(self):
        origin = (5e6, -1e7)
        canvas = [(origin[0] + x, origin[1] + y) for x, y in ((0, 0), (200, 0), (0, 300), (200, 300))]
        stage = [(1.23*(x-origin[0]) - .2*(y-origin[1]) + 500,
                  .21*(x-origin[0]) + 1.17*(y-origin[1]) - 200) for x, y in canvas]
        inverse = PreparedGLPInverse(canvas, stage)
        for p in ((origin[0]+51.234, origin[1]+63.456), (origin[0]-150.9, origin[1]+550.2)):
            self.assertLess(math.dist(p, inverse.predict(inverse.forward.predict(p))), 1e-7)

    def test_ambiguous_folded_map_is_rejected(self):
        canvas = [(x, y) for x in range(-2, 3) for y in range(5)]
        inverse = PreparedGLPInverse(canvas, [(x*x, y) for x, y in canvas])
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            inverse.predict(inverse.forward.predict((-1.25, .73)))

    def test_stage_point_in_neighborhood_gap_reports_failed_forward_verification(self):
        inverse = PreparedGLPInverse(*warped_grid())
        # A 0.1 µm shift near a nearest-12 switch can fall outside the piecewise
        # map's image. Import must not claim this is an exact export inverse.
        target = (1170.8996235884567, 1303.8616060225845)
        with self.assertRaisesRegex(ValueError, "Best attempted forward residual"):
            inverse.predict(target)

    def test_insufficient_collinear_singular_and_nonfinite_references_fail(self):
        with self.assertRaisesRegex(ValueError, "four"):
            PreparedGLPInverse([(0, 0)]*3, [(0, 0)]*3)
        inverse = PreparedGLPInverse([(x, 0) for x in range(4)], [(x*2, 0) for x in range(4)])
        with self.assertRaisesRegex(ValueError, "collinear"):
            inverse.predict((1.2, 0))
        canvas = [(0, 0), (1, 0), (0, 1), (1, 1)]
        singular = PreparedGLPInverse(canvas, [(x, 0) for x, y in canvas])
        with self.assertRaisesRegex(ValueError, "singular"):
            singular.predict((.25, 0))
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            PreparedGLPInverse(canvas, [(math.nan, 0)]*4)
        with self.assertRaisesRegex(ValueError, "finite"):
            singular.predict((math.inf, 0))

    def test_reference_filter_matches_monkeynavigator2_enabled_coordinate_and_beam_rules(self):
        records = [dict(r=i, used=2, canvas=(i, i+1), stage=(i+2, i+3),
                        beam=dict(position=[500, 500], size=7, eccentricity=.8)) for i in range(8)]
        records[0]["used"] = 1  # MN2 accepts older enabled state as well.
        records[2]["used"] = 0
        records[3]["beam"]["size"] = 0
        records[4]["beam"]["position"] = (1393, 500)
        records[5]["stage"] = (-999999999, 1)
        records[6]["canvas"] = (math.nan, 2)
        records[7]["used"] = True
        self.assertEqual([r[0] for r in reference_snapshot(records)], [0, 1])


if __name__ == "__main__":
    unittest.main()
