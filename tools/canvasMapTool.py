# -*- coding: utf-8 -*-
import math

from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import Qgis, QgsPoint, QgsRectangle
from qgis.gui import QgsMapTool, QgsRubberBand


class CanvasMapTool(QgsMapTool):
    # Mouse Event
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

    fov_size = [1392, 1040]  # pixel size of BadgerScope's field of view

    def __init__(self, canvas, toolbarBtn):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

        self.refPoints = {
            "main": {
                "xy": {"ref1": [], "ref2": []},
                "obj": {"ref1": None, "ref2": None},
            },
            "sub": {
                "xy": {"ref1": [], "ref2": []},
                "obj": {"ref1": None, "ref2": None},
            },
        }

        self.fov = None
        self.fovColor = QColor(255, 255, 255, 255)

        self.currentPoint = None

        self.lip = None
        self.sweetspot = None
        self.spot = None
        self.spotColor = QColor(0, 255, 255, 200)
        self.refpoint2 = [None, None]

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
        elif (
            QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier
            and e.key() == Qt.Key_Z
        ):
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
        if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self.canvasClickedWShift.emit(event)
            return

    def canvasMoveEvent(self, event):
        pt = self.getMapCoordinates(event)
        self.canvasMoved.emit(pt)
        return

    def canvasReleaseEvent(self, event):
        pt = self.getMapCoordinates(event)

        if event.button() == Qt.RightButton:
            self.canvasClickedRight.emit(pt)
        else:
            if QtWidgets.QApplication.keyboardModifiers() == (
                Qt.ShiftModifier | Qt.AltModifier
            ):
                self.canvasReleaseWAltShift.emit(event)
            elif QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.canvasReleaseWShift.emit(event)
            elif QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
                self.canvasReleaseWAlt.emit(event)
            else:
                self.canvasClicked.emit(pt)

    def getMapCoordinates(self, event):
        return self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
