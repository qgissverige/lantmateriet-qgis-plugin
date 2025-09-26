from pathlib import Path

from qgis.core import (
    QgsMessageLog,
    QgsSettingsTree,
    QgsStringUtils,
)
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon, QValidator
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.utils import iface

from lantmateriet_qgis.__about__ import (
    __icon_path__,
    __title__,
    __uri_homepage__,
)
from lantmateriet_qgis.config import URLConfig
from lantmateriet_qgis.core.settings import Settings
from lantmateriet_qgis.core.util.oauth_config import (
    load_oauth_config,
    store_oauth_config,
)
from lantmateriet_qgis.gui.dlg_access import CreateLMOAuthConfigurationDialog

FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "{}.ui".format(Path(__file__).stem)
)


class UrlValidator(QValidator):
    def validate(self, input: str, pos: int):
        if QgsStringUtils.isUrl(input):
            return QValidator.State.Acceptable, input, pos
        return QValidator.State.Intermediate, input, pos


def _auth_url(is_prod: bool, is_ver: bool) -> str | None:
    if is_prod:
        return URLConfig.LM_PROD_AUTH_URL
    elif is_ver:
        return URLConfig.LM_VER_AUTH_URL
    else:
        return None


class ConfigOptionsPage(FORM_CLASS, QgsOptionsPageWidget):
    """Settings form embedded into QGIS 'options' menu."""

    def __init__(self, parent):
        super().__init__(parent)

        # load UI and set objectName
        self.setupUi(self)
        self.setObjectName("mOptionsPage{}".format(__title__))

        self.line_edit_ngp_custom.setValidator(UrlValidator(self))
        self.line_edit_ovrig_custom.setValidator(UrlValidator(self))
        self.button_ngp_custom.toggled.connect(self.line_edit_ngp_custom.setEnabled)
        self.button_ovrig_custom.toggled.connect(self.line_edit_ovrig_custom.setEnabled)
        self.button_ngp_custom.toggled.connect(self.button_ngp_auth.setDisabled)
        self.button_ovrig_custom.toggled.connect(self.button_ovrig_auth.setDisabled)

        self.button_ngp_auth.clicked.connect(self.enter_keys_ngp)
        self.button_ovrig_auth.clicked.connect(self.enter_keys_ovrig)

        self.button_add_connections.clicked.connect(self.add_to_connections)
        self.button_validate.clicked.connect(self.validate)

        self.load_settings()

    def enter_keys_ngp(self):
        url_base = _auth_url(
            self.button_ngp_prod.isChecked(), self.button_ngp_ver.isChecked()
        )
        if url_base is None:
            return
        dlg = CreateLMOAuthConfigurationDialog(
            url_base, "PROD" if self.button_ngp_prod.isChecked() else "VER", self
        )
        if dlg.exec() == CreateLMOAuthConfigurationDialog.Accepted:
            self.auth_ngp.setConfigId("")
            self.auth_ngp.setConfigId(dlg.new_auth_cfg_id)

    def enter_keys_ovrig(self):
        url_base = _auth_url(
            self.button_ovrig_prod.isChecked(), self.button_ovrig_ver.isChecked()
        )
        if url_base is None:
            return
        dlg = CreateLMOAuthConfigurationDialog(
            url_base, "VER" if self.button_ovrig_ver.isChecked() else "PROD", self
        )
        if dlg.exec() == CreateLMOAuthConfigurationDialog.Accepted:
            self.auth_ovrig.setConfigId("")
            self.auth_ovrig.setConfigId(dlg.new_auth_cfg_id)

    def _to_settings(self) -> Settings:
        s = Settings()

        s.ngp_enabled = self.group_box_ngp.isChecked()
        s.ngp_authcfg = self.auth_ngp.configId()
        if self.button_ngp_prod.isChecked():
            s.ngp = "production"
        elif self.button_ngp_ver.isChecked():
            s.ngp = "verification"
        else:
            s.ngp = self.line_edit_ngp_custom.text()

        s.ovrig_enabled = self.group_box_ovrig.isChecked()
        s.ovrig_authcfg = self.auth_ovrig.configId()
        if self.button_ovrig_prod.isChecked():
            s.ovrig = "production"
        elif self.button_ovrig_ver.isChecked():
            s.ovrig = "verification"
        else:
            s.ovrig = self.line_edit_ovrig_custom.text()

        s.fastighetsindelning_direkt_enabled = (
            self.button_fastighetsindelning_direkt.isChecked()
        )
        s.belagenhetsadress_direkt_enabled = (
            self.button_belagenhetsadress_direkt.isChecked()
        )
        s.fastighet_direkt_enabled = self.button_fastighet_direkt.isChecked()
        s.registerbeteckning_direkt_enabled = (
            self.button_registerbeteckning_direkt.isChecked()
        )
        s.gemensamhetsanlaggning_direkt_enabled = (
            self.button_gemensamhetsanlaggning_direkt.isChecked()
        )
        s.ortofoto_nedladdning_enabled = self.button_ortofoto_nedladdning.isChecked()
        s.hojdgrid_nedladdning_enabled = self.button_hojdgrid_nedladdning.isChecked()

        return s

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""

        s = self._to_settings()
        QgsMessageLog.logMessage(f"Storing settings: {repr(s)}")
        s.store_to_settings()

        if (
            s.ovrig_enabled
            and s.ovrig in ("production", "verification")
            and s.ovrig_authcfg
        ):
            config = load_oauth_config(s.ovrig_authcfg)
            required_scopes = []
            if s.fastighetsindelning_direkt_enabled:
                required_scopes.append("ogc-features:fastighetsindelning.read")
            if s.fastighet_direkt_enabled:
                required_scopes.append("fastighetochsamfallighet_direkt_v31_read")
            if s.registerbeteckning_direkt_enabled:
                required_scopes.append("registerbeteckning_direkt_v5_read")
            if s.gemensamhetsanlaggning_direkt_enabled:
                required_scopes.append("gemensamhetsanlaggning_direkt_v21_read")
            if s.belagenhetsadress_direkt_enabled:
                required_scopes.append("belagenhetsadress_direkt_v42_read")
            existing_scopes = config.get("scope", "").split(" ")
            missing_scopes = set(required_scopes) - set(existing_scopes)
            if missing_scopes:
                res = QMessageBox.warning(
                    self,
                    self.tr("Lägg till scopes"),
                    self.tr(
                        "Följande scopes saknas i autentisering: {0}. Vill du lägga till dem?"
                    ).format(", ".join(missing_scopes)),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                )
                if res == QMessageBox.StandardButton.Yes:
                    config["scope"] = " ".join(existing_scopes + list(missing_scopes))
                    store_oauth_config(s.ovrig_authcfg, config)

    def validate(self):
        s = self._to_settings()
        errors = s.validate()
        if len(errors) > 0:
            msg = self.tr("Följande fel har hittats i konfigurationen:") + "\n"
            for error in errors:
                msg += "\n• " + error
            QMessageBox.warning(self, self.tr("Fel i konfigurationen"), msg)
        else:
            QMessageBox.information(
                self,
                self.tr("Konfigurationen är korrekt"),
                self.tr("Konfigurationen är korrekt."),
            )

    def get_existing_stac_connection_keys(self):
        # Get STAC connections node
        stac_settings_node = QgsSettingsTree.node("connections").childNode("stac")

        return stac_settings_node.items()

    def get_existing_oapif_connection_keys(self):
        # Get WFS/OAPIF connections node
        oapif_settings_node = (
            QgsSettingsTree.node("connections")
            .childNode("ows")
            .childNode("connections")
        )

        return oapif_settings_node.items(["wfs"])

    def select_connections(self, stac_connections: dict, oapif_connections: dict):
        dialog = QDialog()
        dialog.setWindowTitle("Välj tjänster att lägga till i browsern")
        layout = QVBoxLayout()

        label = QLabel("STAC:")
        layout.addWidget(label)
        checkboxes_stac = {}
        stac_keys = self.get_existing_stac_connection_keys()
        for key in stac_connections:
            checkbox = QCheckBox(key, dialog)
            checkboxes_stac[key] = checkbox
            # Check if connection already exists, then disable since connections can't be removed once added
            for stac_key in stac_keys:
                if stac_key == key:
                    checkbox.setChecked(True)
                    checkbox.setEnabled(False)
            layout.addWidget(checkbox)

        label = QLabel("OGC API Features:")
        layout.addWidget(label)
        checkboxes_oapif = {}
        oapif_keys = self.get_existing_oapif_connection_keys()
        for key in oapif_connections:
            checkbox = QCheckBox(key, dialog)
            checkboxes_oapif[key] = checkbox
            # Check if connection already exists, then disable since connections can't be removed once added
            for oapif_key in oapif_keys:
                if oapif_key == key:
                    checkbox.setChecked(True)
                    checkbox.setEnabled(False)
            layout.addWidget(checkbox)

        button_layout = QVBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Cancel", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        dialog.setLayout(layout)

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            checked_stac_connections = {
                key: checkbox.isChecked() for key, checkbox in checkboxes_stac.items()
            }
            checked_oapif_connections = {
                key: checkbox.isChecked() for key, checkbox in checkboxes_oapif.items()
            }
            return checked_stac_connections, checked_oapif_connections
        else:
            return None, None  # Cancel pressed

    def add_to_connections(self):
        """Create connection settings, base urls, service names"""

        s = self._to_settings()
        if len(s.validate()) > 0:
            QMessageBox.warning(
                self,
                self.tr("Lägg till tjänster"),
                self.tr(
                    "Det finns fel i konfigurationen, verifiera och spara den på nytt."
                ),
            )
            return

        stac_connections: dict[str, tuple[str, str]] = dict()
        oapif_connections: dict[str, tuple[str, str]] = dict()
        if s.ngp_enabled:
            stac_connections["NGP Detaljplan"] = (
                s.ngp_url + URLConfig.NGP_STAC_DETALJPLAN,
                s.ngp_authcfg,
            )
            stac_connections["NGP Byggnad"] = (
                s.ngp_url + URLConfig.NGP_STAC_BYGGNAD,
                s.ngp_authcfg,
            )
            stac_connections["NGP Kulturhistorisk lämning"] = (
                s.ngp_url + URLConfig.NGP_STAC_KULTURHISTORISK_LAMNING,
                s.ngp_authcfg,
            )
            stac_connections["NGP Gräns för fjällnära skog"] = (
                s.ngp_url + URLConfig.NGP_STAC_GRANS_FOR_FJALLNARA_SKOG,
                s.ngp_authcfg,
            )
        if s.ovrig_enabled and s.ortofoto_nedladdning_enabled:
            stac_connections["Ortofoton Nedladdning"] = (
                s.ovrig_url + URLConfig.LM_STAC_ORTO_NEDLADD,
                s.ovrig_authcfg,
            )
        if s.ovrig_enabled and s.hojdgrid_nedladdning_enabled:
            stac_connections["Markhöjdmodell Nedladdning"] = (
                s.ovrig_url + URLConfig.LM_STAC_HOJDGRID_NEDLADD,
                s.ovrig_authcfg,
            )
        if s.ovrig_enabled and s.fastighetsindelning_direkt_enabled:
            oapif_connections["Fastighetsindelning Direkt"] = (
                s.ovrig_url + URLConfig.LM_OAPIF_FASTIGHETSINDELNING_DIREKT,
                s.ovrig_authcfg,
            )

        oapif_connections.update(stac_connections)

        # Let user decide which connections to add
        selected_connections_stac, selected_connections_oapif = self.select_connections(
            stac_connections, oapif_connections
        )

        # User pressed cancel
        if selected_connections_stac is None and selected_connections_oapif is None:
            return

        # Only add selected connections
        if selected_connections_stac is not None:
            for key, checked in selected_connections_stac.items():
                if not checked:
                    stac_connections.pop(key, None)

        if selected_connections_oapif is not None:
            for key, checked in selected_connections_oapif.items():
                if not checked:
                    oapif_connections.pop(key, None)

        # Get STAC connections node
        stac_settings_node = QgsSettingsTree.node("connections").childNode("stac")

        # Get WFS/OAPIF connections node
        dyn_param = ["wfs"]
        oapif_settings_node = (
            QgsSettingsTree.node("connections")
            .childNode("ows")
            .childNode("connections")
        )

        # Check if a connection already exists with the same name and if it differs in authcfg or url. If so, let user decide what to do.
        keys = self.get_existing_stac_connection_keys()
        for key in keys:
            item = stac_connections.get(key, None)
            if item is not None:
                url, authcfg = item
                existing_url = stac_settings_node.childSetting("url").value(key)
                existing_authcfg = stac_settings_node.childSetting("authcfg").value(key)
                if url != existing_url or authcfg != existing_authcfg:
                    msg = self.tr(
                        "Tjänsten {0} finns redan men med en annan autentisering eller url. Vill du skriva över?"
                    ).format(key)
                    res = QMessageBox.warning(
                        self,
                        self.tr("Spara tjänster"),
                        msg,
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Cancel,
                    )
                    if res == QMessageBox.StandardButton.No:
                        stac_connections.pop(key)
                    elif res == QMessageBox.StandardButton.Cancel:
                        return

        keys = self.get_existing_oapif_connection_keys()
        for key in keys:
            item = oapif_connections.get(key, None)
            if item is not None:
                url, authcfg = item
                existing_url = oapif_settings_node.childSetting("url").value(
                    [dyn_param[0], key]
                )
                existing_authcfg = oapif_settings_node.childSetting("authcfg").value(
                    [dyn_param[0], key]
                )
                if url != existing_url or authcfg != existing_authcfg:
                    msg = self.tr(
                        "Tjänsten {0} finns redan men med en annan autentisering eller url. Vill du skriva över?"
                    ).format(key)
                    res = QMessageBox.warning(
                        self,
                        self.tr("Spara tjänster"),
                        msg,
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Cancel,
                    )
                    if res == QMessageBox.StandardButton.No:
                        oapif_connections.pop(key)
                    elif res == QMessageBox.StandardButton.Cancel:
                        return

        # Create the connection(s)
        for connection_name, (url, authcfg) in stac_connections.items():
            stac_settings_node.childSetting("url").setValue(url, connection_name)
            stac_settings_node.childSetting("authcfg").setValue(
                authcfg, connection_name
            )

        for connection_name, (url, authcfg) in oapif_connections.items():
            oapif_settings_node.childSetting("url").setValue(
                url, ["wfs", connection_name]
            )
            oapif_settings_node.childSetting("authcfg").setValue(
                authcfg, ["wfs", connection_name]
            )
            # TODO: behöver andra inställningar skapas enligt default?

        # Refresh connections
        iface.mainWindow().findChildren(QWidget, "Browser")[0].refresh()

    def load_settings(self):
        """Load options from QgsSettings into UI form."""

        s = Settings.load_from_settings()
        QgsMessageLog.logMessage(f"Loaded settings: {repr(s)}")

        self.group_box_ngp.setChecked(s.ngp_enabled)
        if s.ngp == "production":
            self.button_ngp_prod.setChecked(True)
            self.line_edit_ngp_custom.setText("")
        elif s.ngp == "verification":
            self.button_ngp_ver.setChecked(True)
            self.line_edit_ngp_custom.setText("")
        else:
            self.button_ngp_custom.setChecked(True)
            self.line_edit_ngp_custom.setText(s.ngp)
        self.auth_ngp.setConfigId(s.ngp_authcfg)

        self.group_box_ovrig.setChecked(s.ovrig_enabled)
        if s.ovrig == "production":
            self.button_ovrig_prod.setChecked(True)
            self.line_edit_ovrig_custom.setText("")
        elif s.ovrig == "verification":
            self.button_ovrig_ver.setChecked(True)
            self.line_edit_ovrig_custom.setText("")
        else:
            self.button_ovrig_custom.setChecked(True)
            self.line_edit_ovrig_custom.setText(s.ovrig)
        self.auth_ovrig.setConfigId(s.ovrig_authcfg)

        self.button_fastighetsindelning_direkt.setChecked(
            s.fastighetsindelning_direkt_enabled
        )
        self.button_belagenhetsadress_direkt.setChecked(
            s.belagenhetsadress_direkt_enabled
        )
        self.button_fastighet_direkt.setChecked(s.fastighet_direkt_enabled)
        self.button_registerbeteckning_direkt.setChecked(
            s.registerbeteckning_direkt_enabled
        )
        self.button_gemensamhetsanlaggning_direkt.setChecked(
            s.gemensamhetsanlaggning_direkt_enabled
        )
        self.button_ortofoto_nedladdning.setChecked(s.ortofoto_nedladdning_enabled)
        self.button_hojdgrid_nedladdning.setChecked(s.hojdgrid_nedladdning_enabled)


class PluginOptionsWidgetFactory(QgsOptionsWidgetFactory):
    """Factory for options widget."""

    def __init__(self):
        """Constructor."""
        super().__init__()

    def icon(self) -> QIcon:
        """Returns plugin icon, used to as tab icon in QGIS options tab widget.

        :return: _description_
        :rtype: QIcon
        """
        return QIcon(str(__icon_path__))

    def createWidget(self, parent: QWidget = None) -> ConfigOptionsPage:
        """Create settings widget.

        :param parent: Qt parent where to include the options page.
        :type parent: QObject

        :return: options page for tab widget
        :rtype: ConfigOptionsPage
        """
        return ConfigOptionsPage(parent)

    def title(self) -> str:
        """Returns plugin title, used to name the tab in QGIS options tab widget.

        :return: plugin title from about module
        :rtype: str
        """
        return __title__

    def helpId(self) -> str:
        """Returns plugin help URL.

        :return: plugin homepage url from about module
        :rtype: str
        """
        return __uri_homepage__
