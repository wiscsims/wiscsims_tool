# -*- coding: utf-8 -*-
import math


class CoordinateTool:
    """docstring for CoordinateTool"""

    def __init__(self):
        # super(CoordinateTool, self).__init__()
        self.initParams()

    def initParams(self):
        self.aligned = False

        self.ref1canvas = []  # reference point #1 on canvas [x1, y1]
        self.ref2canvas = []  # reference point #2 on canvas [x2, y2]
        self.ref1stage = []  # reference point #1 on stage  [x1, y1]
        self.ref2stage = []  # reference point #2 on stage  [x2, y2]

        self.scale = 1
        self.rotation = 0

    def setReferencePoints(self, ref1canvas, ref1stage, ref2canvas, ref2stage):
        # ref1c: reference point #1 on canvas [x1, y1]
        # ref1s: reference point #1 on stage  [x1, y1]
        # ref2c: reference point #2 on canvas [x2, y2]
        # ref2s: reference point #2 on stage  [x2, y2]
        self.ref1canvas = ref1canvas
        self.ref2canvas = ref2canvas
        self.ref1stage = ref1stage
        self.ref2stage = ref2stage

        seg1 = [self.ref2canvas, self.ref1canvas]  # canvas
        seg2 = [self.ref2stage, self.ref1stage]  # stage

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

    def getWtAverageNew(self, pt, conv_param, toStage=False, debug=False):
        position_index = int(toStage)
        weights, wpt_x, wpt_y = [], [], []
        tmp = []  # for debug

        # print(conv_param)

        for cp in conv_param:
            params = [cp["scale"], cp["offset"], cp["rotation"]]
            w = cp["weight"]
            tmp2 = []  # for debug
            if toStage:
                np = self.toStageCoordinates2(pt, params)
            else:
                np = self.toCanvasCoordinates2(pt, params)
            weights.append(w)
            wpt_x.append(w * np[0])
            wpt_y.append(w * np[1])
            tmp2.append(w)
            tmp.append(tmp2)
        sum_weights = sum(weights)
        if debug:
            for i in range(len(tmp)):
                print(i + 1, [100 * ww / sum_weights for ww in tmp[i]])
        out = [p / sum_weights for p in [sum(wpt_x), sum(wpt_y)]]
        if toStage:
            # round for stage cooridnates (integer)
            out = [self.true_round_int(p) for p in out]
        return out

    def getWtAverage(self, pt, model, toStage=False, debug=False):
        position_index = int(toStage)
        weights, wpt_x, wpt_y = [], [], []
        tmp = []  # for debug
        for m in model:
            if m["used"] == 0:
                continue
            params = [m["scale"], m["offset"], m["rotation"]]
            tmp2 = []  # for debug
            for i in [1, 2]:
                d = self.getDistance(pt, m["point_" + str(i)][position_index])
                if d == 0:
                    d = 1e-10
                w = 1 / (d**2)
                if i == 1:
                    if toStage:
                        np = self.toStageCoordinates2(pt, params)
                    else:
                        np = self.toCanvasCoordinates2(pt, params)
                weights.append(w)
                wpt_x.append(w * np[0])
                wpt_y.append(w * np[1])
                tmp2.append(w)
            tmp.append(tmp2)
        sum_weights = sum(weights)
        if debug:
            for i in range(len(tmp)):
                print(i + 1, [100 * ww / sum_weights for ww in tmp[i]])
        out = [p / sum_weights for p in [sum(wpt_x), sum(wpt_y)]]
        if toStage:
            # round for stage cooridnates (integer)
            out = [self.true_round_int(p) for p in out]
        return out

    def getWtAveragedCanvasToStage(self, pt, model, debug=False):
        return self.getWtAverageNew(pt, model, toStage=True, debug=debug)

    def getWtAveragedStageToCanvas(self, pt, model, debug=False):
        return self.getWtAverageNew(pt, model, toStage=False, debug=debug)

    def toStageCoordinates2(self, pt, params, toCanvas=False):
        # params: [scale, offset, rotation]
        scale, offset, rotation = params
        pt = [pt[0] - offset[0][0], pt[1] - offset[0][1]]
        pt = self.rotateCoordinates([p * scale for p in pt], rotation, offset[1])
        if not toCanvas:
            pt = [self.true_round_int(v) for v in pt]
        return pt

    def toCanvasCoordinates2(self, pt, params):
        # params: [scale, offset, rotation]
        params = [1 / params[0], params[1][::-1], -1 * params[2]]
        return self.toStageCoordinates2(pt, params, toCanvas=True)

    def true_round_int(self, val):
        return int((val * 2 + 1) // 2)
