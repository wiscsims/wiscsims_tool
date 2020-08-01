# -*- coding: utf-8 -*-
from PyQt5.QtCore import QPointF, QSizeF
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QTextDocument

from qgis.core import QgsMarkerSymbol, QgsTextAnnotation, QgsMargins, QgsFillSymbol
from qgis.gui import QgsRubberBand, QgsMapCanvasAnnotationItem

class AlignmentModel(QStandardItemModel):
    """docstring for AlignmentModel"""

    updateFlag = False

    def __init__(self):
        super(AlignmentModel, self).__init__()
        self.c = {
            'used': 0,
            'refname': 1,
            'point_1': 2,  # [[stage_x, stage_y], [canvas_x, canvas_y]]
            'point_2': 3,  # [[stage_x, stage_y], [canvas_x, canvas_y]]
            'scale': 4,    #
            'offset': 5,   # [x, y]
            'rotation': 6,
            'ref1': 7,
            'ref2': 8,
        }
        self.n = len(self.c)
        _ = [self.insertColumn(i) for i in range(self.n)]
        self.setHorizontalHeaderLabels(['', 'Name', '', '', '', '', '', 'Ref. 1', 'Ref. 2'])
        print('Initialized Table View Model')

    """""""""""""""""""""""""""""""""""""""
    * Methods
    """""""""""""""""""""""""""""""""""""""

    def isAvailable(self):
        n = self.rowCount()
        if n == 0:
            return False
        return sum([self.getCheckStatus(r) for r in range(n)])

    def addNewRefPoints(self, used, refname, pt1, pt2, scale, offset, rotation):
        return self.addRefPoints(used, refname, pt1, pt2, scale, offset, rotation, import_from_json=False)

    def addRefPoints(self, used, refname, pt1, pt2, scale, offset, rotation, import_from_json=True):
        newRow = [QStandardItem() for _ in range(self.n)]

        # scale, offset, rotation = [1, [0, 0], 0]

        newRow[self.c['used']].setCheckable(True)
        newRow[self.c['used']].setCheckState(used)
        newRow[self.c['refname']].setText(refname)
        newRow[self.c['point_1']].setData(pt1, 0)
        newRow[self.c['point_2']].setData(pt2, 0)
        newRow[self.c['scale']].setData(scale, 0)
        newRow[self.c['offset']].setData(offset, 0)
        newRow[self.c['rotation']].setData(rotation, 0)
        if import_from_json:
            newRow[self.c['ref1']].setText('EDIT')
            newRow[self.c['ref2']].setText('EDIT')
        else:
            newRow[self.c['ref1']].setText('')
            newRow[self.c['ref2']].setText('')
        newRow[self.c['ref1']].setEditable(False)
        newRow[self.c['ref2']].setEditable(False)

        self.appendRow(newRow)

        return self.rowCount() - 1

    def getColumnIndex(self, colName):
        return self.c[colName]

    def getColulmnNames(self):
        return self.c.keys()

    def getItem(self, row, col):
        return self.item(row, col)

    def setRefPoint(self, row, ref, pt):
        col = self.c['point_1'] if ref == 1 else self.c['point_2']
        print(ref, row, col, pt)
        self.item(row, col).setData(pt, 0)
        return True

    def setAlignment(self, refname, pt1, pt2, scale, offset, rotation, row):
        return self.updateRefPoint(refname, pt1, pt2, scale, offset, rotation, row)

    def updateRefPoint(self, refname, pt1, pt2, scale, offset, rotation, row):
        try:
            self.item(row, self.c['used']).setCheckState(2)
            self.item(row, self.c['refname']).setText(refname)
            self.item(row, self.c['point_1']).setData(pt1, 0)
            self.item(row, self.c['point_2']).setData(pt2, 0)
            self.item(row, self.c['scale']).setData(scale, 0)
            self.item(row, self.c['offset']).setData(offset, 0)
            self.item(row, self.c['rotation']).setData(rotation, 0)
            self.item(row, self.c['ref1']).setData('EDIT', 0)
            self.item(row, self.c['ref2']).setData('EDIT', 0)

            return True
        except Exception:
            return False

    def ExportAsObject(self):
        rowN = self.rowCount()
        alns = []
        for r in range(0, rowN):
            aln = {}
            aln['r'] = r
            aln['used'] = self.getCheckStatus(r)
            aln['refname'] = self.getRefName(r)
            aln['point_1'] = self.getRefPoint(r, 1)
            aln['point_2'] = self.getRefPoint(r, 2)
            aln['scale'], aln['offset'], aln['rotation'] = self.getAlignmentParams(r)
            alns.append(aln)
        return alns

    def ImportFromsJson(self, json):
        try:
            for o in json:
                self.addRefPoints(
                    o['used'],
                    o['refname'],
                    o['point_1'],
                    o['point_2'],
                    o['scale'],
                    o['offset'],
                    o['rotation'],
                )
            return True
        except Exception:
            print('Error on importing JSON')
            return False

    """""""""""""""""""""""""""""""""""""""
    * GETTERS
    """""""""""""""""""""""""""""""""""""""

    def getCheckStatus(self, row):
        return self.item(row, self.c['used']).checkState()

    def getRefName(self, row):
        return self.item(row, self.c['refname']).data(0)

    def getRefNames(self):
        # rowN = self.rowCount()
        # names = []
        # for r in xrange(0, rowN):
        #     names.append(self.getRefName(r))
        return [self.getRefName(r) for r in range(self.rowCount())]
        # return names

    def getScale(self, row):
        return self.item(row, self.c['scale']).data(0)

    def getScales(self):
        return [self.getScale(r) for r in range(self.rowCount()) if self.getCheckStatus(r)]

    def getRotation(self, row):
        return self.item(row, self.c['rotation']).data(0)

    def getRotations(self):
        return [self.getRotation(r) for r in range(self.rowCount()) if self.getCheckStatus(r)]

    def getRefPoint(self, row, pointNum):
        stage, canvas = self.item(row, self.c['point_{}'.format(pointNum)]).data(0)
        # i(stage, canvas)
        return [stage, canvas]
        # [stage, canvas] = self.item(row, self.c['point_{}'.format(pointNum)]).data(0)
        # return (stage[0], stage[1], canvas[0], canvas[1])

    def getAlignmentParams(self, row):
        scale = self.item(row, self.c['scale']).data(0)
        offset = self.item(row, self.c['offset']).data(0)
        rotation = self.item(row, self.c['rotation']).data(0)
        return (scale, offset, rotation)

    def getAverage(self, arr):
        return sum(arr) / len(arr) * 1.0

    def getAverageParams(self):
        return self.getParams()

    def getParams(self):
        if not self.isAvailable():
            return None
        scales = self.getScales()
        rotations = self.getRotations()
        return {
            'scale': self.getAverage(scales),
            'rotation': self.getAverage(rotations)
        }

    def getRefPointStatus(self, row):
        return {
            'ref1': self.item(row, self.getColumnIndex('ref1')).data(0) == 'EDIT',
            'ref2': self.item(row, self.getColumnIndex('ref2')).data(0) == 'EDIT'
        }

    def getIndexes(self, col):
        return [self.index(r, col) for r in range(self.rowCount())]

    """""""""""""""""""""""""""""""""""""""
    * SETTERS
    """""""""""""""""""""""""""""""""""""""

    def setCheckState(self, row, state):
        self.item(row, self.c['used']).setCheckState(state)


"""""""""""""""""""""""""""""""""""""""
*** Alignment Marker Class
"""""""""""""""""""""""""""""""""""""""
class AlignmentMarker():
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
        html = '<body><div style="backround-color: #f00; color: #fff; font-weight: bold">{}</div></body>'
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
