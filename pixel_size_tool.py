from PyQt5 import (
    QtWidgets,
    uic,
)

from PyQt5.QtCore import Qt, pyqtSignal


import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "pixel_size_tool.ui"))


class PixelSizeTool(QtWidgets.QDialog, FORM_CLASS):
    setPxSize = pyqtSignal("float")
    canceled = pyqtSignal()

    # closingPlugin = pyqtSignal()

    def __init__(self, parent=None, params=None):
        """Constructor."""
        super(PixelSizeTool, self).__init__(parent)
        self.setupUi(self)

        self.setModal(0)  # set Tool Window to modeless window

        self.Btn_Cancel.clicked.connect(self.reject)
        self.Btn_Set.clicked.connect(self.accept)
        self.SPN_ScaleBar_Len_um.valueChanged.connect(self.update_px_size)
        self.SPN_ScaleBar_Len_Px.valueChanged.connect(self.update_px_size)

        self.scale_coordinates = [
            self.TXT_Start_X,
            self.TXT_Start_Y,
            self.TXT_End_X,
            self.TXT_End_Y,
        ]

        # get default text color by hex
        self.original_text_color = self.Grp_Step1.palette().text().color().name(0)
        # self.emphasize_color = 'F7A400'  # orange
        self.emphasize_color = "C43C39"  # red

        self.btn_original_color = self.palette().text().color().name(0)
        self.btn_emphasize_color = self.emphasize_color

        print(self.palette().window().color().name(0) == "#323232")
        if self.palette().window().color().name(0) == "#323232":
            self.btn_emphasize_color = "ffffff"

        self.return_to_normal_step()

        self.init_scale_coordinates()

    def init_scale_coordinates(self):
        [x.setText("0") for x in self.scale_coordinates]
        self.emphasize_step(1)

    def set_scale_start_end(self, s, e):
        self.TXT_Start_X.setText(str(round(s.x(), 4)))
        self.TXT_Start_Y.setText(str(round(s.y(), 4)))
        self.TXT_End_X.setText(str(round(e.x(), 4)))
        self.TXT_End_Y.setText(str(round(e.y(), 4)))

        # self.show()
        # self.setWindowState(Qt.WindowState.WindowActive)
        # self.activateWindow()

        d = s.distance(e)
        self.SPN_ScaleBar_Len_Px.setValue(d)

        self.return_to_normal_step()
        self.emphasize_step(2)

    def update_px_size(self, val):
        d = self.SPN_ScaleBar_Len_Px.value()
        scale_length = self.SPN_ScaleBar_Len_um.value()

        if d <= 0:
            return

        px_size = round(scale_length / d, 3)

        self.SPN_PixelSize.setValue(px_size)

        # after the Step 2
        if d > 0 and scale_length != 1:
            self.return_to_normal_step()
            self.Btn_Set.setStyleSheet(f"color: #{self.btn_emphasize_color}")

        else:
            self.Btn_Set.setStyleSheet(f"color: #{self.btn_original_color}")

        self.Btn_Set.setDefault((d > 0))

    def emphasize_step(self, step):
        if step == 1:
            # set emphasized color for the Step 1
            self.Grp_Step1.setStyleSheet(f"QGroupBox::title {{ color: #{self.emphasize_color} }};")
            self.Grp_Step2.setStyleSheet(f"QGroupBox::title {{ color: #{self.original_text_color} }};")
        elif step == 2:
            # set emphasized color for the Step 2
            self.Grp_Step1.setStyleSheet(f"QGroupBox::title {{color: #{self.original_text_color}}};")
            self.Grp_Step2.setStyleSheet(f"QGroupBox::title {{ color: #{self.emphasize_color} }};")
            # set focus to the scale length input
            self.SPN_ScaleBar_Len_um.setFocus()
            self.SPN_ScaleBar_Len_um.selectAll()
        else:
            self.return_to_normal_step()

    def return_to_normal_step(self):
        self.Grp_Step1.setStyleSheet(f"QGroupBox::title {{color: #{self.original_text_color}}};")
        self.Grp_Step2.setStyleSheet(f"QGroupBox::title {{ color: #{self.original_text_color} }};")
