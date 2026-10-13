"""Workbook values must survive the actual Shapefile import path."""

import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from qgis.core import QgsApplication, QgsPointXY, QgsProject
    from qgis.gui import QgsMapCanvas
    from qgis.PyQt.QtCore import QTimer
    from qgis.PyQt.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.tools.imports.importTool import ImportTool
    from wiscsims_tool_class.tools.imports.coordinateTool import CoordinateTool
    from wiscsims_tool_class.tools.imports.glpInverse import PreparedGLPInverse
    from wiscsims_tool_class.ui.wiscsims_tool_dockwidget import WiscSIMSToolDockWidget
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class ExcelLayerImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], True)
        cls.app.initQgis()

    def setUp(self):
        self.canvas = QgsMapCanvas()
        self.dock = WiscSIMSToolDockWidget()
        self.tool = ImportTool(self.dock, self.canvas)
        self.dock.Grp_Alignment.setChecked(False)
        self.directory = tempfile.TemporaryDirectory()
        self.layers = []

    def tearDown(self):
        self.tool.unload()
        for layer in self.layers:
            QgsProject.instance().removeMapLayer(layer.id())
        self.dock.deleteLater()
        self.canvas.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def workbook(self, headers, rows):
        self.tool.xl = SimpleNamespace(
            ws=True, get_headers=lambda: headers, get_values=lambda: rows,
            get_asc_list=lambda: [row[0] for row in rows],
            filter_by_asc=lambda **kwargs: rows,
            find_columns=lambda labels, spreadsheet: [headers.index(label) for label in labels],
            get_workbook_name=lambda: "example.xlsx",
        )
        self.tool.workbook_udpated()

    def create_layer(self):
        path = os.path.join(self.directory.name, "example.shp")
        with patch.object(QFileDialog, "getSaveFileName", return_value=(path, "")), patch.object(
            QInputDialog, "getText", return_value=("example", True)
        ):
            layer = self.tool.create_new_layer()
        self.assertIsNotNone(layer)
        self.layers.append(layer)
        return layer

    def test_blank_dates_times_and_mixed_text_survive_shapefile_roundtrip(self):
        headers = ["File", "Comment", "Result", "Date", "Time", "X", "Y", "EMHV diff"]
        rows = [
            ["20260928@1.asc", "", None, datetime(2026, 9, 28), time(12, 47), 1, 2, 0.5],
            ["20260928@2.asc", "sample", "", datetime(2026, 9, 28), time(13, 1), 3, 4, "rejected"],
        ]
        self.workbook(headers, rows)
        layer = self.create_layer()
        with patch.object(QMessageBox, "warning") as warning, patch.object(QMessageBox, "information"):
            self.tool.import_from_excel()
        warning.assert_not_called()
        self.assertEqual(layer.featureCount(), 2)
        # Reopen the saved file through OGR; in-memory coercion alone is insufficient.
        from qgis.core import QgsVectorLayer
        saved = QgsVectorLayer(layer.source(), "saved", "ogr")
        features = list(saved.getFeatures())
        self.assertEqual(features[0]["Date"], "2026-09-28T00:00:00")
        self.assertEqual(features[0]["Time"], "12:47:00")
        self.assertEqual(features[1]["EMHV diff"], "rejected")
        self.assertEqual(features[0]["EMHV diff"], "0.5")
        self.assertTrue(features[0]["Result"].isNull())
        self.assertEqual(features[1].geometry().asPoint().x(), 3)

    def test_incompatible_existing_numeric_field_stops_before_any_point_is_added(self):
        headers = ["File", "Result", "X", "Y"]
        rows = [["20260928@1.asc", 1.25, 1, 2], ["20260928@2.asc", 2.5, 3, 4]]
        self.workbook(headers, rows)
        layer = self.create_layer()
        rows[1][1] = "rejected"
        with patch.object(QMessageBox, "warning") as warning, patch.object(QMessageBox, "information"):
            self.tool.import_from_excel()
        self.assertEqual(layer.featureCount(), 0)
        self.assertIn("rejected", warning.call_args.args[2])
        self.assertIn("Create a new layer", warning.call_args.args[2])

    def glp_alignment(self, canvas, stage):
        self.tool.cot = CoordinateTool(new=True)
        for i, (c, s) in enumerate(zip(canvas, stage)):
            self.tool.model.addRefPoints(
                2, f"ref-{i}", QgsPointXY(*s), QgsPointXY(*c),
                dict(position=[500, 500], size=7, eccentricity=.8),
            )
        self.dock.Grp_Alignment.setChecked(True)
        self.dock.Cmb_Import_Conversion.setCurrentIndex(1)

    def test_glp_import_returns_exported_spots_and_keeps_stage_attributes(self):
        canvas = [(x*1000, y*1000) for x in range(5) for y in range(5)]
        stage = [(1.2*x - .15*y + 120 + 1e-6*x*y,
                  .15*x + 1.2*y - 50 + 2e-6*x*x) for x, y in canvas]
        forward = PreparedGLPInverse(canvas, stage).forward
        spots = [(350.2, 870.8), (2000.3, 1700.7), (4100.1, -300.2)]
        rows = [[f"20261001@{i}.asc", f"spot-{i}", *forward.predict(p)] for i, p in enumerate(spots, 1)]
        self.workbook(["File", "Comment", "X", "Y"], rows)
        layer = self.create_layer()
        self.glp_alignment(canvas, stage)
        with patch.object(QMessageBox, "warning") as warning, patch.object(QMessageBox, "information"):
            self.tool.import_from_excel()
        warning.assert_not_called()
        for feature, point, row in zip(layer.getFeatures(), spots, rows):
            self.assertAlmostEqual(feature.geometry().asPoint().x(), point[0], places=8)
            self.assertAlmostEqual(feature.geometry().asPoint().y(), point[1], places=8)
            self.assertAlmostEqual(feature["X"], row[2], places=6)
        self.assertEqual(layer.featureCount(), 3)

    def test_glp_failure_does_not_write_earlier_valid_points_or_fall_back_to_current(self):
        canvas = [(x*1000, y*1000) for x in range(4) for y in range(4)]
        stage = [(x*2+10, y*2-20) for x, y in canvas]
        self.workbook(["File", "X", "Y"], [["20261001@1.asc", 100, 200], ["20261001@2.asc", 300, 400]])
        layer = self.create_layer()
        self.glp_alignment(canvas, stage)
        inverse = self.tool.prepare_glp_inverse()
        with patch.object(inverse, "predict", side_effect=[(45, 110), ValueError("Ambiguous GLP point")]), patch.object(
            self.tool, "get_conversion_models", side_effect=AssertionError("Unexpected Current fallback")
        ), patch.object(self.tool, "review_glp_failures", return_value="cancel") as review, patch.object(QMessageBox, "information"):
            self.tool.import_from_excel()
        self.assertEqual(layer.featureCount(), 0)
        self.assertEqual(review.call_args.args, ([("20261001@2.asc", "Ambiguous GLP point")], 1))

    def test_explicit_partial_import_writes_only_verified_points(self):
        canvas = [(x*1000, y*1000) for x in range(4) for y in range(4)]
        stage = [(x*2+10, y*2-20) for x, y in canvas]
        self.workbook(["File", "X", "Y"], [
            ["20261001@1.asc", 100, 200], ["20261001@2.asc", 300, 400],
            ["20261001@3.asc", 500, 600], ["20261001@4.asc", 700, 800],
        ])
        layer = self.create_layer()
        self.glp_alignment(canvas, stage)
        inverse = self.tool.prepare_glp_inverse()
        with patch.object(inverse, "predict", side_effect=[
            (45, 110), ValueError("No inverse"), (245, 310), ValueError("Ambiguous inverse"),
        ]), patch.object(self.tool, "get_conversion_models", side_effect=AssertionError("Unexpected Current fallback")), patch.object(
            self.tool, "review_glp_failures", return_value="verified"
        ) as review, patch.object(QMessageBox, "information") as information:
            self.tool.import_from_excel()
        self.assertEqual(review.call_args.args, ([
            ("20261001@2.asc", "No inverse"), ("20261001@4.asc", "Ambiguous inverse"),
        ], 2))
        features = list(layer.getFeatures())
        self.assertEqual([f["File"] for f in features], ["20261001@1.asc", "20261001@3.asc"])
        self.assertEqual(features[1].geometry().asPoint(), QgsPointXY(245, 310))
        self.assertIn("2 points", information.call_args.args[2])

    def test_glp_review_defaults_to_cancel_and_requires_explicit_import(self):
        failures = [("20261001@2.asc", "No inverse"), ("20261001@4.asc", "Ambiguous inverse")]
        for action in ("cancel", "verified", "pairs"):
            seen = {}

            def choose():
                box = QApplication.activeModalWidget()
                seen["details"] = box.detailedText()
                seen["default"] = box.defaultButton() is box.button(QMessageBox.Cancel)
                if action == "cancel":
                    button = box.button(QMessageBox.Cancel)
                else:
                    role = QMessageBox.AcceptRole if action == "verified" else QMessageBox.ActionRole
                    button = next(b for b in box.buttons() if box.buttonRole(b) == role)
                button.click()

            QTimer.singleShot(0, choose)
            self.assertEqual(self.tool.review_glp_failures(failures, 2), action)
            self.assertTrue(seen["default"])
            self.assertIn("20261001@2.asc", seen["details"])
            self.assertIn("20261001@4.asc", seen["details"])

    def test_glp_review_offers_only_pairs_or_cancel_when_no_points_are_verified(self):
        seen = {}

        def cancel():
            box = QApplication.activeModalWidget()
            seen["can_import"] = any(box.buttonRole(b) == QMessageBox.AcceptRole for b in box.buttons())
            next(b for b in box.buttons() if box.buttonRole(b) == QMessageBox.ActionRole).click()

        QTimer.singleShot(0, cancel)
        self.assertEqual(self.tool.review_glp_failures([("20261001@1.asc", "No inverse")], 0), "pairs")
        self.assertFalse(seen["can_import"])

    def test_pairs_option_converts_only_failed_points_and_preserves_order(self):
        canvas = [(x*1000, y*1000) for x in range(4) for y in range(4)]
        stage = [(x*2+10, y*2-20) for x, y in canvas]
        rows = [["20261001@1.asc", 100, 200], ["20261001@2.asc", 300, 400], ["20261001@3.asc", 500, 600]]
        self.workbook(["File", "X", "Y"], rows)
        layer = self.create_layer()
        self.glp_alignment(canvas, stage)
        inverse = self.tool.prepare_glp_inverse()
        self.tool.update_conv_params()
        expected = [self.tool.convert_with_reference_pairs(row[1:]) for row in rows]
        glp_point = (144.25, 210.75)
        with patch.object(inverse, "predict", side_effect=[ValueError("No inverse"), glp_point, ValueError("Ambiguous inverse")]), patch.object(
            self.tool, "review_glp_failures", return_value="pairs"
        ), patch.object(self.tool, "convert_with_reference_pairs", wraps=self.tool.convert_with_reference_pairs) as pairs, patch.object(
            QMessageBox, "information"
        ) as information:
            self.tool.import_from_excel()
        self.assertEqual([call.args[0] for call in pairs.call_args_list], [rows[0][1:], rows[2][1:]])
        features = list(layer.getFeatures())
        self.assertEqual([f["File"] for f in features], [row[0] for row in rows])
        for feature, point in zip(features, [expected[0], glp_point, expected[2]]):
            self.assertLess(feature.geometry().asPoint().distance(QgsPointXY(*point)), 1e-8)
        self.assertEqual([(f["X"], f["Y"]) for f in features], [(row[1], row[2]) for row in rows])
        self.assertIn("2 points were converted with Current (reference pairs)", information.call_args.args[2])

    def test_failed_pair_fallback_aborts_before_any_provider_write(self):
        canvas = [(0, 0), (100, 0), (0, 100), (100, 100)]
        stage = [(x*2+10, y*2-20) for x, y in canvas]
        self.workbook(["File", "X", "Y"], [["20261001@1.asc", 100, 200], ["20261001@2.asc", 300, 400]])
        layer = self.create_layer()
        self.glp_alignment(canvas, stage)
        inverse = self.tool.prepare_glp_inverse()
        with patch.object(inverse, "predict", side_effect=[(45, 110), ValueError("No inverse")]), patch.object(
            self.tool, "review_glp_failures", return_value="pairs"
        ), patch.object(self.tool, "convert_with_reference_pairs", side_effect=ValueError("No usable pair")), patch.object(
            QMessageBox, "warning"
        ) as warning, patch.object(QMessageBox, "information") as information:
            self.tool.import_from_excel()
        self.assertEqual(layer.featureCount(), 0)
        self.assertIn("20261001@2.asc", warning.call_args.args[2])
        self.assertIn("No usable pair", warning.call_args.args[2])
        information.assert_not_called()

    def test_alignment_edits_and_enabled_states_invalidate_glp_cache(self):
        canvas = [(0, 0), (100, 0), (0, 100), (100, 100)]
        stage = [(x*2+10, y*2-20) for x, y in canvas]
        self.glp_alignment(canvas, stage)
        first = self.tool.prepare_glp_inverse()
        self.assertIs(first, self.tool.prepare_glp_inverse())
        # Block unrelated Current UI refresh; the GLP cache must inspect the
        # actual coordinates even without a refresh signal.
        self.tool.model.blockSignals(True)
        self.tool.model.item(0, self.tool.model.c["stage"]).setData(QgsPointXY(11, -20), 0)
        self.assertIsNot(first, self.tool.prepare_glp_inverse())
        self.tool.model.setCheckState(0, 0)
        with self.assertRaisesRegex(ValueError, "four"):
            self.tool.prepare_glp_inverse()
        self.assertIsNone(self.tool._glp_inverse)
        self.tool.model.blockSignals(False)
