# -*- coding: utf-8 -*-
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class TableViewModel(QStandardItemModel):
    """docstring for TableViewModel"""

    updateFlag = False

    def __init__(self):
        super(TableViewModel, self).__init__()
        self.c = {
            "used": 0,
            "refname": 1,
            "point_1": 2,  # [[stage_x, stage_y], [canvas_x, canvas_y]]
            "point_2": 3,  # [[stage_x, stage_y], [canvas_x, canvas_y]]
            "scale": 4,
            "offset": 5,  # [x, y]
            "rotation": 6,
        }
        self.n = len(self.c)
        _ = [self.insertColumn(i) for i in range(self.n)]
        self.setHorizontalHeaderLabels(["", "Name"])
        print("Initialized Table View Model")

    """""" """""" """""" """""" """""" """""" """
    * Methods
    """ """""" """""" """""" """""" """""" """"""

    def isAvailable(self):
        n = self.rowCount()
        if n == 0:
            return False
        return sum([self.getCheckStatus(r) for r in range(n)])

    def addRefPoints(self, used, refname, pt1, pt2, scale, offset, rotation):
        newRow = [QStandardItem() for _ in range(self.n)]

        # scale, offset, rotation = [1, [0, 0], 0]

        newRow[self.c["used"]].setCheckable(True)
        newRow[self.c["used"]].setCheckState(used)
        newRow[self.c["refname"]].setText(refname)
        newRow[self.c["point_1"]].setData(pt1, 0)
        newRow[self.c["point_2"]].setData(pt2, 0)
        newRow[self.c["scale"]].setData(scale, 0)
        newRow[self.c["offset"]].setData(offset, 0)
        newRow[self.c["rotation"]].setData(rotation, 0)

        self.appendRow(newRow)

        return self.rowCount() - 1

    def getColumnIndex(self, colName):
        return self.c[colName]

    def getColulmnNames(self):
        return self.c.keys()

    def updateRefPoint(self, refname, pt1, pt2, scale, offset, rotation, row):
        try:
            self.item(row, self.c["used"]).setCheckState(2)
            self.item(row, self.c["refname"]).setText(refname)
            self.item(row, self.c["point_1"]).setData(pt1, 0)
            self.item(row, self.c["point_2"]).setData(pt2, 0)
            self.item(row, self.c["scale"]).setData(scale, 0)
            self.item(row, self.c["offset"]).setData(offset, 0)
            self.item(row, self.c["rotation"]).setData(rotation, 0)
            return True
        except:
            return False

    def ExportAsObject(self):
        rowN = self.rowCount()
        alns = []
        for r in range(0, rowN):
            aln = {}
            aln["used"] = self.getCheckStatus(r)
            aln["refname"] = self.getRefName(r)
            aln["point_1"] = self.getRefPoint(r, 1)
            aln["point_2"] = self.getRefPoint(r, 2)
            aln["scale"], aln["offset"], aln["rotation"] = self.getAlignmentParams(r)
            alns.append(aln)
        return alns

    def ImportFromsJson(self, json):
        try:
            for o in json:
                self.addRefPoints(
                    o["used"], o["refname"], o["point_1"], o["point_2"], o["scale"], o["offset"], o["rotation"]
                )
        except:
            print("Error on importing JSON")

    """""" """""" """""" """""" """""" """""" """
    * GETTERS
    """ """""" """""" """""" """""" """""" """"""

    def getCheckStatus(self, row):
        return self.item(row, self.c["used"]).checkState()

    def getRefName(self, row):
        return self.item(row, self.c["refname"]).data(0)

    def getRefNames(self):
        return [self.getRefName(r) for r in range(self.rowCount())]

    def getScale(self, row):
        return self.item(row, self.c["scale"]).data(0)

    def getScales(self):
        return [self.getScale(r) for r in range(self.rowCount()) if self.getCheckStatus(r)]

    def getRotation(self, row):
        return self.item(row, self.c["rotation"]).data(0)

    def getRotations(self):
        return [self.getRotation(r) for r in range(self.rowCount()) if self.getCheckStatus(r)]

    def getRefPoint(self, row, pointNum):
        stage, canvas = self.item(row, self.c["point_{}".format(pointNum)]).data(0)
        return [stage, canvas]

    def getAlignmentParams(self, row):
        scale = self.item(row, self.c["scale"]).data(0)
        offset = self.item(row, self.c["offset"]).data(0)
        rotation = self.item(row, self.c["rotation"]).data(0)
        return (scale, offset, rotation)

    """""" """""" """""" """""" """""" """""" """
    * SETTERS
    """ """""" """""" """""" """""" """""" """"""

    def setCheckState(self, row, state):
        self.item(row, self.c["used"]).setCheckState(state)
