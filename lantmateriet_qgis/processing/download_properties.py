from typing import Any, Literal, Optional

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsFeedback,
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
from qgis.PyQt.QtCore import QDateTime, QMetaType, Qt

from lantmateriet_qgis.core.clients import (
    FastighetOchSamfallighetDirektClient,
    FastighetsindelningDirektClient,
)
from lantmateriet_qgis.core.clients.fastighetochsamfallighetdirekt import IncludableData
from lantmateriet_qgis.core.clients.fastighetsindelningdirekt import (
    Collection,
    Registerenhet,
)
from lantmateriet_qgis.core.settings import Settings
from lantmateriet_qgis.core.util import omit
from lantmateriet_qgis.core.util.municipalities import municipalities


def make_fields(source: Literal["fastighetsindelningdirekt"] | IncludableData):
    fields = QgsFields()
    fields.append(QgsField("objektidentitet", QMetaType.Type.QString))
    fields.append(QgsField("objekttyp", QMetaType.Type.QString))
    fields.append(QgsField("senastandrad", QMetaType.Type.QDateTime))
    fields.append(QgsField("lanskod", QMetaType.Type.QString))
    fields.append(QgsField("kommunkod", QMetaType.Type.QString))
    fields.append(QgsField("kommunnamn", QMetaType.Type.QString))
    fields.append(QgsField("trakt", QMetaType.Type.QString))
    fields.append(QgsField("block", QMetaType.Type.QString))
    fields.append(QgsField("enhet", QMetaType.Type.UInt))
    fields.append(QgsField("etikett", QMetaType.Type.QString))
    fields.append(QgsField("beteckning", QMetaType.Type.QString))

    if source != "fastighetsindelningdirekt":
        fields.append(QgsField("data", QMetaType.Type.QVariantMap, "json"))

    return fields


def geometry_iterator(source: QgsProcessingFeatureSource, feedback: QgsFeedback):
    req = QgsFeatureRequest()
    req.setFeedback(feedback)
    req.setNoAttributes()
    for current, feature in enumerate(source.getFeatures(req)):
        if feedback.isCanceled():
            return

        geom = feature.geometry()
        if geom is None:
            continue

        yield geom


