from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AlignmentInfo(QDialog):
    def __init__(self, parent, info, isNew=True):
        QDialog.__init__(self, parent)

        self.setWindowTitle("Aligment Information")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = ""
        if info is not None:
            if isNew:
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
            else:
                refname = info["name"]
                p1_sx = round(info["Point 1"]["stage"].x())
                p1_sy = round(info["Point 1"]["stage"].y())
                p2_sx = round(info["Point 2"]["stage"].x())
                p2_sy = round(info["Point 2"]["stage"].y())
                p1_cx = round(info["Point 1"]["canvas"].x(), 2)
                p1_cy = round(info["Point 1"]["canvas"].y(), 2)
                p2_cx = round(info["Point 2"]["canvas"].x(), 2)
                p2_cy = round(info["Point 2"]["canvas"].y(), 2)
                message = QLabel(
                    f'"{refname}"\n\n'
                    + "Point 1\n"
                    + f"   Stage: {p1_sx: 9}, {p1_sy: 9}\n"
                    + f"  Canvas: {p1_cx: 9}, {p1_cy: 9}\n\n"
                    + "Point 2\n"
                    + f"   Stage: {p2_sx: 9}, {p2_sy: 9}\n"
                    + f"  Canvas: {p2_cx: 9}, {p2_cy: 9}\n"
                )

            # message.setStyleSheet('font: 13pt "monospaced";')
            message.setFont(QFont("Courier", 13))

        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
