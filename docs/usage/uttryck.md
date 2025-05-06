# Uttryck

Pluginet tillhandahåller flera funktioner som kan användas i uttryck, t.ex. för stilsättning och enklare geokodning.

!!! note "Ej lämpligt för större datamängder"

    På grund av hur QGIS hanterar uttryck så är de ej lämpliga för att använda på större datamängder, då det inte
    finns någon möjligt att batcha flera anrop till Lantmäteriets direkttjänster. Algoritmer å anda sidan har möjlighet att
    batcha flera anrop och är därför att föredra för större datamängder.

    Exempelvis går det att använda uttrycken som erbjuds för geokodning (via den inbyggda algoritmen
    [_Geometri med uttryck_](https://docs.qgis.org/latest/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html#qgisgeometrybyexpression)),
    men det kommer innebära många frågor mot Lantmäteriets direkttjänster vilket innebär trögare utförande.

    För att säkerställa att uppritningen fungerar snabbt så kan man på lager med många objekt använda skalberoende
    stilsättning genom [regel-baserad stilsättning](https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/vector_properties.html#rule-based-renderer),
    för att använda symbolik utan dessa uttryck för mindre skalor.

## `address(geometri | id | beteckning, [kommunkod])` { #address data-toc-label='address' }

Hämtar information om en adress. Funktionen kan ta olika typer av argument.

### Argument

#### Geometri

Hämtar information för den adress som ligger närmast den givna geometrin.

##### Syntax

    address(geometri)

##### Argument

<table>
    <tr>
        <td><pre><code>geometri</code></pre></td>
        <td>geometri som ska sökas i närheten av</td>
    </tr>
</table>

#### UUID

Hämtar information för adressen med en given identitet (UUID).

##### Syntax

    address(id)

##### Argument

<table>
    <tr>
        <td><pre><code>id</code></pre></td>
        <td>identitet för den adress som ska hämtas</td>
    </tr>
</table>

#### Beteckning

Hämtar information för adressen med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.

##### Syntax

    address(beteckning, [kommunkod])

`[ ]` markerar ett valfritt argument

##### Argument

<table>
    <tr>
        <td><pre><code>beteckning</code></pre></td>
        <td>beteckning för den adress som ska hämtas</td>
    </tr>
    <tr>
        <td><pre><code>kommunkod</code></pre></td>
        <td>kommunkod inom vilken adresser ska sökas på</td>
    </tr>
</table>

##### Noteringar

Sökning på beteckning utan kommunkod kan ge adresser i fel del av landet

### Svar

Funktionen returnerar en värdekarta i en nivå med information. Använd index-operatorn (`[]`) eller
funktionen `map_get` för att plocka ut informationen som önskas. Följande nycklar finns att välja
på (vissa kan dock vara tomma eller saknas):

| Nyckel                                                                 | Datatyp                                                                                        |
|------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `objektidentitet`                                                      | Sträng (UUID)                                                                                  |
| `adressplatsattribut.adressplatsbeteckning.adressplatsnummer`          | Sträng                                                                                         |
| `adressplatsattribut.adressplatsbeteckning.bokstavstillagg`            | Sträng                                                                                         |
| `adressplatsattribut.adressplatsbeteckning.lagestillagg`               | Sträng ("UH", "UV", "U")                                                                       |
| `adressplatsattribut.adressplatsbeteckning.lagestillagsnummer`         | Heltal                                                                                         |
| `adressplatsattribut.adressplatsbeteckning.avvikandeAdressplatsBeteckning` | Sträng                                                                                         |
| `adressplatsattribut.adressplatsbeteckning.avvikerFranStandarden`      | Boolskt                                                                                        |
| `adressplatsattribut.adressplatstyp`                                   | Sträng ("Gatuadressplats", "Metertalsadressplats", "Byadressplats", "Gårdsadressplats")        |
| `adressplatsattribut.insamlingslage`                                   | Sträng ("Byggnad", "Ingång", "Infart", "Tomtplats", "Ungefärligt lägesbestämd", "Övrigt läge") |
| `adressplatsattribut.status`                                           | Sträng ("Reserverad", "Gällande")                                                              |
| `adressplatsattribut.objektstatus`                                     | Sträng ("Gällande")                                                                            |
| `adressplatsattribut.postnummer`                                       | Heltal                                                                                         |
| `adressplatsattribut.postort`                                          | Sträng                                                                                         |
| `adressplatsnamn.popularnamn`                                          | Sträng                                                                                         |
| `adressplatsnamn.ortid`                                                | Sträng                                                                                         |
| `adressomrade.objektidentitet`                                         | Sträng (UUID)                                                                                  |
| `adressomrade.objektversion`                                           | Heltal                                                                                         |
| `adressomrade.versionGiltigFran`                                       | Sträng (Datum)                                                                                 |
| `adressomrade.faststalltNamn`                                           | Sträng                                                                                         |
| `adressomrade.ortid`                                                   | Sträng                                                                                         |
| `adressomrade.adressomradestyp`                                        | Sträng ("Gatuadressomrade", "Metertalsadressomrade", "Byadressomrade")                         |
| `adressomrade.objektstatus`                                            | Sträng ("Gällande")                                                                            |
| `adressomrade.kommundel.objektidentitet`                               | Sträng (UUID)                                                                                  |
| `adressomrade.kommundel.objektversion`                                 | Heltal                                                                                         |
| `adressomrade.kommundel.versionGiltigFran`                             | Sträng (Datum)                                                                                 |
| `adressomrade.kommundel.faststalltNamn`                                 | Sträng                                                                                         |
| `adressomrade.kommundel.ortid`                                         | Sträng                                                                                         |
| `adressomrade.kommundel.objektstatus`                                  | Sträng ("Gällande")                                                                            |
| `adressomrade.kommundel.kommunkod`                                     | Sträng                                                                                         |
| `adressomrade.kommundel.kommunnamn`                                    | Sträng                                                                                         |
| `gardsadressomrade.faststalltNamn`                                      | Sträng                                                                                         |
| `gardsadressomrade.ortid`                                              | Sträng                                                                                         |
| `gardsadressomrade.objektstatus`                                       | Sträng ("Gällande")                                                                            |
| `gardsadressomrade.adressomrade.objektidentitet`                       | Sträng (UUID)                                                                                  |
| `gardsadressomrade.adressomrade.objektversion`                         | Heltal                                                                                         |
| `gardsadressomrade.adressomrade.versionGiltigFran`                     | Sträng (Datum)                                                                                 |
| `gardsadressomrade.adressomrade.faststalltNamn`                         | Sträng                                                                                         |
| `gardsadressomrade.adressomrade.ortid`                                 | Sträng                                                                                         |
| `gardsadressomrade.adressomrade.adressomradestyp`                      | Sträng ("Gatuadressomrade", "Metertalsadressomrade", "Byadressomrade")                         |
| `gardsadressomrade.adressomrade.objektstatus`                          | Sträng ("Gällande")                                                                            |
| `gardsadressomrade.adressomrade.kommundel.objektidentitet`             | Sträng (UUID)                                                                                  |
| `gardsadressomrade.adressomrade.kommundel.objektversion`               | Heltal                                                                                         |
| `gardsadressomrade.adressomrade.kommundel.versionGiltigFran`           | Sträng (Datum)                                                                                 |
| `gardsadressomrade.adressomrade.kommundel.faststalltNamn`              | Sträng                                                                                         |
| `gardsadressomrade.adressomrade.kommundel.ortid`                       | Sträng                                                                                         |
| `gardsadressomrade.adressomrade.kommundel.objektstatus`                | Sträng ("Gällande")                                                                            |
| `gardsadressomrade.adressomrade.kommundel.kommunkod`                   | Sträng                                                                                         |
| `gardsadressomrade.adressomrade.kommundel.kommunnamn`                  | Sträng                                                                                         |
| `adressplatsanmarkning`                                                | Lista med värdekartor                                                                          |
| `adressplatsanmarkning[*].anmarkningstyp`                              | Sträng                                                                                         |
| `adressplatsanmarkning[*].anmarkningstext`                             | Sträng                                                                                         |
| `adressattAnlaggning.anlaggningstyp`                                   | Sträng                                                                                         |
| `adressattAnlaggning.anlaggningstext`                                  | Sträng                                                                                         |
| `distriktstillhorighet.distriktskod`                                   | Sträng                                                                                         |
| `distriktstillhorighet.distriktsnamn`                                  | Sträng                                                                                         |
| `registerenhetsreferens.objektidentitet`                               | Sträng (UUID)                                                                                  |
| `registerenhetsreferens.beteckning`                                    | Sträng                                                                                         |
| `registerenhetsreferens.typ`                                           | Sträng ("Fastighet" eller "Samfällighet")                                                      |

### Exempel

* `address( @geometry )` &rarr; värdekarta med information för den adress som ligger närmast aktuellt objekt</li>
* `address( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )[ 'registerenhetsreferens.beteckning' ]` &rarr; fastighetsbeteckning för adressen med den givna identiteten</li>
* `address( 'Gjörwellsgatan 22' )[ 'adressomrade.faststalltNamn' ]` &rarr; `'Gjörwellsgatan'`</li>
* `map_get( address( 'Kyrkogatan 10' ), 'adressplatsattribut.adressplatsbeteckning.adressplatsnummer' )` &rarr; `'10'` (notera att adressbeteckningen förekommer i många orter i Sverige, och exakt vilken adress som returneras därmed ej är definerat)</li>
* `map_get( address( 'Kyrkogatan 10', '1784' ), 'adressomrade.kommundel.kommunnamn' )` &rarr; `'Arvika'`</li>

## `address_geometry(geometri | id | beteckning, [kommunkod])` { #address_geometry data-toc-label='address_geometry' }

Hämtar geometrin för en adress. Funktionen kan ta olika typer av argument.

### Argument

#### Geometri

Hämtar geometrin för den adress som ligger närmast den givna geometrin.

##### Syntax

    address(geometri)

##### Argument

<table>
    <tr>
        <td><pre><code>geometri</code></pre></td>
        <td>geometri som ska sökas i närheten av</td>
    </tr>
</table>

#### UUID

Hämtar geometrin för adressen med en given identitet (UUID).

##### Syntax

    address(id)

##### Argument

<table>
    <tr>
        <td><pre><code>id</code></pre></td>
        <td>identitet för den adress som ska hämtas</td>
    </tr>
</table>

#### Beteckning

Hämtar geometrin för adressen med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.

##### Syntax

    address(beteckning, [kommunkod])

`[ ]` markerar ett valfritt argument

##### Argument

<table>
    <tr>
        <td><pre><code>beteckning</code></pre></td>
        <td>beteckning för den adress som ska hämtas</td>
    </tr>
    <tr>
        <td><pre><code>kommunkod</code></pre></td>
        <td>kommunkod inom vilken adresser ska sökas på</td>
    </tr>
</table>

##### Noteringar

Sökning på beteckning utan kommunkod kan ge adresser i fel del av landet

### Svar

En punktgeometri.

### Exempel

* `address_geometry( @geometry )` &rarr; punktgeometri för den adress som ligger närmast aktuellt objekt</li>
* `address_geometry( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )` &rarr; punktgeometri för adressen med den givna identiteten</li>
* `address_geometry( 'Gjörwellsgatan 22' )` &rarr; punktgeometri för adressen till Swecos huvudkontor</li>
* `address_geometry( 'Kyrkogatan 10' )` &rarr; punktgeometri för adressen "Kyrkogatan 10" i en slumpvis ort i Sverige där adressen förekommer</li>
* `address_geometry( 'Kyrkogatan 10', '1784' )` &rarr; punktgeometri för adressen "Kyrkogatan 10", garanterat i Arvika</li>

## `property(geometri | id | beteckning, [kommunkod])` { #property data-toc-label='property' }

Hämtar information för en fastighet eller samfällighet. Funktionen kan ta olika typer av argument.

### Argument

#### Geometri

Hämtar information för den fastighet eller samfällighet inom vilken den givna punkten ligger.

##### Syntax

    property_geometry(geometri)

##### Argument

<table>
  <tr>
     <td><pre><code>geometri</code></pre></td>
     <td>geometri som ska sökas i närheten av</td>
  </tr>
</table>

#### UUID

Hämtar information för fastigheten eller samfälligheten med en given identitet (UUID).

##### Syntax

    property_geometry(id)

##### Argument

<table>
    <tr>
        <td><pre><code>id</code></pre></td>
        <td>identitet för den fastighet eller samfällighet vars information som ska hämtas</td>
    </tr>
</table>

#### Beteckning

Hämtar information för fastigheten eller samfälligheten med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.

##### Syntax

    property_geometry(beteckning, [kommunkod])

`[ ]` markerar ett valfritt argument

##### Argument

<table>
    <tr>
        <td><pre><code>beteckning</code></pre></td>
        <td>beteckning för den fastigheten eller samfälligheten som ska hämtas</td>
    </tr>
    <tr>
        <td><pre><code>kommunkod</code></pre></td>
        <td>kommunkod inom vilken fastigheter och samfälligheter ska sökas på</td>
    </tr>
</table>

##### Noteringar

Sökning på beteckning utan kommunkod eller kommunnamn i beteckningen kan ge fastigheter eller samfälligheter i fel del av landet.

### Svar

#### För Fastighetsinformation Direkt

| Nyckel          | Beskrivning                 |
|-----------------|-----------------------------|
| objektidentitet | Sträng (UUID)               |
| objekttyp       | Sträng ("fastighetsområde") |
| senastandrad    | Sträng (Datum & Tid)        |
| lanskod         | Sträng                      |
| kommunkod       | Sträng                      |
| kommunnamn      | Sträng                      |
| trakt           | Sträng                      |
| block           | Sträng                      |
| enhet           | Heltal                      |
| etikett         | Sträng                      |
| beteckning      | Sträng                      |

#### För Fastighet och Samfällighet Direkt

### Exempel

* `property( @geometry )` &rarr; värdekarta med information för den fastighet eller samfällighet inom vilken aktuellt objekt ligger
* `property( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )[ 'beteckning' ]` &rarr; beteckning för fastigheten eller samfälligheten med den givna identiteten
* `property( 'Stockholm Trängkåren 6' )[ 'objektidentitet' ]` &rarr; identitet för fastigheten på vilken Swecos huvudkontor ligger
* `map_get( property( 'Torp 1:3' ), 'kommunnamn' )` &rarr; kommunnamn fastigheten "Torp 1:3" i en slumpvis ort i Sverige där fastighetsbeteckningen förekommer
* `map_get( property( 'Torp 1:3', '2084' ), 'kommunnamn ')` &rarr; `'Avesta'`

## `property_geometry(geometri | id | beteckning, [kommunkod])` { #property_geometry data-toc-label='property_geometry' }

Hämtar geometrin för en fastighet eller samfällighet. Funktionen kan ta olika typer av argument.

### Argument

#### Geometri

Hämtar geometrin för den fastighet eller samfällighet inom vilken den givna punkten ligger.

##### Syntax

    property_geometry(geometri)

##### Argument

<table>
  <tr>
     <td><pre><code>geometri</code></pre></td>
     <td>geometri som ska sökas i närheten av</td>
  </tr>
</table>

#### UUID

Hämtar geometrin för fastigheten eller samfälligheten med en given identitet (UUID).

##### Syntax

    property_geometry(id)

##### Argument

<table>
    <tr>
        <td><pre><code>id</code></pre></td>
        <td>identitet för den fastighet eller samfällighet vars geometri som ska hämtas</td>
    </tr>
</table>

#### Beteckning

Hämtar geometrin för fastigheten eller samfälligheten med en given beteckning, sökningen kan valfritt begränsas till en given kommunkod.

##### Syntax

    property_geometry(beteckning, [kommunkod])

`[ ]` markerar ett valfritt argument

##### Argument

<table>
    <tr>
        <td><pre><code>beteckning</code></pre></td>
        <td>beteckning för den fastigheten eller samfälligheten som ska hämtas</td>
    </tr>
    <tr>
        <td><pre><code>kommunkod</code></pre></td>
        <td>kommunkod inom vilken fastigheter och samfälligheter ska sökas på</td>
    </tr>
</table>

##### Noteringar

Sökning på beteckning utan kommunkod eller kommunnamn i beteckningen kan ge fastigheter eller samfälligheter i fel del av landet.

Majoriteten av fastigheter är redovisade som polygoner, men det finns såväl fastigheter som samfälligheter som istället är redovisade som linjer eller punkter.

### Exempel

* `property_geometry( @geometry )` &rarr; geometri för den fastighet eller samfällighet inom vilken aktuellt objekt ligger
* `property_geometry( '8e0cd471-f10c-47eb-a9ea-e95355e4f2e1' )` &rarr; geometri för adressen med den givna identiteten
* `property_geometry( 'Stockholm Trängkåren 6' )` &rarr; polygongeometri för fastigheten på vilken Swecos huvudkontor ligger
* `property_geometry( 'Torp 1:3' )` &rarr; geometri för fastigheten "Torp 1:3" i en slumpvis ort i Sverige där fastighetsbeteckningen förekommer
* `property_geometry( 'Torp 1:3', '2084' )` &rarr; polygongeometri för fastigheten "Torp 1:3", garanterat i Avesta
