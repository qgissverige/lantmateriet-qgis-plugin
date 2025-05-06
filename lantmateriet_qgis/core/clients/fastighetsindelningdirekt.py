import json
from typing import Iterable, Literal, TypedDict, overload

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsJsonUtils,
    QgsProject,
    QgsReferencedGeometry,
)
from qgis.PyQt.QtCore import QDateTime, Qt, QUrlQuery

from lantmateriet_qgis.core.clients.base import BaseClient
from lantmateriet_qgis.core.util import cql2, omit

Collection = Literal[
    "registerenhetsomradesytor",
    "registerenhetsomradeslinjer",
    "registerenhetsomradespunkter",
]


def format_beteckning(properties: dict) -> str:
    return f"{properties['kommunnamn']} {properties['trakt']} {properties['etikett'].split('>')[0].replace('(', '').replace(')', '')}"


class RegisterenhetsOmrade(TypedDict):
    objektidentitet: str
    registerenhetsreferens: str
    objekttyp: Literal["fastighetsområde"]
    senastandrad: QDateTime
    lanskod: str
    kommunkod: str
    kommunnamn: str
    trakt: str
    block: str
    enhet: int | None
    omradesnummer: int
    etikett: str
    beteckning: str


class RegisterenhetsOmradeWithGeometry(RegisterenhetsOmrade):
    geometry: QgsReferencedGeometry


class Registerenhet(TypedDict):
    objektidentitet: str
    objekttyp: Literal["fastighetsområde"]
    senastandrad: QDateTime
    lanskod: str
    kommunkod: str
    kommunnamn: str
    trakt: str
    block: str
    enhet: int | None
    etikett: str
    beteckning: str
    geometry: QgsReferencedGeometry


