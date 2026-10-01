"""Preset layer creation, symbol units and shapefile-compatible size settings.

Existing projects encode spot and pixel sizes in ``ss_`` and ``ps_`` field
names. Keep that format so saved projects remain readable by earlier versions.
"""

import math

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    Qgis, QgsField, QgsMarkerSymbol, QgsPalLayerSettings, QgsPropertyCollection,
    QgsVectorFileWriter, QgsVectorLayer, QgsVectorLayerSimpleLabeling,
)


def size_fields(spot_size, pixel_size):
    return [
        QgsField(f"ss_{spot_size}", QVariant.Int),
        QgsField(f"ps_{pixel_size}", QVariant.Double),
    ]


def read_sizes(layer):
    """Read legacy field names; malformed or absent values use the UI defaults."""
    sizes = {"ss": 10, "ps": 1.0}
    for field in layer.fields():
        prefix, separator, value = field.name().partition("_")
        if separator and prefix in sizes:
            try:
                number = float(value)
            except ValueError:
                continue
            if math.isfinite(number) and number > 0:
                if prefix == "ps":
                    sizes[prefix] = number
                elif number.is_integer():
                    sizes[prefix] = int(number)
    return sizes


def write_sizes(layer, spot_size, pixel_size):
    """Update each size field without committing a user's existing edit session."""
    owns_edit = not layer.isEditable()
    if owns_edit and not layer.startEditing():
        return False
    values = {"ss": spot_size, "ps": pixel_size}
    found = set()
    success = True
    for index, field in enumerate(layer.fields()):
        prefix = field.name()[:2]
        if field.name().startswith(("ss_", "ps_")):
            found.add(prefix)
            new_name = f"{prefix}_{values[prefix]}"
            if field.name() != new_name:
                success = layer.renameAttribute(index, new_name) and success
    for field in size_fields(spot_size, pixel_size):
        if field.name()[:2] not in found:
            success = layer.addAttribute(field) and success
    if owns_edit:
        if not success:
            layer.rollBack()
            return False
        return layer.commitChanges()
    return success


def set_symbol_size(layer, diameter):
    """Set the top-level Marker unit, including its width and offset units."""
    symbol = layer.renderer().symbol()
    symbol.setOutputUnit(Qgis.RenderUnit.MapUnits)
    symbol.setSize(diameter)
    layer.emitStyleChanged()
    layer.triggerRepaint()


def create_layer(path, name, crs, spot_size, pixel_size, scale):
    """Create and style an OGR layer. The caller registers it in the project."""
    temporary = QgsVectorLayer("Point", "temporary_points", "memory")
    temporary.setCrs(crs)
    temporary.setProviderEncoding("UTF-8")
    temporary.dataProvider().addAttributes([
        QgsField("Comment", QVariant.String), *size_fields(spot_size, pixel_size),
    ])
    temporary.updateFields()
    error, message = QgsVectorFileWriter.writeAsVectorFormat(
        temporary, path, "UTF-8", crs, "ESRI Shapefile",
    )
    if error != QgsVectorFileWriter.NoError:
        raise ValueError(message)

    layer = QgsVectorLayer(path, name, "ogr")
    if not layer.isValid():
        raise ValueError(f"Unable to open preset layer: {path}")
    props = layer.renderer().symbol().symbolLayer(0).properties()
    props["name"] = "circle"
    layer.renderer().setSymbol(QgsMarkerSymbol.createSimple(props))
    set_symbol_size(layer, scale * spot_size)
    layer.updateExtents()

    settings = QgsPalLayerSettings()
    settings.enabled = True
    settings.fieldName = "Comment"
    settings.displayAll = True
    properties = QgsPropertyCollection("preset")
    properties.setProperty(settings.ShadowDraw, True)
    properties.setProperty(settings.BufferDraw, True)
    settings.setDataDefinedProperties(properties)
    layer.setLabelsEnabled(True)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    return layer
