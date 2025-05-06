import json
from typing import Literal, TypedDict
from uuid import UUID

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsJsonUtils,
    QgsPointXY,
    QgsProject,
    QgsReferencedGeometry,
)
from qgis.PyQt.QtCore import QUrlQuery, QUuid

from lantmateriet_qgis.core.clients.base import BaseClient, coerce_uuid_to_str
from lantmateriet_qgis.core.clients.belagenhetsadressdirekt import (
    Utbytesobjekt,
)
from lantmateriet_qgis.core.clients.direkt_utils import coerce_crs, is_supported_crs


class Registerenhetsomrade(TypedDict):
    omradesnummer: int
    markering: bool | None
    centralpunktskoordinat: dict | None


class Registerbeteckning(Utbytesobjekt):
    markering: bool | None
    registeromrade: str
    trakt: str
    block: str | None
    enhet: int
    beteckningsstatus: Literal[
        "gällande", "ledig", "omregistrerad", "reserverad", "spärrad"
    ]
    omregistreringsdatum: str | None
    omregistreringsaktbeteckning: str | None
    omregistreradTill: str | None


class GemensamhetsanlaggningsReference(TypedDict):
    objektidentitet: str
    objektstatus: Literal["avregistrerad", "levande"]
    registerenhetsomrade: list[Registerenhetsomrade] | None


class RegisterenhetsReference(TypedDict):
    objektidentitet: str
    objektstatus: Literal["avregistrerad", "levande"]
    typ: Literal["Fastighet", "Samfällighet"]
    registerenhetsomrade: list[Registerenhetsomrade] | None


class Beteckning(TypedDict):
    registerenhetsreferens: RegisterenhetsReference
    gemensamhetsanlaggningsreferens: GemensamhetsanlaggningsReference
    registerbeteckning: list[Registerbeteckning]
    aldreRegisterbeteckning: list[dict]
    aldreTidigareRegisterbeteckning: list[dict]


class RegisterbeteckningsReference(TypedDict):
    objektidentitet: str
    registerenhet: str | None
    registerenhetstyp: Literal["Fastighet", "Samfällighet"] | None
    gemensamhetsanlaggning: str | None
    beteckning: str


def from_feature(data: dict, crs: QgsCoordinateReferenceSystem) -> dict:
    if "geometry" in data and data["geometry"] is not None:
        geometry = QgsJsonUtils.geometryFromGeoJson(json.dumps(data["geometry"]))
        geometry = QgsReferencedGeometry(geometry, crs)
        return dict(**data["properties"], id=data["id"], geometry=geometry)
    else:
        return dict(**data["properties"], id=data["id"], geometry=None)


