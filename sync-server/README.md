# Privater Geräteabgleich für Rubrum

GitHub Pages liefert die App und den Service Worker aus. Der Worker in diesem
Verzeichnis stellt den privaten Snapshot-Endpunkt bereit. Er legt einen
Vollexport inklusive PDFs in einem privaten Cloudflare-R2-Bucket ab. Der
GitHub-Branch enthält nur die Anwendung und die Serverkonfiguration.

## Bereitstellung

1. Cloudflare R2 im eigenen Konto aktivieren und einen privaten Bucket namens
   `rubrum-sync` erstellen. Öffentliche Bucketzugriffe bleiben deaktiviert.
2. Aus diesem Verzeichnis den Worker mit `npx wrangler deploy` veröffentlichen.
   Anschließend einen zufällig erzeugten Schlüssel von mindestens 32 Zeichen
   als Worker-Secret hinterlegen: `npx wrangler secret put RUBRUM_SYNC_KEY`.
   Zum Beispiel liefert `openssl rand -hex 32` einen passenden Schlüssel.
3. Die öffentliche Worker-URL mit dem Pfad `/api/rubrum-snapshot` in
   `sync-server.json` im Stamm von `rubrum-pages` eintragen. Nur die URL
   kommt in die Datei. Den Schlüssel ausschließlich im Worker und direkt
   in Rubrum auf den eigenen Geräten hinterlegen.
4. Auf dem Gerät mit dem aktuellen Datenstand einen Vollexport sichern.
   Rubrum online öffnen und unter **Privater Geräteabgleich** den Schlüssel
   eingeben und **Diesen Stand als Startstand senden** wählen. Auf dem zweiten
   Gerät gegebenenfalls ebenfalls einen Vollexport sichern, dann denselben
   Schlüssel eingeben und **Serverstand übernehmen** wählen.

Der Abgleich läuft bei geöffneter App. Zwei unabhängig bearbeitete Stände
lösen einen Konflikt aus. Beide lassen sich vor der manuellen Entscheidung
als getrennte Backups sichern. Der Dienst speichert einen aktuellen
Vollexport mit bis zu 90 MiB. Lokale Daten und Vollexporte bleiben über
Rubrum verfügbar, wenn ein Upload wegen der Größe abgelehnt wird.
