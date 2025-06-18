from typing import Self

from qgis.core import (
    Qgis,
    QgsFeedback,
    QgsIconUtils,
    QgsLocatorContext,
    QgsLocatorResult,
)
from qgis.gui import QgisInterface

from lantmateriet_qgis.core.clients import BelagenhetsadressDirektClient
from lantmateriet_qgis.core.clients.base import Canceled
from lantmateriet_qgis.core.locators.base import BaseLocatorFilter
from lantmateriet_qgis.core.settings import Settings


class AddressLocatorFilter(BaseLocatorFilter):
    def __init__(self, iface: QgisInterface):
        super().__init__(iface)

        self.setFetchResultsDelay(300)
        self.setUseWithoutPrefix(False)

    def clone(self) -> Self:
        return AddressLocatorFilter(self._iface)

    def name(self) -> str:
        return "lantmateriet.address"

    def displayName(self) -> str:
        return "Adresser"

    def prefix(self) -> str:
        return "adr"

    def fetchResults(
        self,
        string: str | None,
        context: QgsLocatorContext,
        feedback: QgsFeedback | None,
    ):
        s = Settings.load_from_settings()
        if (
            not s.ovrig_enabled
            or not s.ovrig_authcfg
            or not s.belagenhetsadress_direkt_enabled
        ):
            self.setEnabled(False)
            return
        client = BelagenhetsadressDirektClient(s.ovrig_url, s.ovrig_authcfg, feedback)

        if string is None or len(string) < 3:
            return

        try:
            references = client.get_references_from_text(
                string, max_hits=20, split_address=True
            )
        except Canceled:
            return None
        except Exception as e:
            self.log_exception(e)

        for adress in references:
            result = QgsLocatorResult(self, adress["objektidentitet"], adress)
            result.displayString = adress["adress"].replace(
                f"{adress['kommun']} {adress['kommundel']} ", ""
            )
            result.icon = QgsIconUtils.iconPoint()
            self.resultFetched.emit(result)

    def triggerResult(self, result: QgsLocatorResult):
        self.clearPreviousResults()

        s = Settings.load_from_settings()
        if (
            not s.ovrig_enabled
            or not s.ovrig_authcfg
            or not s.belagenhetsadress_direkt_enabled
        ):
            self.logMessage(
                "BelägenhetsadressDirekt is not enabled, cannot highlight results",
                Qgis.MessageLevel.Warning,
            )
            return
        client = BelagenhetsadressDirektClient(s.ovrig_url, s.ovrig_authcfg)

        user_data = self.get_user_data(result)
        try:
            address = client.get_one(user_data["objektidentitet"], "basinformation")
        except Canceled:
            return
        except Exception as e:
            self.log_exception(e)
            return

        self.highlight(address["geometry"])
