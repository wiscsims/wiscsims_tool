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
        return [f.name() for f in layer.fields()]

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
        layers = QgsProject.instance().mapLayers().values()
        if layertype == -1:
            return layers
        # Filter by layer type.
        return [layer for layer in layers if layer.type() == layertype]

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
