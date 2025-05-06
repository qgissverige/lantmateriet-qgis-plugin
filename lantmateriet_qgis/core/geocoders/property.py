from qgis.core import (
    Qgis,
    QgsFeedback,
    QgsField,
    QgsFields,
    QgsGeocoderContext,
    QgsGeocoderInterface,
    QgsGeocoderResult,
)
from qgis.PyQt.QtCore import QVariant

from lantmateriet_qgis.core.clients import (
    FastighetsindelningDirektClient,
)
from lantmateriet_qgis.core.util.designation import parse_designation


class FastighetsindelningDirektGeocoder(QgsGeocoderInterface):
    def __init__(self, authcfg: str, base_url: str):
        super().__init__()
        self._authcfg = authcfg
        self._base_url = base_url

    def flags(self) -> QgsGeocoderInterface.Flag:
        return QgsGeocoderInterface.Flag.GeocodesStrings

    def appendedFields(self) -> QgsFields:
        fields = QgsFields()
        fields.append(QgsField("registerenhetsreferens", QVariant.String))
        fields.append(QgsField("objekttyp", QVariant.String))
        fields.append(QgsField("senastandrad", QVariant.DateTime))
        fields.append(QgsField("lanskod", QVariant.String))
        fields.append(QgsField("kommunkod", QVariant.String))
        fields.append(QgsField("kommunnamn", QVariant.String))
        fields.append(QgsField("trakt", QVariant.String))
        fields.append(QgsField("block", QVariant.String))
        fields.append(QgsField("enhet", QVariant.Int))
        fields.append(QgsField("omradesnummer", QVariant.Int))
        fields.append(QgsField("etikett", QVariant.String))
        return fields

    def wkbType(self) -> Qgis.WkbType:
        return Qgis.WkbType.MultiPolygon

    def geocodeString(
        self,
        string: str,
        context: QgsGeocoderContext,
        feedback: QgsFeedback | None = None,
    ) -> list[QgsGeocoderResult]:
        result: list[QgsGeocoderResult] = []

        filter = parse_designation(string)
        if not filter:
            return []

        client = FastighetsindelningDirektClient(
            self._authcfg, self._base_url, feedback
        )

        for collection in (
            "registerenhetsomradesytor",
            "registerenhetsomradeslinjer",
            "registerenhetsomradespunkter",
        ):
            response = client.find_registerenheter(collection, filter)
            if response is None:
                return []

            if len(response) == 0:
                continue

            geometries = client.get_registerenheter(
                collection, [f["objektidentitet"] for f in response]
            )

            for feature in response:
                feature = geometries[feature["objektidentitet"]]

                item = QgsGeocoderResult(
                    identifier=feature["objektidentitet"],
                    geometry=feature["geometry"],
                    crs=feature["geometry"].crs(),
                )
                item.setDescription(feature["beteckning"])
                item.setAdditionalAttributes(feature)

                result.append(item)

        return result
