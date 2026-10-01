"""Exercise Line and Grid placement through the current map-click route."""

import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qgis.core import Qgis, QgsApplication, QgsPointXY, QgsProject, QgsRectangle, QgsStyle
    from qgis.gui import QgsMapCanvas, QgsMapMouseEvent, QgsSymbolsListWidget
    from qgis.PyQt.QtCore import QEvent, QPoint, Qt
    from qgis.PyQt.QtTest import QSignalSpy
    from qgis.PyQt.QtWidgets import QComboBox, QFileDialog, QWidget

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.tools.canvasMapTool import CanvasMapTool
    from wiscsims_tool_class.tools.preset.presetTool import PresetTool
    from wiscsims_tool_class.tools.preset.layer_settings import read_sizes, write_sizes
    from wiscsims_tool_class.ui.wiscsims_tool_dockwidget import WiscSIMSToolDockWidget
    from wiscsims_tool_class.wiscsims_tool import WiscSIMSTool
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class PresetLineGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance()
        if cls.app is None:
            cls.app = QgsApplication([], True)
            cls.app.initQgis()

    def setUp(self):
        self.canvas = QgsMapCanvas()
        self.canvas.resize(600, 600)
        self.canvas.setExtent(QgsRectangle(0, 0, 1000, 1000))
        self.dock = WiscSIMSToolDockWidget()
        self.preset = PresetTool(self.dock, self.canvas)
        self.preset.show_tooltip = lambda _situation: None
        self.directory = tempfile.TemporaryDirectory()
        path = os.path.join(self.directory.name, "preset.shp")
        with patch.object(QFileDialog, "getSaveFileName", return_value=(path, "ESRI Shapefile (*.shp)")):
            self.preset.create_preset_layer()
        self.layer = self.preset.get_preset_layer()
        self.preset.active = True
        self.controller = SimpleNamespace(current_tool="preset", preset=self.preset)

    def tearDown(self):
        self.preset.preview.cleanup_old_layers()
        QgsProject.instance().removeMapLayer(self.layer.id())
        self.dock.deleteLater()
        self.canvas.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def click(self, pt, right=False):
        if right:
            WiscSIMSTool.canvasClickedRight(self.controller, pt)
        else:
            WiscSIMSTool.canvasClicked(self.controller, pt)

    def test_spot_size_converts_selected_symbol_to_map_units(self):
        symbol = self.layer.renderer().symbol()
        self.assertEqual(symbol.sizeUnit(), Qgis.RenderUnit.MapUnits)
        symbol.setOutputUnit(Qgis.RenderUnit.Millimeters)
        self.assertEqual(symbol.sizeUnit(), Qgis.RenderUnit.Millimeters)
        style_changes = QSignalSpy(self.layer.styleChanged)

        self.dock.Spn_Preset_Spot_Size.setValue(20)
        current_symbol = self.layer.renderer().symbol()
        self.assertEqual(current_symbol.sizeUnit(), Qgis.RenderUnit.MapUnits)
        self.assertEqual(current_symbol.outputUnit(), Qgis.RenderUnit.MapUnits)
        self.assertEqual(current_symbol.symbolLayer(0).sizeUnit(), Qgis.RenderUnit.MapUnits)
        self.assertAlmostEqual(current_symbol.size(), 20 / self.dock.Spn_Preset_Pixel_Size.value())
        self.assertGreater(len(style_changes), 0)

        # This is the unit dropdown used for the top-level Marker in Layer Properties.
        symbol_widget = QgsSymbolsListWidget(current_symbol, QgsStyle.defaultStyle(), None, None, self.layer)
        unit_widget = symbol_widget.findChild(QWidget, "mMarkerUnitWidget")
        unit_combo = unit_widget.findChild(QComboBox, "mUnitCombo")
        self.assertEqual(unit_combo.currentData(), Qgis.RenderUnit.MapUnits)

        self.dock.Spn_Preset_Pixel_Size.setValue(2)
        self.assertEqual(self.layer.renderer().symbol().sizeUnit(), Qgis.RenderUnit.MapUnits)
        self.assertAlmostEqual(self.layer.renderer().symbol().size(), 10)

        self.layer.renderer().symbol().setOutputUnit(Qgis.RenderUnit.Millimeters)
        self.preset.handle_change_preset_layer(self.dock.Cmb_Preset_Layer.currentIndex())
        self.assertEqual(self.layer.renderer().symbol().outputUnit(), Qgis.RenderUnit.MapUnits)

    def test_line_preview_add_and_undo(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(1)
        self.dock.Spn_Line_N_Spot.setValue(3)

        self.click(QgsPointXY(10, 20))
        self.assertTrue(self.preset.line_in_progress)
        self.assertFalse(self.dock.Btn_Line_Add_Points.isEnabled())

        self.preset.handle_mouse_moved(QgsPointXY(25, 20))
        self.assertEqual(self.preset.preview.preview_layer.featureCount(), 3)
        self.assertFalse(self.dock.Btn_Line_Add_Points.isEnabled())

        self.click(QgsPointXY(30, 20), right=True)
        self.assertFalse(self.preset.line_in_progress)
        self.assertTrue(self.dock.Btn_Line_Add_Points.isEnabled())
        self.assertEqual([(p[1], p[2]) for p in self.preset.preset_points], [(10, 20), (20, 20), (30, 20)])
        self.assertEqual(self.dock.Spn_Line_Step_Size.value(), 10)

        self.dock.Btn_Line_Add_Points.click()
        self.assertEqual(self.layer.featureCount(), 3)
        self.assertEqual(self.preset.preset_points, [])
        self.assertFalse(self.dock.Btn_Line_Add_Points.isEnabled())
        self.preset.handle_undo()
        self.assertEqual(self.layer.featureCount(), 0)

    def test_line_step_size_keeps_fixed_spacing_and_rejects_same_point(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(1)
        self.dock.Opt_Line_Step_Size.setChecked(True)
        self.dock.Spn_Line_Step_Size.setValue(10)

        self.click(QgsPointXY(0, 0))
        self.click(QgsPointXY(0, 0))
        self.assertTrue(self.preset.line_in_progress)
        self.assertFalse(self.dock.Btn_Line_Add_Points.isEnabled())
        self.assertEqual(self.preset.preview.preview_layer.featureCount(), 1)

        self.click(QgsPointXY(25, 0))
        self.assertEqual([p[1] for p in self.preset.preset_points], [0, 10, 20])
        self.assertEqual(self.dock.Spn_Line_N_Spot.value(), 3)
        self.assertTrue(self.dock.Btn_Line_Add_Points.isEnabled())

        self.click(QgsPointXY(0, 0))
        self.click(QgsPointXY(30, 0))
        self.assertEqual([p[1] for p in self.preset.preset_points], [0, 10, 20, 30])

        self.click(QgsPointXY(0, 0))
        self.click(QgsPointXY(5, 0))
        self.assertEqual([p[1] for p in self.preset.preset_points], [0])
        self.assertEqual(self.dock.Spn_Line_N_Spot.value(), 1)
        self.assertTrue(self.dock.Btn_Line_Add_Points.isEnabled())
        self.dock.Btn_Line_Add_Points.click()
        self.assertEqual(self.layer.featureCount(), 1)
        self.dock.Opt_Line_N_Spot.setChecked(True)
        self.assertEqual(self.dock.Spn_Line_N_Spot.minimum(), 2)
        self.assertEqual(self.dock.Spn_Line_N_Spot.value(), 2)

    def test_grid_order_spacing_and_repeated_placement(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(2)
        self.dock.Spn_Grid_N_Point_X.setValue(2)
        self.dock.Spn_Grid_N_Point_Y.setValue(3)
        self.dock.Spn_Grid_Step_Size_X.setValue(20)
        self.dock.Spn_Grid_Step_Size_Y.setValue(-10)
        self.dock.Cmb_Grid_Move_Order.setCurrentIndex(0)
        self.dock.Tbx_Comment.setText("spot-{:02}")
        self.dock.Cbx_Number_Increment.setChecked(True)

        self.click(QgsPointXY(100, 100))
        expected = [(100, 100), (120, 100), (100, 90), (120, 90), (100, 80), (120, 80)]
        self.assertEqual([(p[1], p[2]) for p in self.preset.preset_points], expected)
        self.assertEqual([p[0] for p in self.preset.preset_points], [f"spot-{i:02}" for i in range(1, 7)])
        self.assertTrue(self.dock.Btn_Grid_Add_Points.isEnabled())

        self.dock.Cmb_Grid_Move_Order.setCurrentIndex(1)
        self.assertEqual(
            [(p[1], p[2]) for p in self.preset.preset_points],
            [(100, 100), (100, 90), (100, 80), (120, 100), (120, 90), (120, 80)],
        )
        self.dock.Btn_Grid_Add_Points.click()
        self.assertEqual(self.layer.featureCount(), 6)
        self.assertEqual(self.dock.Spn_Current_Number.value(), 7)

        self.click(QgsPointXY(200, 200))
        self.assertEqual(self.preset.preset_points[0][0], "spot-07")

    def test_grid_refuses_excessive_point_count(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(2)
        self.dock.Spn_Grid_N_Point_X.setValue(999999)
        self.dock.Spn_Grid_N_Point_Y.setValue(9999)

        self.click(QgsPointXY(100, 100))
        self.assertEqual(self.preset.preset_points, [])
        self.assertFalse(self.dock.Btn_Grid_Add_Points.isEnabled())
        self.assertIn("Maximum", self.dock.Btn_Grid_Add_Points.toolTip())

        self.dock.Spn_Grid_N_Point_X.setValue(2)
        self.dock.Spn_Grid_N_Point_Y.setValue(2)
        self.dock.Spn_Grid_Step_Size_X.setValue(0)
        self.assertEqual(self.preset.preset_points, [])
        self.assertFalse(self.dock.Btn_Grid_Add_Points.isEnabled())

    def test_grid_updates_for_canvas_rotation_and_mode_change_clears_preview(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(2)
        self.dock.Spn_Grid_N_Point_X.setValue(2)
        self.dock.Spn_Grid_N_Point_Y.setValue(1)
        self.dock.Spn_Grid_Step_Size_X.setValue(10)
        self.click(QgsPointXY(0, 0))
        self.assertEqual([(p[1], p[2]) for p in self.preset.preset_points], [(0, 0), (10, 0)])

        self.canvas.setRotation(90)
        self.assertAlmostEqual(self.preset.preset_points[1][1], 0, places=6)
        self.assertAlmostEqual(self.preset.preset_points[1][2], 10, places=6)

        self.dock.Tab_Preset_Mode.setCurrentIndex(1)
        self.assertEqual(self.preset.preset_points, [])
        self.assertFalse(self.dock.Btn_Grid_Add_Points.isEnabled())
        self.assertEqual(self.preset.preview.preview_layer.featureCount(), 0)

    def test_map_tool_right_click_does_not_create_point_or_start_line(self):
        map_tool = CanvasMapTool(self.canvas)
        map_tool.canvasPressed.connect(self.preset.handle_mouse_pressed)
        map_tool.canvasReleased.connect(self.preset.handle_mouse_released)
        map_tool.canvasClicked.connect(lambda pt: WiscSIMSTool.canvasClicked(self.controller, pt))
        map_tool.canvasClickedRight.connect(lambda pt: WiscSIMSTool.canvasClickedRight(self.controller, pt))

        def click_at(position, button):
            press = QgsMapMouseEvent(self.canvas, QEvent.MouseButtonPress, position, button, button, Qt.NoModifier)
            release = QgsMapMouseEvent(self.canvas, QEvent.MouseButtonRelease, position, button, Qt.NoButton, Qt.NoModifier)
            map_tool.canvasPressEvent(press)
            map_tool.canvasReleaseEvent(release)

        click_at(QPoint(100, 100), Qt.RightButton)
        self.assertEqual(self.layer.featureCount(), 0)

        self.dock.Tab_Preset_Mode.setCurrentIndex(1)
        click_at(QPoint(100, 100), Qt.RightButton)
        self.assertFalse(self.preset.line_in_progress)
        click_at(QPoint(100, 100), Qt.LeftButton)
        self.assertTrue(self.preset.line_in_progress)
        click_at(QPoint(200, 100), Qt.RightButton)
        self.assertTrue(self.dock.Btn_Line_Add_Points.isEnabled())

    def test_drag_preserves_grab_offset_and_can_be_undone(self):
        self.preset.add_preset_point(QgsPointXY(10, 20))
        original = next(self.layer.getFeatures())
        self.preset.handle_shift_key_state_changed(True)
        self.preset.handle_mouse_pressed(QgsPointXY(11, 21))
        self.assertEqual(self.preset.feature_id, original.id())
        self.preset.handle_mouse_moved(QgsPointXY(31, 41))
        self.preset.handle_mouse_released(QgsPointXY(31, 41))
        event = SimpleNamespace(mapPoint=lambda: QgsPointXY(31, 41))
        WiscSIMSTool.canvasReleaseWShift(self.controller, event)
        moved = self.layer.getFeature(original.id()).geometry().asPoint()
        self.assertEqual((moved.x(), moved.y()), (30, 40))
        self.assertEqual(self.layer.featureCount(), 1)
        self.preset.handle_undo()
        restored = self.layer.getFeature(original.id()).geometry().asPoint()
        self.assertEqual((restored.x(), restored.y()), (10, 20))

    def test_size_settings_preserve_existing_edit_session_and_missing_fields(self):
        self.layer.startEditing()
        pixel_index = next(i for i, f in enumerate(self.layer.fields()) if f.name().startswith("ps_"))
        self.layer.deleteAttribute(pixel_index)
        self.assertTrue(write_sizes(self.layer, 12, 0.25))
        self.assertTrue(self.layer.isEditable())
        self.assertEqual(read_sizes(self.layer), {"ss": 12, "ps": 0.25})
        self.layer.rollBack()
        self.assertEqual(read_sizes(self.layer), {"ss": 10, "ps": 1.0})

    def test_malformed_size_fields_fall_back_to_defaults(self):
        self.layer.startEditing()
        for index, field in enumerate(self.layer.fields()):
            if field.name().startswith("ss_"):
                self.layer.renameAttribute(index, "ss_invalid")
            elif field.name().startswith("ps_"):
                self.layer.renameAttribute(index, "ps_nan")
        self.assertEqual(read_sizes(self.layer), {"ss": 10, "ps": 1.0})
        self.layer.rollBack()

    def test_undo_after_layer_switch_targets_original_layer(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(1)
        self.dock.Spn_Line_N_Spot.setValue(2)
        self.click(QgsPointXY(10, 10))
        self.click(QgsPointXY(20, 10))
        self.dock.Btn_Line_Add_Points.click()
        self.assertEqual(self.layer.featureCount(), 2)

        second_path = os.path.join(self.directory.name, "second.shp")
        with patch.object(QFileDialog, "getSaveFileName", return_value=(second_path, "ESRI Shapefile (*.shp)")):
            self.preset.create_preset_layer()
        second_layer = self.preset.get_preset_layer()
        try:
            self.preset.handle_undo()
            self.assertEqual(self.layer.featureCount(), 0)
            self.assertEqual(second_layer.featureCount(), 0)
        finally:
            QgsProject.instance().removeMapLayer(second_layer.id())


if __name__ == "__main__":
    unittest.main()
