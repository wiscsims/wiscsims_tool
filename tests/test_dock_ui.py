"""Layout checks also runnable with QT_SCALE_FACTOR=2 for high DPI displays."""

import os
import importlib
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QPoint, QPointF, Qt
    from qgis.PyQt.QtGui import QFont, QWheelEvent
    from qgis.PyQt.QtWidgets import QLabel

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.ui.wiscsims_tool_dockwidget import WiscSIMSToolDockWidget
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class DockUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance()
        if cls.app is None:
            cls.app = QgsApplication([], True)
            cls.app.initQgis()

    def setUp(self):
        self.dock = WiscSIMSToolDockWidget()
        self.dock.resize(420, 760)
        self.dock.show()
        self.app.processEvents()

    def tearDown(self):
        self.dock.close()
        self.dock.deleteLater()
        self.app.processEvents()

    def test_all_tabs_fit_at_native_and_large_font_sizes(self):
        base_font = QFont(self.dock.font())
        for multiplier in (1, 1.5, 2):
            font = QFont(base_font)
            font.setPointSizeF(base_font.pointSizeF() * multiplier)
            self.dock.setFont(font)
            # Exercise the narrowest supported width with limited vertical space.
            self.dock.resize(self.dock.minimumWidth(), 600)
            for tab, mode, scroll in (
                (0, 0, self.dock.tab_scroll),
                (1, 0, self.dock.tab_2_scroll),
                (1, 1, self.dock.tab_2_scroll),
                (1, 2, self.dock.tab_2_scroll),
                (2, 0, self.dock.tab_3_scroll),
            ):
                with self.subTest(font=multiplier, tab=tab, mode=mode):
                    self.dock.Tab_Tool.setCurrentIndex(tab)
                    self.dock.Tab_Preset_Mode.setCurrentIndex(mode)
                    for _ in range(3):
                        self.app.processEvents()
                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                    for label in scroll.findChildren(QLabel):
                        if label.isVisible() and label.wordWrap():
                            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                    self.app.processEvents()
                    self.assertLessEqual(scroll.widget().geometry().bottom(), scroll.viewport().height())

    def test_point_page_does_not_reserve_grid_height(self):
        self.dock.Tab_Preset_Mode.setCurrentIndex(2)
        self.app.processEvents()
        grid_height = self.dock.Tab_Preset_Mode.sizeHint().height()
        self.dock.Tab_Preset_Mode.setCurrentIndex(0)
        self.app.processEvents()
        self.assertLess(self.dock.Tab_Preset_Mode.sizeHint().height(), grid_height)

    def test_custom_widget_loads_under_a_different_plugin_package_name(self):
        source = pathlib.Path(__file__).resolve().parents[1] / "ui"
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "release_test_plugin" / "ui"
            target.mkdir(parents=True)
            (target.parent / "__init__.py").write_text("")
            (target / "__init__.py").write_text("")
            for name in ("wiscsims_tool_dockwidget.py", "wiscsims_tool_dockwidget_base.ui", "activePageTabWidget.py"):
                shutil.copy2(source / name, target / name)
            with patch.object(sys, "path", [directory, *sys.path]), patch.dict(sys.modules):
                module = importlib.import_module("release_test_plugin.ui.wiscsims_tool_dockwidget")
                dock = module.WiscSIMSToolDockWidget()
                self.assertEqual(type(dock.Tab_Preset_Mode).__module__, "release_test_plugin.ui.activePageTabWidget")
                dock.deleteLater()
                self.app.processEvents()

    def test_empty_layer_hint_tracks_blocked_combo_updates(self):
        combo = self.dock.Cmb_Preset_Layer
        self.assertFalse(self.dock.Hint_PresetLayer.isHidden())
        combo.blockSignals(True)
        combo.addItem("Existing layer")
        self.assertTrue(self.dock.Hint_PresetLayer.isHidden())
        combo.clear()
        combo.blockSignals(False)
        self.assertFalse(self.dock.Hint_PresetLayer.isHidden())

    def test_wheel_does_not_change_an_unfocused_size_field(self):
        spin = self.dock.Spn_Preset_Spot_Size
        self.dock.Tbx_Comment.setFocus()
        self.app.processEvents()
        old_value = spin.value()
        wheel = QWheelEvent(QPointF(5, 5), QPointF(spin.mapToGlobal(QPoint(5, 5))),
                            QPoint(), QPoint(0, 120), Qt.NoButton, Qt.NoModifier,
                            Qt.NoScrollPhase, False)
        self.app.sendEvent(spin, wheel)
        self.assertEqual(spin.value(), old_value)


if __name__ == "__main__":
    unittest.main()
