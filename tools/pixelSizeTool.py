from PyQt5.QtCore import (
    QRect,
    pyqtSignal,
    QObject,
)
from PyQt5.QtGui import (
    QColor,
    QCursor,
)
from PyQt5.QtWidgets import (
    QToolTip,
)

from qgis.core import (
    QgsPointXY,
    QgsWkbTypes,
)

from qgis.gui import (
    QgsRubberBand,
)


class PixelSizeTool(QObject):
    setPixelSize = pyqtSignal(float)

    def __init__(self, dock, canvas):
        QObject.__init__(self)

        self._dock = dock
        self._canvas = canvas
        self._dock.SPN_PST_ScaleBar_Len_um.valueChanged.connect(self.update_px_size)
        self._dock.SPN_PST_ScaleBar_Len_Px.valueChanged.connect(self.update_px_size)
        self._dock.Btn_PST_Set.clicked.connect(self.set_pixel_size)

        self.scale_coordinates = [
            self._dock.TXT_PST_Start_X,
            self._dock.TXT_PST_Start_Y,
            self._dock.TXT_PST_End_X,
            self._dock.TXT_PST_End_Y,
        ]

        # get default text color by hex
        self.original_text_color = self._dock.Grp_Step1.palette().text().color().name(0)
        # self.emphasize_color = 'F7A400'  # orange
        self.emphasize_color = "C43C39"  # red

        self.btn_original_color = self._dock.palette().text().color().name(0)
        self.btn_emphasize_color = self.emphasize_color

        if self._dock.palette().window().color().name(0) == "#323232":
            self.btn_emphasize_color = "ffffff"

        self.pxsize_line = QgsRubberBand(self._canvas, QgsWkbTypes.LineGeometry)
        self.pxsize_start_point = QgsPointXY()
        self.pxsize_end_point = QgsPointXY()

        self.reset_emphasize_step()

        self.reset()
        self.init_scale_coordinates()

    def reset(self):
        if self.pxsize_line.size() > 0:
            self.pxsize_line.reset()
        self.pxsize_line = QgsRubberBand(self._canvas, QgsWkbTypes.LineGeometry)
        self.pxsize_line.setWidth(4)
        self.pxsize_line.setColor(QColor(127, 255, 0, 60))

        self.pxsize_start_point = QgsPointXY()
        self.pxsize_end_point = QgsPointXY()

        self._dock.TXT_PST_Start_X.setText("0")
        self._dock.TXT_PST_Start_Y.setText("0")
        self._dock.TXT_PST_End_X.setText("0")
        self._dock.TXT_PST_End_Y.setText("0")

        self._dock.SPN_PST_PixelSize.setValue(0)

        self.show_tooltip()

    def init_scale_coordinates(self):
        [x.setText("0") for x in self.scale_coordinates]
        self.emphasize_step(1)

    def handle_cursor_moved(self, pt):
        if not self.pxsize_start_point.isEmpty() and self.pxsize_end_point.isEmpty():
            self.pxsize_line.removeLastPoint()  # remove temp end-point (cursor)
            self.pxsize_line.addPoint(pt, True)  # add new temp end-point

        self.show_tooltip()

    def handle_selecting_point(self, pt):
        # handling selecting start/end points on the map
        if not self.pxsize_end_point.isEmpty():
            # Activate input
            self.reset()

        if self.pxsize_start_point.isEmpty():
            # start point selected
            self.pxsize_start_point = pt

            # start showing rubberband
            # add start point
            self.pxsize_line.addPoint(self.pxsize_start_point, False)
            # add end point (dummy)
            self.pxsize_line.addPoint(self.pxsize_start_point, True)

            # update labels for start point (X, Y)
            self._dock.TXT_PST_Start_X.setText(str(round(pt.x(), 4)))
            self._dock.TXT_PST_Start_Y.setText(str(round(pt.y(), 4)))
            self.show_tooltip()
        else:
            # end point selected
            self.pxsize_end_point = pt

            # update labels for end point (X, Y)
            self._dock.TXT_PST_End_X.setText(str(round(pt.x(), 4)))
            self._dock.TXT_PST_End_Y.setText(str(round(pt.y(), 4)))

            self.set_scale_start_end(self.pxsize_start_point, self.pxsize_end_point)
            self.hide_tooltip()

    def set_scale_start_end(self, s, e):
        d = s.distance(e)
        self._dock.SPN_PST_ScaleBar_Len_Px.setValue(d)

        self.reset_emphasize_step()
        self.emphasize_step(2)

    def update_px_size(self, val):
        d = self._dock.SPN_PST_ScaleBar_Len_Px.value()
        scale_length = self._dock.SPN_PST_ScaleBar_Len_um.value()

        if d <= 0:
            return

        px_size = round(scale_length / d, 3)

        self._dock.SPN_PST_PixelSize.setValue(px_size)

        # after the Step 2
        if d > 0 and scale_length != 1:
            self.reset_emphasize_step()
            self._dock.Btn_PST_Set.setStyleSheet(f"color: #{self.btn_emphasize_color}")

        else:
            self._dock.Btn_PST_Set.setStyleSheet(f"color: #{self.btn_original_color}")

        self._dock.Btn_PST_Set.setDefault((d > 0))

    def set_pixel_size(self):
        self.setPixelSize.emit(self._dock.SPN_PST_PixelSize.value())

    def emphasize_step(self, step):
        if step == 1:
            # set emphasized color for the Step 1
            self._dock.Grp_Step1.setStyleSheet(
                f"QGroupBox::title {{ color: #{self.emphasize_color} }};"
            )
            self._dock.Grp_Step2.setStyleSheet(
                f"QGroupBox::title {{ color: #{self.original_text_color} }};"
            )
        elif step == 2:
            # set emphasized color for the Step 2
            self._dock.Grp_Step1.setStyleSheet(
                f"QGroupBox::title {{color: #{self.original_text_color}}};"
            )
            self._dock.Grp_Step2.setStyleSheet(
                f"QGroupBox::title {{ color: #{self.emphasize_color} }};"
            )
            # set focus to the scale length input
            self._dock.SPN_PST_ScaleBar_Len_um.setFocus()
            self._dock.SPN_PST_ScaleBar_Len_um.selectAll()
        else:
            self.reset_emphasize_step()

    def reset_emphasize_step(self):
        self._dock.Grp_Step1.setStyleSheet(
            f"QGroupBox::title {{color: #{self.original_text_color}}};"
        )
        self._dock.Grp_Step2.setStyleSheet(
            f"QGroupBox::title {{ color: #{self.original_text_color} }};"
        )

    def show_tooltip(self):
        self.hide_tooltip()

        pos = QCursor.pos()

        if self.pxsize_start_point.isEmpty():
            txt = "🌱 Click Start point of known scale"
        elif self.pxsize_end_point.isEmpty():
            txt = "🌱 Click End point of known scale"
        else:
            txt = ""
        QToolTip.showText(
            pos, txt, self._canvas, QRect(pos.x(), pos.y(), 200, 200), 30000
        )
        # QToolTip.showText(pos, txt, self.window)
        #

    def hide_tooltip(self):
        QToolTip.hideText()
