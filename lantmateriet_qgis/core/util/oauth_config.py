import json
from typing import Any, TypedDict

from qgis.core import QgsApplication, QgsAuthManager, QgsAuthMethodConfig


class GrantFlow:
    AUTH_CODE = 0
    IMPLICIT = 1
    RESOURCE_OWNER = 2
    AUTH_CODE_PKCE = 3
    CLIENT_CREDENTIALS = 4


class OAuth2ConfigData(TypedDict, total=False):
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


def _parse_oauth_config(payload: str | None) -> OAuth2ConfigData:
    """Parse the ``oauth2config`` payload of an authentication configuration.

    The authentication database is shared between all plugins, so the payload
    is not necessarily something this plugin wrote. Anything that is not a
    readable JSON object is treated as an empty configuration rather than
    raising.

    :param payload: raw ``oauth2config`` value, may be empty or invalid
    :type payload: str | None

    :return: parsed configuration, empty if the payload is unusable
    :rtype: OAuth2ConfigData
    """
    if not payload:
        return OAuth2ConfigData()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return OAuth2ConfigData()
    if not isinstance(data, dict):
        return OAuth2ConfigData()
    return OAuth2ConfigData(**data)


def get_scopes(config: OAuth2ConfigData) -> list[str]:
    """Return the scopes of an OAuth2 configuration.

    ``scope`` may be missing, ``null`` or an empty string depending on what
    wrote the configuration, so every one of those is read as "no scopes".

    :param config: OAuth2 configuration
    :type config: OAuth2ConfigData

    :return: scopes, empty if none are set
    :rtype: list[str]
    """
    scope = config.get("scope")
    if not isinstance(scope, str):
        return []
    return scope.split()


def load_oauth_config(authcfg: str) -> OAuth2ConfigData:
    auth_manager: QgsAuthManager = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    auth_manager.loadAuthenticationConfig(authcfg, config, True)
    return _parse_oauth_config(config.config("oauth2config"))


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
