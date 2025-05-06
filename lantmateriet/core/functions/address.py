from qgis.core import (
    QgsExpressionContext,
    QgsGeometry,
    QgsReferencedGeometry,
    qgsfunction,
)

from lantmateriet.core.clients import BelagenhetsadressDirektClient
from lantmateriet.core.settings import Settings
from lantmateriet.core.util import UUID_RE


@qgsfunction(group="Lantmäteriet")
def address(
    source: QgsGeometry | QgsReferencedGeometry | str,
    kommunkod: str | None = None,
    context: QgsExpressionContext = None,
) -> dict | None:
    """
    Hämtar information om en adress. Funktionen kan ta olika typer av argument.

    <h3>Argument</h3>
    <h4>Geometri</h4>
    <div class="description"><p>Hämtar information för den adress som ligger närmast den givna geometrin.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address</span>(<span class="argument">geometri</span>)</code>
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">geometri</td>
             <td>geometri som ska sökas i närheten av</td>
          </tr>
       </table>
    </div>
    <h4>UUID</h4>
    <div class="description"><p>Hämtar information för adressen med en given identitet (UUID).</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address</span>(<span class="argument">id</span>)</code>
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">id</td>
             <td>identitet för den adress som ska hämtas</td>
          </tr>
       </table>
    </div>
    <h4>Beteckning</h4>
    <div class="description"><p>Hämtar information för adressen med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address</span>(<span class="argument">beteckning</span>, [<span class="argument">kommunkod</span>])</code>
    <br/><br/>[ ] markerar ett valfritt argument
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">beteckning</td>
             <td>beteckning för den adress som ska hämtas</td>
          </tr>
          <tr>
             <td class="argument">kommunkod</td>
             <td>kommunkod inom vilken adresser ska sökas på</td>
          </tr>
       </table>
    </div>
    <h5>Noteringar</h5>
    <div class="notes"><p>Sökning på beteckning utan kommunkod kan ge adresser i fel del av landet</p></div>

    <h3>Svar</h3>
    Funktionen returnerar en värdekarta i en nivå med information. Använd index-operatorn ([]) eller funktionen
    <span class="functionname">map_get</span> för att plocka ut informationen som önskas. Följande nycklar finns att välja på (vissa kan dock vara tomma
    eller saknas):

    <table>
    <tr><th>Nyckel</th><th>Datatyp</th></tr>
    <tr><td>objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.adressplatsnummer</td><td>Sträng</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.bokstavstillagg</td><td>Sträng</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.lagestillagg</td><td>Sträng ("UH", "UV", "U")</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.lagestillagsnummer</td><td>Heltal</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.avvikandeAdressplatsBeteckning</td><td>Sträng</td></tr>
    <tr><td>adressplatsattribut.adressplatsbeteckning.avvikerFranStandarden</td><td>Boolskt</td></tr>
    <tr><td>adressplatsattribut.adressplatstyp</td><td>Sträng ("Gatuadressplats", "Metertalsadressplats", "Byadressplats", "Gårdsadressplats")</td></tr>
    <tr><td>adressplatsattribut.insamlingslage</td><td>Sträng ("Byggnad", "Ingång", "Infart", "Tomtplats", "Ungefärligt lägesbestämd", "Övrigt läge")</td></tr>
    <tr><td>adressplatsattribut.status</td><td>Sträng ("Reserverad", "Gällande")</td></tr>
    <tr><td>adressplatsattribut.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>adressplatsattribut.postnummer</td><td>Heltal</td></tr>
    <tr><td>adressplatsattribut.postort</td><td>Sträng</td></tr>
    <tr><td>adressplatsnamn.popularnamn</td><td>Sträng</td></tr>
    <tr><td>adressplatsnamn.ortid</td><td>Sträng</td></tr>
    <tr><td>adressomrade.objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>adressomrade.objektversion</td><td>Heltal</td></tr>
    <tr><td>adressomrade.versionGiltigFran</td><td>Sträng (Datum)</td></tr>
    <tr><td>adressomrade.faststalltNamn</td><td>Sträng</td></tr>
    <tr><td>adressomrade.ortid</td><td>Sträng</td></tr>
    <tr><td>adressomrade.adressomradestyp</td><td>Sträng ("Gatuadressomrade", "Metertalsadressomrade", "Byadressomrade")</td></tr>
    <tr><td>adressomrade.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>adressomrade.kommundel.objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>adressomrade.kommundel.objektversion</td><td>Heltal</td></tr>
    <tr><td>adressomrade.kommundel.versionGiltigFran</td><td>Sträng (Datum)</td></tr>
    <tr><td>adressomrade.kommundel.faststalltNamn</td><td>Sträng</td></tr>
    <tr><td>adressomrade.kommundel.ortid</td><td>Sträng</td></tr>
    <tr><td>adressomrade.kommundel.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>adressomrade.kommundel.kommunkod</td><td>Sträng</td></tr>
    <tr><td>adressomrade.kommundel.kommunnamn</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.faststalltNamn</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.ortid</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>gardsadressomrade.adressomrade.objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>gardsadressomrade.adressomrade.objektversion</td><td>Heltal</td></tr>
    <tr><td>gardsadressomrade.adressomrade.versionGiltigFran</td><td>Sträng (Datum)</td></tr>
    <tr><td>gardsadressomrade.adressomrade.faststalltNamn</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.adressomrade.ortid</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.adressomrade.adressomradestyp</td><td>Sträng ("Gatuadressomrade", "Metertalsadressomrade", "Byadressomrade")</td></tr>
    <tr><td>gardsadressomrade.adressomrade.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.objektversion</td><td>Heltal</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.versionGiltigFran</td><td>Sträng (Datum)</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.faststalltNamn</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.ortid</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.objektstatus</td><td>Sträng ("Gällande")</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.kommunkod</td><td>Sträng</td></tr>
    <tr><td>gardsadressomrade.adressomrade.kommundel.kommunnamn</td><td>Sträng</td></tr>
    <tr><td>adressplatsanmarkning</td><td>Lista med värdekartor</td></tr>
    <tr><td>adressplatsanmarkning[*].anmarkningstyp</td><td>Sträng</td></tr>
    <tr><td>adressplatsanmarkning[*].anmarkningstext</td><td>Sträng</td></tr>
    <tr><td>adressattAnlaggning.anlaggningstyp</td><td>Sträng</td></tr>
    <tr><td>adressattAnlaggning.anlaggningstext</td><td>Sträng</td></tr>
    <tr><td>distriktstillhorighet.distriktskod</td><td>Sträng</td></tr>
    <tr><td>distriktstillhorighet.distriktsnamn</td><td>Sträng</td></tr>
    <tr><td>registerenhetsreferens.objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>registerenhetsreferens.beteckning</td><td>Sträng</td></tr>
    <tr><td>registerenhetsreferens.typ</td><td>Sträng ("Fastighet" eller "Samfällighet")</td></tr>
    </table>

    <h3>Exempel</h3>
    <div class="examples">
       <ul>
          <li><code>address( @geometry )</code> &rarr; <code>värdekarta med information för den adress som ligger närmast aktuellt objekt</code></li>
          <li><code>address( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )[ 'registerenhetsreferens.beteckning' ]</code> &rarr; <code>fastighetsbeteckning för adressen med den givna identiteten</code></li>
          <li><code>address( 'Gjörwellsgatan 22' )[ 'adressomrade.faststalltNamn' ]</code> &rarr; <code>'Gjörwellsgatan'</code></li>
          <li><code>map_get( address( 'Kyrkogatan 10' ), 'adressplatsattribut.adressplatsbeteckning.adressplatsnummer' )</code> &rarr; <code>'10'</code> (notera att adressbeteckningen förekommer i många orter i Sverige, och exakt vilken adress som returneras därmed ej är definerat)</li>
          <li><code>map_get( address( 'Kyrkogatan 10', '1784' ), 'adressomrade.kommundel.kommunnamn' )</code> &rarr; <code>'Arvika'</code></li>
       </ul>
    </div>
    """
    try:
        s = Settings.load_from_settings()
        if (
            not s.ovrig_enabled
            or not s.ovrig_authcfg
            or not s.belagenhetsadress_direkt_enabled
        ):
            raise Exception("Belägenhetsadress Direkt is not enabled in settings")
        client = BelagenhetsadressDirektClient(
            s.ovrig_url, s.ovrig_authcfg, context.feedback()
        )

        if isinstance(source, str) and UUID_RE.fullmatch(source) is not None:
            response = client.get_one(source, "total")
        elif isinstance(source, str):
            response = client.get_references_from_text(source, municipality=kommunkod)
            if len(response) == 0:
                return None
            response = client.get_one(response[0]["objektidentitet"], "total")
        else:
            response = client.get_by_point(source, "total")
    except (ValueError, KeyError):
        return None
    del response["geometry"]
    return response
