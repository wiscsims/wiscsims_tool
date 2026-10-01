"""Regression for creating a preset layer while the layer tree emits signals."""

import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qgis.core import Qgis, QgsApplication, QgsPointXY, QgsProject, QgsRectangle, QgsTextAnnotation, QgsVectorFileWriter, QgsVectorLayer
    from qgis.gui import QgsMapCanvas, QgsMapCanvasAnnotationItem, QgsMapMouseEvent
    from qgis.PyQt import sip
    from qgis.PyQt.QtCore import QEvent, QPoint, QSettings, Qt
    from qgis.PyQt.QtWidgets import QDockWidget, QDoubleSpinBox, QFileDialog, QMainWindow, QToolBar

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.ui.wiscsims_tool_dockwidget import WiscSIMSToolDockWidget
    from wiscsims_tool_class.tools.canvasMapTool import CanvasMapTool
    from wiscsims_tool_class.tools.preset.presetTool import PresetTool
    from wiscsims_tool_class.tools.pixelsize.pixelSizeTool import PixelSizeTool
    from wiscsims_tool_class.wiscsims_tool import WiscSIMSTool
    from wiscsims_tool_class.tools.signal_connections import SignalConnections
    from wiscsims_tool_class.tools.imports.alignmentMarker import AlignmentMarker
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class QgisLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance()
        if cls.app is None:
            cls.app = QgsApplication([], True)
            cls.app.initQgis()

    def test_creating_layer_with_synchronous_legend_callbacks(self):
        canvas = QgsMapCanvas()
        dock = WiscSIMSToolDockWidget()
        preset = PresetTool(dock, canvas)
        root = QgsProject.instance().layerTreeRoot()

        def refresh(*_args):
            preset.init_preset_layer_combobox()

        root.addedChildren.connect(refresh)
        root.removedChildren.connect(refresh)
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "preset.shp")
                with patch.object(
                    QFileDialog,
                    "getSaveFileName",
                    return_value=(path, "ESRI Shapefile (*.shp)"),
                ):
                    preset.create_preset_layer()

                self.assertEqual(dock.Cmb_Preset_Layer.count(), 1)
                self.assertFalse(dock.Cmb_Preset_Layer.signalsBlocked())
                self.assertIsNotNone(
                    QgsProject.instance().mapLayer(preset.preview.preview_layer_id)
                )

                layer = dock.Cmb_Preset_Layer.currentData()
                QgsProject.instance().removeMapLayer(layer.id())
                self.assertEqual(dock.Cmb_Preset_Layer.count(), 0)
                preset.preview.cleanup_old_layers()
        finally:
            root.addedChildren.disconnect(refresh)
            root.removedChildren.disconnect(refresh)
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_removing_layer_refreshes_preset_combo(self):
        class Controller:
            handle_legend_layers_changed = WiscSIMSTool.handle_legend_layers_changed
            create_legend_connections = WiscSIMSTool.create_legend_connections
            remove_legend_connections = WiscSIMSTool.remove_legend_connections

            def __init__(self, preset):
                self.imp = Mock()
                self.preset = preset
                self._legend_connections = SignalConnections()

        canvas = QgsMapCanvas()
        dock = WiscSIMSToolDockWidget()
        preset = PresetTool(dock, canvas)
        controller = Controller(preset)
        controller.create_legend_connections()
        controller.create_legend_connections()
        try:
            with tempfile.TemporaryDirectory() as directory:
                layer_ids = []
                for name in ("first", "second"):
                    path = os.path.join(directory, f"{name}.shp")
                    with patch.object(
                        QFileDialog,
                        "getSaveFileName",
                        return_value=(path, "ESRI Shapefile (*.shp)"),
                    ):
                        preset.create_preset_layer()
                    layer_ids.append(preset.get_preset_layer().id())

                self.assertEqual(dock.Cmb_Preset_Layer.count(), 2)
                QgsProject.instance().removeMapLayer(layer_ids[1])

                self.assertEqual(dock.Cmb_Preset_Layer.count(), 1)
                self.assertEqual(preset.get_preset_layer().id(), layer_ids[0])
                QgsProject.instance().removeMapLayer(layer_ids[0])

                self.assertEqual(dock.Cmb_Preset_Layer.count(), 0)
                self.assertIsNone(preset.preset_layer)
                self.assertIsNone(preset.preview.preset_layer)
        finally:
            controller.remove_legend_connections()
            preset.preview.cleanup_old_layers()
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_existing_layer_spot_size_uses_selected_layer_and_map_units(self):
        canvas = QgsMapCanvas()
        dock = WiscSIMSToolDockWidget()
        preset = None
        layer = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "existing.shp")
                source = QgsVectorLayer("Point?field=Comment:string", "source", "memory")
                error, _ = QgsVectorFileWriter.writeAsVectorFormat(
                    source, path, "UTF-8", source.crs(), "ESRI Shapefile"
                )
                self.assertEqual(error, QgsVectorFileWriter.NoError)
                layer = QgsVectorLayer(path, "existing", "ogr")
                layer.renderer().symbol().setOutputUnit(Qgis.RenderUnit.Millimeters)
                QgsProject.instance().addMapLayer(layer)

                preset = PresetTool(dock, canvas)
                self.assertEqual(preset.get_preset_layer().id(), layer.id())
                self.assertEqual(layer.renderer().symbol().outputUnit(), Qgis.RenderUnit.MapUnits)

                layer.renderer().symbol().setOutputUnit(Qgis.RenderUnit.Millimeters)
                preset.preset_layer = None
                dock.Spn_Preset_Spot_Size.setValue(20)
                self.assertEqual(layer.renderer().symbol().outputUnit(), Qgis.RenderUnit.MapUnits)
                self.assertAlmostEqual(layer.renderer().symbol().size(), 20 / preset.dock.Spn_Preset_Pixel_Size.value())
        finally:
            if preset is not None:
                preset.preview.cleanup_old_layers()
            if layer is not None and QgsProject.instance().mapLayer(layer.id()) is not None:
                QgsProject.instance().removeMapLayer(layer.id())
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_option_click_edits_existing_point_without_adding_one(self):
        canvas = QgsMapCanvas()
        canvas.resize(600, 600)
        canvas.setExtent(QgsRectangle(0, 0, 1000, 1000))
        dock = WiscSIMSToolDockWidget()
        preset = PresetTool(dock, canvas)
        map_tool = CanvasMapTool(canvas)
        map_tool.canvasPressed.connect(preset.handle_mouse_pressed)
        map_tool.canvasReleaseWAlt.connect(preset.edit_point)

        def click(pos, modifiers=Qt.NoModifier):
            press = QgsMapMouseEvent(
                canvas, QEvent.MouseButtonPress, pos, Qt.LeftButton, Qt.LeftButton, modifiers
            )
            release = QgsMapMouseEvent(
                canvas, QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.NoButton, modifiers
            )
            map_tool.canvasPressEvent(press)
            map_tool.canvasReleaseEvent(release)

        try:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "preset.shp")
                with patch.object(
                    QFileDialog,
                    "getSaveFileName",
                    return_value=(path, "ESRI Shapefile (*.shp)"),
                ):
                    preset.create_preset_layer()

                layer = preset.get_preset_layer()
                point = QPoint(100, 100)
                click(point)
                self.assertEqual(layer.featureCount(), 1)
                original_id = next(layer.getFeatures()).id()

                with patch(
                    "wiscsims_tool_class.tools.preset.presetTool.EditDialog"
                ) as edit_dialog:
                    edit_dialog.return_value.get_exit_state.return_value = 1
                    edit_dialog.return_value.return_new_comment.return_value = "edited"
                    click(point, Qt.AltModifier)
                    self.assertEqual(layer.featureCount(), 1)
                    self.assertEqual(next(layer.getFeatures()).id(), original_id)
                    self.assertEqual(next(layer.getFeatures())["Comment"], "edited")
                    edit_dialog.assert_called_once()

                    click(QPoint(500, 500), Qt.AltModifier)
                    self.assertEqual(layer.featureCount(), 1)
                    edit_dialog.assert_called_once()

                QgsProject.instance().removeMapLayer(layer.id())
                preset.preview.cleanup_old_layers()
        finally:
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_preset_cursor_follows_every_move_without_layer_repaint(self):
        canvas = QgsMapCanvas()
        canvas.resize(600, 600)
        canvas.setExtent(QgsRectangle(0, 0, 1000, 1000))
        dock = WiscSIMSToolDockWidget()
        preset = PresetTool(dock, canvas)
        marker = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "preset.shp")
                with patch.object(
                    QFileDialog,
                    "getSaveFileName",
                    return_value=(path, "ESRI Shapefile (*.shp)"),
                ):
                    preset.create_preset_layer()

                preset.active = True
                dock.Opt_Point_Preview.setChecked(True)
                preset.update_preview_cursor()
                marker = preset.preview.cursor_marker
                self.assertTrue(marker.isVisible())
                self.assertEqual(canvas.cursor().shape(), Qt.BlankCursor)

                preset.handle_shift_key_state_changed(True)
                self.assertFalse(marker.isVisible())
                self.assertEqual(canvas.cursor().shape(), Qt.OpenHandCursor)
                preset.handle_shift_key_state_changed(False)
                self.assertTrue(marker.isVisible())
                self.assertEqual(canvas.cursor().shape(), Qt.BlankCursor)

                dock.Opt_Point_Preview.setChecked(False)
                preset.handle_shift_key_state_changed(True)
                self.assertEqual(canvas.cursor().shape(), Qt.OpenHandCursor)
                preset.handle_shift_key_state_changed(False)
                self.assertEqual(canvas.cursor().shape(), Qt.CrossCursor)
                dock.Opt_Point_Preview.setChecked(True)
                self.assertEqual(canvas.cursor().shape(), Qt.BlankCursor)

                stationary_center = marker.center()
                canvas.setExtent(QgsRectangle(0, 0, 100, 100))
                self.assertGreater(
                    preset.preview.cursor_diameter,
                    preset.preview.MIN_CURSOR_DIAMETER_PX,
                )
                zoomed_in_width = marker.boundingRect().width()
                self.assertEqual(marker.center(), stationary_center)
                canvas.setExtent(QgsRectangle(0, 0, 1_000_000, 1_000_000))
                self.assertEqual(
                    preset.preview.cursor_diameter,
                    preset.preview.MIN_CURSOR_DIAMETER_PX,
                )
                self.assertGreaterEqual(
                    marker.boundingRect().width(),
                    preset.preview.MIN_CURSOR_DIAMETER_PX,
                )
                self.assertLess(marker.boundingRect().width(), zoomed_in_width)
                self.assertEqual(marker.center(), stationary_center)
                canvas.setExtent(QgsRectangle(0, 0, 1000, 1000))

                for x in range(25):
                    point = QgsPointXY(x, x + 1)
                    preset.handle_mouse_moved(point)
                    self.assertEqual(marker.center(), point)

                self.assertEqual(preset.preview.preview_layer.featureCount(), 0)
                preset.add_preset_point(point)
                preset.relocating_spot = True
                preset.initiate_relocation(point)
                moved_point = QgsPointXY(30, 31)
                preset.handle_mouse_moved(moved_point)
                self.assertEqual(marker.center(), moved_point)
                self.assertEqual(preset.preview.preview_layer.featureCount(), 0)

                layer = preset.get_preset_layer()
                QgsProject.instance().removeMapLayer(layer.id())
                preset.preview.cleanup_old_layers()
                self.assertTrue(sip.isdeleted(marker))
                canvas.setExtent(QgsRectangle(0, 0, 2000, 2000))
        finally:
            if preset.preview.preview_layer_id is not None:
                preset.preview.cleanup_old_layers()
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_preset_text_preview_updates_without_redrawing_layer(self):
        canvas = QgsMapCanvas()
        canvas.resize(600, 600)
        canvas.setExtent(QgsRectangle(0, 0, 1000, 1000))
        canvas.show()
        dock = WiscSIMSToolDockWidget()
        preset = PresetTool(dock, canvas)
        layer_id = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "preset.shp")
                with patch.object(
                    QFileDialog,
                    "getSaveFileName",
                    return_value=(path, "ESRI Shapefile (*.shp)"),
                ):
                    preset.create_preset_layer()

                layer_id = preset.get_preset_layer().id()
                preset.active = True
                preset.update_preview_cursor()
                dock.Tbx_Comment.setText("Spot A")
                dock.Opt_Comment_Preview.setChecked(True)
                marker = preset.preview.cursor_marker
                label = preset.preview.cursor_label
                self.assertTrue(label.isVisible())
                self.assertEqual(label.text(), "Spot A")
                self.assertTrue(preset.preview.preview_layer.labelsEnabled())

                def text_is_drawn():
                    self.app.processEvents()
                    image = canvas.grab().toImage()
                    rect = label.sceneBoundingRect().toAlignedRect().intersected(image.rect())
                    return any(
                        image.pixelColor(x, y).red() > image.pixelColor(x, y).green() + 50
                        for x in range(rect.left(), rect.right() + 1)
                        for y in range(rect.top(), rect.bottom() + 1)
                    )

                before = label.scenePos()
                preset.handle_mouse_moved(QgsPointXY(500, 500))
                self.assertNotEqual(label.scenePos(), before)
                self.assertEqual(preset.preview.preview_layer.featureCount(), 0)
                self.assertTrue(text_is_drawn())

                dock.Tbx_Comment.setText("Spot {}")
                dock.Spn_Current_Number.setValue(3)
                dock.Cbx_Number_Increment.setChecked(True)
                self.assertEqual(label.text(), "Spot 3")

                dock.Opt_Point_Preview.setChecked(False)
                self.assertTrue(label.isVisible())
                self.assertFalse(preset.preview.cursor_icon_visible)
                self.assertEqual(canvas.cursor().shape(), Qt.CrossCursor)
                self.assertTrue(text_is_drawn())

                dock.Opt_Comment_Preview.setChecked(False)
                self.assertFalse(marker.isVisible())
                dock.Opt_Comment_Preview.setChecked(True)
                self.assertTrue(text_is_drawn())

                dock.Tab_Preset_Mode.setCurrentIndex(1)
                self.assertTrue(preset.preview.preview_layer.labelsEnabled())
                dock.Opt_Comment_Preview.setChecked(False)
                self.assertFalse(preset.preview.preview_layer.labelsEnabled())

                preset.preview.cleanup_old_layers()
                self.assertTrue(sip.isdeleted(label))
        finally:
            if layer_id is not None and QgsProject.instance().mapLayer(layer_id) is not None:
                QgsProject.instance().removeMapLayer(layer_id)
            if preset.preview.preview_layer_id is not None:
                preset.preview.cleanup_old_layers()
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_pixel_size_clicks_accept_fractional_map_distance(self):
        canvas = QgsMapCanvas()
        dock = WiscSIMSToolDockWidget()
        tool = PixelSizeTool(dock, canvas)
        try:
            original_band = tool.pxsize_line
            for _ in range(5):
                tool.reset()
            self.assertIs(tool.pxsize_line, original_band)
            tool.handle_selecting_point(QgsPointXY(1, 2))
            tool.handle_cursor_moved(QgsPointXY(2, 3))
            tool.handle_selecting_point(QgsPointXY(2.5, 2))
            self.assertIsInstance(dock.SPN_PST_ScaleBar_Len_Px, QDoubleSpinBox)
            self.assertAlmostEqual(dock.SPN_PST_ScaleBar_Len_Px.value(), 1.5, places=4)
            expected = [(1, 2), (2.5, 2)]
            self.assertEqual(
                [(p.x(), p.y()) for p in tool.pxsize_line.asGeometry().asPolyline()],
                expected,
            )
            tool.handle_cursor_moved(QgsPointXY(8, 9))
            self.assertEqual(
                [(p.x(), p.y()) for p in tool.pxsize_line.asGeometry().asPolyline()],
                expected,
            )
            # A new measurement also finalizes correctly without a mouse move.
            tool.handle_selecting_point(QgsPointXY(3, 4))
            tool.handle_selecting_point(QgsPointXY(6, 4))
            self.assertEqual(
                [(p.x(), p.y()) for p in tool.pxsize_line.asGeometry().asPolyline()],
                [(3, 4), (6, 4)],
            )
        finally:
            dock.deleteLater()
            canvas.deleteLater()
            self.app.processEvents()

    def test_alignment_refresh_preserves_other_annotations_and_releases_own_items(self):
        canvas = QgsMapCanvas()
        annotation = QgsTextAnnotation()
        other_item = QgsMapCanvasAnnotationItem(annotation, canvas)
        markers = AlignmentMarker(canvas, None)
        try:
            markers.add_ref_marker(QgsPointXY(10, 20), "Reference")
            markers.add_ref_marker_annotation(QgsPointXY(10, 20), "Reference", False)
            own_marker = markers.ref_markers[0]
            own_label = markers.ref_annotations[0]
            markers.init_ref_point_markers()
            markers.init_ref_point_markers()
            self.assertTrue(sip.isdeleted(own_marker))
            self.assertTrue(sip.isdeleted(own_label))
            self.assertFalse(sip.isdeleted(other_item))
            self.assertIn(other_item, canvas.scene().items())
        finally:
            canvas.deleteLater()
            self.app.processEvents()

    def test_unload_deletes_dock_before_reloading(self):
        class Interface:
            def __init__(self):
                self.window = QMainWindow()
                self.canvas = QgsMapCanvas()

            def mainWindow(self):
                return self.window

            def mapCanvas(self):
                return self.canvas

            def addToolBar(self, name):
                return self.window.addToolBar(name)

            def addPluginToMenu(self, name, action):
                pass

            def removePluginMenu(self, name, action):
                pass

            def addDockWidget(self, area, dock):
                self.window.addDockWidget(area, dock)

            def removeDockWidget(self, dock):
                self.window.removeDockWidget(dock)

            def setActiveLayer(self, layer):
                pass

        settings = QSettings()
        previous_locale = settings.value("locale/userLocale")
        settings.setValue("locale/userLocale", "en_US")
        iface = Interface()
        try:
            first = WiscSIMSTool(iface)
            first.initGui()
            first.wiscsims_tool_action.setChecked(True)
            rotation_receivers = iface.canvas.receivers(iface.canvas.rotationChanged)
            first.run()
            old_dock = first.dockwidget
            preset_band = first.preset.rb_line
            pixel_band = first.pxsizetool.pxsize_line
            old_preset = first.preset
            old_pixel_tool = first.pxsizetool
            first.unload()
            first.unload()
            self.assertTrue(sip.isdeleted(old_dock))
            self.assertTrue(sip.isdeleted(preset_band))
            self.assertTrue(sip.isdeleted(pixel_band))
            self.assertTrue(sip.isdeleted(old_preset))
            self.assertTrue(sip.isdeleted(old_pixel_tool))
            self.assertEqual(iface.canvas.receivers(iface.canvas.rotationChanged), rotation_receivers)
            self.assertEqual(len(iface.window.findChildren(QDockWidget)), 0)
            self.assertEqual(len(iface.window.findChildren(QToolBar)), 0)

            second = WiscSIMSTool(iface)
            second.initGui()
            second.wiscsims_tool_action.setChecked(True)
            second.run()
            self.assertEqual(len(iface.window.findChildren(QDockWidget)), 1)
            second.dockwidget.close()
            second.wiscsims_tool_action.setChecked(True)
            second.run()
            self.assertEqual(len(iface.window.findChildren(QDockWidget)), 1)
            second.unload()
            second.unload()
            self.assertEqual(len(iface.window.findChildren(QDockWidget)), 0)
            self.assertEqual(len(iface.window.findChildren(QToolBar)), 0)
        finally:
            if previous_locale is None:
                settings.remove("locale/userLocale")
            else:
                settings.setValue("locale/userLocale", previous_locale)
            iface.window.deleteLater()
            iface.canvas.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
