# Åtkomstnycklar från Lantmäteriet

Denna sida innehåller en sammanfattning av stegen man behöver gå för att gå tillgång till de åtkomstnycklar som krävs
för att kunna använda detta plugin.

Mer information finns att läsa hos Lantmäteriet, särskilt:

* [Information om API Portalen](https://apimanager.lantmateriet.se/docs/) (engelska)
* [Nationella geodataplattformen - Konsument](https://www.lantmateriet.se/sv/nationella-geodataplattformen/konsument/)

Notera att flera av stegen som beskrivs här innebär en manuell hantering hos Lantmäteriet, beroende på vad det gäller
och deras aktuella arbetsbelastning kan hanteringen ta allt från några timmar till flera veckor.

Dessa instruktioner antar att du inte har något konto eller liknande hos Lantmäteriet sedan tidigare. Om du redan har
konto, beställt tjänster, eller använt API-managern så kan du hoppa över de steg som inte är aktuella för dig.

## 1. Skapa ett konto på Geotorget

Först behöver du ha tillgång till ett konto på Geotorget:

1. Gå till [Geotorget](https://geotorget.lantmateriet.se/), klicka på Logga in
2. Välj kontotyp och följ stegen

## 2. Beställ datamängderna på Geotorget

### 2a. Nationella geodataplattformen

1. Logga in på Geotorget
2. Välj _Nationella geodataplattformen_
3. Under _Bli konsument_, klicka på _Ansök_
4. Läs igenom och godkänn användarvillkoren
5. Skicka in ansökan

För Nationella geodataplattformen får du automatiskt behörighet till APIerna, det kan dock ta några minuter för systemet
att registrera allt.

### 2b. Övriga tjänster

1. Logga in på Geotorget
2. Välj _Geodataprodukter_
3. Sök fram respektive tjänst du vill använda och klicka på högerpilen för att gå vidare
4. Säkerställ att du väljer samma systemkonto för samtliga tjänster
    * Du kan skapa nya systemkonton från [Mitt konto / Behörigheter](https://geotorget.lantmateriet.se/mitt-konto/kontohantering#systemkonton) 
5. Beroende på tjänsten kommer du behöva besvara några frågor

Detta plugin kan använda sig av följande tjänster:

* Belägenhetsadress Direkt
* Fastighetsindelning Direkt
* Gemensamhetsanläggning Direkt
* Registerbeteckning Direkt
* Fastighet och Samfällighet Direkt (avgiftsbelagd)
* Ortofoto Nedladdning
* Markhöjdmodell Nedladdning

## 3. Skapa åtkomstnycklar i API-managern

1. Gå till [Lantmäteriets API-manager](https://apimanager.lantmateriet.se/)
2. Logga in:

=== "Organisationskonto"

    Använd användarnamnet på det systemkonto som skapats, och lösenordet du fått per mail när du skapade systemkontot.

=== "Privatperson"

    Använd samma inloggningsuppgifter som till Geotorget.

3. Gå till _Applications_ i menyraden, välj _Add New Application_
4. Ge applikationen ett namn och valfri beskrivning

=== "Organisationskonto"

    **Tips:** Ange dina initialer eller liknande i applikationsnamnet om enbart du själv kommer använda åtkomstnycklarna
    du skapat. Lägg även in t.ex. din mailadress i beskrivningen.

    Eftersom det ofta är flera personer som använder samma systemkonto inom en organisation, och därmed kommer åt samma
    applikationer, underlättar det mycket att veta vem som ansvarar för vilken applikation.

=== "Privatperson"

    Eftersom enbart du själv kommer använda ditt konto kan du get applikationen valfritt namn och beskrivning.

5. På sidan för applikationen, gå till _Subscriptions_
6. Välj _Subscribe APIs_ och välj _Subscribe_ på de APIer du vill använda, namnen på APIerna i API-managern kan dock skilja sig från
   tjänstens namn:

| Tjänst                            | API-namn i API-managern        |
|-----------------------------------|--------------------------------|
| Belägenhetsadress Direkt          | Belägenhetsadress_Direkt       |
| Fastighetsindelning Direkt        | OGC-FEATURES-GEOSERVER         |
| Gemensamhetsanläggning Direkt     | Gemensamhetsanläggning_Direkt  |
| Registerbeteckning Direkt         | Registerbeteckning_Direkt      |
| Fastighet och Samfällighet Direkt | FastighetOchSamfällighetDirekt |
| Ortofoto Nedladdning              | STAC-bild                      |
| Markhöjdmodell Nedladdning        | STAC-hojd                      |

7. Gå till _Production Keys_, skrolla ner och klicka på _Generate Keys_
8. Kopiera _Consumer Key_ och _Consumer Secret_ och klistra in dem i [OAuth 2-inställningar](../installningar.md#oauth-2-installningar) i
   pluginet

## Mer information

### Användarkonton, Organisationskonton, Systemkonton och Applikationer

När man använder Lantmäteriets tjänster kommer man i kontakt med flera olika kontotyper, vilket kan vara väldigt
förvirrande.

* **Användarkonto** - Ett användarkonto är det konto med vilket du loggar in på Geotorget. För privatpersoner är detta
  din mailadress, för organisationer är det ett användarnamn bestående av en förkortning av din organisations namn följt
  av en förkortning av ditt för- och efternamn.
* **Organisationskonto** - Om man inte är privatperson så är det användarkonto med vilket man loggar in till Geotorget
  kopplat till ett organisationskonto. Som regel kan alla användare som är kopplade till samma organisation se samma
  information på Geotorget (alltså även varandras beställningar o.s.v.).
    * Det är möjligt att ha flera olika organisationskonton för samma organisation/organisationsnummer om man har olika
      "roller" i organisationen, t.ex. som slutkonsument respektive vidareföräldare. Användarkonton är då kopplade till
      enbart ett av dessa organisationskonton, som alla har unika kundnummer.
* **Systemkonto** - Organisationskonton har ett antal systemkonton kopplade till sig. När man beställer en behörighet på
  Geotorget kopplas behörigheten till ett systemkonto. För organisationer används systemkontot för att logga in på
  API-managern.
* **Applikation** - Varje systemkonto har ett antal applikationer kopplade till sig, och varje applikation kan ges
  behörighet till en eller flera APIer. När man ansluter från en programvara (som från QGIS) är det med en applikations
  åtkomstnycklar man gör det.

Detta innebär att "flödet" av konton ser ut såhär:

=== "Organisationskonto"

    1. Du loggar in på Geotorget med ett _användarkonto_ som är kopplat till ett _organisationskonto_
    2. Du beställer behörigheter som kopplas till ett _systemkonto_
    3. Du loggar in på API-managern med _systemkontot_
    4. Du skapar en _applikation_ som kopplas till _systemkontot_
    5. Du ger _applikationen_ behörighet till en eller flera APIer
    6. Du använder _applikationens_ åtkomstnycklar för att ansluta till APIerna från QGIS

=== "Privatperson"

    1. Du loggar in på Geotorget med ett _användarkonto_
    2. Du beställer behörigheter som kopplas till ditt _användarkonto_
    3. Du loggar in på API-managern med ditt _användarkonto_
    4. Du skapar en _applikation_ som kopplas till ditt _användarkonto_
    5. Du ger _applikationen_ behörighet till en eller flera APIer
    6. Du använder _applikationens_ åtkomstnycklar för att ansluta till APIerna från QGIS
