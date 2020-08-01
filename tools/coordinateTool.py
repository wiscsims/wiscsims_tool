# -*- coding: utf-8 -*-
import math


class CoordinateTool():
    """docstring for CoordinateTool"""

    def __init__(self):
        # super(CoordinateTool, self).__init__()
        self.initParams()

    def initParams(self):
        self.aligned = False

        self.ref1c = []  # reference point #1 on canvas [x1, y1]
        self.ref2c = []  # reference point #2 on canvas [x2, y2]
        self.ref1s = []  # reference point #1 on stage  [x1, y1]
        self.ref2s = []  # reference point #2 on stage  [x2, y2]

        self.scale = 1
        self.rotation = 0

    def setReferencePoints(self,
                           ref1canvas, ref1stage,
                           ref2canvas, ref2stage):
        # ref1c: reference point #1 on canvas [x1, y1]
        # ref1s: reference point #1 on stage  [x1, y1]
        # ref2c: reference point #2 on canvas [x2, y2]
        # ref2s: reference point #2 on stage  [x2, y2]
        self.ref1c = ref1canvas
        self.ref2c = ref2canvas
        self.ref1s = ref1stage
        self.ref2s = ref2stage

        seg1 = [self.ref2c, self.ref1c]  # canvas
        seg2 = [self.ref2s, self.ref1s]  # stage

        self.scale = self.getScale(seg1, seg2)
        self.rotation = self.getRotation(seg1, seg2)
        self.aligned = True

    def getOffset(self, pt1, pt2, scale=1):
        # pt1 = [x1, y1]
        # pt2 = [x2, y2]
        return [pt1[0] - pt2[0] * scale, pt1[1] - pt2[1] * scale]

    def getLength(self, seg1):
        # seg1 = [[x2, y2], [x1, y1]]
        return self.getDistance(seg1[0], seg1[1])

    def getDistance(self, pt1, pt2):
        # pt1 = [x1, y1]
        # pt2 = [x2, y2]
        a = math.pow(pt2[0] - pt1[0], 2)
        b = math.pow(pt2[1] - pt1[1], 2)
        return math.sqrt(a + b)

    def getScale(self, seg1, seg2):
        # seg1 = [[x2, y2], [x1, y1]]
        # seg2 = [[x2, y2], [x1, y1]]
        # return scale of seg2 relative to seg1
        dSeg2 = self.getDistance(seg2[0], seg2[1])
        dSeg1 = self.getDistance(seg1[0], seg1[1])
        return dSeg2 / dSeg1

    def getAngle(self, seg1):
        # seg1 = [[x2, y2], [x1, y1]]
        # angle from horizontal line with CW (clockwise)
        # return angle in degrees
        pt1 = seg1[0]
        pt2 = seg1[1]
        diff = self.getOffset(pt1, pt2)
        # if diff[0] < 0:
        #     diff = [d * -1 for d in diff]
        angle = math.degrees(math.atan2(diff[1], diff[0]))
        return float(angle)

    def getRotation(self, seg1, seg2):
        # seg1 = [[x2, y2], [x1, y1]] : [x1, y1] is rotation center
        # seg2 = [[x2, y2], [x1, y1]] : [x1, y1] is rotation center
        # rotation in degrees (CW: clockwise)
        angle = self.getAngle(seg1) - self.getAngle(seg2)

        # -180 < angle < 180
        if angle < -180:
            angle += 360
        elif angle > 180:
            angle -= 360

        return angle
        # return angle if angle > -180 and angle < 180 else angle - 180

    def rotateCoordinates(self, pt, degree, offset=[0, 0]):
        # degree (CW)
        r = math.radians(-degree)
        cos = math.cos(r)
        sin = math.sin(r)
        x = pt[0] * cos - pt[1] * sin + offset[0]
        y = pt[0] * sin + pt[1] * cos + offset[1]
        return [x, y]

    def getConvertParams(self, stage1, canvas1, stage2, canvas2):
        # convert from Canvas to Stage
        seg_s = [stage2, stage1]
        seg_c = [canvas2, canvas1]
        scale = self.getScale(seg_c, seg_s)
        rotation = self.getRotation(seg_c, seg_s)
        tmp = [(canvas2[0] - canvas1[0]) * scale, (canvas2[1] - canvas1[1]) * scale]
        tmp = self.rotateCoordinates(tmp, rotation)
        offset = [canvas1, stage1]
        return (scale, offset, rotation)

    def toStageCoordinates2(self, pt, params):
        # params: [scale, offset, rotation]
        scale, offset, rotation = params
        pt = [pt[0] - offset[0][0], pt[1] - offset[0][1]]
        return self.rotateCoordinates([p * scale for p in pt], rotation, offset[1])

    def toCanvasCoordinates2(self, pt, params):
        # params: [scale, offset, rotation]
        params = [1 / params[0], params[1][::-1], -1 * params[2]]
        return self.toStageCoordinates2(pt, params)

    def toStageCoordinates(self, pt):
        if (len(self.ref1c) < 2):
            tmp = pt
            offset = [0, 0]
        else:
            tmp = [(pt[0] - self.ref1c[0]) * self.scale,
                   (pt[1] - self.ref1c[1]) * self.scale]
            offset = self.ref1s
        return self.rotateCoordinates(tmp, self.rotation, offset)

    def toCanvasCoordinates(self, pt):
        tmp = [(pt[0] - self.ref1s[0]) / self.scale,
               (pt[1] - self.ref1s[1]) / self.scale]
        return self.rotateCoordinates(tmp, -1 * self.rotation, self.ref1c)
