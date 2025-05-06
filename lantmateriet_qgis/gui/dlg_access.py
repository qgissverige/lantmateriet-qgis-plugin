import json
import os

from qgis.core import Qgis, QgsApplication, QgsAuthManager, QgsAuthMethodConfig
from qgis.PyQt import QtWidgets, uic

from lantmateriet_qgis.core.util.oauth_config import GrantFlow

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "dlg_access.ui"))


class CreateLMOAuthConfigurationDialog(QtWidgets.QDialog, FORM_CLASS):
    """Create access keys"""

    def __init__(self, base_url: str, name_base: str):
        super(CreateLMOAuthConfigurationDialog, self).__init__()
        self.base_url = base_url
        self.name_base = name_base
        self.setupUi(self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.helpRequested.connect(lambda: None)
        self.new_auth_cfg_id = None

    def accept(self):
        """Save user provided clientId and clientSecret
        and config_map from config.OAuthConfig"""
        client_id = self.line_edit_client_id.text()
        client_secret = self.line_edit_client_secret.text()

        auth_manager: QgsAuthManager = QgsApplication.authManager()
        auth_config = QgsAuthMethodConfig()
        auth_config.setName(f"LM {self.name_base} ({client_id})")
        auth_config.setMethod("OAuth2")  # Set the authentication method type
        auth_config.setConfigMap(
            dict(
                oauth2config=json.dumps(
                    dict(
                        clientId=client_id,
                        clientSecret=client_secret,
                        requestUrl=self.base_url + "authorize",
                        tokenUrl=self.base_url + "token",
                        grantFlow=GrantFlow.CLIENT_CREDENTIALS
                        if Qgis.versionInt() >= 34300
                        else GrantFlow.AUTH_CODE_PKCE,
                    )
                )
            )
        )
        auth_manager.storeAuthenticationConfig(auth_config)
        auth_manager.updateConfigAuthMethods()
        self.new_auth_cfg_id = auth_config.id()

        super().accept()
