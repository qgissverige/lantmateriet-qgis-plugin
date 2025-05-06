from qgis.core import (
    QgsExpressionContext,
    QgsGeometry,
    QgsProject,
    QgsReferencedGeometry,
    qgsfunction,
)

from lantmateriet_qgis.core.clients import (
    FastighetOchSamfallighetDirektClient,
    FastighetsindelningDirektClient,
    RegisterbeteckningDirektClient,
)
from lantmateriet_qgis.core.clients.fastighetsindelningdirekt import Registerenhet
from lantmateriet_qgis.core.settings import Settings
from lantmateriet_qgis.core.util import UUID_RE, cql2, municipalities
from lantmateriet_qgis.core.util.designation import parse_designation


def fastighetsindelning_by_uuid(
    uuid: str, client: FastighetsindelningDirektClient
) -> dict[str, Registerenhet] | None:
    for collection in (
        "registerenhetsomradesytor",
        "registerenhetsomradeslinjer",
        "registerenhetsomradespunkter",
    ):
        response = client.get_registerenheter(collection, [uuid])
        if len(response) != 0:
            return response
    return None


def fastighetsindelning_by_designation(
    source: str, kommunkod: str, client: FastighetsindelningDirektClient
) -> dict[str, Registerenhet] | None:
    filter = parse_designation(source)
    if filter is None:
        return None
    for collection in (
        "registerenhetsomradesytor",
        "registerenhetsomradeslinjer",
        "registerenhetsomradespunkter",
    ):
        registerenheter = client.find_registerenheter(
            collection,
            cql2.and_([filter, cql2.equals(cql2.property("kommunkod"), kommunkod)])
            if kommunkod is not None
            else filter,
            limit=1,
        )
        if len(registerenheter) == 0:
            continue
        response = client.get_registerenheter(
            collection, [registerenheter[0]["objektidentitet"]]
        )
        if len(response) != 0:
            return response
    return None


def fastighetsindelning_by_geometry(
    geometry: QgsGeometry | QgsReferencedGeometry,
    client: FastighetsindelningDirektClient,
) -> dict[str, Registerenhet] | None:
    if isinstance(geometry, QgsReferencedGeometry):
        omrade = client.get_omrade_at_point(
            "registerenhetsomradesytor", geometry, geometry.crs(), False
        )
    else:
        geometry: QgsGeometry
        omrade = client.get_omrade_at_point(
            "registerenhetsomradesytor",
            geometry,
            QgsProject.instance().crs(),
            False,
        )
    if omrade is None:
        return None
    return client.get_registerenheter(
        "registerenhetsomradesytor", [omrade["registerenhetsreferens"]]
    )


def registerbeteckning_find_reference(
    designation: str, kommunkod: str, client: RegisterbeteckningDirektClient
):
    if kommunkod:
        results = client.get_by_name(f"{municipalities[kommunkod]} {designation}")
        if not results:
            results = client.get_by_name(designation)
    else:
        results = client.get_by_name(designation)
    results = [r for r in results if "registerenhetsreferens" in r]
    if not results:
        return None
    return results[0]["registerenhetsreferens"]["objektidentitet"]


@qgsfunction(group="Lantmäteriet")
def property_geometry(
    source: QgsGeometry | QgsReferencedGeometry | str,
    kommunkod: str | None = None,
    context: QgsExpressionContext = None,
) -> dict | None:
    """
    Hämtar geometrin för en fastighet eller samfällighet. Funktionen kan ta olika typer av argument.

    <h3>Argument</h3>
    <h4>Geometri</h4>
    <div class="description"><p>Hämtar geometrin för den fastighet eller samfällighet inom vilken den givna punkten ligger.</p></div>
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
    <div class="description"><p>Hämtar geometrin för fastigheten eller samfälligheten med en given identitet (UUID).</p></div>
    <h5>Syntax</h5>
    <div class="syntax">
    <code><span class="functionname">property_geometry</span>(<span class="argument">id</span>)</code>
    <h5>Argument</h5>
    <div class="arguments">
       <table>
          <tr>
             <td class="argument">id</td>
             <td>identitet för den fastighet eller samfällighet vars geometri som ska hämtas</td>
          </tr>
       </table>
    </div>
    <h4>Beteckning</h4>
    <div class="description"><p>Hämtar geometrin för fastigheten eller samfälligheten med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.</p></div>
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
    <div class="notes"><p>Majoriteten av fastigheter är redovisade som polygoner, men det finns såväl fastigheter som samfälligheter som istället är redovisade som linjer eller punkter.</p></div>

    <h3>Exempel</h3>
    <div class="examples">
       <ul>
          <li><code>property_geometry( @geometry )</code> &rarr; <code>geometri för den fastighet eller samfällighet inom vilken aktuellt objekt ligger</code></li>
          <li><code>property_geometry( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )</code> &rarr; <code>geometri för adressen med den givna identiteten</code></li>
          <li><code>property_geometry( 'Stockholm Trängkåren 6' )</code> &rarr; <code>polygongeometri för fastigheten på vilken Swecos huvudkontor ligger</code></li>
          <li><code>property_geometry( 'Torp 1:3' )</code> &rarr; <code>geometri för fastigheten "Torp 1:3" i en slumpvis ort i Sverige där fastighetsbeteckningen förekommer</code></li>
          <li><code>property_geometry( 'Torp 1:3', '2084' )</code> &rarr; <code>polygongeometri för fastigheten "Torp 1:3", garanterat i Avesta</code></li>
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
                item = client.get_one(source, "omrade")
            elif isinstance(source, str):
                regbet_client = RegisterbeteckningDirektClient(
                    s.ovrig_url, s.ovrig_authcfg, context.feedback()
                )
                ref = registerbeteckning_find_reference(
                    source, kommunkod, regbet_client
                )
                if ref is None:
                    return None

                item = client.get_one(ref, "omrade")
            else:
                refs = client.get_references_from_geometry(source)
                if not refs:
                    return None
                item = client.get_one(refs[0]["objektidentitet"], "omrade")
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
    return item["geometry"]
