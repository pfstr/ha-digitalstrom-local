# digitalSTROM Local für Home Assistant (Kurzfassung)

Eine kleine, lokale und ereignisgesteuerte Home-Assistant-Integration für den **digitalSTROM-Server (dSS)**, dazu Blueprints aus einer echten Wohnung.

## Das Wichtigste

- **Kein Passwort in Home Assistant:** Die Einrichtung fordert beim dSS einen App-Zugang an, den du einmal im Configurator freigibst.
- **Ereignisgesteuert:** Taster, Szenen sowie Gehen und Kommen kommen sofort in Home Assistant an.
- **Schont den dS485-Bus:** Zustände kommen aus dem Zwischenspeicher des dSS und aus Ereignissen. Direkte Abfragen der Klemmen gibt es nur alle 15 Minuten.
- **Ereignisse für Automationen:** Jede Raumszene sowie Gehen und Kommen werden als `digitalstrom_local_event` gemeldet. Damit lassen sich 2× oder 4× Tippen auf einem normalen Lichtschalter frei belegen.
- **Nur lokal:** keine Cloud, kein Konto, keine Telemetrie.

## Einrichtung

1. Integration über HACS (benutzerdefiniertes Repository) oder manuell installieren und Home Assistant neu starten.
2. **Einstellungen > Geräte & Dienste > Integration hinzufügen > digitalSTROM Local**, Adresse des dSS eingeben (Standard `dss.local`, Port `8080`).
3. Im Configurator unter **System > Zugriffsberechtigung** den Zugang „Home Assistant" mit der angezeigten Endung freigeben und **Übernehmen** klicken.
4. In Home Assistant absenden.

## Blueprints

- **Bewegungslicht:** lässt von Hand eingeschaltetes Licht in Ruhe, übersteht Neustarts, optional mit Dunkelheitsschwelle, Zeitfenster und Nachthelligkeit
- **Duschmodus:** 2× Tippen hält das Badlicht an, die erste Bewegung nach einer Schonfrist beendet ihn
- **Mehrfach-Tippen:** zum Beispiel startet 4× Tippen die Musik im Raum
- **Gehen und Kommen per Handy-Anwesenheit**
- **Sonos starten** (Skript): tritt einer laufenden Gruppe bei, sonst Fortsetzen oder ein Radiosender, immer mit derselben Startlautstärke

Details und Import-Knöpfe stehen im [englischen README](README.md).

Kein offizielles Produkt der digitalSTROM AG. Lizenz: [MIT](LICENSE).
