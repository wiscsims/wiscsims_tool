# -*- coding: utf-8 -*-
from PyQt5.QtCore import QPointF, QSizeF
from PyQt5.QtGui import QColor, QTextDocument
from qgis.core import (QgsFillSymbol, QgsMargins, QgsMarkerSymbol,
                       QgsTextAnnotation)
from qgis.gui import QgsMapCanvasAnnotationItem, QgsRubberBand

"""""" """""" """""" """""" """""" """""" """
*** Alignment Marker Class
""" """""" """""" """""" """""" """""" """"""


class AlignmentMarker:
    """docstring for AlignmentMarker"""

    def __init__(self, canvas, model):
        self.canvas = canvas
        self.scene = self.canvas.scene()
        self.model = model
        self.ref_markers = []
        self.cursor_ann = None

    def add_ref_marker(self, pt, name, current=False):
        rb = QgsRubberBand(self.canvas, False)
        rb.setIconSize(15)
        rb.setIcon(QgsRubberBand.ICON_CROSS)
        color = QColor(255, 40, 0) if current else QColor(0, 40, 255)
        rb.setColor(color)
        rb.addPoint(pt, True)
        self.ref_markers.append(rb)

    def add_ref_marker_annotation(self, pt, name, current):
        symbol = QgsMarkerSymbol()
        symbol.setSize(0)
        frm = QgsFillSymbol()
        html = '<body style="color: #ffffff; background-color: {};"><b>{}</b></body>'
        if current:
            frm.setColor(QColor(255, 0, 0))
            bg_color = "#FF0000"
        else:
            frm.setColor(QColor(0, 0, 0))
            bg_color = "#000000"
        a = QgsTextAnnotation()
        c = QTextDocument()
        c.setHtml(html.format(bg_color, name))
        a.setDocument(c)
        a.setFrameSize(QSizeF(c.size().width(), c.size().height()))
        a.setMarkerSymbol(symbol)
        a.setFrameOffsetFromReferencePoint(QPointF(20, -70))
        a.setMapPosition(pt)
        a.setFillSymbol(frm)
        a.setContentsMargin(QgsMargins(0, 0, 0, 0))
        QgsMapCanvasAnnotationItem(a, self.canvas)

    def init_cursor_annotation(self, name=None):
        symbol = QgsMarkerSymbol()
        symbol.setSize(0)
        frm = QgsFillSymbol()
        # frm.createSimple({'color': 'black'})
        frm.setColor(QColor("#f00"))
        # frm.setOpacity(0.5)
        html = '<body><div style="backround-color: #f00;' ' color: #fff; font-weight: bold">{}</div></body>'
        a = QgsTextAnnotation()
        c = QTextDocument()
        c.setHtml(html.format(name))
        a.setDocument(c)
        a.setFrameSize(QSizeF(c.size().width(), c.size().height()))
        a.setMarkerSymbol(symbol)
        a.setFrameOffsetFromReferencePoint(QPointF(20, -70))
        a.setFillSymbol(frm)
        a.setContentsMargin(QgsMargins(0, 0, 0, 0))
        self.cursor_ann = a
        QgsMapCanvasAnnotationItem(self.cursor_ann, self.canvas)

    def init_ref_point_markers(self):
        # print('init markers')
        [marker.reset() for marker in self.ref_markers]
        self.ref_markers = []
        self.init_annotation()
        return True

    def init_annotation(self):
        [self.remove_scene_item(i) for i in self.scene.items() if self.is_annotation_item(i)]

    def is_annotation_item(self, item):
        return issubclass(type(item), QgsMapCanvasAnnotationItem)

    def remove_scene_item(self, item):
        self.scene.removeItem(item)
