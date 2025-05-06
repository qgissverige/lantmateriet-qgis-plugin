import json
from typing import Literal, TypedDict, overload
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
from lantmateriet_qgis.core.clients.direkt_utils import coerce_crs, is_supported_crs


class BelagenhetsadressReference(TypedDict):
    """A reference to an address."""

    objektidentitet: str
    adress: str


class BelagenhetsadressReferenceWithComponents(BelagenhetsadressReference):
    """A reference to an address, with separate components."""

    kommun: str
    kommundel: str
    adressomrade: str
    gardsadressomrade: str | None
    adressplatsnummer: str | None
    bokstavstillagg: str | None
    lagestillagg: str | None
    lagestillagsnummer: str | None
    avvikandeAdressplatsBeteckning: str | None
    postnummer: str | None
    postort: str | None


class Belagenhetsadress(TypedDict):
    id: str


class BelagenhetsadressNoInfo(Belagenhetsadress):
    geometry: None


class Utbytesobjekt(TypedDict):
    objektidentitet: str
    objektversion: int
    versionGiltigFran: str | None


class AdressplatsBeteckning(TypedDict):
    adressplatsnummer: str | None
    bokstavstillagg: str | None
    lagestillagg: Literal["UH", "UV", "U"] | None
    lagestillagsnummer: int | None
    avvikandeAdressplatsBeteckning: str | None
    avvikerFranStandarden: bool


class AdressplatsNamn(TypedDict):
    popularnamn: str
    ortid: str


class Kommun(TypedDict):
    kommunkod: str
    kommunnamn: str


class Kommundel(Utbytesobjekt):
    faststalltNamn: str
    ortid: int | None
    objektstatus: Literal["Gällande"]
    kommun: Kommun


class Adressomrade(Utbytesobjekt):
    faststalltNamn: str
    ortid: str | None
    adressomradestyp: Literal[
        "Gatuadressomrade", "Metertalsadressomrade", "Byadressomrade"
    ]
    objektstatus: Literal["Gällande"]
    kommundel: Kommundel


class Gardsadressomrade(TypedDict):
    faststalltNamn: str
    ortid: str | None
    objektstatus: Literal["Gällande"]
    adressomrade: Adressomrade


class AdressplatsAnmarkning(TypedDict):
    anmarkningstyp: Literal[
        "Angöringsplats för taxi",
        "Busshållplats",
        "Järnvägsstation/hållplats",
        "Kajplats",
        "Spårvagnshållplats",
        "Stoppställe för postutdelning",
        "Tunnelbanestationsnedgång",
        "Övrig anmärkning",
    ]
    anmarkningstext: str


class AdressattAnlaggning(TypedDict):
    anlaggningstyp: Literal[
        "Avloppspumpstation",
        "Brygga",
        "Idrottsanläggning",
        "Småbåtshamn",
        "Återvinningsstation",
    ]
    anlaggningstext: str | None


class Distriktstillhorighet(TypedDict):
    distriktskod: str
    distriktsnamn: str


class AdressplatsAttribut(Utbytesobjekt):
    adressplatsbeteckning: AdressplatsBeteckning
    adressplatstyp: Literal[
        "Gatuadressplats", "Metertalsadressplats", "Byadressplats", "Gårdsadressplats"
    ]
    insamlingslage: Literal[
        "Byggnad",
        "Ingång",
        "Infart",
        "Tomtplats",
        "Ungefärligt lägesbestämd",
        "Övrigt läge",
    ]
    status: Literal["Reserverad", "Gällande"]
    objektstatus: Literal["Gällande"]
    postnummer: int | None
    postort: str | None


class BelagenhetsadressBasinformation(Belagenhetsadress):
    geometry: QgsReferencedGeometry
    objektidentitet: str
    adressplatsattribut: AdressplatsAttribut
    adressplatsnamn: AdressplatsNamn
    adressomrade: Adressomrade
    gardsadressomrade: Gardsadressomrade | None
    adressplatsanmarkning: list[AdressplatsAnmarkning]
    adressattAnlaggning: AdressattAnlaggning | None
    distriktstillhorighet: Distriktstillhorighet | None


class RegisterenhetsReference(TypedDict):
    objektidentitet: str
    beteckning: str
    typ: Literal["Fastighet", "Samfällighet"]


class BelagenhetsadressBerorkrets(BelagenhetsadressNoInfo):
    registerenhetsreferens: RegisterenhetsReference


class BelagenhetsadressTotal(BelagenhetsadressBasinformation):
    registerenhetsreferens: RegisterenhetsReference


def from_feature(
    data: dict, crs: QgsCoordinateReferenceSystem
) -> BelagenhetsadressBasinformation | BelagenhetsadressTotal:
    geometry = QgsJsonUtils.geometryFromGeoJson(json.dumps(data["geometry"]))
    geometry = QgsReferencedGeometry(geometry, crs)
    return dict(**data["properties"], id=data["id"], geometry=geometry)


