from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsWkbTypes,
)
from qgis.gui import QgisInterface, QgsRubberBand
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


class BaseLocatorFilter(QgsLocatorFilter):
    def __init__(self, iface: QgisInterface):
        super().__init__()
        self._iface = iface
        self._rubber_band: QgsRubberBand | None = None

    def clearPreviousResults(self):
        if self._rubber_band is not None:
            self._rubber_band = None

    @property
    def iface(self) -> QgisInterface:
        return self._iface

    def highlight(self, geometry: QgsGeometry, crs: QgsCoordinateReferenceSystem):
        dest_crs = self._iface.mapCanvas().mapSettings().destinationCrs()
        if crs != dest_crs:
            transformer = QgsCoordinateTransform(
                crs, dest_crs, self._iface.mapCanvas().mapSettings().transformContext()
            )
            geometry.transform(transformer)

        self._iface.mapCanvas().zoomToFeatureExtent(geometry.boundingBox())
        self._iface.mapCanvas().flashGeometries([geometry])

        self._rubber_band = QgsRubberBand(self._iface.mapCanvas(), geometry.type())
        self._rubber_band.setColor(QColor(255, 50, 50, 200))
        self._rubber_band.setBrushStyle(Qt.BrushStyle.NoBrush)
        if geometry.wkbType() == QgsWkbTypes.GeometryType.PointGeometry:
            self._rubber_band.setLineStyle(Qt.PenStyle.DashLine)
            self._rubber_band.setWidth(2)
        else:
            self._rubber_band.setIcon(QgsRubberBand.IconType.ICON_CIRCLE)
            self._rubber_band.setIconSize(15)
            self._rubber_band.setWidth(4)
        self._rubber_band.addGeometry(geometry, None)

    @staticmethod
    def get_user_data(result: QgsLocatorResult) -> dict:
        if hasattr(result, "getUserData"):
            return result.getUserData()
        else:
            return result.userData
