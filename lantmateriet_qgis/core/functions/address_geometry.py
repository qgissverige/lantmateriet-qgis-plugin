from qgis.core import (
    QgsExpressionContext,
    QgsGeometry,
    QgsReferencedGeometry,
    qgsfunction,
)

from lantmateriet_qgis.core.clients import BelagenhetsadressDirektClient
from lantmateriet_qgis.core.settings import Settings
from lantmateriet_qgis.core.util import UUID_RE


@qgsfunction(group="Lantmäteriet")
def address_geometry(
    source: QgsGeometry | QgsReferencedGeometry | str,
    kommunkod: str | None = None,
    context: QgsExpressionContext = None,
) -> QgsGeometry | None:
    """
    Hämtar geometrin för en adress. Funktionen kan ta olika typer av argument.

    <h3>Argument</h3>
    <h4>Geometri</h4>
    <div class="description"><p>Hämtar geometrin för den adress som ligger närmast den givna geometrin.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address_geometry</span>(<span class="argument">geometri</span>)</code>
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
    <div class="description"><p>Hämtar geometrin för adressen med en given identitet (UUID).</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address_geometry</span>(<span class="argument">id</span>)</code>
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">id</td>
             <td>identitet för den adress vars geometri som ska hämtas</td>
          </tr>
       </table>
    </div>
    <h4>Beteckning</h4>
    <div class="description"><p>Hämtar geometrin för adressen med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">address_geometry</span>(<span class="argument">beteckning</span>, [<span class="argument">kommunkod</span>])</code>
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

    <h3>Exempel</h3>
    <div class="examples">
       <ul>
          <li><code>address_geometry( @geometry )</code> &rarr; <code>punktgeometri för den adress som ligger närmast aktuellt objekt</code></li>
          <li><code>address_geometry( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )</code> &rarr; <code>punktgeometri för adressen med den givna identiteten</code></li>
          <li><code>address_geometry( 'Gjörwellsgatan 22' )</code> &rarr; <code>punktgeometri för adressen till Swecos huvudkontor</code></li>
          <li><code>address_geometry( 'Kyrkogatan 10' )</code> &rarr; <code>punktgeometri för adressen "Kyrkogatan 10" i en slumpvis ort i Sverige där adressen förekommer</code></li>
          <li><code>address_geometry( 'Kyrkogatan 10', '1784' )</code> &rarr; <code>punktgeometri för adressen "Kyrkogatan 10", garanterat i Arvika</code></li>
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
            response = client.get_one(source, "basinformation")
        elif isinstance(source, str):
            response = client.get_references_from_text(source, municipality=kommunkod)
            if len(response) == 0:
                return None
            response = client.get_one(response[0]["objektidentitet"], "basinformation")
        else:
            response = client.get_by_point(source, "basinformation")
    except (ValueError, KeyError):
        return None
    return response["geometry"]