class BelagenhetsadressDirektClient(BaseClient):
    """Client for the Belägenhetsadress Direkt API."""

    base_path = "/distribution/produkter/belagenhetsadress/v4.2"

    MAX_GET_MANY = 250

    @classmethod
    def _handle_results(
        cls,
        include: Literal["basinformation", "berorkrets", "total"] | None,
        srid: QgsCoordinateReferenceSystem | None,
        results: list[dict],
    ) -> list[
        BelagenhetsadressNoInfo
        | BelagenhetsadressBasinformation
        | BelagenhetsadressBerorkrets
        | BelagenhetsadressTotal
    ]:
        if include is None:
            return [
                BelagenhetsadressNoInfo(id=result["id"], geometry=None)
                for result in results["features"]
            ]
        elif include == "basinformation":
            return [
                from_feature(
                    result, srid or QgsCoordinateReferenceSystem.fromEpsgId(3006)
                )
                for result in results["features"]
            ]
        elif include == "berorkrets":
            return [
                BelagenhetsadressBerorkrets(
                    id=result["id"],
                    geometry=None,
                    registerenhetsreferens=RegisterenhetsReference(
                        **result["properties"]["registerenhetsreferens"]
                    ),
                )
                for result in results["features"]
            ]
        elif include == "total":
            return [
                from_feature(
                    result, srid or QgsCoordinateReferenceSystem.fromEpsgId(3006)
                )
                for result in results["features"]
            ]
        else:
            raise ValueError(
                "Invalid include parameter. Must be one of: 'basinformation', 'berorkrets', 'total'."
            )

    @overload
    def get_one(
        self,
        id: str | UUID | QUuid,
        include: None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressNoInfo: ...
    @overload
    def get_one(
        self,
        id: str | UUID | QUuid,
        include: Literal["basinformation"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressBasinformation: ...
    @overload
    def get_one(
        self,
        id: str | UUID | QUuid,
        include: Literal["berorkrets"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressBasinformation: ...
    @overload
    def get_one(
        self,
        id: str | UUID | QUuid,
        include: Literal["total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressBasinformation: ...
    def get_one(
        self,
        id: str | UUID | QUuid,
        include: Literal["basinformation", "berorkrets", "total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> (
        BelagenhetsadressNoInfo
        | BelagenhetsadressBasinformation
        | BelagenhetsadressBerorkrets
        | BelagenhetsadressTotal
    ):
        """Download a single address."""
        query = QUrlQuery()
        query.addQueryItem("includeData", include or "basinformation")
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        result = self._get(f"/{coerce_uuid_to_str(id)}", query)
        return self._handle_results(include, srid, result)[0]

    @overload
    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressNoInfo]: ...
    @overload
    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: Literal["basinformation"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressBasinformation]: ...
    @overload
    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: Literal["berorkrets"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressBerorkrets]: ...
    @overload
    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: Literal["total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressTotal]: ...
    def get_many(
        self,
        ids: list[str | UUID | QUuid],
        include: Literal["basinformation", "berorkrets", "total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[
        BelagenhetsadressNoInfo
        | BelagenhetsadressBasinformation
        | BelagenhetsadressBerorkrets
        | BelagenhetsadressTotal
    ]:
        """Download many single addresses."""
        if len(ids) > self.MAX_GET_MANY:
            raise ValueError(
                f"Too many IDs. Maximum is {self.MAX_GET_MANY}, got {len(ids)}."
            )

        query = QUrlQuery()
        query.addQueryItem("includeData", include or "basinformation")
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        ids = [coerce_uuid_to_str(id) for id in ids]
        results = self._post("/", query, ids)
        return self._handle_results(include, srid, results)

    @overload
    def get_by_registerenhet(
        self,
        registerenhet_id: str | UUID | QUuid | list[str | UUID | QUuid],
        include: None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressNoInfo]: ...
    @overload
    def get_by_registerenhet(
        self,
        registerenhet_id: str | UUID | QUuid | list[str | UUID | QUuid],
        include: Literal["basinformation"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressBasinformation]: ...
    @overload
    def get_by_registerenhet(
        self,
        registerenhet_id: str | UUID | QUuid | list[str | UUID | QUuid],
        include: Literal["berorkrets"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressBerorkrets]: ...
    @overload
    def get_by_registerenhet(
        self,
        registerenhet_id: str | UUID | QUuid | list[str | UUID | QUuid],
        include: Literal["total"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[BelagenhetsadressTotal]: ...
    def get_by_registerenhet(
        self,
        registerenhet_id: str | UUID | QUuid | list[str | UUID | QUuid],
        include: Literal["basinformation", "berorkrets", "total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> list[
        BelagenhetsadressNoInfo
        | BelagenhetsadressBasinformation
        | BelagenhetsadressBerorkrets
        | BelagenhetsadressTotal
    ]:
        """Get addresses belonging to a specific property."""
        query = QUrlQuery()
        query.addQueryItem("includeData", include or "basinformation")
        if srid is not None:
            query.addQueryItem("srid", str(coerce_crs(srid)))

        if isinstance(registerenhet_id, list):
            registerenhet_id = [coerce_uuid_to_str(id) for id in registerenhet_id]
            results = self._post("/registerenhet", query, registerenhet_id)
        else:
            results = self._get(
                f"/registerenhet/{coerce_uuid_to_str(registerenhet_id)}", query
            )
        return self._handle_results(include, srid, results)

    @overload
    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        include: None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressNoInfo: ...
    @overload
    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        include: Literal["basinformation"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressBasinformation: ...
    @overload
    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        include: Literal["berorkrets"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressBerorkrets: ...
    @overload
    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        include: Literal["total"] = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> BelagenhetsadressTotal: ...
    def get_by_point(
        self,
        point: QgsGeometry | QgsReferencedGeometry,
        include: Literal["basinformation", "berorkrets", "total"] | None = None,
        srid: QgsCoordinateReferenceSystem | None = None,
    ) -> (
        BelagenhetsadressNoInfo
        | BelagenhetsadressBasinformation
        | BelagenhetsadressBerorkrets
        | BelagenhetsadressTotal
    ):
        """Get the adress closest to a given point."""
        query = QUrlQuery()
        query.addQueryItem("includeData", include or "basinformation")
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
        return self._handle_results(include, srid, result)[0]

    @overload
    def get_references_from_text(
        self,
        text: str,
        municipality: str | None = None,
        status: Literal["Gällande", "Reserverad"] | None = None,
        max_hits: int = 100,
        split_address: Literal[False] = False,
    ) -> list[BelagenhetsadressReference]: ...
    @overload
    def get_references_from_text(
        self,
        text: str,
        municipality: str | None = None,
        status: Literal["Gällande", "Reserverad"] | None = None,
        max_hits: int = 100,
        split_address: Literal[True] = False,
    ) -> list[BelagenhetsadressReferenceWithComponents]: ...
    def get_references_from_text(
        self,
        text: str,
        municipality: str | None = None,
        status: Literal["Gällande", "Reserverad"] | None = None,
        max_hits: int = 100,
        split_address: Literal[True, False] = False,
    ) -> list[BelagenhetsadressReference | BelagenhetsadressReferenceWithComponents]:
        """Get references to addresses matching a given text."""
        query = QUrlQuery()
        query.addQueryItem("adress", text)
        if municipality is not None:
            query.addQueryItem("kommunkod", municipality)
        if status is not None:
            query.addQueryItem("status", status)
        query.addQueryItem("maxHits", str(max_hits))
        query.addQueryItem("splitAdress", str(split_address).lower())

        result = self._get("/referens/fritext", query)
        if split_address:
            return [
                BelagenhetsadressReferenceWithComponents(
                    objektidentitet=item["objektidentitet"],
                    adress=item["adress"],
                    **item["adressComponents"],
                )
                for item in result
            ]
        else:
            return [BelagenhetsadressReference(**item) for item in result]

    @overload
    def get_references_from_geometry(
        self,
        geometry: QgsGeometry | QgsReferencedGeometry,
        buffer: int = 0,
        status: Literal["Gällande", "Reserverad"] | None = None,
        split_address: Literal[False] = False,
    ) -> list[BelagenhetsadressReference]: ...
    @overload
    def get_references_from_geometry(
        self,
        geometry: QgsGeometry | QgsReferencedGeometry,
        buffer: int = 0,
        status: Literal["Gällande", "Reserverad"] | None = None,
        split_address: Literal[True] = False,
    ) -> list[BelagenhetsadressReferenceWithComponents]: ...
    def get_references_from_geometry(
        self,
        geometry: QgsGeometry | QgsReferencedGeometry,
        buffer: int = 0,
        status: Literal["Gällande", "Reserverad"] | None = None,
        split_address: Literal[True, False] = False,
    ) -> list[BelagenhetsadressReference | BelagenhetsadressReferenceWithComponents]:
        """Get references to addresses matching a given geometry."""

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
        query.addQueryItem("splitAdress", str(split_address).lower())

        data = json.loads(geometry.asJson())
        data["crs"] = {
            "type": "name",
            "properties": {"name": geometry.crs().toOgcUrn()},
        }
        data = {"geometri": data, "buffer": buffer}

        result = self._post("/referens/geometri", query, data)
        if result is None:
            raise ValueError("Error retrieving references")
        if split_address:
            return [
                BelagenhetsadressReferenceWithComponents(
                    objektidentitet=item["objektidentitet"],
                    adress=item["adress"],
                    **item["adressComponents"],
                )
                for item in result
            ]
        else:
            return [BelagenhetsadressReference(**item) for item in result]

    def autocomplete(
        self,
        search: str,
        status: Literal["Gällande", "Reserverad"] | None = None,
        max_hits: int = 100,
    ) -> list[str]:
        query = QUrlQuery()
        query.addQueryItem("adress", search)
        if status is not None:
            query.addQueryItem("status", status)
        query.addQueryItem("maxHits", str(max_hits))

        return self._get("/autocomplete/adress", query)

    def autocomplete_references(self, *args, **kwargs):
        raise NotImplementedError()