class RegisterbeteckningDirektClient(BaseClient):
    """Client for the Registerbeteckning Direkt API."""

    base_path = "/distribution/produkter/registerbeteckning/v5"

    @classmethod
    def _handle_results(
        cls, srid: QgsCoordinateReferenceSystem | None, results: list[dict]
    ) -> list[dict]:
        return [
            from_feature(result, srid or QgsCoordinateReferenceSystem.fromEpsgId(3006))
            for result in results["features"]
        ]

    def get_one(
        self, id: str | UUID | QUuid, srid: QgsCoordinateReferenceSystem | None = None
    ) -> Beteckning:
        """Resolve a single designation."""
        query = QUrlQuery()
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        result = self._get(f"/{coerce_uuid_to_str(id)}", query)
        return self._handle_results(srid, result)[0]

    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[Beteckning]:
        """Resolve multiple designations."""
        query = QUrlQuery()
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        ids = [coerce_uuid_to_str(id) for id in ids]
        results = self._post("/", query, ids)
        return self._handle_results(srid, results)

    def get_by_name(
        self, name: str | list[str], srid: QgsCoordinateReferenceSystem | None = None
    ) -> list[Beteckning]:
        """Find designations matching a given name."""
        query = QUrlQuery()
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        if isinstance(name, str):
            query.addQueryItem("namn", name)
            result = self._get("/namn", query)
        else:
            result = self._post("/namn", query, name)
        return self._handle_results(srid, result)

    def get_by_belongs_to(
        self,
        belongs_to: str | UUID | QUuid,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[Beteckning]:
        """Find designations belonging to a given object."""
        query = QUrlQuery()
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        result = self._get(f"/tillhor/{coerce_uuid_to_str(belongs_to)}", query)
        return self._handle_results(srid, result)

    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[Beteckning]:
        """Find designations overlapping a given point."""

        query = QUrlQuery()
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        if isinstance(point, QgsReferencedGeometry):
            if is_supported_crs(point.crs()):
                query.addQueryItem("punktSrid", str(coerce_crs(point.crs())))
            else:
                transformer = QgsCoordinateTransform(
                    point.crs(),
                    QgsCoordinateReferenceSystem.fromEpsgId(3006),
                    QgsProject.instance().transformContext(),
                )
                point.transform(transformer)
        try:
            point: QgsPointXY = point.asPoint()
        except TypeError:
            raise ValueError("Invalid geometry type. Expected a point.")
        query.addQueryItem("koordinater", f"{point.y()},{point.x()}")

        result = self._get("/punkt", query)
        return self._handle_results(srid, result)

    def get_references_from_text(
        self,
        text: str,
        municipality_or_lan: str | None = None,
        status: Literal["gällande", "ledig", "omregistrerad", "reserverad", "spärrad"]
        | None = None,
        objektstatus: Literal["levande", "avregistrerad"] | None = None,
        max_hits: int = 100,
    ) -> list[RegisterbeteckningsReference]:
        """Find references to designations based on a text search."""

        query = QUrlQuery()
        query.addQueryItem("beteckning", text)
        if municipality_or_lan is not None:
            if len(municipality_or_lan) != 2:
                query.addQueryItem("kommunkod", municipality_or_lan)
            else:
                query.addQueryItem("lankod", municipality_or_lan)

        if status is not None:
            query.addQueryItem("status", status)
        if objektstatus is not None:
            query.addQueryItem("objektstatus", objektstatus)
        query.addQueryItem("maxHits", str(max_hits))

        result = self._get("/referens/fritext", query)
        return [RegisterbeteckningsReference(**item) for item in result]

    def get_references_from_geometry(
        self,
        geometry: QgsGeometry | QgsReferencedGeometry,
        buffer: int = 0,
        status: Literal["gällande", "ledig", "omregistrerad", "reserverad", "spärrad"]
        | None = None,
    ) -> list[RegisterbeteckningsReference]:
        """Find references to designations within a given geometry, or within a buffer distance thereof."""

        query = QUrlQuery()
        if isinstance(geometry, QgsReferencedGeometry):
            if not is_supported_crs(geometry.crs()):
                transformer = QgsCoordinateTransform(
                    geometry.crs(),
                    QgsCoordinateReferenceSystem.fromEpsgId(3006),
                    QgsProject.instance().transformContext(),
                )
                geometry.transform(transformer)
                geometry = QgsReferencedGeometry(
                    geometry.geometry(), QgsCoordinateReferenceSystem.fromEpsgId(3006)
                )
        else:
            geometry = QgsReferencedGeometry(
                geometry, QgsCoordinateReferenceSystem.fromEpsgId(3006)
            )
        if status is not None:
            query.addQueryItem("status", status)

        data = json.loads(geometry.asJson())
        data["crs"] = {
            "type": "name",
            "properties": {"name": geometry.crs().toOgcUrn()},
        }
        data = {"geometri": data, "buffer": buffer}

        result = self._post("/referens/geometri", query, data)
        if result is None:
            raise ValueError("Error retrieving references")
        return [RegisterbeteckningsReference(**item) for item in result]
