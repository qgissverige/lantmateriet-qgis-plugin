from qgis.core import QgsCoordinateReferenceSystem


def is_supported_crs(crs: QgsCoordinateReferenceSystem | int | None) -> bool:
    if not isinstance(crs, int):
        crs = coerce_crs(crs)
    return 3006 <= crs <= 3018


def coerce_crs(crs: QgsCoordinateReferenceSystem | None) -> int | None:
    if crs is None:
        return 3006
    authid = crs.authid()
    if not authid.startswith("EPSG:"):
        raise ValueError(f"Unsupported CRS: {authid}")
    authid = int(authid[5:])
    if not is_supported_crs(authid):
        raise ValueError(f"Unsupported CRS: EPSG:{authid}")
    return authid
