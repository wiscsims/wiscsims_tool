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
    from qgis.core import QgsApplication, QgsProject
    from qgis.gui import QgsMapCanvas
    from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.tools.imports.importTool import ImportTool
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
