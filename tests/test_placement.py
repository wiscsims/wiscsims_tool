"""Numerical placement contracts, runnable without a QGIS installation."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from wiscsims_tool_class.tools.preset.placement import grid_positions, line_positions


class PlacementTests(unittest.TestCase):
    def test_step_has_priority_over_endpoint_and_handles_short_lines(self):
        line = line_positions((0, 0), (25, 0), step=10)
        self.assertEqual(line.points, [[0, 0], [10, 0], [20, 0]])
        self.assertEqual(line_positions((3, 4), (6, 4), step=10).points, [[3, 4]])

    def test_diagonal_line_uses_physical_spacing(self):
        # 50 map units at 0.5 map units per micrometer is a 100 µm line.
        line = line_positions((1, 2), (31, 42), scale=0.5, step=20)
        self.assertEqual(len(line.points), 6)
        for first, second in zip(line.points, line.points[1:]):
            distance = ((second[0] - first[0])**2 + (second[1] - first[1])**2)**0.5
            self.assertAlmostEqual(distance, 10)
        self.assertEqual(line.points[-1], [31, 42])

    def test_count_mode_includes_both_endpoints(self):
        line = line_positions((-10, 4), (20, 4), count=4)
        self.assertEqual(line.points, [[-10, 4], [0, 4], [10, 4], [20, 4]])
        self.assertEqual(line.step, 10)

    def test_line_limits_and_invalid_inputs(self):
        for options in ({"step": 0}, {"count": 1}, {"step": 1, "count": 3}, {}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                line_positions((0, 0), (10, 0), **options)
        with self.assertRaisesRegex(ValueError, "Maximum 5 spots"):
            line_positions((0, 0), (1_000_000, 0), step=1, limit=5)
        with self.assertRaisesRegex(ValueError, "different end point"):
            line_positions((3, 4), (3, 4), step=10)

    def test_grid_order_rotation_and_negative_step(self):
        horizontal = grid_positions((5, 8), (-2, 3), (2, 2), 0)
        vertical = grid_positions((5, 8), (-2, 3), (2, 2), 1)
        self.assertEqual(horizontal, [[5, 8], [3, 8], [5, 11], [3, 11]])
        self.assertEqual(vertical, [horizontal[i] for i in (0, 2, 1, 3)])
        rotated = grid_positions((5, 8), (-2, 3), (2, 2), 0, scale=2, rotation=90)
        for actual, expected in zip(rotated, [[5, 8], [5, 4], [-1, 8], [-1, 4]]):
            self.assertAlmostEqual(actual[0], expected[0])
            self.assertAlmostEqual(actual[1], expected[1])

    def test_grid_limits_and_single_spot_axes(self):
        self.assertEqual(grid_positions((1, 2), (0, 0), (1, 1), 0), [[1, 2]])
        for count in ((0, 2), (2, 0), (2, 2)):
            with self.subTest(count=count), self.assertRaises(ValueError):
                grid_positions((0, 0), (0, 10), count, 0)
        with self.assertRaisesRegex(ValueError, "Maximum 5 spots"):
            grid_positions((0, 0), (10, 10), (1000000, 1000000), 0, limit=5)


if __name__ == "__main__":
    unittest.main()