class AbstractDownloadPropertiesAlgorithm(QgsProcessingAlgorithm):
    OUTPUT_POLYGONS = "OUTPUT_POLYGONS"
    OUTPUT_LINES = "OUTPUT_LINES"
    OUTPUT_POINTS = "OUTPUT_POINTS"

    def group(self) -> str:
        return "Nedladdning"

    def groupId(self) -> str:
        return "downloading"

    def helpUrl(self) -> str:
        return f"https://qgissverige.github.io/lantmateriet-qgis-plugin/usage/algoritmer/{self.name().replace('_', '-')}/"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POLYGONS,
                "Output layer (Polygons)",
                QgsProcessing.SourceType.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                "Output layer (Lines)",
                QgsProcessing.SourceType.TypeVectorLine,
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POINTS,
                "Output layer (Points)",
                QgsProcessing.SourceType.TypeVectorPoint,
                optional=True,
                createByDefault=False,
            )
        )

    def load_sinks(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        fields: QgsFields,
    ):
        sink_polygons: QgsFeatureSink
        (sink_polygons, dest_polygons_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_POLYGONS,
            context,
            fields,
            QgsWkbTypes.Type.MultiPolygon,
            QgsCoordinateReferenceSystem.fromEpsgId(3006),
        )
        if sink_polygons is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT_POLYGONS)
            )

        sink_lines: QgsFeatureSink | None = None
        if self.OUTPUT_LINES in parameters:
            (sink_lines, dest_lines_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT_LINES,
                context,
                fields,
                QgsWkbTypes.Type.LineString,
                QgsCoordinateReferenceSystem.fromEpsgId(3006),
            )
            if sink_lines is None:
                raise QgsProcessingException(
                    self.invalidSinkError(parameters, self.OUTPUT_LINES)
                )

        sink_points: QgsFeatureSink | None = None
        if self.OUTPUT_POINTS in parameters:
            (sink_points, dest_points_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT_POINTS,
                context,
                fields,
                QgsWkbTypes.Type.Point,
                QgsCoordinateReferenceSystem.fromEpsgId(3006),
            )
            if sink_points is None:
                raise QgsProcessingException(
                    self.invalidSinkError(parameters, self.OUTPUT_POINTS)
                )

        outputs = {self.OUTPUT_POLYGONS: dest_polygons_id}
        if sink_lines is not None:
            outputs[self.OUTPUT_LINES] = dest_lines_id
        if sink_points is not None:
            outputs[self.OUTPUT_POINTS] = dest_points_id

        return sink_polygons, sink_lines, sink_points, outputs

    @classmethod
    def add_fastighetsindelning_objects(
        self,
        sink: QgsFeatureSink,
        extent: QgsGeometry,
        objects: dict[str, Registerenhet],
        fields: QgsFields,
    ):
        for object in objects.values():
            if not object["geometry"].intersects(extent):
                continue

            feature = QgsFeature(fields)
            feature.setGeometry(object["geometry"])
            feature.setAttributes(
                [
                    object["objektidentitet"],
                    object["objekttyp"],
                    object["senastandrad"],
                    object["lanskod"],
                    object["kommunkod"],
                    object["kommunnamn"],
                    object["trakt"],
                    object["block"],
                    object["enhet"],
                    object["etikett"],
                    f"{object['kommunnamn']} {object['trakt']} {object['etikett']}",
                ]
            )

            sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert)

    @classmethod
    def fetch_fastighetsindelning_references(
        cls,
        collection: Collection,
        extent: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        client: FastighetsindelningDirektClient,
        feedback: QgsProcessingFeedback,
    ) -> set[str]:
        omraden = client.get_omraden_at_rect(
            collection, extent, crs, with_geometry=False
        )
        for omrade in omraden:
            if "outrettomradesinformation" in omrade:
                feedback.pushWarning(
                    f"Hittade ett outrett område i svaret från Lantmäteriet. Detta kommer inte inkluderas i nedladdningen. Objektidentitet: {omrade['objektidentitet']}"
                )
        return set(
            omr["registerenhetsreferens"]
            for omr in omraden
            if "outrettomradesinformation" not in omr
        )

    @classmethod
    def add_fastighetdirekt_object(
        cls,
        object: dict[str, Any],
        sink_polygons: QgsFeatureSink,
        sink_lines: QgsFeatureSink,
        sink_points: QgsFeatureSink,
        feedback: QgsProcessingFeedback,
        fields: QgsFields,
    ):
        feature = QgsFeature(fields)
        feature.setGeometry(object["geometry"])
        attributes: dict | None = object.get(
            "fastighetsattribut", object.get("samfallighetsattribut", None)
        )
        etikett = (
            f"{attributes['block']}:{attributes['enhet']}"
            if attributes.get("enhet", None) is not None
            else attributes["block"]
        )
        municipality_name = municipalities[
            attributes["lanskod"] + attributes["kommunkod"]
        ].upper()
        feature.setAttributes(
            [
                object["objektidentitet"],
                object["typ"],
                QDateTime.fromString(
                    attributes["versionGiltigFran"], Qt.DateFormat.ISODate
                ),
                attributes["lanskod"],
                attributes["lanskod"] + attributes["kommunkod"],
                municipality_name,
                attributes["trakt"],
                attributes["block"],
                attributes.get("enhet", None),
                etikett,
                f"{municipality_name} {attributes['trakt']} {etikett}",
                omit(object, ("objectidentitet", "typ")),
            ]
        )

        geom_type = QgsWkbTypes.singleType(feature.geometry().wkbType())
        if geom_type == QgsWkbTypes.Type.Polygon:
            sink_polygons.addFeature(feature, QgsFeatureSink.Flag.FastInsert)
        elif geom_type == QgsWkbTypes.Type.LineString:
            if sink_lines is not None:
                sink_lines.addFeature(feature, QgsFeatureSink.Flag.FastInsert)
        elif geom_type == QgsWkbTypes.Type.Point:
            if sink_points is not None:
                sink_points.addFeature(feature, QgsFeatureSink.Flag.FastInsert)
        else:
            feedback.pushWarning(
                f"Unknown geometry type {feature.geometry().wkbType()} for feature {object['objektidentitet']}. Skipping."
            )


