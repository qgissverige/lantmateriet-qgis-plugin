# API-referens

Utöver funktioner för slutanvändare så erbjuder detta plugin även diverse interna klasser m.m. som kan
användas av andra plugin som önskar använda Lantmäteriets tjänster. De kan även användas från processing-skript,
för att bygga egna uttryck, m.m.

Då det primärt är intern kod så lämnas ingen garanti på varken framåt- eller bakåtkompatibilitet, men det
eftersträvas ändå att hålla kompatibilitet så långt det är rimligt.

## API-klienter

Pluginet erbjuder API-klienter för att hämta data från Lantmäteriets tjänster. Dessa klienter ger ett typat
gränssnitt för att kommunicera med tjänsterna, och är anpassade för användning i QGIS.

Klienter finns för följande APIer:

 - [Belägenhetsadress Direkt](belagenhetsadressdirekt.md)
 - [Fastighet och Samfällighet Direkt](fastighetochsamfallighetdirekt.md)
 - [Fastighetsindelning Direkt](fastighetsindelningdirekt.md)
 - [Gemensamhetsanläggning Direkt](gemensamhetsanlaggningdirekt.md)
 - [Registerbeteckning Direkt](registerbeteckningdirekt.md)

## CQL2-stöd

Vid kommunikation med OGC API Features-baserade APIer behöver man ofta bygga CQL2-frågor för att göra
mer avancerad filtrering. Funktionerna i [`lantmateriet.core.cql2`](cql2.md)-modulen kan hjälpa till med detta.
