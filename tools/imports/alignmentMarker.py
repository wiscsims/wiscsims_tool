# -*- coding: utf-8 -*-
"""Own the reference markers and labels drawn by the Import tool."""

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QPointF, QSizeF
from qgis.PyQt.QtGui import QColor, QTextDocument
from qgis.core import QgsFillSymbol, QgsMargins, QgsMarkerSymbol, QgsTextAnnotation, Qgis
from qgis.gui import QgsMapCanvasAnnotationItem, QgsRubberBand

class AlignmentMarker:
    """Track canvas items so refreshing references removes only our own items."""

    def __init__(self, canvas, model):
        self.canvas = canvas
        self.scene = self.canvas.scene()
        self.model = model
        self.ref_markers = []
        self.ref_annotations = []

    def add_ref_marker(self, pt, name, current=False):
        rb = QgsRubberBand(self.canvas, Qgis.GeometryType.Point)
        rb.setIconSize(15)
        rb.setIcon(QgsRubberBand.ICON_CROSS)
        color = QColor(255, 40, 0) if current else QColor(0, 40, 255)
        rb.setColor(color)
        rb.addPoint(pt, True)
        self.ref_markers.append(rb)

    def add_ref_marker_annotation(self, pt, name, current):
        shrink = 0.7
        symbol = QgsMarkerSymbol()
        symbol.setSize(0)
        frm = QgsFillSymbol()
        if current:
            bg_color = "#AAAAAA"
            fg_color = "#000000"
        else:
            bg_color = "#000000"
            fg_color = "#ffffff"
        frm.setColor(QColor(bg_color))  # <- color of triangler part of annotation
        html = f'<body style="color: {fg_color}; background: {bg_color}"><b>{name.strip()}</b></body>'

        c = QTextDocument()
        c.setHtml(html)
        s = QSizeF(c.size().width() * shrink, c.size().height() * shrink)
        a = QgsTextAnnotation()

        a.setDocument(c)
        a.setFrameSize(s)
        a.setMarkerSymbol(symbol)
        a.setFrameOffsetFromReferencePoint(QPointF(20, -70))
        a.setMapPosition(pt)
        a.setFillSymbol(frm)
        a.setContentsMargin(QgsMargins(0, 0, 0, 0))
        self.ref_annotations.append(QgsMapCanvasAnnotationItem(a, self.canvas))

    def init_ref_point_markers(self):
        for marker in self.ref_markers:
            self.remove_scene_item(marker)
        self.ref_markers = []

        self.init_annotation()
        return True

    def init_annotation(self):
        for item in self.ref_annotations:
            self.remove_scene_item(item)
        self.ref_annotations = []

    def remove_scene_item(self, item):
        if not sip.isdeleted(item):
            self.scene.removeItem(item)
            sip.delete(item)
