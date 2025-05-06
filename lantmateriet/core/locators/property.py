from itertools import groupby
from typing import Self

from qgis.core import (
    Qgis,
    QgsFeedback,
    QgsIconUtils,
    QgsLocatorContext,
    QgsLocatorResult,
)
from qgis.gui import QgisInterface

from lantmateriet.core.clients import (
    FastighetOchSamfallighetDirektClient,
    FastighetsindelningDirektClient,
    GemensamhetsanlaggningDirektClient,
    RegisterbeteckningDirektClient,
)
from lantmateriet.core.clients.base import Canceled
from lantmateriet.core.locators.base import BaseLocatorFilter
from lantmateriet.core.settings import Settings
from lantmateriet.core.util.designation import parse_designation


class PropertyLocatorFilter(BaseLocatorFilter):
    def __init__(self, iface: QgisInterface):
        super().__init__(iface)

        self.setFetchResultsDelay(300)
        self.setUseWithoutPrefix(False)

    def clone(self) -> Self:
        return PropertyLocatorFilter(self._iface)

    def name(self) -> str:
        return "lantmateriet.fastighet"

    def displayName(self) -> str:
        return "Fastighetsregistret"

    def prefix(self) -> str:
        return "fgh"

    def fetchResults(
        self, string: str, context: QgsLocatorContext, feedback: QgsFeedback
    ):
        s = Settings.load_from_settings()
        if not s.ovrig_enabled or not s.ovrig_authcfg:
            self.setEnabled(False)
            return

        if s.registerbeteckning_direkt_enabled:
            client = RegisterbeteckningDirektClient(
                s.ovrig_url, s.ovrig_authcfg, feedback
            )
            try:
                results = client.get_references_from_text(
                    string, status="gällande", objektstatus="levande", max_hits=100
                )
            except Canceled:
                return

            for type, items in groupby(
                results,
                lambda i: "gemensamhetsanläggning"
                if "gemensamhetsanlaggning" in i
                else i["registerenhetstyp"].lower(),
            ):
                for item in list(items)[:10]:
                    if type == "gemensamhetsanläggning":
                        result = QgsLocatorResult(
                            self,
                            item["gemensamhetsanlaggning"],
                            dict(
                                objektidentitet=item["gemensamhetsanlaggning"],
                                type=type,
                            ),
                        )
                        result.group = "Gemensamhetsanläggning"
                    else:
                        result = QgsLocatorResult(
                            self,
                            item["registerenhet"],
                            dict(objektidentitet=item["registerenhet"], type=type),
                        )
                        result.group = item["registerenhetstyp"]
                    result.displayString = item["beteckning"]
                    self.resultFetched.emit(result)
        elif s.fastighetsindelning_direkt_enabled:
            filters = parse_designation(string)
            if not filters:
                return

            client = FastighetsindelningDirektClient(
                s.ovrig_url, s.ovrig_authcfg, feedback
            )

            for collection in (
                "registerenhetsomradesytor",
                "registerenhetsomradeslinjer",
                "registerenhetsomradespunkter",
            ):
                for filter in filters:
                    try:
                        response = client.find_registerenheter(collection, filter)
                    except Canceled:
                        continue

                    for feature in response:
                        data = dict(**feature)
                        data["collection"] = collection
                        data["type"] = (
                            "samfällighet" if feature["block"] == "s" else "fastighet"
                        )
                        result = QgsLocatorResult(
                            self, feature["objektidentitet"], data
                        )
                        result.displayString = feature["beteckning"]
                        if collection == "registerenhetsomradesytor":
                            result.icon = QgsIconUtils.iconPolygon()
                        elif collection == "registerenhetsomradeslinjer":
                            result.icon = QgsIconUtils.iconLine()
                        elif collection == "registerenhetsomradespunkter":
                            result.icon = QgsIconUtils.iconPoint()
                        self.resultFetched.emit(result)
        else:
            self.setEnabled(False)

    def triggerResult(self, result: QgsLocatorResult):
        self.clearPreviousResults()

        user_data = self.get_user_data(result)
        identifier = user_data["objektidentitet"]

        s = Settings.load_from_settings()
        if not s.ovrig_enabled or not s.ovrig_authcfg:
            return

        if user_data["type"] == "gemensamhetsanläggning":
            if not s.gemensamhetsanlaggning_direkt_enabled:
                self.logMessage(
                    "Gemensamhetsanläggning Direkt is not enabled, cannot show result",
                    Qgis.MessageLevel.Warning,
                )
                return
            client = GemensamhetsanlaggningDirektClient(s.ovrig_url, s.ovrig_authcfg)
            try:
                result = client.get_one(identifier, "geometri")
            except Canceled:
                return
            except Exception as e:
                self.logMessage(str(e), Qgis.MessageLevel.Warning)
                return
            geometry = result["geometry"]
        else:
            if s.fastighet_direkt_enabled:
                client = FastighetOchSamfallighetDirektClient(
                    s.ovrig_url, s.ovrig_authcfg
                )
                try:
                    result = client.get_one(identifier, "omrade")
                except Canceled:
                    return
                except Exception as e:
                    self.logMessage(str(e), Qgis.MessageLevel.Warning)
                    return
                geometry = result["geometry"]
            elif s.fastighetsindelning_direkt_enabled:
                client = FastighetsindelningDirektClient(s.ovrig_url, s.ovrig_authcfg)

                try:
                    geometries = client.get_registerenheter(
                        user_data["collection"], [identifier]
                    )
                except Canceled:
                    return
                except Exception as e:
                    self.logMessage(str(e), Qgis.MessageLevel.Warning)
                    raise
                geometry = geometries[identifier][
                    "geometry"
                ]  # get the one geometry we fetched
            else:
                return

        self.highlight(geometry)
