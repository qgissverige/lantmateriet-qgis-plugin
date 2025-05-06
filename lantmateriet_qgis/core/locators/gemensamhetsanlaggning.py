from typing import Self

from qgis.core import Qgis, QgsFeedback, QgsLocatorContext, QgsLocatorResult
from qgis.gui import QgisInterface

from lantmateriet_qgis.core.clients import (
    GemensamhetsanlaggningDirektClient,
)
from lantmateriet_qgis.core.locators.base import BaseLocatorFilter


class GemensamhetsanlaggningLocatorFilter(BaseLocatorFilter):
    def __init__(self, authcfg: str, base_url: str, iface: QgisInterface):
        super().__init__(iface)
        self._authcfg = authcfg
        self._base_url = base_url

        self.setFetchResultsDelay(300)
        self.setUseWithoutPrefix(False)

    def clone(self) -> Self:
        return GemensamhetsanlaggningLocatorFilter(
            self._authcfg, self._base_url, self._iface
        )

    def name(self) -> str:
        return "lantmateriet.gemensamhetsanlaggning"

    def displayName(self) -> str:
        return "Gemensamhetsanläggningar"

    def prefix(self) -> str:
        return "gan"

    def fetchResults(
        self,
        string: str | None,
        context: QgsLocatorContext,
        feedback: QgsFeedback | None,
    ):
        client = GemensamhetsanlaggningDirektClient(
            self._base_url, self._authcfg, feedback
        )

        if string is None or len(string) < 3:
            return

        try:
            references = client.get_references_from_text(string)
        except Exception:
            return None

        for ga in references:
            result = QgsLocatorResult(self, ga["objektidentitet"], ga)
            result.displayString = ga["beteckning"]
            self.resultFetched.emit(result)

    def triggerResult(self, result: QgsLocatorResult):
        self.clearPreviousResults()

        client = GemensamhetsanlaggningDirektClient(self._base_url, self._authcfg)
        user_data = self.get_user_data(result)
        try:
            ga = client.get_one(user_data["objektidentitet"], "geometri")
        except Exception as e:
            self.logMessage(str(e), Qgis.MessageLevel.Warning)
            return

        self.highlight(ga["geometry"])
