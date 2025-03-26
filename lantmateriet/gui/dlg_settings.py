#! python3  # noqa: E265

"""
    Plugin settings form integrated into QGIS 'Options' menu.
"""

# standard
import platform
from functools import partial
from pathlib import Path
from urllib.parse import quote

# PyQGIS
from qgis.core import Qgis, QgsApplication, QgsSettings, QgsSettingsTree, QgsBrowserModel
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.Qt import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QMessageBox

# project
from lantmateriet.__about__ import (
    __icon_path__,
    __title__,
    __uri_homepage__,
    __uri_tracker__,
    __version__,
)
from lantmateriet.toolbelt import PlgLogger, PlgOptionsManager
from lantmateriet.toolbelt.preferences import PlgSettingsStructure

# ############################################################################
# ########## Globals ###############
# ##################################

FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "{}.ui".format(Path(__file__).stem)
)


# ############################################################################
# ########## Classes ###############
# ##################################


class ConfigOptionsPage(FORM_CLASS, QgsOptionsPageWidget):
    """Settings form embedded into QGIS 'options' menu."""

    def __init__(self, parent):
        super().__init__(parent)
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager()

        # load UI and set objectName
        self.setupUi(self)
        self.setObjectName("mOptionsPage{}".format(__title__))

        report_context_message = quote(
            "> Reported from plugin settings\n\n"
            f"- operating system: {platform.system()} "
            f"{platform.release()}_{platform.version()}\n"
            f"- QGIS: {Qgis.QGIS_VERSION}"
            f"- plugin version: {__version__}\n"
        )

        # header
        self.lbl_title.setText(f"{__title__} - Version {__version__}")

        # customization
        self.btn_help.setIcon(QIcon(QgsApplication.iconPath("mActionHelpContents.svg")))
        self.btn_help.pressed.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )


        self.btn_report.setIcon(
            QIcon(QgsApplication.iconPath("console/iconSyntaxErrorConsole.svg"))
        )
        
        self.btn_report.pressed.connect(
            partial(QDesktopServices.openUrl, QUrl(f"{__uri_tracker__}new/choose"))
        )
        


        self.btn_reset.setIcon(QIcon(QgsApplication.iconPath("mActionUndo.svg")))
        self.btn_reset.pressed.connect(self.reset_settings)

        # initiate settings
        #s = QgsSettings()
        #self.enable_annotations.setChecked(int(s.value('/plugins/slyr/enable_annotations', 0)))
        #self.checkBox_fast_direkt.setChecked(int(s.value('/plugins/lantmateriet/lm_hojd_enabled', 0)))
        #self.checkBox_fast_direkt.setChecked(int(s.value("/plugins/lantmateriet/lm_fastighet_direkt_enabled", 0)))
        

        # load previously saved settings
        self.load_settings()

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        settings = self.plg_settings.get_plg_settings()
        s = QgsSettings()
        #s.setValue("/plugins/lantmateriet/mytext", "hello world")
        
        #Nationella geodataplattformen
        s.setValue("/plugins/lantmateriet/lm_ngp_authcfg", "1lmgy5x") # TODO: hämta in authcfg dynamiskt
        s.setValue("/plugins/lantmateriet/lm_ngp_prod_enabled", 0 if not self.rb_ngdp_lmprod.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_ngp_ver_enabled", 0 if not self.rb_ngdp_lmver.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_ngp_egen_enabled", 0 if not self.rb_ngdp_lm_egenurl.isChecked() else 1)
        if self.rb_ngdp_lm_egenurl.isChecked():
            s.setValue("/plugins/lantmateriet/lm_ngp_egen_url", "https://egen.proxy.se") # TODO: läsa in från GUI

        #Övriga tjänster
        s.setValue("/plugins/lantmateriet/lm_ovr_authcfg", "1lmgy5x") # TODO: hämta in authcfg dynamiskt
        s.setValue("/plugins/lantmateriet/lm_ovr_prod_enabled", 0 if not self.rb_ovrig_prod.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_ovr_ver_enabled", 0 if not self.rb_ovrig_ver.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_ovr_egen_enabled", 0 if not self.rb_ovrig_lm_egenurl.isChecked() else 1)
        if self.rb_ovrig_lm_egenurl.isChecked():
            s.setValue("/plugins/lantmateriet/lm_ovr_egen_url", "https://egen.proxy.se") # TODO: läsa in från GUI     
        
        #Tjänster
        s.setValue("/plugins/lantmateriet/lm_fastighet_direkt_enabled", 0 if not self.checkBox_fast_direkt.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_belagenhet_direkt_enabled", 0 if not self.checkBox_bel_adress_direkt.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_fast_samf_direkt_enabled", 0 if not self.checkBox_fast_samf_direkt.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_orto_nedladd_enabled", 0 if not self.checkBox_ortofoto_nedladdning.isChecked() else 1)
        s.setValue("/plugins/lantmateriet/lm_hojdgrid_nedladd_enabled", 0 if not self.checkBox_hojdgrid_nedladdning.isChecked() else 1)

        #self.mGroupBox.setChecked(False)
        #self.mGroupBox.setEnabled(True)


        # misc
        settings.debug_mode = self.opt_debug.isChecked()
        settings.version = __version__

        # dump new settings into QgsSettings
        self.plg_settings.save_from_object(settings)

        # Automatically create LM connections based on settings
        self.add_to_connections()

        if __debug__:
            self.log(
                message="DEBUG - Settings successfully saved.",
                log_level=4,
            )

    def add_to_connections(self):

        lm_prod_url = "https://api.lantmateriet.se"
        lm_ver_url = "https://api.lantmateriet-ver.se"

        # Read plugin settings
        settings = QgsSettings()

        lm_ovr_authcfg = settings.value("/plugins/lantmateriet/lm_ovriga_authcfg")
        lm_ngp_authcfg = settings.value("/plugins/lantmateriet/lm_ngp_authcfg")
        
        lm_ngp_prod_enabled = settings.value("/plugins/lantmateriet/lm_ngp_prod_enabled")
        lm_ngp_ver_enabled = settings.value("/plugins/lantmateriet/lm_ngp_ver_enabled")
        lm_ngp_egen_enabled = settings.value("/plugins/lantmateriet/lm_ngp_egen_enabled")

        lm_ovr_prod_enabled = settings.value("/plugins/lantmateriet/lm_ovr_prod_enabled")
        lm_ovr_ver_enabled = settings.value("/plugins/lantmateriet/lm_ovr_ver_enabled")
        lm_ovr_egen_enabled = settings.value("/plugins/lantmateriet/lm_ovr_egen_enabled")
        
        lm_fastighet_direkt_enabled = settings.value("/plugins/lantmateriet/lm_fastighet_direkt_enabled")
        lm_belagenhet_direkt_enabled = settings.value("/plugins/lantmateriet/lm_belagenhet_direkt_enabled")
        lm_fast_samf_direkt_enabled = settings.value("/plugins/lantmateriet/lm_fast_samf_direkt_enabled")
        lm_orto_nedladd_enabled = settings.value("/plugins/lantmateriet/lm_orto_nedladd_enabled")
        lm_hojdgrid_nedladd_enabled = settings.value("/plugins/lantmateriet/lm_hojdgrid_nedladd_enabled")

        # TODO: how to best store list of service names
        stac_snames = ["Höjdgrid nedladdning", 
                       "Ortofoton nedladdning", 
                       "Belägenhetsadress direkt", 
                       "Fastighetsindelning direkt",
                       "Fastighet och samfällighet direkt"]
        
        oapif_snames= ["Detaljplan",
                       "Byggnad",
                       "Kulturhistorisk lämning",
                       "Gräns för fjällnära skog"]
        
        # TODO: felhantering, om t.ex. autentisering saknas borde det inte gå att spara
        """if not lm_ovr_authcfg or lm_ngp_authcfg:
            # If no auth we can not configure connections
            return"""

        lm_ngp_baseurl = ""
        if lm_ngp_prod_enabled:
            lm_ngp_baseurl = lm_prod_url
        elif lm_ngp_ver_enabled:
            lm_ngp_baseurl = lm_ver_url
        elif lm_ngp_egen_enabled:
            lm_ngp_baseurl = settings.value("/plugins/lantmateriet/lm_ngp_egen_url")  
        
        lm_ovr_baseurl = ""
        if lm_ovr_prod_enabled:
            lm_ovr_baseurl = lm_prod_url
        elif lm_ovr_ver_enabled:
            lm_ovr_baseurl = lm_ver_url
        elif lm_ovr_egen_enabled:
            lm_ovr_baseurl = settings.value("/plugins/lantmateriet/lm_ovr_egen_url") 
         
        # Create STAC connection urls based on users settings
        stac_connections = {}
        if int(lm_fastighet_direkt_enabled):
            stac_connections["Fastighetsindelning direkt"] = lm_ovr_baseurl + "/stac-vektor/v1/collections/fastighetsindelning"
        if int(lm_belagenhet_direkt_enabled):
            stac_connections["Belägenhetsadress direkt"] = lm_ovr_baseurl + "/stac-vektor/v1/collections/belagenhetsadresser"
        if int(lm_orto_nedladd_enabled):
            stac_connections["Ortofoton nedladdning"] = lm_ovr_baseurl + "/stac-bild/v1"
        if int(lm_hojdgrid_nedladd_enabled):
            stac_connections["Höjdgrid nedladdning"] = lm_ovr_baseurl + "/stac-hojd/v1"
        # TODO: vad är endpoint för Fastighet och samfällighet direkt?
        """if lm_belagenhet_direkt_enabled:
            connections["Fastighet och samfällighet direkt"] = lm_ovriga_baseurl + "TBD"""

        # And for OGC API features
        oapif_connections = {
            "Detaljplan": lm_ngp_baseurl + "/distribution/geodatakatalog/sokning/v1/detaljplan/v2",
            "Byggnad": lm_ngp_baseurl + "/distribution/geodatakatalog/sokning/v1/byggnad/v1",
            "Kulturhistorisk lämning": lm_ngp_baseurl + "/geodatakatalog/sokning/v1/kulturhistorisklamning/v1",
            "Gräns för fjällnära skog": lm_ngp_baseurl + "/distribution/geodatakatalog/sokning/v1/gransforfjallnaraskog/v1",
        }
        
        # Get STAC connections node
        stac_settings_node = (
            QgsSettingsTree.node("connections")
                .childNode("stac")
        )

        # Get WFS/OAPIF connections node
        dyn_param = ["wfs"]
        oapif_settings_node = (
            QgsSettingsTree.node("connections")
                .childNode("ows")
                .childNode("connections")
        )
        
        # Check if a connection alread exists with same name and if it differsn in authcfg or url. If so, let user decide what to do. 
        keys = stac_settings_node.items()
        for key in keys:
            if key in stac_snames:
                url = stac_settings_node.childSetting("url").value(key)
                authcfg = stac_settings_node.childSetting("authcfg").value(key)
                updated_url = stac_connections[key]
                if url != updated_url or authcfg != lm_ovr_authcfg:
                    msg = self.tr("Tjänsten {0} finns redan men med en annan autentisering eller url. Vill du skriva över?").format(key)
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

        keys = oapif_settings_node.items(dyn_param)
        for key in keys:
            if key in oapif_snames:
                url = oapif_settings_node.childSetting("url").value(key)
                authcfg = oapif_settings_node.childSetting("authcfg").value(key)
                updated_url = oapif_connections[key]
                if url != updated_url or authcfg != lm_ngp_authcfg:
                    msg = self.tr("Tjänsten {0} finns redan men med en annan autentisering eller url. Vill du skriva över?").format(key)
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
        for connection_name in stac_connections:
            stac_settings_node.childSetting("url").setValue(stac_connections[connection_name], connection_name)
            stac_settings_node.childSetting("authcfg").setValue(lm_ovr_authcfg, connection_name)
            # Also add as OGC API Features
            dyn_param.append(connection_name)
            oapif_settings_node.childSetting("url").setValue(stac_connections[connection_name], dyn_param)
            oapif_settings_node.childSetting("authcfg").setValue(lm_ovr_authcfg, dyn_param)
            dyn_param.remove(connection_name)

        for connection_name in oapif_connections:
            dyn_param.append(connection_name)
            oapif_settings_node.childSetting("url").setValue(oapif_connections[connection_name], dyn_param)
            oapif_settings_node.childSetting("authcfg").setValue(lm_ovr_authcfg, dyn_param)
            # TODO: behöver andra inställningar skapas enligt default?
            dyn_param.remove(connection_name)
                
        # Refresh connections
        # TODO: call to iface crashes QGIS...
        """items = iface.browserModel().rootItems()
        stac_connection = [item for item in items if 'stac' in str(item)]
        if stac_connection is not None:
            #Can there be only one?
            stac_connection[0].refreshConnections("STAC")"""

    def load_settings(self):
        """Load options from QgsSettings into UI form."""
        settings = self.plg_settings.get_plg_settings()
        #print(f"row116: {dir(settings)}")

        # global
        self.opt_debug.setChecked(settings.debug_mode)
        self.lbl_version_saved_value.setText(settings.version)

        # initiate settings
        s = QgsSettings()
        #self.enable_annotations.setChecked(int(s.value('/plugins/slyr/enable_annotations', 0)))
        #self.checkBox_fast_direkt.setChecked(int(s.value('/plugins/lantmateriet/lm_hojd_enabled', 0)))
        self.checkBox_fast_direkt.setChecked(int(s.value("/plugins/lantmateriet/lm_fastighet_direkt_enabled", 0)))
        self.checkBox_bel_adress_direkt.setChecked(int(s.value("/plugins/lantmateriet/lm_belagenhet_direkt_enabled", 0)))
        self.checkBox_fast_samf_direkt.setChecked(int(s.value("/plugins/lantmateriet/lm_fast_samf_direkt_enabled", 0)))
        self.checkBox_ortofoto_nedladdning.setChecked(int(s.value("/plugins/lantmateriet/lm_orto_nedladd_enabled", 0)))
        self.checkBox_hojdgrid_nedladdning.setChecked(int(s.value("/plugins/lantmateriet/lm_hojdgrid_nedladd_enabled", 0)))

        self.rb_ngdp_lmprod.setChecked(int(s.value("/plugins/lantmateriet/lm_ngp_prod_enabled", 0)))
        self.rb_ovrig_prod.setChecked(int(s.value("/plugins/lantmateriet/lm_ovr_prod_enabled", 0)))

        self.rb_ngdp_lmver.setChecked(int(s.value("/plugins/lantmateriet/lm_ngp_ver_enabled", 0)))
        self.rb_ovrig_ver.setChecked(int(s.value("/plugins/lantmateriet/lm_ovr_ver_enabled", 0)))

        self.rb_ngdp_lm_egenurl.setChecked(int(s.value("/plugins/lantmateriet/lm_ngp_egen_enabled", 0)))
        self.rb_ovrig_lm_egenurl.setChecked(int(s.value("/plugins/lantmateriet/lm_ovr_egen_enabled", 0)))
        

    def reset_settings(self):
        """Reset settings to default values (set in preferences.py module)."""
        default_settings = PlgSettingsStructure()

        # dump default settings into QgsSettings
        self.plg_settings.save_from_object(default_settings)

        # update the form
        self.load_settings()

class PlgOptionsFactory(QgsOptionsWidgetFactory):
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

    def createWidget(self, parent) -> ConfigOptionsPage:
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

