import json
from typing import Any, TypedDict

from qgis.core import QgsApplication, QgsAuthManager, QgsAuthMethodConfig


class GrantFlow:
    AUTH_CODE = 0
    IMPLICIT = 1
    RESOURCE_OWNER = 2
    AUTH_CODE_PKCE = 3
    CLIENT_CREDENTIALS = 4


class OAuth2ConfigData(TypedDict):
    accessMethod: int
    apiKey: str
    clientId: str
    clientSecret: str
    configType: int
    customHeader: str
    extraTokens: dict[str, Any]
    description: str
    grantFlow: int
    id: str
    name: str
    objectName: str
    password: str
    persistToken: bool
    queryPairs: dict[str, Any]
    redirectHost: str
    redirectPort: int
    redirectUrl: str
    refreshTokenUrl: str
    requestTimeout: int
    requestUrl: str
    scope: str
    tokenUrl: str
    username: str
    version: int


def load_oauth_config(authcfg: str) -> OAuth2ConfigData:
    auth_manager: QgsAuthManager = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    auth_manager.loadAuthenticationConfig(authcfg, config, True)
    data = json.loads(config.config("oauth2config"))
    return OAuth2ConfigData(**data)


def store_oauth_config(authcfg: str, data: OAuth2ConfigData):
    auth_manager: QgsAuthManager = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    auth_manager.loadAuthenticationConfig(authcfg, config, True)
    config.setConfigMap(
        dict(
            oauth2config=json.dumps(data),
        )
    )
    auth_manager.storeAuthenticationConfig(config, overwrite=True)
    auth_manager.updateConfigAuthMethods()
