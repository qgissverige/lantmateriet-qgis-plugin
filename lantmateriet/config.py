"""Configuration settings"""


class URLConfig:
    # Base URLs
    LM_PROD_URL = "https://api.lantmateriet.se"
    LM_PROD_AUTH_URL = "https://apimanager.lantmateriet.se/oauth2/"
    LM_VER_URL = "https://api.lantmateriet-ver.se"
    LM_VER_AUTH_URL = "https://apimanager-ver.lantmateriet.se/oauth2/"

    LM_STAC_FASTIGHET_DIREKT = "/stac-vektor/v1/collections/fastighetsindelning"
    LM_STAC_BELAGENHET_DIREKT = "/stac-vektor/v1/collections/belagenhetsadresser"
    LM_STAC_ORTO_NEDLADD = "/stac-bild/v1"
    LM_STAC_HOJDGRID_NEDLADD = "/stac-hojd/v1"

    LM_OAPIF_FASTIGHETSINDELNING_DIREKT = "/ogc-features/v1/fastighetsindelning"

    NGP_STAC_DETALJPLAN = "/distribution/geodatakatalog/sokning/v1/detaljplan/v2"
    NGP_STAC_BYGGNAD = "/distribution/geodatakatalog/sokning/v1/byggnad/v1"
    NGP_STAC_KULTURHISTORISK_LAMNING = (
        "/geodatakatalog/sokning/v1/kulturhistorisklamning/v1"
    )
    NGP_STAC_GRANS_FOR_FJALLNARA_SKOG = (
        "/distribution/geodatakatalog/sokning/v1/gransforfjallnaraskog/v1"
    )
