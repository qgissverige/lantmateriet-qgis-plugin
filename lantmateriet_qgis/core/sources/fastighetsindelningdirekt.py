from qgis.core import QgsDataSourceUri, QgsVectorLayer


def provider(authcfg: str, base_url: str) -> QgsVectorLayer:
    uri = QgsDataSourceUri()
    uri.setAuthConfigId(authcfg)
    uri.setParam("url", f"{base_url}/ogc-features/v1/fastighetsindelning")
    uri.setParam("typeName", "registerenhetsomradesytor")

    return QgsVectorLayer(
        uri.uri(False), "Fastighetsindelning Direkt", "oapif", uri.providerName()
    )
