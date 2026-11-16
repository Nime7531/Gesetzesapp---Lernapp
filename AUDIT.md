# Rubrum – technischer Audit- und Änderungsbericht

Stand: 16.11.2026  
Arbeitsbranch: `fix/data-file-connection-audit-2026-11-16`  
Ziel: Datenintegrität zuerst, danach Funktionsstabilität, Installierbarkeit und UI/UX.

## Befund aus der Quellcodeprüfung

Die Anwendung ist eine große, eigenständige HTML-Datei mit eingebetteten JavaScript-Modulen und PDF.js. Der Funktionsumfang umfasst Gesetzesimport und -analyse, XML-/ZIP- und PDF-Verarbeitung, Markierungen, Notizen und Querverweise, Übersichten, Lernkarten, Fach-/Modulverwaltung, Kalender, Lernplan, Aufgaben, Timer, Skriptverwaltung mit PDF-Reader und Linkverwaltung.

Die Oberfläche besitzt bereits drei Farbthemen, ein responsives Layout, Karten-/Glasflächen, mobile Anpassungen und Systemschrift-Stacks. Das Redesign muss daher auf einer behutsamen Konsolidierung aufbauen und darf nicht durch einen Funktionsverlust oder einen kompletten Austausch der App erkauft werden.

## Behobene Fehler und Risiken

1. **Externe Datendatei nach Neustart:** Der gespeicherte File-Handle wurde wiedergefunden und die Berechtigung abgefragt, aber der Rückgabewert von `fload()` wurde nicht in den App-Zustand übernommen. Die automatische Wiederherstellung lädt die Datei jetzt tatsächlich und setzt den Verbindungsstatus.
2. **Import-Zusammenführung:** Bei einem Import ohne Markierungsdaten wurden vorhandene Markierungen eines bereits vorhandenen Gesetzes durch ein leeres Objekt ersetzt. Fehlende Markierungsdaten überschreiben bestehende Markierungen jetzt nicht mehr.
3. **Unvollständige Markierungsobjekte:** Die Prüfung auf vorhandene Markierungen setzte stets ein Array `hl` voraus. Sie ist jetzt defensiv; beim Zugriff werden fehlende Highlight-/Verweis-Arrays initialisiert.
4. **Lernzeit-Timer:** Ein neuer Timer konnte einen bestehenden Timer unter 60 Sekunden stillschweigend ersetzen. Jeder bereits laufende/gespeicherte Timer muss jetzt zuerst gebucht oder verworfen werden.
5. **Download-Aufräumen:** Object-URLs der JSON- und Markdown-Backups werden nach dem Download freigegeben.
6. **Externe Datei-Schreibpfade:** Schreibvorgänge werden serialisiert; fehlerhafte Schreibvorgänge werden abgefangen und als Verbindungsfehler angezeigt. Ungültige Dateien werden vor dem Wechsel des App-Zustands geprüft.
7. **Import-Validierung:** Gesetzesdatensätze werden vor dem Übernehmen auf ID und vollständige Paragrafenstruktur geprüft; Markierungsdaten werden normalisiert und Merge-Operationen laufen auf einer Kopie des aktuellen Zustands.
8. **Abweichende Datenstände:** Wenn lokaler Browserstand und verbundene JSON-Datei nach einem Neustart auseinanderlaufen, fragt Rubrum vor dem Überschreiben nach: Datei übernehmen oder Browserstand in die Datei schreiben.

## PWA-Ergänzung

- Installationsmanifest mit Rubrum-Name, Startadresse, Theme-Farbe und Icon ergänzt.
- Bestehendes HTML registriert den Service Worker.
- Offline-Cache für HTML-App, Manifest und Icon ergänzt.
- Das originale eigenständige HTML bleibt die eigentliche App; kein iframe-Wrapper und keine zweite Datenhaltung.
- GitHub-Actions-Workflow zur Veröffentlichung über GitHub Pages ergänzt; er läuft erst bei Push auf `main` oder manuellem Start.

## Durchgeführte Prüfungen

- Alle eingebetteten JavaScript-Blöcke nach den Änderungen erfolgreich mit `new Function()` syntaktisch geprüft.
- Service-Worker-Skript syntaktisch geprüft.
- Manifest als JSON geparst.
- Statische Prüfung der 37 referenzierten DOM-IDs: keine fehlenden IDs.
- Keine Verwendung von `innerHTML`, `eval`, `new Function` oder `document.write` im Anwendungscode festgestellt (die Syntaxprüfung nutzt `new Function` nur außerhalb der App als Prüfwerkzeug).
- Linkverwaltung beschränkt nutzbare Linkprotokolle auf HTTP(S) und mailto; externe Tabs erhalten `noopener noreferrer`.

## Noch offen – nicht als bestanden behaupten

- Browser-End-to-End-Tests für Chrome und Edge, insbesondere Dateiauswahl, persistente Berechtigungen und Neustart.
- Test mit realen, großen JSON-Exporten und XML-/ZIP-/PDF-Dateien.
- Offline-Test nach Erstinstallation und Cache-Update.
- Visuelle Regressionstests auf schmalen Mobilgeräten, Tablet und Desktop.
- Vollständige Accessibility-Prüfung mit Tastatur und Screenreader.
- Konfliktbehandlung, wenn Browserstand und externe JSON-Datei nach einem unerwarteten Schließen auseinanderlaufen.
- Wiederherstellung beschädigter lokaler Speicherstände und ein automatisierter Regressionstest des Konflikt-Dialogs.

## Sicherheits- und Datenhinweis

Vor dem produktiven Einsatz einen vollständigen Vollexport erstellen und separat aufbewahren. Die Änderungen liegen in einem eigenen Branch und werden nicht automatisch in `main` übernommen.
