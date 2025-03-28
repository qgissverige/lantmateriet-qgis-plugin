"""Module os miscellaneous operating system interfaces, module logging used for debug,
module logging used for debug"""
import os
import logging
from qgis.PyQt import uic, QtWidgets
from qgis.core import QgsApplication, QgsAuthMethodConfig
from .. import config


# Konfigurera loggningsnivån
logging.basicConfig(level=logging.DEBUG)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dlg_access.ui'))

class ClassCreateAccessKeys(QtWidgets.QDialog, FORM_CLASS):
    """Create access keys"""
    def __init__(self, url):
        """ClassSubclassBrowserParentIdDialog Constructor"""
        super(ClassCreateAccessKeys, self).__init__()
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        self.logger = logging.getLogger(__name__)
        self.debug_mode = False
        self.url = url
        self.title_string = "Ange åtkomstnyckeL"
        #print(self.url)
        self.setupUi(self)
        self.init_gui()
        self.button_box_save.accepted.connect(self.save_credentials)
        self.button_box_save.rejected.connect(self.reject)
        self.newAuthCfgId = None

    def init_gui(self):
        """Initialize gui components and load data"""
        self.setWindowTitle(f"{self.title_string}")
        #self.show()

    def save_credentials(self):
        """Save user provided clientId and clientSecret
        and config_map from config.OAuthConfig"""
        client_id = self.line_edit_client_id.text()
        client_secret = self.m_line_edit_client_secret.text()

        auth_manager = QgsApplication.authManager()
        auth_config = QgsAuthMethodConfig()
        auth_config.setName(client_id)
        auth_config.setMethod("OAuth2") # Set the authentication method type
        config_map = config.OAuthConfig()
        config_map.set_value('clientId', client_id)
        config_map.set_value('clientSecret', client_secret)
        config_map.set_value('requestUrl', self.url)
        auth_config.setConfigMap(config_map.get_config_map())
        auth_manager.storeAuthenticationConfig(auth_config)
        auth_manager.updateConfigAuthMethods()
        self.newAuthCfgId = auth_config.id()
        if self.debug_mode:
            #self.logger.debug(f"Debug info:{auth_manager.availableAuthMethodConfigs()}")
            self.logger.debug("Debug info: %s", auth_manager.availableAuthMethodConfigs())
            self.logger.debug("Stored configuration ID: %s", self.newAuthCfgId)
        self.accept()
