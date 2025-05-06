from typing import Any, Optional

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeatureSource,
    QgsProcessingFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsRectangle,
    QgsReferencedGeometry,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from lantmateriet.core.clients import (
    BelagenhetsadressDirektClient,
)
from lantmateriet.core.clients.belagenhetsadressdirekt import (
    BelagenhetsadressReference,
    BelagenhetsadressTotal,
)
from lantmateriet.core.settings import Settings

fields = QgsFields()
fields.append(QgsField("objektidentitet", QVariant.String))
fields.append(QgsField("adressplatsattribut", QVariant.Map))
fields.append(QgsField("adressplatsnamn", QVariant.Map))
fields.append(QgsField("adressomrade", QVariant.Map))
fields.append(QgsField("gardsadressomrade", QVariant.Map))
fields.append(QgsField("adressplatsanmarkning", QVariant.List, subType=QVariant.Map))
fields.append(QgsField("adressattAnlaggning", QVariant.Map))
fields.append(QgsField("distriktstillhorighet", QVariant.Map))
fields.append(QgsField("registerenhetsreferens", QVariant.Map))


def to_feature(address: BelagenhetsadressTotal) -> QgsFeature:
    feature = QgsFeature(fields)
    feature.setGeometry(address["geometry"])
    feature.setAttributes(
        [
            address["objektidentitet"],
            address["adressplatsattribut"],
            address["adressplatsnamn"] if "adressplatsnamn" in address else None,
            address["adressomrade"],
            address["gardsadressomrade"] if "gardsadressomrade" in address else None,
            address["adressplatsanmarkning"]
            if "adressplatsanmarkning" in address
            else [],
            address["adressattAnlaggning"]
            if "adressattAnlaggning" in address
            else None,
            address["distriktstillhorighet"]
            if "distriktstillhorighet" in address
            else None,
            address["registerenhetsreferens"],
        ]
    )
    return feature


class AbstractDownloadPropertiesAlgorithm(QgsProcessingAlgorithm):
    OUTPUT = "OUTPUT"

    def group(self) -> str:
        return "Nedladdning"

    def groupId(self) -> str:
        return "downloading"

    def helpUrl(self) -> str:
        return f"https://qgissverige.github.io/lantmateriet-qgis-plugin/usage/algoritmer/{self.name().replace('_', '-')}/"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, "Output layer", QgsProcessing.SourceType.TypeVectorPoint
            )
        )

    def load_sink(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
    ) -> tuple[QgsFeatureSink, str]:
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            QgsCoordinateReferenceSystem.fromEpsgId(3006),
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        return sink, dest_id

    @classmethod
    def add_address_objects(
        cls,
        sink: QgsFeatureSink,
        references: list[BelagenhetsadressReference],
        feedback: QgsProcessingFeedback,
        client: BelagenhetsadressDirektClient,
        from_: float,
    ):
        feedback.pushInfo("Fetching address geometries...")
        references_chunks = [
            references[i : i + BelagenhetsadressDirektClient.MAX_GET_MANY]
            for i in range(
                0, len(references), BelagenhetsadressDirektClient.MAX_GET_MANY
            )
        ]
        total = (100.0 - from_) / len(references_chunks) if references_chunks else 0
        for current, chunk in enumerate(references_chunks):
            if feedback.isCanceled():
                return dict()

            objects = client.get_many(
                [ref["objektidentitet"] for ref in chunk], "total"
            )
            features = [to_feature(obj) for obj in objects]
            sink.addFeatures(features, QgsFeatureSink.Flag.FastInsert)

            feedback.setProgress(from_ + int(current * total))


class DownloadAddressesPolygonAlgorithm(AbstractDownloadPropertiesAlgorithm):
    INPUT = "INPUT"

    def name(self) -> str:
        return "download_addresses_polygons"

    def displayName(self) -> str:
        return "Hämta adresser inom polygoner"

    def shortHelpString(self) -> str:
        return "Hämtar alla adresser som finns inom givna polygoner"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Input layer",
                [QgsProcessing.SourceType.TypeVectorPolygon],
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        source: QgsProcessingFeatureSource | None = self.parameterAsSource(
            parameters, self.INPUT, context
        )
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )

        (sink, dest_id) = self.load_sink(parameters, context)

        s = Settings.load_from_settings()
        if (
            not s.ovrig_enabled
            or not s.belagenhetsadress_direkt_enabled
            or not s.ovrig_authcfg
        ):
            raise QgsProcessingException(
                "Belägenhetsadress Direkt is not enabled in the settings"
            )
        client = BelagenhetsadressDirektClient(s.ovrig_url, s.ovrig_authcfg, feedback)

        feedback.pushInfo("Fetching address references within polygons...")
        references: dict[str, BelagenhetsadressReference] = {}

        total = 50.0 / source.featureCount() if source.featureCount() else 0
        req = QgsFeatureRequest()
        req.setFeedback(feedback)
        req.setNoAttributes()
        for current, feature in enumerate(source.getFeatures(req)):
            if feedback.isCanceled():
                return dict()

            geom = feature.geometry()
            if geom is None:
                continue

            refs = client.get_references_from_geometry(
                QgsReferencedGeometry(geom, source.sourceCrs())
            )
            references.update({ref["objektidentitet"]: ref for ref in refs})

            feedback.setProgress(int(current * total))

        self.add_address_objects(
            sink, list(references.values()), feedback, client, 50.0
        )

        return {self.OUTPUT: dest_id}

    def createInstance(self):
        return self.__class__()


class DownloadAddressesBoundingAlgorithm(AbstractDownloadPropertiesAlgorithm):
    EXTENT = "EXTENT"

    def name(self) -> str:
        return "download_addresses_bounding"

    def displayName(self) -> str:
        return "Hämta adresser inom ett område"

    def shortHelpString(self) -> str:
        return "Hämtar alla adresser som finns inom ett givet område"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                "Extent",
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        extent: QgsRectangle | None = self.parameterAsExtent(
            parameters,
            self.EXTENT,
            context,
            crs=QgsCoordinateReferenceSystem.fromEpsgId(3006),
        )
        if extent is None:
            raise QgsProcessingException("Invalid extent provided")

        (sink, dest_id) = self.load_sink(parameters, context)

        s = Settings.load_from_settings()
        if (
            not s.ovrig_enabled
            or not s.belagenhetsadress_direkt_enabled
            or not s.ovrig_authcfg
        ):
            raise QgsProcessingException(
                "Belägenhetsadress Direkt is not enabled in the settings"
            )
        client = BelagenhetsadressDirektClient(s.ovrig_url, s.ovrig_authcfg, feedback)

        feedback.pushInfo("Fetching address references within extent...")
        references = client.get_references_from_geometry(QgsGeometry.fromRect(extent))
        feedback.setProgress(20.0)

        self.add_address_objects(sink, references, feedback, client, 20.0)

        return {self.OUTPUT: dest_id}

    def createInstance(self):
        return self.__class__()