class FastighetsindelningDirektClient(BaseClient):
    """Client for the Fastighetsindelning Direkt API."""

    base_path = "/ogc-features/v1/fastighetsindelning"

    def find_registerenheter(
        self, collection: Collection, filter: dict, limit: int = 10
    ) -> list[Registerenhet]:
        """Find a list of properties based on a CQL2 filter."""

        query = QUrlQuery()
        query.addQueryItem("filter", json.dumps(filter))
        query.addQueryItem("filter-lang", "cql2-json")
        query.addQueryItem("limit", str(limit))
        query.addQueryItem("omradesnummer", "1")
        response = self.get_omraden(collection, query, False)
        return [
            Registerenhet(
                **omit(
                    feature,
                    (
                        "geometry",
                        "omradesnummer",
                        "objektidentitet",
                        "registerenhetsreferens",
                        "beteckning",
                    ),
                ),
                objektidentitet=feature["registerenhetsreferens"],
                beteckning=format_beteckning(feature),
            )
            for feature in response
        ]

    @overload
    def get_omrade_at_point(
        self,
        collection: Collection,
        point: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[True] = False,
    ) -> RegisterenhetsOmradeWithGeometry: ...
    @overload
    def get_omrade_at_point(
        self,
        collection: Collection,
        point: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[False] = False,
    ) -> RegisterenhetsOmrade: ...
    def get_omrade_at_point(
        self,
        collection: Collection,
        point: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[True, False] = False,
    ) -> RegisterenhetsOmrade | RegisterenhetsOmradeWithGeometry:
        """Get the registerenhetsområde at a given point."""

        query = QUrlQuery()
        if crs.authid() not in ("EPSG:3006", "EPSG:4326"):
            transformer = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem.fromEpsgId(3006),
                QgsProject.instance().transformContext(),
            )
            point.transform(transformer)
            crs = QgsCoordinateReferenceSystem.fromEpsgId(3006)
        query.addQueryItem(
            "bbox",
            f"{point.centroid().asPoint().y()},{point.centroid().asPoint().x()},{point.centroid().asPoint().y()},{point.centroid().asPoint().x()}",
        )
        query.addQueryItem("bbox-crs", crs.toOgcUri())
        query.addQueryItem("limit", "1")
        omraden = self.get_omraden(collection, query, with_geometry)
        if len(omraden) == 0:
            return None
        return omraden[0]

    @overload
    def get_omraden_at_rect(
        self,
        collection: Collection,
        rect: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[True] = False,
    ) -> list[RegisterenhetsOmradeWithGeometry]: ...
    @overload
    def get_omraden_at_rect(
        self,
        collection: Collection,
        rect: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[False] = False,
    ) -> list[RegisterenhetsOmrade]: ...
    def get_omraden_at_rect(
        self,
        collection: Collection,
        rect: QgsGeometry,
        crs: QgsCoordinateReferenceSystem,
        with_geometry: Literal[True, False] = False,
    ) -> list[RegisterenhetsOmrade | RegisterenhetsOmradeWithGeometry]:
        """Get all registerenhetsområden within a given rectangle."""

        query = QUrlQuery()
        if crs.authid() not in ("EPSG:3006", "EPSG:4326"):
            transformer = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem.fromEpsgId(3006),
                QgsProject.instance().transformContext(),
            )
            rect.transform(transformer)
            crs = QgsCoordinateReferenceSystem.fromEpsgId(3006)
        query.addQueryItem(
            "bbox",
            f"{rect.boundingBox().yMinimum()},{rect.boundingBox().xMinimum()},{rect.boundingBox().yMaximum()},{rect.boundingBox().xMaximum()}",
        )
        query.addQueryItem("bbox-crs", crs.toOgcUri())
        query.addQueryItem("limit", "10000")
        return self.get_omraden(collection, query, with_geometry)

    @overload
    def get_omraden(
        self,
        collection: Collection,
        query: QUrlQuery,
        with_geometry: Literal[False] = False,
    ) -> list[RegisterenhetsOmrade]: ...
    @overload
    def get_omraden(
        self,
        collection: Collection,
        query: QUrlQuery,
        with_geometry: Literal[True] = False,
    ) -> list[RegisterenhetsOmradeWithGeometry]: ...
    def get_omraden(
        self, collection: Collection, query: QUrlQuery, with_geometry: bool = False
    ) -> list[RegisterenhetsOmrade | RegisterenhetsOmradeWithGeometry]:
        """Get all registerenhetsområden based on a URL query."""

        response, headers = self._get_with_headers(
            f"/collections/{collection}/items", query
        )

        crs_header = headers.get("content-crs", "").replace("<", "").replace(">", "")
        if crs_header == "http://www.opengis.net/def/crs/OGC/1.3/CRS84":
            crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        elif crs_header.startswith("http://www.opengis.net/def/crs/EPSG/0/"):
            epsg_id = int(crs_header.rpartition("EPSG/0/")[2])
            crs = QgsCoordinateReferenceSystem.fromEpsgId(epsg_id)
        else:
            raise ValueError(f"Unsupported CRS: {crs_header}")

        def maybe_flip(geometry: QgsGeometry) -> QgsGeometry:
            if crs.authid() == "EPSG:4326":
                return geometry
            absgeom = geometry.get()
            absgeom.swapXy()
            return QgsGeometry(absgeom.clone())

        if with_geometry:
            return [
                RegisterenhetsOmradeWithGeometry(
                    **omit(
                        feature["properties"],
                        ("senastandrad", "geometry", "beteckning"),
                    ),
                    senastandrad=QDateTime.fromString(
                        feature["properties"]["senastandrad"], Qt.ISODate
                    ),
                    geometry=QgsReferencedGeometry(
                        maybe_flip(
                            QgsJsonUtils.geometryFromGeoJson(
                                json.dumps(feature["geometry"])
                            )
                        ),
                        crs,
                    ),
                    beteckning=f"{feature['properties']['kommunnamn']} {feature['properties']['trakt']} {feature['properties']['etikett']}",
                )
                for feature in response["features"]
            ]
        else:
            return [
                RegisterenhetsOmrade(
                    **omit(feature["properties"], ("senastandrad", "beteckning")),
                    senastandrad=QDateTime.fromString(
                        feature["properties"]["senastandrad"], Qt.ISODate
                    ),
                    beteckning=f"{feature['properties']['kommunnamn']} {feature['properties']['trakt']} {feature['properties']['etikett']}",
                )
                for feature in response["features"]
            ]

    def get_registerenheter(
        self, collection: Collection, ids: Iterable[str]
    ) -> dict[str, Registerenhet] | None:
        """Get full representations of the requested properties."""

        query = QUrlQuery()
        if len(ids) == 1:
            query.addQueryItem("registerenhetsreferens", list(ids)[0])
        else:
            query.addQueryItem(
                "filter",
                json.dumps(
                    cql2.in_(cql2.property("registerenhetsreferens"), list(ids))
                ),
            )
            query.addQueryItem("filter-lang", "cql2-json")
        query.addQueryItem("limit", "1000")
        query.addQueryItem(
            "crs", QgsCoordinateReferenceSystem.fromEpsgId(3006).toOgcUri()
        )
        response = self.get_omraden(collection, query, True)
        response = {
            id: [fg for fg in response if fg["registerenhetsreferens"] == id]
            for id in ids
        }
        return {
            id: Registerenhet(
                **omit(
                    omraden[0],
                    (
                        "senastandrad",
                        "geometry",
                        "beteckning",
                        "registerenhetsreferens",
                        "objektidentitet",
                        "etikett",
                    ),
                ),
                objektidentitet=omraden[0]["registerenhetsreferens"],
                senastandrad=max(omrade["senastandrad"] for omrade in omraden),
                geometry=QgsReferencedGeometry(
                    QgsGeometry.unaryUnion([omrade["geometry"] for omrade in omraden]),
                    omraden[0]["geometry"].crs(),
                ),
                etikett=omraden[0]["etikett"].split(">")[0],
                beteckning=format_beteckning(omraden[0]),
            )
            for id, omraden in response.items()
        }
