"""Capture the five-step first-spot guide in a disposable QGIS profile.

Run with QGIS --code. Set WISCSIMS_RECORD_ROOT, WISCSIMS_RECORD_SESSION
and WISCSIMS_FFMPEG as described in the recording README.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

from osgeo import gdal
from qgis.core import QgsCoordinateReferenceSystem, QgsPointXY, QgsProject, QgsRectangle
from qgis.PyQt.QtCore import QPoint, QRect, Qt, QTimer
from qgis.PyQt.QtGui import QColor, QImage, QPainter, QPen
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication, QDockWidget, QFileDialog, QToolBar
from qgis.utils import iface

ROOT = pathlib.Path(os.environ["WISCSIMS_RECORD_ROOT"]).resolve()
SESSION = pathlib.Path(os.environ["WISCSIMS_RECORD_SESSION"]).resolve()
if not SESSION.is_relative_to(pathlib.Path(tempfile.gettempdir()).resolve()) or not SESSION.parent.name.startswith("wiscsims-quick-start-"):
    raise ValueError("Use a dedicated temporary session and QGIS profile.")
ASSETS = ROOT / "img/readme"
FFMPEG = os.environ["WISCSIMS_FFMPEG"]
sys.path.insert(0, str(ROOT.parent))
QApplication.setAttribute(Qt.AA_DontUseNativeDialogs, True)


def settle():
    QApplication.processEvents()
    iface.mapCanvas().refresh()
    iface.mapCanvas().waitWhileRendering()
    QApplication.processEvents()


def record():
    try:
        print("QUICK_START_STEPS_RECORDING", flush=True)
        SESSION.mkdir(parents=True, exist_ok=True)
        window = iface.mainWindow()
        window.resize(1460, 960)
        for toolbar in window.findChildren(QToolBar):
            toolbar.setVisible(toolbar.objectName() in ("mFileToolBar", "mMapNavToolBar"))
        for dock in window.findChildren(QDockWidget):
            if "Browser" in dock.windowTitle():
                dock.hide()
        image = SESSION / "sample-reflected-light.tif"
        dataset = gdal.Translate(str(image), str(ASSETS / "pixel-size-source.png"), format="GTiff")
        dataset.SetGeoTransform((0, 1, 0, 0, 0, -1))
        dataset.SetProjection(QgsCoordinateReferenceSystem("EPSG:3857").toWkt())
        dataset = None
        iface.actionNewProject().trigger()
        raster = iface.addRasterLayer(str(image), "Sample image")
        canvas = iface.mapCanvas()
        canvas.setExtent(raster.extent())
        window.show()
        QTest.qWait(300)
        settle()
        iface.messageBar().clearWidgets()
        settle()
        top = canvas.mapTo(window, QPoint(0, 0)).y()
        window.grab(QRect(0, top, window.width(), canvas.height())).save(str(ASSETS / "quick-start-01-image.png"))

        from wiscsims_tool_class.wiscsims_tool import WiscSIMSTool
        plugin = WiscSIMSTool(iface)
        plugin.initGui()
        plugin.wiscsims_tool_action.trigger()
        dock = plugin.dockwidget
        dock.setFixedWidth(420)
        plugin.preset.show_tooltip = lambda *_args: None
        settle()
        tabs = dock.Tab_Tool.tabBar()
        tab_bottom = tabs.mapTo(dock, QPoint(0, 0)).y() + tabs.height() + 8
        dock.grab(QRect(0, 0, dock.width(), tab_bottom)).save(str(ASSETS / "quick-start-02-preset.png"))
        dock.Btn_Create_Preset_Layer.parentWidget().grab().save(str(ASSETS / "quick-start-03-layer.png"))
        # The image illustrates the New layer control. Keep file selection out
        # of this short recording, while using the real layer creation path.
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(SESSION / "spots.shp"), "")):
            QTest.mouseClick(dock.Btn_Create_Preset_Layer, Qt.LeftButton)
        layer = plugin.preset.get_preset_layer()
        assert layer is not None and layer.isValid()
        dock.Spn_Preset_Pixel_Size.setValue(0.87)
        dock.Spn_Preset_Spot_Size.setValue(12)
        dock.Tbx_Comment.setText("spot-1")
        dock.Cbx_Number_Increment.setChecked(False)
        dock.Opt_Comment_Preview.setChecked(False)
        dock.Tab_Preset_Mode.setCurrentIndex(0)
        settle()
        dock.Spn_Preset_Spot_Size.parentWidget().grab().save(str(ASSETS / "quick-start-04-size.png"))

        canvas.setExtent(QgsRectangle(650, -620, 1290, -70))
        settle()
        position = canvas.getCoordinateTransform().transform(QgsPointXY(870, -315))
        position = QPoint(round(position.x()), round(position.y()))
        center = canvas.viewport().mapTo(window, position)
        crop = QRect(center.x() - 110, center.y() - 90, 270, 190)
        # QPixmap dimensions include display scaling; rawvideo needs physical
        # pixels rather than the logical QRect dimensions.
        captured_size = window.grab(crop).size()
        video = ASSETS / "quick-start-first-point.mp4"
        encoder = subprocess.Popen([
            FFMPEG, "-hide_banner", "-loglevel", "error", "-xerror", "-y", "-f", "rawvideo",
            "-pix_fmt", "rgba", "-s", f"{captured_size.width()}x{captured_size.height()}", "-r", "20", "-i", "-",
            "-an", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(video),
        ], stdin=subprocess.PIPE)

        def frame(point, ring=True):
            QTest.mouseMove(canvas.viewport(), point)
            settle()
            pixmap = window.grab(crop)
            if ring:
                painter = QPainter(pixmap)
                painter.setPen(QPen(QColor("#216ee3"), 2))
                painter.setBrush(QColor(33, 110, 227, 30))
                local = canvas.viewport().mapTo(window, point) - crop.topLeft()
                painter.drawEllipse(local, 8, 8)
                painter.end()
            rgba = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
            assert rgba.size() == captured_size
            data = rgba.bits()
            data.setsize(rgba.sizeInBytes())
            encoder.stdin.write(bytes(data))
            QTest.qWait(50)

        for index in range(20):
            frame(position + QPoint(round(-40 * (1 - index / 19)), round(-25 * (1 - index / 19))))
        for _ in range(8):
            frame(position)
        QTest.mouseClick(canvas.viewport(), Qt.LeftButton, Qt.NoModifier, position)
        settle()
        assert layer.featureCount() == 1
        assert next(layer.getFeatures())["Comment"] == "spot-1"
        for index in range(15):
            frame(position + QPoint(round(190 * index / 14), round(120 * index / 14)))
        for _ in range(30):
            frame(position + QPoint(190, 120), ring=False)
        encoder.stdin.close()
        assert encoder.wait(timeout=30) == 0
        (ROOT / "docs/media/quick-start-steps.json").write_text(json.dumps({
            "source_video": "../../img/readme/quick-start-first-point.mp4",
            "fps": 20, "frames": 73, "duration_seconds": 3.65,
            "video_width": captured_size.width() + captured_size.width() % 2,
            "video_height": captured_size.height() + captured_size.height() % 2,
            "analysis_spot_um": 10, "selection_diameter_um": 12,
            "example_pixel_size": 0.87, "saved_point_count": layer.featureCount(),
            "saved_comment": next(layer.getFeatures())["Comment"],
            "note": "The blue circle is a recording overlay showing the pointer position.",
        }, indent=2) + "\n")
        print("QUICK_START_STEPS_OK", flush=True)
        os._exit(0)
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        os._exit(1)


QTimer.singleShot(1800, record)
