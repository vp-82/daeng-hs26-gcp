SPEZIFIKATION

Ziel: Ein Cloud-Run-Job holt die Bahnverkehrsinformationen der SBB (Dataset rail-traffic-information auf data.sbb.ch, Opendatasoft-Plattform, kein Schlüssel, Lizenz: offene Nutzung mit Quellenangabe), legt jede Antwort unverändert in den Bucket des Projekts und lädt sie roh nach BigQuery, eine Partition pro Tag. Der Job ist Lehrmaterial: Studierende mit wenig Erfahrung lesen ihn. Deshalb ein einziges main.py, kurze Funktionen, deutsche Kommentare, die sagen warum, nicht was. Er ist das Gegenstück zu ingest/: dort eine Version alle paar Tage, hier laufend einzelne Meldungen.

Dateien: alerts/main.py, alerts/requirements.txt (google-cloud-bigquery>=3,<4, google-cloud-storage>=3,<4, requests>=2,<3), alerts/Dockerfile (python:3.12-slim, requirements installieren, main.py kopieren, CMD python main.py), alerts/README.md (zehn Zeilen: was der Job tut, welche Dateien, welche Umgebungsvariablen).

Konfiguration über Umgebungsvariablen mit Standardwerten: SOURCE_URL (Standard https://data.sbb.ch/api/explore/v2.1/catalog/datasets/rail-traffic-information/exports/jsonl), FROM_DATE und TO_DATE (YYYY-MM-DD, beide eingeschlossen, Standard: TO_DATE heute in UTC, FROM_DATE zwei Tage davor), BUCKET (Standard <projekt-id>-raw), DATASET (Standard raw), TABLE (Standard alerts), LOCATION (Standard europe-west6). FROM_DATE nach TO_DATE: abbrechen mit klarer Meldung.

Eigenheiten der Quelle, die der Code berücksichtigen und in Kommentaren nennen muss:
- Das Feld published ist beim Publisher ein Textfeld. Ein Bereichsfilter darauf (published >= '...') wird mit einem Typfehler abgelehnt. Was funktioniert: where=startswith(published,'YYYY-MM-DD'), ein Tag pro Anfrage. Deshalb holt der Job pro Tag im Fenster genau eine Datei.
- Jede Aktualisierung einer Meldung ist eine eigene Zeile mit neuem published. Der Job dedupliziert nicht, das ist Aufgabe der Transformation.
- startdatetime und enddatetime tragen Schweizer Lokalzeit mit dem Offset +00:00. Der Job ändert daran nichts, die Rohschicht hält fest, was kam.
- Anonym sind 6000 Anfragen pro Tag erlaubt. Ein Monat braucht 31.

Ablauf, vier Schritte, in dieser Reihenfolge und als solche im Code erkennbar:
1. Fenster bestimmen: FROM_DATE bis TO_DATE. Standard ist heute und die zwei Tage davor, absichtlich überlappend, damit ein ausgefallener Tag beim nächsten Lauf nachgeholt wird. Weil jede Partition ersetzt wird, erzeugt die Überlappung keine Duplikate.
2. Pro Tag die Meldungen holen: ein GET auf SOURCE_URL mit dem startswith-Filter, Timeout 60 Sekunden, Antwort als Bytes behalten. Zeilen zählen.
3. Original ablegen: die Antwort unverändert nach gs://BUCKET/raw/alerts/day=YYYY-MM-DD/alerts.jsonl. Das ist die Landing Zone.
4. Nach BigQuery laden: Dataset DATASET in LOCATION anlegen falls nötig. Pro Tag ein Load-Job von der GCS-URI in die Partition DATASET.TABLE$YYYYMMDD (Ingestion-Time-Partitionierung nach Tag, Partition-Decorator). Schreibmodus WRITE_TRUNCATE, damit ein zweiter Lauf desselben Tages genau diese Partition ersetzt. Format NEWLINE_DELIMITED_JSON. Schema explizit, zwölf Spalten, alle STRING: title, link, description, published, cause, startdatetime, enddatetime, dailyvaliditybegin, dailyvalidityend, type, author, description_html. ignore_unknown_values, damit ein neues Feld beim Publisher den Lauf nicht bricht. Keine Ablauffrist auf den Partitionen: die Tabelle bleibt klein, und Lektion 3 rechnet auf einem festen Monat. Ein Tag ohne Meldungen hat eine leere Datei: ablegen, aber nicht laden.

Logging auf stdout, eine Zeile pro Ereignis, genau diese Form, weil die Anleitung sie zitiert:
- "Quelle <url>, Tage <from> bis <to>"
- pro Tag in Schritt 3: "gs://<bucket>/<pfad>  <n> Zeilen"
- pro Tag in Schritt 4: "alerts$<YYYYMMDD>  <n> Zeilen"
- am Ende: "Fertig: <k> Tage, <n> Zeilen in <projekt>.<dataset>.<table>"
Fehler nicht abfangen, der Job soll bei einem Fehler mit Exit-Code ungleich null enden, das ist die Grundlage für den Alarm.

Nicht tun: kein Bereichsfilter auf published, kein autodetect, keine Typumwandlung, keine Deduplizierung, kein Schlüssel, keine zusätzlichen Bibliotheken, keine Klassen, kein argparse.
