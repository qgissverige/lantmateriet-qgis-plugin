from dataclasses import dataclass
from typing import Literal, Self

from qgis._core import QgsSettings


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
        return []
