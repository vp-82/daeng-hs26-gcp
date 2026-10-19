SPEZIFIKATION

Ziel: Ein Cloud-Run-Job holt den Schweizer GTFS-Fahrplan vom Publisher, legt ihn unverändert in den Bucket des Projekts und lädt die Dateien roh nach BigQuery, eine Partition pro Feed-Version. Der Job ist Lehrmaterial: Studierende mit wenig Erfahrung lesen ihn. Deshalb ein einziges main.py, kurze Funktionen, deutsche Kommentare, die sagen warum, nicht was.

Dateien: ingest/main.py, ingest/requirements.txt (nur google-cloud-bigquery, google-cloud-storage, requests, jeweils auf die aktuelle Major-Version festgelegt: google-cloud-bigquery>=3,<4, google-cloud-storage>=3,<4, requests>=2,<3), ingest/Dockerfile (python:3.12-slim, requirements installieren, main.py kopieren, CMD python main.py), ingest/README.md (zehn Zeilen: was der Job tut, welche Dateien, welche Umgebungsvariablen). ingest/.gitkeep löschen.

Konfiguration über Umgebungsvariablen mit Standardwerten: SOURCE_URL (Standard https://data.opentransportdata.swiss/dataset/timetable-2026-gtfs2020/permalink, kein API-Schlüssel nötig), BUCKET (Standard <projekt-id>-raw, Projekt-ID aus dem BigQuery-Client), DATASET (Standard raw), LOCATION (Standard europe-west6).

Ablauf, fünf Schritte, in dieser Reihenfolge und als solche im Code erkennbar:
1. Zip holen: ein einziger GET mit Redirects, als Stream in eine temporäre Datei. Kein HEAD vorher. Die letzte URL in der Redirect-Kette ist signiert und 60 Sekunden gültig, deshalb nur ein Versuch pro Lauf. Zip ist etwa 280 MB, Dateisystem in Cloud Run ist Arbeitsspeicher.
2. Version bestimmen: aus dem Dateinamen der endgültigen URL, Muster YYYYMMDD oder YYYY-MM-DD, normalisiert auf YYYYMMDD (Beispiel gtfs_fp2026_20261014.zip -> 20261014). Fallback: feed_version aus feed_info.txt in der Zip. Ohne Version abbrechen mit klarer Meldung.
3. Original ablegen: die Zip unverändert nach gs://BUCKET/raw/gtfs/version=<version>/gtfs.zip. Das ist die Landing Zone, was ankam bleibt erhalten.
4. Acht Dateien in den Bucket streamen: agency, routes, trips, stop_times, stops, calendar, calendar_dates, feed_info (je .txt). Direkt aus der Zip in den Bucket, nie auf Platte entpacken, stop_times.txt ist 3.7 GB. transfers.txt und frequencies.txt werden nicht geladen. Ziel gs://BUCKET/raw/gtfs/version=<version>/<name>.txt.
5. Nach BigQuery laden: Dataset DATASET in LOCATION anlegen falls nötig. Pro Datei ein Load-Job von der GCS-URI in die Tabelle DATASET.<name>, Ziel ist die Partition <name>$<version> (Ingestion-Time-Partitionierung nach Tag, Partition-Decorator). Schreibmodus WRITE_TRUNCATE, damit ein zweiter Lauf derselben Version genau diese Partition ersetzt und sonst nichts. Schema explizit, nicht autodetect: alle Spalten STRING, Spaltennamen aus der Kopfzeile der jeweiligen Datei (BOM entfernen, Anführungszeichen entfernen, unzulässige Zeichen durch _ ersetzen). ALLOW_FIELD_ADDITION, damit eine neue Spalte in einer künftigen Version dazukommt statt den Lauf zu brechen. Partitionen verfallen nach 90 Tagen. CSV mit Kopfzeile überspringen, Trennzeichen Komma, Anführungszeichen doppelt, UTF-8.

Logging auf stdout, eine Zeile pro Ereignis, genau diese Form, weil die Anleitung sie zitiert:
- "Quelle <url>, Version <version>, Zip <n> MB"
- pro Datei in Schritt 4: "gs://<bucket>/<pfad>  <n> MB"
- pro Tabelle in Schritt 5: "<name>$<version>  <zeilen> Zeilen"
- am Ende: "Fertig: Version <version> in <projekt>.<dataset>"
Temporäre Zip am Ende löschen. Fehler nicht abfangen, der Job soll bei einem Fehler mit Exit-Code ungleich null enden, das ist in Lektion 2 die Grundlage für den Alarm.

Nicht tun: keine Wiederholungen mit der signierten URL, kein autodetect, keine Typumwandlung, kein Entpacken auf Platte, keine zusätzlichen Bibliotheken, keine Klassen, kein argparse.