class DownloadPropertiesPolygonAlgorithm(AbstractDownloadPropertiesAlgorithm):
    INPUT = "INPUT"

    def name(self) -> str:
        return "download_properties_polygons"

    def displayName(self) -> str:
        return "Hämta fastigheter och samfälligheter inom polygoner"

    def shortHelpString(self) -> str:
        return (
            "Hämtar alla fastigheter och samfälligheter som finns inom givna polygoner"
        )

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

        s = Settings.load_from_settings()
        if not s.ovrig_enabled or not s.ovrig_authcfg:
            raise QgsProcessingException("Services not enabled in settings")

        fields = (
            make_fields("basinformation")
            if s.fastighet_direkt_enabled
            else make_fields("fastighetsindelningdirekt")
        )
        sink_polygons, sink_lines, sink_points, dest_ids = self.load_sinks(
            parameters, context, fields
        )

        if s.fastighet_direkt_enabled:
            feedback.pushInfo("Using service: Fastighet Direkt")
            client = FastighetOchSamfallighetDirektClient(s.ovrig_url, s.ovrig_authcfg)
            references: set[str] = set()

            total = 50.0 / source.featureCount() if source.featureCount() else 0
            for current, geometry in enumerate(geometry_iterator(source, feedback)):
                refs = client.get_references_from_geometry(
                    QgsReferencedGeometry(geometry, source.sourceCrs())
                )
                references.update({ref["objektidentitet"] for ref in refs})

                feedback.setProgress(int(current * total))

            # = client.get_references_from_geometry(extent_geom)
            # TODO: we get error messages when attempting to load more than one item
            # references_chunks = [references[i:i + FastighetOchSamfallighetDirektClient.MAX_GET_MANY] for i in range(0, len(references), FastighetOchSamfallighetDirektClient.MAX_GET_MANY)]
            # for chunk in references_chunks:
            #    objects = client.get_many([ref["objektidentitet"] for ref in chunk], "total")
            #    for object in objects:
            for reference in references:
                object = client.get_one(reference, ("basinformation", "omrade"))
                self.add_fastighetdirekt_object(
                    object, sink_polygons, sink_lines, sink_points, feedback, fields
                )
        elif s.fastighetsindelning_direkt_enabled:
            feedback.pushInfo("Using service: Fastighetsindelning Direkt")
            client = FastighetsindelningDirektClient(
                s.ovrig_url, s.ovrig_authcfg, feedback
            )

            for idx, (collection, sink) in enumerate(
                (
                    ("registerenhetsomradesytor", sink_polygons),
                    ("registerenhetsomradeslinjer", sink_lines),
                    ("registerenhetsomradespunkter", sink_points),
                ),
            ):
                if sink is None:
                    continue

                references: set[str] = set()

                total = 50.0 / source.featureCount() if source.featureCount() else 0
                for current, geometry in enumerate(geometry_iterator(source, feedback)):
                    references.update(
                        self.fetch_fastighetsindelning_references(
                            collection, geometry, source.sourceCrs(), client, feedback
                        )
                    )
                    feedback.setProgress(int(current * total))

                extents = QgsGeometry.unaryUnion(
                    list(geometry_iterator(source, feedback))
                )

                objects = client.get_registerenheter(collection, references)
                self.add_fastighetsindelning_objects(sink, extents, objects, fields)
                feedback.setProgress(idx * 33.3)
        else:
            raise QgsProcessingException(
                "Neither Fastighet Direkt nor Fastighetsindelning Direkt is enabled in the settings"
            )

        return dest_ids

    def createInstance(self):
        return self.__class__()


class DownloadPropertiesBoundingAlgorithm(AbstractDownloadPropertiesAlgorithm):
    EXTENT = "EXTENT"

    def name(self) -> str:
        return "download_properties_bounding"

    def displayName(self) -> str:
        return "Hämta fastigheter och samfälligheter inom ett område"

    def shortHelpString(self) -> str:
        return (
            "Hämtar alla fastigheter och samfälligheter som finns inom ett givet område"
        )

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
        extent_geom = QgsGeometry.fromRect(extent)

        s = Settings.load_from_settings()
        if not s.ovrig_enabled or not s.ovrig_authcfg:
            raise QgsProcessingException("Services not enabled in settings")

        fields = (
            make_fields("basinformation")
            if s.fastighet_direkt_enabled
            else make_fields("fastighetsindelningdirekt")
        )
        sink_polygons, sink_lines, sink_points, dest_ids = self.load_sinks(
            parameters, context, fields
        )

        if s.fastighet_direkt_enabled:
            feedback.pushInfo("Using service: Fastighet Direkt")
            client = FastighetOchSamfallighetDirektClient(
                s.ovrig_url, s.ovrig_authcfg, feedback
            )
            references = client.get_references_from_geometry(extent_geom)
            # TODO: we get error messages when attempting to load more than one item
            # references_chunks = [references[i:i + FastighetOchSamfallighetDirektClient.MAX_GET_MANY] for i in range(0, len(references), FastighetOchSamfallighetDirektClient.MAX_GET_MANY)]
            # for chunk in references_chunks:
            #    objects = client.get_many([ref["objektidentitet"] for ref in chunk], "total")
            #    for object in objects:
            for reference in references:
                obj = client.get_one(
                    reference["objektidentitet"], ("basinformation", "omrade")
                )
                self.add_fastighetdirekt_object(
                    obj, sink_polygons, sink_lines, sink_points, feedback, fields
                )
        elif s.fastighetsindelning_direkt_enabled:
            feedback.pushInfo("Using service: Fastighetsindelning Direkt")
            client = FastighetsindelningDirektClient(
                s.ovrig_url, s.ovrig_authcfg, feedback
            )

            for idx, (collection, sink) in enumerate(
                (
                    ("registerenhetsomradesytor", sink_polygons),
                    ("registerenhetsomradeslinjer", sink_lines),
                    ("registerenhetsomradespunkter", sink_points),
                ),
            ):
                if sink is None:
                    continue
                references = self.fetch_fastighetsindelning_references(
                    collection,
                    extent_geom,
                    QgsCoordinateReferenceSystem.fromEpsgId(3006),
                    client,
                    feedback,
                )
                if references:
                    objects = client.get_registerenheter(collection, references)
                    self.add_fastighetsindelning_objects(
                        sink, extent_geom, objects, fields
                    )
                feedback.setProgress(idx * 33.3)
        else:
            raise QgsProcessingException(
                "Neither Fastighet Direkt nor Fastighetsindelning Direkt is enabled in the settings"
            )

        return dest_ids

    def createInstance(self):
        return self.__class__()
