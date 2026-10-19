"""Ingest-Job: holt den Schweizer GTFS-Fahrplan und legt ihn roh in den Bucket und nach BigQuery.

Die fünf Schritte stehen in main(). Die Spezifikation steht in SPEC.md.
"""

import csv
import io
import os
import re
import shutil
import sys
import tempfile
import zipfile
from urllib.parse import urlparse

import requests
from google.cloud import bigquery, storage

SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://data.opentransportdata.swiss/dataset/timetable-2026-gtfs2020/permalink",
)
DATASET = os.environ.get("DATASET", "raw")
LOCATION = os.environ.get("LOCATION", "europe-west6")

# transfers und frequencies fehlen absichtlich: die späteren Lektionen brauchen sie nicht.
FILES = ["agency", "routes", "trips", "stop_times", "stops", "calendar", "calendar_dates", "feed_info"]

# Die Frist zählt ab dem Datum der Partition (der Feed-Version), nicht ab dem Ladetag.
PARTITION_EXPIRATION_MS = 90 * 24 * 60 * 60 * 1000
MB = 1_000_000
CHUNK = 8 * 1024 * 1024


def log(message):
    # flush, damit die Zeile sofort in Cloud Logging erscheint und nicht erst beim Beenden.
    print(message, flush=True)


def download_zip(url, path):
    # Nur ein Versuch: das letzte Ziel der Redirect-Kette ist signiert und nach 60 Sekunden ungültig.
    with requests.get(url, stream=True, allow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with open(path, "wb") as f:
            # Stückweise, damit die 280 MB nicht zusätzlich als ein Block im Python-Speicher liegen.
            for chunk in response.iter_content(chunk_size=CHUNK):
                f.write(chunk)
        return response.url


def normalize_version(text):
    # Publisher schreiben mal 20261014, mal 2026-10-14; der Partition-Decorator braucht YYYYMMDD.
    match = re.search(r"(?<!\d)(\d{4})-?(\d{2})-?(\d{2})(?!\d)", text)
    return "".join(match.groups()) if match else None


def determine_version(final_url, zip_path):
    version = normalize_version(os.path.basename(urlparse(final_url).path))
    if version:
        return version
    # Fallback, falls der Dateiname einmal neutral ist: feed_info.txt nennt die Version auch.
    with zipfile.ZipFile(zip_path) as z:
        if "feed_info.txt" in z.namelist():
            with z.open("feed_info.txt") as f:
                row = next(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")), {})
                version = normalize_version(row.get("feed_version", ""))
    if not version:
        sys.exit(f"Keine Version gefunden: weder im Dateinamen von {final_url} noch in feed_info.txt")
    return version


def upload_original(bucket, zip_path, version):
    # Landing Zone: was ankam, bleibt erhalten, damit wir jede Version später neu laden können.
    bucket.blob(f"raw/gtfs/version={version}/gtfs.zip").upload_from_filename(zip_path)


def upload_members(bucket, zip_path, version):
    with zipfile.ZipFile(zip_path) as z:
        for name in FILES:
            info = z.getinfo(f"{name}.txt")
            path = f"raw/gtfs/version={version}/{name}.txt"
            # Direkt von der Zip in den Bucket: entpackt wäre stop_times.txt 3.7 GB, mehr als der Job Speicher hat.
            with z.open(info) as src, bucket.blob(path).open("wb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
            log(f"gs://{bucket.name}/{path}  {info.file_size / MB:.1f} MB")


def column_names(zip_path, name):
    with zipfile.ZipFile(zip_path) as z, z.open(f"{name}.txt") as f:
        # utf-8-sig entfernt das BOM, das sonst im ersten Spaltennamen landet.
        header = io.TextIOWrapper(f, encoding="utf-8-sig").readline()
    # csv.reader entfernt die Anführungszeichen; BigQuery erlaubt in Spaltennamen nur Buchstaben, Ziffern und _.
    return [re.sub(r"[^A-Za-z0-9_]", "_", col.strip()) for col in next(csv.reader([header]))]


def load_table(bq, uri, table_id, columns):
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        field_delimiter=",",
        quote_character='"',
        encoding="UTF-8",
        # Alles STRING: die Rohschicht hält fest, was kam; Typen setzen erst die Transformationen.
        schema=[bigquery.SchemaField(column, "STRING") for column in columns],
        # Ersetzt nur die Partition dieser Version, ein zweiter Lauf erzeugt also keine Duplikate.
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        # Eine neue Spalte in einer künftigen Version kommt dazu, statt den Lauf abzubrechen.
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            expiration_ms=PARTITION_EXPIRATION_MS,
        ),
    )
    job = bq.load_table_from_uri(uri, table_id, job_config=job_config, location=LOCATION)
    job.result()
    return job.output_rows


def load_bigquery(bq, bucket_name, zip_path, version):
    dataset = bigquery.Dataset(f"{bq.project}.{DATASET}")
    dataset.location = LOCATION
    bq.create_dataset(dataset, exists_ok=True)
    for name in FILES:
        uri = f"gs://{bucket_name}/raw/gtfs/version={version}/{name}.txt"
        table_id = f"{bq.project}.{DATASET}.{name}${version}"
        rows = load_table(bq, uri, table_id, column_names(zip_path, name))
        log(f"{name}${version}  {rows} Zeilen")


def main():
    bq = bigquery.Client()
    bucket_name = os.environ.get("BUCKET", f"{bq.project}-raw")
    bucket = storage.Client(project=bq.project).bucket(bucket_name)

    fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        # Schritt 1: Zip holen
        final_url = download_zip(SOURCE_URL, zip_path)

        # Schritt 2: Version bestimmen
        version = determine_version(final_url, zip_path)
        log(f"Quelle {SOURCE_URL}, Version {version}, Zip {os.path.getsize(zip_path) / MB:.1f} MB")

        # Schritt 3: Original ablegen
        upload_original(bucket, zip_path, version)

        # Schritt 4: Acht Dateien in den Bucket streamen
        upload_members(bucket, zip_path, version)

        # Schritt 5: Nach BigQuery laden
        load_bigquery(bq, bucket_name, zip_path, version)
    finally:
        # Kein except: ein Fehler soll den Job mit Exit-Code ungleich null beenden. Aufräumen trotzdem,
        # weil die Zip in Cloud Run Arbeitsspeicher belegt und lokal sonst in /tmp liegen bliebe.
        os.remove(zip_path)

    log(f"Fertig: Version {version} in {bq.project}.{DATASET}")


if __name__ == "__main__":
    main()
