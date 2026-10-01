# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QPoint, Qt, pyqtSignal
from qgis.gui import QgsMapTool


class CanvasMapTool(QgsMapTool):
    """Expose map gestures as signals, separating them from tool actions."""

    # Mouse Event
    canvasPressed = pyqtSignal("QgsPointXY")
    canvasReleased = pyqtSignal("QgsPointXY")

    canvasClicked = pyqtSignal("QgsPointXY")
    canvasReleaseWShift = pyqtSignal("QgsMapMouseEvent")
    canvasReleaseWAlt = pyqtSignal("QgsMapMouseEvent")
    canvasReleaseWAltShift = pyqtSignal("QgsMapMouseEvent")
    canvasClickedRight = pyqtSignal("QgsPointXY")
    canvasMoved = pyqtSignal("QgsPointXY")

    # Key Event
    canvasCtrlKeyState = pyqtSignal("bool")
    canvasShiftKeyState = pyqtSignal("bool")
    canvasAltKeyState = pyqtSignal("bool")
    canvasEscapeKeyState = pyqtSignal()
    canvasUndoKey = pyqtSignal()  # Ctrl/Cmd-Z

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.state_ctrl = False
        self.state_alt = False
        self.state_shift = False

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.canvasShiftKeyState.emit(True)
            self.state_shift = True
        elif e.key() == Qt.Key_Alt:
            self.canvasAltKeyState.emit(True)
            self.state_alt = True
        elif e.key() == Qt.Key_Control:
            self.canvasCtrlKeyState.emit(True)
            self.state_ctrl = True
        elif QApplication.keyboardModifiers() == Qt.ControlModifier and e.key() == Qt.Key_Z:
            # Undo
            self.canvasUndoKey.emit()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.canvasShiftKeyState.emit(False)
            self.state_shift = False
        elif e.key() == Qt.Key_Alt:
            self.canvasAltKeyState.emit(False)
            self.state_alt = False
        elif e.key() == Qt.Key_Control:
            self.canvasCtrlKeyState.emit(False)
            self.state_ctrl = False
        elif e.key() == Qt.Key_Escape:
            # Clear preview spots
            self.canvasEscapeKeyState.emit()

    def canvasPressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pt = self.getMapCoordinates(event)
        modifiers = event.modifiers()
        if modifiers & Qt.AltModifier:
            return
        self.canvasPressed.emit(pt)

    def canvasMoveEvent(self, event):
        pt = self.getMapCoordinates(event)
        self.canvasMoved.emit(pt)

    def canvasReleaseEvent(self, event):
        if event.button() not in (Qt.LeftButton, Qt.RightButton):
            return
        pt = self.getMapCoordinates(event)
        modifiers = event.modifiers()

        self.canvasReleased.emit(pt)

        if event.button() == Qt.RightButton:
            self.canvasClickedRight.emit(pt)
        else:
            if modifiers & Qt.ShiftModifier and modifiers & Qt.AltModifier:
                self.canvasReleaseWAltShift.emit(event)
            elif modifiers & Qt.ShiftModifier:
                self.canvasReleaseWShift.emit(event)
            elif modifiers & Qt.AltModifier:
                self.canvasReleaseWAlt.emit(event)
            else:
                self.canvasClicked.emit(pt)

    def getMapCoordinates(self, event):
        return self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
