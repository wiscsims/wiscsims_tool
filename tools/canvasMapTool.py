# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal, QPoint, Qt
from PyQt5.QtGui import QColor
from qgis.core import QgsPoint, QgsRectangle, Qgis
from qgis.gui import QgsRubberBand, QgsMapTool
import math


class CanvasMapTool(QgsMapTool):

    canvasClicked = pyqtSignal('QgsPointXY')
    canvasDoubleClicked = pyqtSignal('QgsPointXY')
    canvasClickedRight = pyqtSignal('QgsPointXY')
    canvasMoved = pyqtSignal('QgsPointXY')

    def __init__(self, canvas, toolbarBtn):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

        self.plColor = [QColor(255, 20, 20, 250),
                        QColor(20, 20, 255, 250),
                        QColor(20, 255, 20, 250)]
        self.refPoints = {
            "main": {
                "xy": {"ref1": [], "ref2": []},
                "obj": {"ref1": None, "ref2": None},
            },
            "sub": {
                "xy": {"ref1": [], "ref2": []},
                "obj": {"ref1": None, "ref2": None},
            }
        }

        self.fov = None
        self.fovColor = QColor(255, 255, 255, 255)

        self.currentPoint = None

        self.lip = None
        self.sweetspot = None
        self.spot = None
        self.spotColor = QColor(0, 255, 255, 200)
        self.refpoint2 = [None, None]

    def canvasPressEvent(self, event):
        return

    def canvasMoveEvent(self, event):
        pt = self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
        self.canvasMoved.emit(pt)
        # self.emit(SIGNAL('mouseMoved'), pt)
        return

    def canvasReleaseEvent(self, event):
        pt = self.getMapCoordinates(event)
        if event.button() == Qt.RightButton:
            self.canvasClickedRight.emit(pt)
        else:
            self.canvasClicked.emit(pt)

    def canvasDoubleClickEvent(self, event):
        pt = self.getMapCoordinates(event)
        self.canvasDoubleClicked.emit(pt)

    def getMapCoordinates(self, event):
        return self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))

    def addReferencePoint(self, pt, isMain=True, ref1=True):
        aln = "main" if isMain else "sub"
        ref = "ref1" if ref1 else "ref2"
        if self.refPoints[aln]["xy"][ref] != []:
            self.refPoints[aln]["obj"][ref].reset()
        self.refPoints[aln]["xy"][ref] = pt
        self.showReferencePoint(isMain)

    def resetReferencePoint2(self):
        [ref2.reset() for ref2 in self.refpoint2 if ref2 is not None]

    def addReferencePoint2(self, pts):
        self.resetReferencePoint2()
        i = 0
        for p in pts:
            tl = QgsRubberBand(self.canvas, Qgis.Point)
            tl.setIconSize(15)
            tl.setIcon(QgsRubberBand.ICON_CROSS)
            tl.setColor(QColor(255, 0, 255, 255))
            tl.addPoint(QgsPoint(*p), True)
            self.refpoint2[i] = tl
            i += 1

    def hideAllReferencePoint(self):
        self.resetReferencePoint2()
        for aln in [True, False]:
            self.hideReferencePoint(aln)

    def hideReferencePoint(self, isMain=True):
        aln = "main" if isMain else "sub"
        for i in ["ref1", "ref2"]:
            if self.refPoints[aln]["obj"][i] is not None:
                self.refPoints[aln]["obj"][i].reset()

    def showReferencePoint(self, isMain=True):
        pointSize = 15
        col = {
            "ref1": QColor(0, 255, 255, 200),  # cyan
            "ref2": QColor(0, 255, 150, 200),  # green
        }
        aln = "main" if isMain else "sub"
        pts = ["ref1", "ref2"]
        self.hideReferencePoint(isMain)
        for i in pts:
            if self.refPoints[aln]["xy"][i] == []:
                continue
            tl = QgsRubberBand(self.canvas, Qgis.Point)
            tl.setIconSize(pointSize)
            if isMain:
                tl.setIcon(QgsRubberBand.ICON_CROSS)
            else:
                tl.setIcon(QgsRubberBand.ICON_X)
            tl.setColor(col[i])
            tl.addPoint(QgsPoint(self.refPoints[aln]["xy"][i][0],
                                 self.refPoints[aln]["xy"][i][1]), True)
            self.refPoints[aln]['obj'][i] = tl

    def displayReferencePoint(self, onoff):
        pass

    def rotateCoordinates(self, pt, th, offset=[0, 0]):
        r = math.radians(-th)
        cos = math.cos(r)
        sin = math.sin(r)
        return [pt[0] * cos - pt[1] * sin + offset[0],
                pt[0] * sin + pt[1] * cos + offset[1]]

    def setFOVColor(self, colorName):
        self.fovColor = QColor(colorName)

    def setSpotColor(self, colorName):
        self.spotColor = QColor(colorName)

    def getFOVColor(self):
        return self.fovColor

    def calcFOV(self, center, scale=1, rotation=0, offset=[696, 520]):

        fovPx = [1392, 1040]  # pixel size of BadgerScope's field of view

        # size of field of view
        baseSize = 494   # micron
        hFactor = 0.803212851  # height 396.8
        width = baseSize / scale
        height = baseSize * hFactor / scale

        xOffset = width * (offset[0] - (fovPx[0] / 2)) / fovPx[0]
        yOffset = height * ((fovPx[1] - offset[1]) - (fovPx[1] / 2)) / fovPx[1]

        pt1 = [-width / 2.0 - xOffset, height / 2.0 - yOffset]
        pt2 = [pt1[0] + width, pt1[1]]
        pt3 = [pt2[0], pt2[1] - height]
        pt4 = [pt1[0], pt3[1]]
        pt1 = self.rotateCoordinates(pt1, -rotation, center)
        pt2 = self.rotateCoordinates(pt2, -rotation, center)
        pt3 = self.rotateCoordinates(pt3, -rotation, center)
        pt4 = self.rotateCoordinates(pt4, -rotation, center)

        return (pt1, pt2, pt3, pt4)  # (TL, TR, BR, BL)

    def drawFieldOfView(self, center, scale=1, rotation=0, offset=[696, 520]):

        pt1, pt2, pt3, pt4 = self.calcFOV(center, scale, rotation, offset)

        self.removeFieldOfView()

        self.fov = QgsRubberBand(self.canvas, Qgis.Polygon)
        self.fov.addPoint(QgsPoint(pt1[0], pt1[1]))
        self.fov.addPoint(QgsPoint(pt2[0], pt2[1]))
        self.fov.addPoint(QgsPoint(pt3[0], pt3[1]))
        self.fov.addPoint(QgsPoint(pt4[0], pt4[1]))
        self.fov.addPoint(QgsPoint(pt1[0], pt1[1]))
        self.fov.setBorderColor(self.getFOVColor())
        self.fov.setFillColor(QColor(255, 255, 250, 0))
        self.fov.setWidth(2)
        self.fov.updatePosition()

    def removeFieldOfView(self):
        if self.fov:
            self.fov.reset()

    def zoomToFOV(self, center, scale, rotation, offset):
        pt1, pt2, pt3, pt4 = self.calcFOV(center, scale, rotation, offset)
        margin = 0.02 * (pt2[0] - pt4[0])
        xmin = pt4[0] - margin
        ymin = pt4[1] - margin
        xmax = pt2[0] + margin
        ymax = pt2[1] + margin
        self.canvas.setExtent(QgsRectangle(xmin, ymin, xmax, ymax))
        self.canvas.refresh()

    def drawSpot(self, center, diameter, aspect, rotation, linewidth=1):
        self.hideSpot()
        a = diameter / 2
        b = a * aspect
        self.spot = QgsRubberBand(self.canvas, Qgis.Polygon)
        for t in range(361):
            x = a * math.cos(math.radians(t))
            y = b * math.sin(math.radians(t))
            tmp = self.rotateCoordinates([x, y], -rotation)
            self.spot.addPoint(QgsPoint(tmp[0] + center[0],
                                        tmp[1] + center[1]))
        self.spot.setBorderColor(self.spotColor)
        self.spot.setFillColor(QColor(255, 0, 0, 0))
        self.spot.setWidth(linewidth)

    def hideSpot(self):
        if self.spot:
            self.spot.reset()

    def drawCircle(self, center, radius, color=QColor(255, 255, 0, 255),
                   linewidth=1):
        rb = QgsRubberBand(self.canvas, Qgis.Polygon)
        for t in range(0, 362, 2):
            x = radius * math.cos(math.radians(t)) + center[0]
            y = radius * math.sin(math.radians(t)) + center[1]
            rb.addPoint(QgsPoint(x, y))
        rb.setBorderColor(color)
        rb.setFillColor(QColor(255, 0, 0, 5))
        rb.setWidth(linewidth)
        rb.show()
        return rb

    def removeRB(self, rb):
        if rb:
            rb.reset()
            rb = None

    def showLip(self, center, radius, color=QColor(255, 255, 0, 255),
                linewidth=1):
        self.lip = self.drawCircle(center, radius, color, linewidth)
        return self.lip

    def hideLip(self):
        self.removeRB(self.lip)

    def showSweetSpot(self, center, radius, color=QColor(255, 0, 255, 255),
                      linewidth=2):
        self.sweetspot = self.drawCircle(center, radius, color, linewidth)
        return self.sweetspot

    def hideSweetSpot(self):
        self.removeRB(self.sweetspot)

    def drawLip(self, center, radius, color=QColor(255, 255, 0, 255),
                linewidth=1):
        return self.drawCircle(self.lip, center, radius, color, linewidth)

    def drawCurrentPoint(self, pt):
        self.removeCurrentPoint()

        self.currentPoint = QgsRubberBand(self.canvas, Qgis.Point)
        self.currentPoint.setIconSize(2)
        self.currentPoint.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.currentPoint.setColor(QColor(255, 0, 0, 200))
        self.currentPoint.addPoint(QgsPoint(pt[0], pt[1]), True)
        self.canvas.refresh()

    def removeCurrentPoint(self):
        if self.currentPoint is not None:
            self.currentPoint.reset()
