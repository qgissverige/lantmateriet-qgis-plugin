from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from lantmateriet_qgis.__about__ import __icon_path__, __title__, __version__
from lantmateriet_qgis.processing.download_addresses import (
    DownloadAddressesBoundingAlgorithm,
    DownloadAddressesPolygonAlgorithm,
)
from lantmateriet_qgis.processing.download_properties import (
    DownloadPropertiesBoundingAlgorithm,
    DownloadPropertiesPolygonAlgorithm,
)


class LantmaterietProvider(QgsProcessingProvider):
    """
    Processing provider class.
    """

    def loadAlgorithms(self):
        """Loads all algorithms belonging to this provider."""
        self.addAlgorithm(DownloadAddressesBoundingAlgorithm())
        self.addAlgorithm(DownloadAddressesPolygonAlgorithm())
        self.addAlgorithm(DownloadPropertiesBoundingAlgorithm())
        self.addAlgorithm(DownloadPropertiesPolygonAlgorithm())

    def id(self) -> str:
        """Unique provider id, used for identifying it. This string should be unique, \
        short, character only string, eg "qgis" or "gdal". \
        This string should not be localised.

        :return: provider ID
        :rtype: str
        """
        return "lantmateriet"

    def name(self) -> str:
        """Returns the provider name, which is used to describe the provider
        within the GUI. This string should be short (e.g. "Lastools") and localised.

        :return: provider name
        :rtype: str
        """
        return __title__

    def icon(self) -> QIcon:
        """QIcon used for your provider inside the Processing toolbox menu.

        :return: provider icon
        :rtype: QIcon
        """
        return QIcon(str(__icon_path__))

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: str
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(self.__class__.__name__, message)

    def versionInfo(self) -> str:
        """Version information for the provider, or an empty string if this is not \
        applicable (e.g. for inbuilt Processing providers). For plugin based providers, \
        this should return the plugin’s version identifier.

        :return: version
        :rtype: str
        """
        return __version__
