from pathlib import Path

from qgis.core import QgsApplication, QgsSettings
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator

import lantmateriet_qgis.core.functions  # noqa
from lantmateriet_qgis.__about__ import (
    DIR_PLUGIN_ROOT,
    __title__,
)
from lantmateriet_qgis.core.locators.address import AddressLocatorFilter
from lantmateriet_qgis.core.locators.property import PropertyLocatorFilter
from lantmateriet_qgis.gui.dlg_settings import PluginOptionsWidgetFactory
from lantmateriet_qgis.processing import LantmaterietProvider


class LantmaterietPlugin:
    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface

        # translation
        # initialize the locale
        self.locale: str = QgsSettings().value("locale/userLocale", QLocale().name())[
            0:2
        ]
        locale_path: Path = (
            DIR_PLUGIN_ROOT
            / "resources"
            / "i18n"
            / f"{__title__.lower()}_{self.locale}.qm"
        )
        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """Set up plugin UI elements."""

        self.options_factory = PluginOptionsWidgetFactory()
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        self.locators = [
            PropertyLocatorFilter(self.iface),
            AddressLocatorFilter(self.iface),
        ]
        for locator in self.locators:
            self.iface.registerLocatorFilter(locator)

        self.provider = LantmaterietProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: string to be translated.
        :type message: str

        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate(self.__class__.__name__, message)

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""

        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        for locator in self.locators:
            self.iface.deregisterLocatorFilter(locator)
            del locator
        self.locators = []

        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.provider = None
