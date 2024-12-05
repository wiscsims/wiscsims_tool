import os

from PyQt5 import QtGui, QtWidgets, uic
# from PyQt5.QtCore import pyqtSignal

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "import_layer_option.ui"))


class ImportLayerOption(QtWidgets.QDialog, FORM_CLASS):
    # closingPlugin = pyqtSignal()

    def __init__(self, parent=None, layers=None):
        """Constructor."""
        super(ImportLayerOption, self).__init__(parent)
        self.setupUi(self)

        # self.setModal(0)  # set Tool Window to modeless window
        self.Btn_Import_Layer_OK.clicked.connect(self.accept)
        self.Btn_Import_Layer_Cancel.clicked.connect(self.reject)

        self.Cmb_Layer_Option.clear()

        if layers is None:
            return
        [self.Cmb_Layer_Option.addItem(layer) for layer in layers]
