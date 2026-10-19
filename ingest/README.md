# ingest: GTFS-Fahrplan laden

Cloud-Run-Job `ingest-gtfs`: holt den Schweizer GTFS-Fahrplan, legt die Zip unverändert unter `gs://BUCKET/raw/gtfs/version=<version>/` ab,
streamt acht Dateien daraus in denselben Ordner und lädt sie als STRING-Spalten in die Partition `<name>$<version>` im Dataset `raw`.

Dateien: `main.py` (der Job, fünf Schritte), `requirements.txt`, `Dockerfile`, `SPEC.md` (Spezifikation).

Umgebungsvariablen (alle optional):
- `SOURCE_URL`: Permalink des GTFS-Feeds auf opentransportdata.swiss
- `BUCKET`: Ziel-Bucket, Standard `<projekt-id>-raw`
- `DATASET` / `LOCATION`: BigQuery-Dataset und Region, Standard `raw` und `europe-west6`
