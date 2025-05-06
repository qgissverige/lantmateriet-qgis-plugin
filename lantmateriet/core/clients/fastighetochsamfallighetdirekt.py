import json
from typing import Iterable, Literal, TypedDict
from uuid import UUID

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsJsonUtils,
    QgsProject,
    QgsReferencedGeometry,
)
from qgis.PyQt.QtCore import QUrlQuery, QUuid

from lantmateriet.core.clients.base import BaseClient, coerce_uuid_to_str
from lantmateriet.core.clients.direkt_utils import coerce_crs, is_supported_crs
from lantmateriet.core.util import omit


class RegisterenhetsReference(TypedDict):
    objektidentitet: str
    beteckning: str
    typ: Literal["fastighet", "samfällighet"]


def from_feature(data: dict, crs: QgsCoordinateReferenceSystem) -> dict:
    if (
        "registerenhetsomrade" in data["properties"]
        and data["properties"]["registerenhetsomrade"] is not None
    ):
        registerenhetsomraden = [
            dict(
                **omit(omr, ("yta",)),
                yta=QgsReferencedGeometry(
                    QgsGeometry.unaryUnion(
                        [
                            QgsJsonUtils.geometryFromGeoJson(json.dumps(yta))
                            for yta in omr["yta"]
                        ]
                    ),
                    crs,
                ),
            )
            for omr in data["properties"]["registerenhetsomrade"]
        ]
        geometry = QgsGeometry.unaryUnion([omr["yta"] for omr in registerenhetsomraden])
        return dict(
            **omit(data["properties"], ("registerenhetsomrade",)),
            registerenhetsomrade=registerenhetsomraden,
            id=data["id"],
            geometry=QgsReferencedGeometry(geometry, crs),
        )
    else:
        return dict(**data["properties"], id=data["id"], geometry=None)


IncludableData = Literal[
    "basinformation",
    "registerbeteckning",
    "atgard",
    "beteckningForeReformen",
    "andel",
    "omrade",
    "historik",
    "total",
]


class FastighetOchSamfallighetDirektClient(BaseClient):
    """Client for the Fastighet och Samfällighet Direkt API."""

    base_path = "/distribution/produkter/fastighetsamfallighet/v3.1"

    MAX_GET_MANY = 250

    @classmethod
    def _handle_results(
        cls,
        _include: IncludableData | Iterable[IncludableData] | None,
        srid: QgsCoordinateReferenceSystem | None,
        results: list[dict],
    ) -> list[dict]:
        return [
            from_feature(result, srid or QgsCoordinateReferenceSystem.fromEpsgId(3006))
            for result in results["features"]
        ]

    def get_one(
        self,
        id: str | UUID | QUuid,
        include: IncludableData | Iterable[IncludableData] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> dict:
        """Download a single property."""
        query = QUrlQuery()
        if isinstance(include, str):
            query.addQueryItem("includeData", include)
        elif include is not None:
            query.addQueryItem("includeData", ",".join(include))
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        result = self._get(f"/{coerce_uuid_to_str(id)}", query)
        return self._handle_results(include, srid, result)[0]

    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: IncludableData | Iterable[IncludableData] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[dict]:
        """Download many single properties."""
        query = QUrlQuery()
        query.addQueryItem("includeData", include or "basinformation")
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        ids = [coerce_uuid_to_str(id) for id in ids]
        results = self._post("/", query, ids)
        return self._handle_results(include, srid, results)

    def get_references_from_aktbeteckning(
        self, text: str
    ) -> list[RegisterenhetsReference]:
        query = QUrlQuery()
        query.addQueryItem("aktbeteckning", text)

        result = self._get("/referens/aktbeteckning", query)
        return [RegisterenhetsReference(**item) for item in result]

    def get_references_from_geometry(
        self, geometry: QgsGeometry | QgsReferencedGeometry, buffer: int = 0
    ) -> list[RegisterenhetsReference]:
        """Download property references based on a geometri."""
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

        data = json.loads(geometry.asJson())
        data["crs"] = {
            "type": "name",
            "properties": {"name": geometry.crs().toOgcUrn()},
        }
        data = {"geometri": data, "buffer": buffer}

        result = self._post("/referens/geometri", query, data)
        if result is None:
            raise ValueError("Error retrieving references")
        return [RegisterenhetsReference(**item) for item in result]
