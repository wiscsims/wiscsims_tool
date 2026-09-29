# -*- coding: utf-8 -*-
import math

from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import Qgis, QgsPoint, QgsRectangle
from qgis.gui import QgsMapTool, QgsRubberBand


class CanvasMapTool(QgsMapTool):
    # Mouse Event
    canvasPressed = pyqtSignal("QgsPointXY")
    canvasReleased = pyqtSignal("QgsPointXY")

    canvasClicked = pyqtSignal("QgsPointXY")
    canvasClickedWShift = pyqtSignal("QgsMapMouseEvent")
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

    state_ctrl = False
    state_alt = False
    state_shift = False

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

    def keyPressEvent(self, e):
        # if e.key() == 16777248:  # Shift
        if e.key() == Qt.Key_Shift:
            self.canvasShiftKeyState.emit(True)
            self.state_shift = True
        # elif e.key() == 16777251:  # Alt/Option
        elif e.key() == Qt.Key_Alt:
            self.canvasAltKeyState.emit(True)
            self.state_alt = True
        elif e.key() == Qt.Key_Control:
            # display spot preview
            self.canvasCtrlKeyState.emit(True)
            self.state_ctrl = True
        elif QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier and e.key() == Qt.Key_Z:
            # Undo
            self.canvasUndoKey.emit()
        return

    def keyReleaseEvent(self, e):
        # if e.key() == 16777248:  # Shift
        if e.key() == Qt.Key_Shift:
            self.canvasShiftKeyState.emit(False)
            self.state_shift = False
            # elif e.key() == 16777251:  # Alt/Option
        elif e.key() == Qt.Key_Alt:
            self.canvasAltKeyState.emit(False)
            self.state_alt = False
        elif e.key() == Qt.Key_Control:
            # display spot preview
            self.canvasCtrlKeyState.emit(False)
            self.state_ctrl = False
        elif e.key() == Qt.Key_Escape:
            # Clear preview spots
            self.canvasEscapeKeyState.emit()

    def canvasPressEvent(self, event):
        pt = self.getMapCoordinates(event)
        modifiers = event.modifiers()
        if modifiers & Qt.AltModifier:
            return
        self.canvasPressed.emit(pt)
        if modifiers & Qt.ShiftModifier:
            self.canvasClickedWShift.emit(event)
            return

    def canvasMoveEvent(self, event):
        pt = self.getMapCoordinates(event)
        self.canvasMoved.emit(pt)
        return

    def canvasReleaseEvent(self, event):
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
