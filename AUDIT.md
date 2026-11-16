# Rubrum – technischer Audit- und Änderungsbericht

Stand: 16.11.2026  
Arbeitsbranch: `fix/data-file-connection-audit-2026-11-16`  
Priorität: Datenintegrität → Funktionsstabilität → Installierbarkeit → UI/UX.

## Bestand

Rubrum ist eine eigenständige HTML-Anwendung mit eingebetteten JavaScript-Modulen und PDF.js. Der Bestand umfasst Gesetzesimport und -analyse, XML-/ZIP- und PDF-Verarbeitung, Markierungen, Notizen und Querverweise, Übersichten, Lernkarten, Fach-/Modulverwaltung, Kalender, Lernplan, Aufgaben, Timer, Skriptverwaltung mit PDF-Reader und Linkverwaltung.

Die Oberfläche hatte bereits drei Farbthemen, responsive Layouts, Karten-/Glasflächen, mobile Anpassungen und Systemschrift-Stacks. Die Änderungen konsolidieren diese Basis, statt die Anwendung durch einen Funktionsverlust zu ersetzen.

## Behobene Fehler und ergänzte Schutzmaßnahmen

1. **Externe Datendatei nach Neustart:** Der gespeicherte File-Handle wurde wiedergefunden und die Berechtigung abgefragt, aber der Rückgabewert von `fload()` wurde nicht in den App-Zustand übernommen. Die automatische Wiederherstellung lädt die Datei jetzt tatsächlich.
2. **Konflikt zwischen Browserstand und Datendatei:** Vor dem Überschreiben fragt Rubrum jetzt, ob die externe Datei übernommen oder der lokale Browserstand in die Datei geschrieben werden soll.
3. **Beschädigter lokaler Speicher:** Ein nicht lesbarer oder strukturell ungültiger localStorage-Datensatz wird vor der nächsten Speicherung als separate Wiederherstellungskopie abgelegt, statt stillschweigend überschrieben zu werden.
4. **Import-Zusammenführung von Markierungen:** Fehlende Markierungsdaten eines Imports überschreiben vorhandene Markierungen nicht mehr.
5. **Markierungsobjekte:** Fehlende Highlight- und Verweis-Arrays werden defensiv normalisiert.
6. **Import-/Dateivalidierung:** Gesetzesdatensätze werden auf ID und vollständige Paragrafenstruktur geprüft, bevor sie den App-Zustand ersetzen.
7. **Schreibreihenfolge:** Externe Dateischreibvorgänge werden serialisiert; Schreibfehler werden abgefangen und als Verbindungsfehler angezeigt.
8. **Lernzeit-Timer:** Ein vorhandener Timer kann nicht mehr versehentlich durch einen neuen Timer überschrieben werden. Im Vollexport wird ein laufender Timer als pausierter Snapshot gesichert, damit ein späterer Import keine künstlich verstrichene Zeit addiert.
9. **Vollständiger Export von Skripten:** Die eigentlichen Skript-PDFs und Vorschaubilder liegen in einer separaten IndexedDB. Der Vollexport nimmt sie jetzt als Daten-URLs in die Sicherung auf. Beim Import werden sie in einer atomaren IndexedDB-Transaktion wiederhergestellt. Fehlt eine referenzierte PDF-Datei, bricht der Vollexport mit einer verständlichen Meldung ab.
10. **Zusammenführen aller Module:** Der Merge-Import berücksichtigt neben Gesetzen und Markierungen jetzt auch Fächer, Aufgaben, Skripte, Links, Kalendertermine, Lernpläne und Einstellungen.
11. **Download-Aufräumen:** Object-URLs der JSON- und Markdown-Backups werden nach dem Download freigegeben.

## PWA und Bedienoberfläche

- Installationsmanifest mit Rubrum-Name, Startadresse, Theme-Farbe und dem originalen orangefarbenen R-PNG-Icon ergänzt; eine skalierbare SVG-Variante bleibt als Fallback enthalten.
- Service Worker mit Offline-Cache für Einstieg, HTML-App, Manifest und Icon ergänzt.
- `index.html` als Einstiegspunkt ergänzt; die eigentliche Anwendung bleibt das eigenständige HTML-Dokument, ohne iframe und ohne zweite Datenhaltung.
- GitHub-Actions-Workflow zur Veröffentlichung über GitHub Pages ergänzt. Er läuft erst nach Push auf `main` oder manuellem Start.
- Tastatur-Fokus, Reduced-Motion-Verhalten und kompakte Mobilansicht verbessert.

## Durchgeführte Prüfungen

- Alle vier eingebetteten JavaScript-Blöcke syntaktisch geprüft.
- Service-Worker-Skript syntaktisch geprüft; Manifest als JSON geparst.
- 43 statische DOM-IDs geprüft: keine doppelten IDs und keine fehlenden statischen Selektorziele.
- Kein `innerHTML`, `eval` oder `document.write` im App-Code festgestellt.
- PWA-Startadresse, Manifest-Link, Service-Worker-Registrierung und Offline-Cache-Ziele statisch geprüft.
- Kleine Logiktests für Gesetzesvalidierung, Normalisierung unvollständiger Markierungsobjekte und Sicherung eines beschädigten localStorage-Eintrags bestanden.
- GitHub-Compare zeigt keine Commits, die der Arbeitsbranch hinter `main` liegt; die Änderungen sind auf einer separaten Review-Linie.

## Noch offen – ausdrücklich nicht als bestanden behauptet

- Echter Chrome-/Edge-End-to-End-Test: Dateiauswahl, persistente Dateiberechtigungen, Neustart und Konflikt-Dialog.
- Vollexport und Import mit echten, großen PDF-Anhängen; inklusive IndexedDB-Wiederherstellung und Merge in ein bestehendes Profil.
- Regressionstest mit persönlichen/großen Datenbeständen sowie XML-/ZIP-/PDF-Dateien.
- PWA-Installation und Offline-Start auf Windows nach erstem Online-Aufruf.
- GitHub-Pages-Quelle muss nach dem Merge einmalig auf **GitHub Actions** gestellt werden; ein Deployment ist noch nicht gelaufen.
- Visuelle Regressionstests auf schmalen Mobilgeräten, Tablet und Desktop.
- Vollständige Accessibility-Prüfung mit Tastatur und Screenreader.

## Datenhinweis

Vor dem produktiven Einsatz einen Vollexport erstellen und separat aufbewahren. Ältere Vollexporte enthalten noch keine eingebetteten Skript-PDFs; diese Dateien müssen bei einer Wiederherstellung aus alten Exporten gegebenenfalls erneut hochgeladen werden.

Die Änderungen liegen in einem eigenen Branch und werden nicht automatisch in `main` übernommen.
