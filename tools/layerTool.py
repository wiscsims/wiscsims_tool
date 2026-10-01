import re
from datetime import date, time

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import sip
from qgis.core import QgsMapLayerType, QgsProject, QgsWkbTypes


class LayerTool:
    """Query user layers in legend order, excluding temporary preview layers."""

    def get_fields(self, layer):
        if layer is None or sip.isdeleted(layer):
            return []
        return [field.name() for field in layer.fields()]

    def get_field_type(self, fieldName, values=()):
        if re.match(r"^(file|comment|sample)", fieldName, re.I):
            return QVariant.String
        # Shapefiles cannot store a time or datetime field. Keep ISO text,
        # and preserve mixed columns (e.g. numbers and "rejected") as text.
        for value in values:
            if value is None or value == "":
                continue
            if isinstance(value, (date, time)):
                return QVariant.String
            try:
                float(value)
            except (TypeError, ValueError):
                return QVariant.String
        return QVariant.Double

    def get_layer_list(self, layertype=-1):
        nodes = QgsProject.instance().layerTreeRoot().findLayers()
        layers = [node.layer() for node in nodes if node.layer() is not None]
        return [layer for layer in layers if layertype == -1 or layer.type() == layertype]

    def get_vector_point_layers(self):
        layers = self.get_layer_list(QgsMapLayerType.VectorLayer)
        return [
            layer
            for layer in layers
            if layer.geometryType() == QgsWkbTypes.PointGeometry
            and layer.name() != "tmp" and layer.storageType() != "Memory storage"
        ]
