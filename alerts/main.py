"""Ingest-Job: holt die Bahnverkehrsinformationen der SBB und legt sie roh in den Bucket und nach BigQuery.

Die vier Schritte stehen in main(). Die Spezifikation steht in SPEC.md.

Unterschied zum GTFS-Job in ingest/: dort kommt alle paar Tage eine ganze Version, hier kommen
laufend einzelne Meldungen. Darum holt dieser Job pro Tag eine Datei und schreibt pro Tag eine
Partition, und darum kann er jeden Tag laufen.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone

import requests
from google.cloud import bigquery, storage

# Export-Endpunkt der Opendatasoft-Plattform von data.sbb.ch. Kein Schlüssel nötig,
# 6000 Anfragen pro Tag erlaubt. Wir brauchen eine pro Tag im Fenster.
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/rail-traffic-information/exports/jsonl",
)
DATASET = os.environ.get("DATASET", "raw")
TABLE = os.environ.get("TABLE", "alerts")
LOCATION = os.environ.get("LOCATION", "europe-west6")

# Die zwölf Felder, die der Publisher liefert, alle als STRING. Die Rohschicht hält fest, was kam;
# Typen setzen erst die Transformationen (Lektion 2 und 3). Zwei Felder sind dort besonders:
# published ist beim Publisher Text, nicht Zeitstempel, und startdatetime/enddatetime tragen
# Schweizer Lokalzeit mit einem falschen +00:00. Beides wird in stg_alerts geradegebogen.
COLUMNS = [
    "title", "link", "description", "published", "cause", "startdatetime", "enddatetime",
    "dailyvaliditybegin", "dailyvalidityend", "type", "author", "description_html",
]


def log(message):
    # flush, damit die Zeile sofort in Cloud Logging erscheint und nicht erst beim Beenden.
    print(message, flush=True)


def parse_window():
    # Standard: heute und die zwei Tage davor. Die Überlappung ist Absicht: ein Tag, dessen Lauf
    # ausgefallen ist, wird beim nächsten Lauf nachgeholt, und weil jede Partition ersetzt statt
    # ergänzt wird, entstehen dabei keine Duplikate. Für einen Nachlad setzt man FROM_DATE und
    # TO_DATE beim Start des Jobs, zum Beispiel auf den ganzen Oktober.
    today = datetime.now(timezone.utc).date()
    to_date = date.fromisoformat(os.environ.get("TO_DATE", today.isoformat()))
    from_date = date.fromisoformat(os.environ.get("FROM_DATE", (to_date - timedelta(days=2)).isoformat()))
    if from_date > to_date:
        sys.exit(f"FROM_DATE {from_date} liegt nach TO_DATE {to_date}")
    return from_date, to_date


def fetch_day(day):
    # published ist beim Publisher ein Textfeld. Ein Bereichsfilter (published >= ...) wird deshalb
    # abgelehnt, ein Präfix pro Tag funktioniert. Die Antwort ist JSON Lines: eine Meldung pro Zeile.
    params = {"where": f"startswith(published,'{day.isoformat()}')"}
    response = requests.get(SOURCE_URL, params=params, timeout=60)
    response.raise_for_status()
    body = response.content
    rows = body.count(b"\n") + (1 if body and not body.endswith(b"\n") else 0)
    return body, rows


def upload_day(bucket, day, body, rows):
    # Landing Zone: die Antwort des Publishers unverändert, ein Ordner pro Tag. Was ankam, bleibt
    # erhalten, auch wenn der Publisher die Meldung später ändert oder löscht.
    path = f"raw/alerts/day={day.isoformat()}/alerts.jsonl"
    bucket.blob(path).upload_from_string(body, content_type="application/x-ndjson")
    log(f"gs://{bucket.name}/{path}  {rows} Zeilen")
    return f"gs://{bucket.name}/{path}"


def load_day(bq, uri, day):
    # Ziel ist die Partition des Tages (Partition-Decorator $YYYYMMDD), Schreibmodus WRITE_TRUNCATE:
    # ein zweiter Lauf desselben Tages ersetzt genau diese Partition und sonst nichts.
    version = day.strftime("%Y%m%d")
    table_id = f"{bq.project}.{DATASET}.{TABLE}${version}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[bigquery.SchemaField(column, "STRING") for column in COLUMNS],
        # Ein neues Feld beim Publisher bricht den Lauf nicht, es wird vorerst ignoriert.
        ignore_unknown_values=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        # Keine Ablauffrist: die Tabelle bleibt klein (einige hundert Zeilen pro Monat), und
        # Lektion 3 rechnet auf einem festen Monat, der nicht verschwinden soll.
        time_partitioning=bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY),
    )
    job = bq.load_table_from_uri(uri, table_id, job_config=job_config, location=LOCATION)
    job.result()
    log(f"{TABLE}${version}  {job.output_rows} Zeilen")
    return job.output_rows


def main():
    bq = bigquery.Client()
    bucket_name = os.environ.get("BUCKET", f"{bq.project}-raw")
    bucket = storage.Client(project=bq.project).bucket(bucket_name)

    dataset = bigquery.Dataset(f"{bq.project}.{DATASET}")
    dataset.location = LOCATION
    bq.create_dataset(dataset, exists_ok=True)

    # Schritt 1: Fenster bestimmen
    from_date, to_date = parse_window()
    log(f"Quelle {SOURCE_URL}, Tage {from_date} bis {to_date}")

    total = 0
    day = from_date
    while day <= to_date:
        # Schritt 2: Meldungen eines Tages holen
        body, rows = fetch_day(day)

        # Schritt 3: Original ablegen
        uri = upload_day(bucket, day, body, rows)

        # Schritt 4: Nach BigQuery laden. Ein Tag ohne Meldungen hat eine leere Datei, da gibt
        # es nichts zu laden. Die Partition bleibt dann, wie sie war.
        if rows:
            total += load_day(bq, uri, day)
        day += timedelta(days=1)

    log(f"Fertig: {(to_date - from_date).days + 1} Tage, {total} Zeilen in {bq.project}.{DATASET}.{TABLE}")


if __name__ == "__main__":
    main()
