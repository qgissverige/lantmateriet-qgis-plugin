"""Configuration settings"""
import json

class URLConfig:
    # Base URLs
    LM_PROD_URL = "https://api.lantmateriet.se"
    LM_VER_URL = "https://api.lantmateriet-ver.se"

    # STAC connections
    LM_STAC_FASTIGHET_DIREKT = "/stac-vektor/v1/collections/fastighetsindelning"
    LM_STAC_BELAGENHET_DIREKT = "/stac-vektor/v1/collections/belagenhetsadresser"
    LM_STAC_ORTO_NEDLADD = "/stac-bild/v1"
    LM_STAC_HOJDGRID_NEDLADD = "/stac-hojd/v1"

    '''# TODO: vad är endpoint för Fastighet och samfällighet direkt?
        """if lm_belagenhet_direkt_enabled:
            connections["Fastighet och samfällighet direkt"] = lm_ovriga_baseurl + "TBD"""'''

    # And for OGC API features oapif_connections
    OGC_API_DETALJPLAN = "/distribution/geodatakatalog/sokning/v1/detaljplan/v2"
    OGC_API_BYGGNAD = "/distribution/geodatakatalog/sokning/v1/byggnad/v1"
    OGC_API_KULTURHISTORISK_LAMNING = "/geodatakatalog/sokning/v1/kulturhistorisklamning/v1"
    OGC_API_GRANS_FOR_FJALLNARA_SKOG = "/distribution/geodatakatalog/sokning/v1/gransforfjallnaraskog/v1"


class StacServiceNames:
    stac_snames = ["Höjdgrid nedladdning",
                       "Ortofoton nedladdning",
                       "Belägenhetsadress direkt",
                       "Fastighetsindelning direkt",
                       "Fastighet och samfällighet direkt"]

class OGCAPIServiceNames:
    oapif_snames= ["Detaljplan",
                       "Byggnad",
                       "Kulturhistorisk lämning",
                       "Gräns för fjällnära skog"]

class OAuthConfig:
    def __init__(self):
        self.config_map = {
            'oauth2config': json.dumps({
                'accessMethod': 0,
                'apiKey': '',
                'clientId': '',
                'clientSecret': '',
                'configType': 1,
                'customHeader': '',
                'description': '',
                'grantFlow': 0,
                'id': '',
                'name': '',
                'objectName': '',
                'password': '',
                'persistToken': False,
                'queryPairs': {},
                'redirectHost': '127.0.0.1',
                'redirectPort': 8080,
                'redirectUrl': '',
                'refreshTokenUrl': '',
                'requestTimeout': 30,
                'requestUrl': '',
                'scope': 'scope',
                'tokenUrl': '',
                'username': '',
                'version': 1
            })
        }

    def set_value(self, key, value):
        # Ladda JSON-strängen som en dictionary
        config_dict = json.loads(self.config_map['oauth2config'])
        if key in config_dict:
            config_dict[key] = value
            # Uppdatera JSON-strängen i config_map
            self.config_map['oauth2config'] = json.dumps(config_dict)
        else:
            raise KeyError(f"{key} is not a valid configuration key")

    def get_config_map(self):
        return self.config_map
