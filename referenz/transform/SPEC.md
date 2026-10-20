SPEZIFIKATION

Ziel: Ein dbt-Projekt, das als Cloud-Run-Job läuft und aus den Rohdaten in raw die Antwort auf die Kursfrage baut: Wie viele Fahrten fährt jede Linie der Verkehrsbetriebe Luzern pro Tag? Das Projekt ist Lehrmaterial: Studierende mit wenig Erfahrung lesen die SQL-Modelle. Deshalb wenige Modelle, sprechende Namen, deutsche Kommentare im SQL, die sagen warum, nicht was. Keine dbt-Packages, keine Makros ausser dem einen unten.

Dateien unter transform/: dbt_project.yml, profiles.yml, Dockerfile, requirements.txt (dbt-core und dbt-bigquery, beide >=1.9,<2), README.md (zehn Zeilen: was läuft, welche Datasets entstehen, wie man es lokal startet), macros/latest_version.sql, macros/generate_schema_name.sql, models/sources.yml, models/staging/*.sql, models/intermediate/*.sql, models/marts/*.sql, models/schema.yml, tests/*.sql. transform/.gitkeep löschen, falls vorhanden.

Profil: method oauth, also Application Default Credentials, kein Schlüssel. project aus der Umgebungsvariable DBT_PROJECT. location europe-west6. Standard-Dataset staging. Ein target prod. profiles.yml liegt im Projektordner, der Job startet mit --profiles-dir .

Datasets: genau staging, intermediate und marts, ohne Präfix. Dafür generate_schema_name überschreiben, sodass ein custom schema wörtlich verwendet wird. dbt legt die Datasets an, wenn sie fehlen, in europe-west6.

Neueste Version: Alle Staging-Modelle lesen genau eine Feed-Version aus raw, die neueste. Das Makro latest_version() ermittelt zur Compile-Zeit per run_query die maximale _PARTITIONDATE von raw.feed_info und gibt sie als Datumsliteral zurück. Die Staging-Modelle filtern mit _PARTITIONDATE = diesem Literal, damit BigQuery nur diese eine Partition liest (Partition Pruning funktioniert mit Literalen, nicht mit Unterabfragen). Jedes Staging-Modell führt _PARTITIONDATE als Spalte feed_version mit. Das Makro schreibt die gewählte Version ins dbt-Log.

Staging (materialized table, Dataset staging), Spalten typisiert, Rest weggelassen:
- stg_agency: agency_id, agency_name, feed_version. Gefiltert auf die Verkehrsbetriebe Luzern. Prüfe vorher mit einer Abfrage auf raw.agency (dry run zuerst, Bytes nennen), welche agency_name auf "luzern" passen, und wähle ein Muster, das genau die Verkehrsbetriebe Luzern trifft. Das Muster ist eine dbt-Variable agency_pattern mit diesem Standardwert.
- stg_routes: route_id, agency_id, route_short_name, route_desc, route_type (INT64), feed_version. Nur Linien der Agenturen aus stg_agency.
- stg_trips: trip_id, route_id, service_id, trip_headsign, direction_id (INT64), feed_version. Nur Fahrten der Linien aus stg_routes.
- stg_calendar: service_id, monday bis sunday (BOOL), start_date, end_date (DATE aus YYYYMMDD), feed_version. Nur service_id aus stg_trips.
- stg_calendar_dates: service_id, date (DATE), exception_type (INT64), feed_version. Nur service_id aus stg_trips.
stop_times wird nicht gebraucht und nicht gelesen.

Intermediate (materialized table, Dataset intermediate):
- int_service_dates: eine Zeile pro (service_id, service_date) für jeden Tag, an dem der Dienst verkehrt, im Fenster vom Versionsdatum (feed_version) bis 13 Tage danach, also 14 Tage. Aus stg_calendar über GENERATE_DATE_ARRAY zwischen start_date und end_date, begrenzt auf das Fenster, mit dem Wochentagsflag des jeweiligen Tages. Dann calendar_dates anwenden: exception_type 1 fügt den Tag hinzu, exception_type 2 entfernt ihn. Kommentar im SQL, warum GTFS Kalender so modelliert (Regel plus Ausnahmen) und warum wir das Fenster begrenzen (das Fahrplanjahr geht bis Dezember, die Frage ist aber "die nächsten zwei Wochen"). Die Fensterlänge ist eine dbt-Variable window_days mit Standardwert 14 in dbt_project.yml: window_end ist feed_version plus window_days minus 1 Tag, und der Test, der alle Tage im Fenster prüft, benutzt dieselbe Variable, weil ein späteres Tutorial das Fenster auf das ganze Fahrplanjahr setzt.

Mart (materialized table, Dataset marts, full refresh bei jedem Lauf, kein incremental):
- trips_per_route_day: service_date, weekday (Name des Wochentags, englisch, aus FORMAT_DATE), route_id, route_short_name, route_desc, route_type, agency_name, n_trips (Anzahl Fahrten), feed_version. Eine Zeile pro (service_date, route_id). Geclustert nach service_date. Kommentar im SQL: Der Mart bildet immer genau eine Version ab, die neueste, und wird bei jedem Lauf ersetzt. Ein Mart über mehrere Versionen würde Fahrten doppelt zählen. Wer die Antwort über die Zeit vergleichen will, baut daraus eine Snapshot-Tabelle, das ist hier nicht Teil der Lektion.

sources.yml: Quelle raw mit den fünf gelesenen Tabellen, je eine Beschreibung in einem Satz.

Tests in schema.yml, nur eingebaute: stg_agency mindestens eine Zeile (als singular test), unique und not_null auf stg_routes.route_id, stg_trips.trip_id, stg_calendar.service_id. relationships stg_trips.route_id zu stg_routes.route_id. Im Mart not_null auf service_date, route_id, n_trips und feed_version. Singular tests unter tests/: (1) (service_date, route_id) im Mart ist eindeutig, (2) jeder der 14 Tage im Fenster kommt im Mart vor, (3) kein n_trips kleiner oder gleich null. Jeder Test mit einem Kommentar, was er schützt.

Dockerfile: python:3.12-slim, requirements installieren, Projekt kopieren, CMD dbt build --profiles-dir . --target prod. dbt build führt Modelle und Tests in Abhängigkeitsreihenfolge aus. Schlägt ein Test fehl, bricht dbt ab und der Job endet mit Exit-Code ungleich null. Das ist Absicht, darauf baut der Alarm.

Nicht tun: keine Packages (kein dbt_utils), kein incremental, keine Views, kein stop_times, keine Typumwandlung in raw, keine Schlüsseldatei für den Service-Account.
