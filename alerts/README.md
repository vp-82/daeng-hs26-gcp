# alerts: Bahnverkehrsinformationen laden

Cloud-Run-Job `ingest-alerts`: holt die Bahnverkehrsinformationen der SBB von data.sbb.ch, einen
Tag pro Anfrage, legt jede Antwort unverändert unter `gs://BUCKET/raw/alerts/day=<tag>/` ab und
lädt sie als STRING-Spalten in die Partition `alerts$<tag>` im Dataset `raw`.

Dateien: `main.py` (der Job, vier Schritte), `requirements.txt`, `Dockerfile`, `SPEC.md`
(Spezifikation).

Umgebungsvariablen (alle optional):
- `FROM_DATE` / `TO_DATE`: das Fenster, Format YYYY-MM-DD, beide Tage eingeschlossen. Standard:
  heute und die zwei Tage davor. Für den Nachlad eines Monats beim Start des Jobs setzen.
- `SOURCE_URL`: Export-Endpunkt des Datasets auf data.sbb.ch
- `BUCKET`: Ziel-Bucket, Standard `<projekt-id>-raw`
- `DATASET` / `TABLE` / `LOCATION`: Standard `raw`, `alerts` und `europe-west6`
