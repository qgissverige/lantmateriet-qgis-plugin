from qgis.core import (
    QgsExpressionContext,
    QgsGeometry,
    QgsReferencedGeometry,
    qgsfunction,
)

from lantmateriet.core.clients import (
    FastighetOchSamfallighetDirektClient,
    FastighetsindelningDirektClient,
    RegisterbeteckningDirektClient,
)
from lantmateriet.core.functions.property_geometry import (
    fastighetsindelning_by_designation,
    fastighetsindelning_by_geometry,
    fastighetsindelning_by_uuid,
    registerbeteckning_find_reference,
)
from lantmateriet.core.settings import Settings
from lantmateriet.core.util import UUID_RE


@qgsfunction(group="Lantmäteriet")
def property(
    source: QgsGeometry | QgsReferencedGeometry | str,
    kommunkod: str | None = None,
    context: QgsExpressionContext = None,
) -> dict | None:
    """
    Hämtar information om en fastighet eller samfällighet. Funktionen kan ta olika typer av argument.

    <h3>Argument</h3>
    <h4>Geometri</h4>
    <div class="description"><p>Hämtar information för den fastighet eller samfällighet inom vilken den givna punkten ligger.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">property_geometry</span>(<span class="argument">geometri</span>)</code>
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
    <div class="description"><p>Hämtar information för fastigheten eller samfälligheten med en given identitet (UUID).</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">property_geometry</span>(<span class="argument">id</span>)</code>
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">id</td>
             <td>identitet för den fastighet eller samfällighet vars information som ska hämtas</td>
          </tr>
       </table>
    </div>
    <h4>Beteckning</h4>
    <div class="description"><p>Hämtar information för fastigheten eller samfälligheten med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">property_geometry</span>(<span class="argument">beteckning</span>, [<span class="argument">kommunkod</span>])</code>
    <br/><br/>[ ] markerar ett valfritt argument
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">beteckning</td>
             <td>beteckning för den fastigheten eller samfälligheten som ska hämtas</td>
          </tr>
          <tr>
             <td class="argument">kommunkod</td>
             <td>kommunkod inom vilken fastigheter och samfälligheter ska sökas på</td>
          </tr>
       </table>
    </div>
    <h5>Noteringar</h5>
    <div class="notes"><p>Sökning på beteckning utan kommunkod eller kommunnamn i beteckningen kan ge fastigheter eller samfälligheter i fel del av landet</p></div>

    <h3>Svar</h3>
    Funktionen returnerar en värdekarta i en nivå med information. Använd index-operatorn ([]) eller funktionen
    <span class="functionname">map_get</span> för att plocka ut informationen som önskas. Följande nycklar finns att välja på (vissa kan dock vara tomma
    eller saknas):

    <h4>För Fastighetsindelning Direkt</h4>
    <table>
    <tr><th>Nyckel</th><th>Beskrivning</th></tr>
    <tr><td>objektidentitet</td><td>Sträng (UUID)</td></tr>
    <tr><td>objekttyp</td><td>Sträng ("fastighetsområde")</td></tr>
    <tr><td>senastandrad</td><td>Sträng (Datum & Tid)</td></tr>
    <tr><td>lanskod</td><td>Sträng</td></tr>
    <tr><td>kommunkod</td><td>Sträng</td></tr>
    <tr><td>kommunnamn</td><td>Sträng</td></tr>
    <tr><td>trakt</td><td>Sträng</td></tr>
    <tr><td>block</td><td>Sträng</td></tr>
    <tr><td>enhet</td><td>Heltal</td></tr>
    <tr><td>etikett</td><td>Sträng</td></tr>
    <tr><td>beteckning</td><td>Sträng</td></tr>
    </table>

    <h4>För Fastighet och Samfällighet Direkt</h4>
    <table>
    <tr><th>Nyckel</th><th>Beskrivning</th></tr>
    </table>

    <h3>Exempel</h3>
    <div class="examples">
       <ul>
          <li><code>property( @geometry )</code> &rarr; <code>värdekarta med information för den fastighet eller samfällighet inom vilken aktuellt objekt ligger</code></li>
          <li><code>property( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )[ 'beteckning' ]</code> &rarr; <code>beteckning för fastigheten eller samfälligheten med den givna identiteten</code></li>
          <li><code>property( 'Stockholm Trängkåren 6' )[ 'objektidentitet' ]</code> &rarr; <code>identitet för fastigheten på vilken Swecos huvudkontor ligger</code></li>
          <li><code>map_get( property( 'Torp 1:3' ), 'kommunnamn' )</code> &rarr; <code>kommunnamn fastigheten "Torp 1:3" i en slumpvis ort i Sverige där fastighetsbeteckningen förekommer</code></li>
          <li><code>map_get( property( 'Torp 1:3', '2084' ), 'kommunnamn ')</code> &rarr; <code>'Avesta'</code></li>
       </ul>
    </div>
    """
    try:
        s = Settings.load_from_settings()
        if not s.ovrig_enabled or not s.ovrig_authcfg:
            raise Exception("Necessary services are not enabled in settings")
        if s.fastighet_direkt_enabled and s.registerbeteckning_direkt_enabled:
            client = FastighetOchSamfallighetDirektClient(
                s.ovrig_url, s.ovrig_authcfg, context.feedback()
            )

            if isinstance(source, str) and UUID_RE.fullmatch(source) is not None:
                item = client.get_one(source, "basinformation")
            elif isinstance(source, str):
                regbet_client = RegisterbeteckningDirektClient(
                    s.ovrig_url, s.ovrig_authcfg, context.feedback()
                )
                ref = registerbeteckning_find_reference(
                    source, kommunkod, regbet_client
                )
                if ref is None:
                    return None

                item = client.get_one(ref, "basinformation")
            else:
                refs = client.get_references_from_geometry(source)
                if not refs:
                    return None
                item = client.get_one(refs[0]["objektidentitet"], "basinformation")
        elif s.fastighetsindelning_direkt_enabled:
            client = FastighetsindelningDirektClient(
                s.ovrig_url, s.ovrig_authcfg, context.feedback()
            )

            if isinstance(source, str) and UUID_RE.fullmatch(source) is not None:
                response = fastighetsindelning_by_uuid(source, client)
            elif isinstance(source, str):
                response = fastighetsindelning_by_designation(source, kommunkod, client)
            else:
                response = fastighetsindelning_by_geometry(source, client)
            if not response:
                return None
            item = response[next(iter(response))]
        else:
            raise Exception("Necessary services are not enabled in settings")
    except (ValueError, KeyError):
        return None
    if "geometry" in item:
        del item["geometry"]  # noqa: accept key removal
    return item
