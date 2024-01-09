import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, pyqtSignal

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "edit_dialog.ui")
)


class EditDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, params=None):
        """Constructor."""
        super(EditDialog, self).__init__(parent)
        self.setupUi(self)

        print(params)
        # exit state 0: cancel, 1: OK, 2: delete
        self.exit_state = 0

        self.Txt_NewComment.setText(params["comment"])

        self.Btn_Cancel.clicked.connect(self.reject)
        self.Btn_OK.clicked.connect(self.accept)
        self.Btn_Delete.clicked.connect(self.delete_point)

    def return_new_comment(self):
        return self.Txt_NewComment.text()

    def get_exit_state(self):
        return self.exit_state

    def delete_point(self):
        self.exit_state = 2
        print("delete point")
        self.close()

    def accept(self):
        self.exit_state = 1
        self.close()
