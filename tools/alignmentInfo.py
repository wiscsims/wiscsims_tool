from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AlignmentInfo(QDialog):
    def __init__(self, parent=None, info=None):
        QDialog.__init__(self)

        self.setWindowTitle("Aligment Information")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = ""
        if info is not None:
            beampos = info["beam"]["position"]
            beamsize = info["beam"]["size"]
            stage = info["stage"]
            canvas = info["canvas"]
            refname = info["name"]

            message = QLabel(
                f'"{refname}"\n\n'
                + f"        Stage: {round(stage.x()): 8}, {round(stage.y()): 8}\n"
                + f"       Canvas: {round(canvas.x(), 2): 8}, {round(canvas.y(), 2): 8}\n"
                + f"Beam Position: {beampos[0]:8}, {beampos[1]:8}\n"
                + f"    Beam Size: {beamsize: 5} µm"
            )
            # message.setStyleSheet('font: 13pt "monospaced";')
            message.setFont(QFont("Courier", 13))

        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
