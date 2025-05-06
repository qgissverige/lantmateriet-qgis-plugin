from dataclasses import dataclass
from typing import Literal, Self

from qgis.core import QgsApplication, QgsAuthManager, QgsSettings, QgsStringUtils

from lantmateriet_qgis.config import URLConfig
from lantmateriet_qgis.core.util.oauth_config import GrantFlow, load_oauth_config


@dataclass
class Settings:
    ngp_enabled: bool = False
    ngp_authcfg: str = ""
    ngp: Literal["production", "verification"] | str = "production"

    ovrig_enabled: bool = False
    ovrig_authcfg: str = ""
    ovrig: Literal["production", "verification"] | str = "production"

    fastighetsindelning_direkt_enabled: bool = False
    belagenhetsadress_direkt_enabled: bool = False
    fastighet_direkt_enabled: bool = False
    registerbeteckning_direkt_enabled: bool = False
    gemensamhetsanlaggning_direkt_enabled: bool = False
    ortofoto_nedladdning_enabled: bool = False
    hojdgrid_nedladdning_enabled: bool = False

    @property
    def ngp_url(self) -> str:
        if self.ngp == "production":
            return URLConfig.LM_PROD_URL
        elif self.ngp == "verification":
            return URLConfig.LM_VER_URL
        else:
            return self.ngp

    @property
    def ovrig_url(self) -> str:
        if self.ovrig == "production":
            return URLConfig.LM_PROD_URL
        elif self.ovrig == "verification":
            return URLConfig.LM_VER_URL
        else:
            return self.ovrig

    @classmethod
    def load_from_settings(cls) -> Self:
        settings = QgsSettings()
        settings.beginGroup("lantmateriet", QgsSettings.Plugins)
        return cls(
            ngp_enabled=bool(settings.value("ngp_enabled", False)),
            ngp_authcfg=settings.value("ngp_authcfg", ""),
            ngp=settings.value("ngp", "production"),
            ovrig_enabled=bool(settings.value("ovrig_enabled", False)),
            ovrig_authcfg=settings.value("ovrig_authcfg", ""),
            ovrig=settings.value("ovrig", "production"),
            fastighetsindelning_direkt_enabled=bool(
                settings.value("fastighetsindelning_direkt_enabled", False)
            ),
            belagenhetsadress_direkt_enabled=bool(
                settings.value("belagenhetsadress_direkt_enabled", False)
            ),
            fastighet_direkt_enabled=bool(
                settings.value("fastighet_direkt_enabled", False)
            ),
            registerbeteckning_direkt_enabled=bool(
                settings.value("registerbeteckning_direkt_enabled", False)
            ),
            gemensamhetsanlaggning_direkt_enabled=bool(
                settings.value("gemensamhetsanlaggning_direkt_enabled", False)
            ),
            ortofoto_nedladdning_enabled=bool(
                settings.value("ortofoto_nedladdning_enabled", False)
            ),
            hojdgrid_nedladdning_enabled=bool(
                settings.value("hojdgrid_nedladdning_enabled", False)
            ),
        )

    def store_to_settings(self):
        settings = QgsSettings()
        settings.beginGroup("lantmateriet", QgsSettings.Plugins)
        settings.setValue("ngp_enabled", self.ngp_enabled)
        settings.setValue("ngp_authcfg", self.ngp_authcfg)
        settings.setValue("ngp", self.ngp)
        settings.setValue("ovrig_enabled", self.ovrig_enabled)
        settings.setValue("ovrig_authcfg", self.ovrig_authcfg)
        settings.setValue("ovrig", self.ovrig)
        settings.setValue(
            "fastighetsindelning_direkt_enabled",
            self.fastighetsindelning_direkt_enabled,
        )
        settings.setValue(
            "belagenhetsadress_direkt_enabled", self.belagenhetsadress_direkt_enabled
        )
        settings.setValue("fastighet_direkt_enabled", self.fastighet_direkt_enabled)
        settings.setValue(
            "registerbeteckning_direkt_enabled", self.registerbeteckning_direkt_enabled
        )
        settings.setValue(
            "gemensamhetsanlaggning_direkt_enabled",
            self.gemensamhetsanlaggning_direkt_enabled,
        )
        settings.setValue(
            "ortofoto_nedladdning_enabled", self.ortofoto_nedladdning_enabled
        )
        settings.setValue(
            "hojdgrid_nedladdning_enabled", self.hojdgrid_nedladdning_enabled
        )

    def validate(self) -> list[str]:
        errors = []

        auth_manager: QgsAuthManager = QgsApplication.authManager()

        if self.ngp_enabled:
            if self.ngp not in ("production", "verification") and (
                self.ngp is None or not QgsStringUtils.isUrl(self.ngp)
            ):
                errors.append(
                    "Egen URL för Nationella geodataplattformen är inte giltig"
                )

            if self.ngp in ("production", "verification"):
                if (
                    not self.ngp_authcfg
                    or self.ngp_authcfg not in auth_manager.configIds()
                ):
                    errors.append(
                        "Autentisering för Nationella geodataplattformen saknas"
                    )
                else:
                    if auth_manager.configAuthMethodKey(self.ngp_authcfg) != "OAuth2":
                        errors.append(
                            "Autentisering för Nationella geodataplattformen är inte giltig"
                        )
                    else:
                        config = load_oauth_config(self.ngp_authcfg)
                        if self.ngp == "production" and config["tokenUrl"] != (
                            URLConfig.LM_PROD_AUTH_URL + "token"
                        ):
                            errors.append(
                                "Token URL för Nationella geodataplattformen är inte giltig"
                            )
                        elif self.ngp == "verification" and config["tokenUrl"] != (
                            URLConfig.LM_VER_AUTH_URL + "token"
                        ):
                            errors.append(
                                "Token URL för Nationella geodataplattformen är inte giltig"
                            )
                        if config["grantFlow"] in (
                            GrantFlow.AUTH_CODE,
                            GrantFlow.AUTH_CODE_PKCE,
                        ):
                            if self.ngp == "production" and config["requestUrl"] != (
                                URLConfig.LM_PROD_AUTH_URL + "authorize"
                            ):
                                errors.append(
                                    "Token URL för Nationella geodataplattformen är inte giltig"
                                )
                            elif self.ngp == "verification" and config[
                                "requestUrl"
                            ] != (URLConfig.LM_VER_AUTH_URL + "authorize"):
                                errors.append(
                                    "Token URL för Nationella geodataplattformen är inte giltig"
                                )

        if self.ovrig_enabled:
            if self.ovrig not in ("production", "verification") and (
                self.ovrig is None or not QgsStringUtils.isUrl(self.ovrig)
            ):
                errors.append("Egen URL för Övriga tjänster är inte giltig")

            if self.ovrig in ("production", "verification"):
                if (
                    not self.ovrig_authcfg
                    or self.ovrig_authcfg not in auth_manager.configIds()
                ):
                    errors.append("Autentisering för Övriga tjänster saknas")
                else:
                    if auth_manager.configAuthMethodKey(self.ovrig_authcfg) != "OAuth2":
                        errors.append(
                            "Autentisering för Övriga tjänster är inte giltig"
                        )
                    else:
                        config = load_oauth_config(self.ovrig_authcfg)
                        if self.ovrig == "production" and config["tokenUrl"] != (
                            URLConfig.LM_PROD_AUTH_URL + "token"
                        ):
                            errors.append(
                                "Token URL för Nationella geodataplattformen är inte giltig"
                            )
                        elif self.ovrig == "verification" and config["tokenUrl"] != (
                            URLConfig.LM_VER_AUTH_URL + "token"
                        ):
                            errors.append(
                                "Token URL för Nationella geodataplattformen är inte giltig"
                            )
                        if config["grantFlow"] in (
                            GrantFlow.AUTH_CODE,
                            GrantFlow.AUTH_CODE_PKCE,
                        ):
                            if self.ovrig == "production" and config["requestUrl"] != (
                                URLConfig.LM_PROD_AUTH_URL + "authorize"
                            ):
                                errors.append(
                                    "Authorize URL för Övriga tjänster är inte giltig"
                                )
                            elif self.ovrig == "verification" and config[
                                "requestUrl"
                            ] != (URLConfig.LM_VER_AUTH_URL + "authorize"):
                                errors.append(
                                    "Authorize URL för Övriga tjänster är inte giltig"
                                )

        return errors
