# Rubrum – Gesetzes- und Lernapp

Rubrum ist eine browserbasierte Lern- und Arbeitsumgebung für Gesetzestexte und die Organisation des Jurastudiums. Die Anwendung bleibt bewusst als eigenständige HTML-Datei nutzbar; alle bestehenden Module und Datenstrukturen bleiben erhalten.

## Starten

- **Direkt lokal:** `Rubrum mit Vollexport.html` in einem aktuellen Browser öffnen. Für die Dateiverbindung und PWA-Funktionen wird eine sichere Browserumgebung benötigt (HTTPS oder localhost).
- **Als installierbare Windows-PWA:** Das Repository über GitHub Pages oder einen anderen HTTPS-Host bereitstellen, die App einmal online öffnen und anschließend in Microsoft Edge oder Google Chrome über das Installieren-Symbol in der Adressleiste bzw. das App-Menü installieren.
- **Offline:** Nach dem ersten erfolgreichen Online-Aufruf legt der Service Worker App, Manifest und Icon im Cache ab. Die App kann danach auch ohne Verbindung geöffnet werden.

## Datensicherheit

- Die App speichert ihren Arbeitsstand im Browser und kann zusätzlich eine externe JSON-Datendatei verbinden.
- Nutze regelmäßig **Vollexport** und bewahre die exportierte JSON-Datei an einem zweiten Ort auf.
- Beim Zusammenführen eines Imports bleiben vorhandene Markierungen erhalten, wenn der Import für ein Gesetz keine Markierungsdaten enthält.
- Eine verbundene Datendatei sollte nach Änderungen vollständig geschrieben werden, bevor Browser oder Gerät geschlossen werden.
- Die Browserberechtigung für eine verbundene Datei kann nach Neustart oder Browserupdate erneut angefordert werden.

## PWA-Dateien

- `manifest.webmanifest`: Installationsmetadaten und Startadresse
- `sw.js`: Offline-Cache für App, Manifest und Icon
- `icons/rubrum.svg`: skalierbares orangefarbenes Rubrum-R-Icon

## Funktionsumfang

Gesetzestexte und XML-/ZIP-Import, PDF-Textimport, Paragrafenmarkierung, Notizen und Verweise, Übersichten und Lernkarten, Modul-/Fachverwaltung, Lernplan, Kalender, Aufgaben, Lernzeit-Timer, Skriptverwaltung mit PDF-Reader sowie Linkverwaltung.

## Qualitätssicherung

Die aktuelle Reparaturserie ist in einem separaten Branch vorbereitet und über einen Draft-Pull-Request einsehbar. Syntax- und statische Integritätsprüfungen wurden ausgeführt. Ein vollständiger Browser-End-to-End-Test mit echten Dateidialogen, Berechtigungen und persönlichen Datensätzen steht noch aus; Änderungen daher vor dem produktiven Einsatz mit einem Backup testen.
