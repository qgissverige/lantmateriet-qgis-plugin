# Snabbstart

## 1. Installera pluginet

1. Öppna pluginhanteraren i QGIS och sök efter "Lantmäteriet". Installera pluginet.

[:octicons-arrow-right-24: Mer om installation](installation.md)

## 2. Ställ in inställningar

1. Öppna inställningarna för QGIS (i menyn under _Inställningar_ > _Alternativ..._) och välj fliken _Lantmäteriet_
2. Klicka på knappen _Ange åtkomstnycklar_ i sektionen för _Nationella geodataplattformen_ och/eller _Övriga tjänster_
3. Ange åtkomstnycklarna (client ID respektive client secret) du fått från Lantmäteriets API-manager
4. Ange de övriga tjänster du har tillgång till i sektionen _Övriga tjänster_
5. Klicka på knappen _Verifiera konfiguration_ för att kontrollera att allt är korrekt inställt

[:octicons-arrow-right-24: Mer om inställningar](installningar.md)

## 3. Börja använda

### 3.1. Sök på adresser eller fastigheter

1. Aktivera sökrutan (klicka på den eller med ++ctrl+k++)
2. Skriv `adr` följt av en adressbeteckning, eller `fgh` följt av en fastighets-, samfällighets- eller gemensamhetsanläggningsbeteckning
3. Klicka på ett sökresultat eller välj det med piltangenterna och tryck på Enter

[:octicons-arrow-right-24: Mer om pluginets sökningar](sokning.md)

[:octicons-arrow-right-24: Mer om sökning i QGIS](https://docs.qgis.org/latest/en/docs/user_manual/introduction/qgis_gui.html#locator-bar)

### 3.2. Ladda ned adresser eller fastigheter

1. Öppna verktygslådan
2. Fäll ut gruppen _Lantmäteriet_ och dubbelklicka på någon av algoritmerna
3. Ange nödvändiga parametrar
4. Kör algoritmen

[:octicons-arrow-right-24: Mer om pluginets algoritmer](algoritmer/index.md)

[:octicons-arrow-right-24: Mer om att använda algoritmer i QGIS](https://docs.qgis.org/3.40/en/docs/user_manual/processing/index.html)

### 3.3. Använd uttryck

1. Hitta ett ställe som tillåter uttryck, t.ex. i en stil eller etikett
2. Klicka på knappen för att öppna uttrycksredigeraren
3. Börja skriva ett uttryck som använder någon av pluginets funktioner, t.ex. `address( @geometry )[ 'adressplatsattribut.postnummer' ]` för att få den närmaste adressens postnummer

[:octicons-arrow-right-24: Mer om pluginets uttryck](uttryck.md)

[:octicons-arrow-right-24: Mer om att använda uttryck i QGIS](https://docs.qgis.org/latest/en/docs/user_manual/expressions/expression.html)

### 3.4. Använd Lantmäteriets tjänster i QGIS

1. I dialogen med inställningar för QGIS, välj fliken _Lantmäteriet_
2. Klicka på knappen _Lägg till tjänster i Datakällor_
3. I datakällor finns nu anslutningar under _STAC_ och _WFS / OGC API Features_ som kan användas som vanligt i QGIS

[:octicons-arrow-right-24: Mer om datakällor i QGIS](https://docs.qgis.org/latest/en/docs/user_manual/introduction/browser.html)

[:octicons-arrow-right-24: Mer om OGC API Features i QGIS](https://docs.qgis.org/latest/en/docs/user_manual/working_with_ogc/ogc_client_support.html#wfs-and-wfs-t-client)
