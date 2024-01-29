import json
import os
import os.path
import re

from PyQt5.QtCore import QVariant
from qgis.core import QgsProject


class LayerTool(object):

    """Docstring for LayerTool."""

    def __init__(self):
        """TODO: to be defined."""
        pass

    def get_fields(self, layer):
        try:
            out = [f.name() for f in layer.fields()]
        except Exception:
            print("Error: ", layer)
        return out

    def get_field_type(self, fieldName):
        if re.match(r"^(file|comment|sample)", fieldName, re.I):
            return QVariant.String
        return QVariant.Double

    def get_layer_list(self, layertype=-1):
        # Layer Types
        #  Vector: 0
        #  Raster: 1
        #  Plugin: 2
        #  Mesh:   3
        # layers = QgsProject.instance().mapLayers().values()
        #
        # maplayers() cannot detect removed layers, so layerTreeRoot is used
        layers = QgsProject.instance().layerTreeRoot().findLayers()
        if layertype == -1:
            return [layer.layer() for layer in layers]
        # Filter by layer type.
        out = [layer.layer() for layer in layers if layer.layer().type() == layertype]
        return out

    def get_vector_point_layers(self):
        # Filter by layer type 0: vector
        layers = self.get_layer_list(layertype=0)
        # filter only point geometry layer 0: point
        out = [
            layer
            for layer in layers
            if layer.geometryType() == 0 and layer.name() != "tmp" and layer.storageType() != "Memory storage"
        ]
        return out
