from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsReferencedGeometry,
    QgsWkbTypes,
)
from qgis.gui import QgisInterface, QgsRubberBand
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QWidget

from lantmateriet_qgis.__about__ import __title__


class BaseLocatorFilter(QgsLocatorFilter):
    def __init__(self, iface: QgisInterface):
        super().__init__()
        self._iface = iface
        self._rubber_band: QgsRubberBand | None = None

    def clearPreviousResults(self):
        if self._rubber_band is not None:
            self._rubber_band = None

    def hasConfigWidget(self) -> bool:
        return True

    def openConfigWidget(self, parent: QWidget | None = None):
        self._iface.showOptionsDialog(
            parent, currentPage="mOptionsPage{}".format(__title__)
        )

    @property
    def iface(self) -> QgisInterface:
        return self._iface

    def highlight(self, geometry: QgsReferencedGeometry):
        if geometry.wkbType() == QgsWkbTypes.GeometryCollection:
            for type_ in (
                Qgis.GeometryType.Point,
                Qgis.GeometryType.Line,
                Qgis.GeometryType.Polygon,
            ):
                geom = QgsGeometry(geometry)
                if (
                    geom.convertGeometryCollectionToSubclass(type_)
                    and not geom.isEmpty()
                ):
                    self.highlight(QgsReferencedGeometry(geom, geometry.crs()))
            return

        dest_crs = self._iface.mapCanvas().mapSettings().destinationCrs()
        if geometry.crs() != dest_crs:
            transformer = QgsCoordinateTransform(
                geometry.crs(),
                dest_crs,
                self._iface.mapCanvas().mapSettings().transformContext(),
            )
            geometry.transform(transformer)

        self._iface.mapCanvas().zoomToFeatureExtent(geometry.boundingBox())
        self._iface.mapCanvas().flashGeometries([geometry])

        self._rubber_band = QgsRubberBand(self._iface.mapCanvas(), geometry.type())
        self._rubber_band.setColor(QColor(255, 50, 50, 200))
        self._rubber_band.setBrushStyle(Qt.BrushStyle.NoBrush)
        if geometry.wkbType() == QgsWkbTypes.Point:
            self._rubber_band.setIcon(QgsRubberBand.IconType.ICON_CIRCLE)
            self._rubber_band.setIconSize(16)
            self._rubber_band.setWidth(4)
        else:
            self._rubber_band.setLineStyle(Qt.PenStyle.DashLine)
            self._rubber_band.setWidth(2)
        self._rubber_band.addGeometry(geometry, None)

    @staticmethod
    def get_user_data(result: QgsLocatorResult) -> dict:
        if hasattr(result, "getUserData"):
            return result.getUserData()
        else:
            return result.userData
