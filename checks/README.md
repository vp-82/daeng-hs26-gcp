# checks: Qualitätsprüfung der Rohdaten

`trips_quality.yaml` ist das Regelwerk des Dataplex-Scans `trips-quality` (europe-west6) auf `raw.trips`.
Pro Feed-Version (Partition `_PARTITIONDATE`): trip_id eindeutig, mindestens eine Million Zeilen. Pro Zeile: trip_id, route_id, service_id nicht null.
Ergebnisse: pro Lauf und Regel eine Zeile in `checks.trips_quality`, dazu in der Console unter Dataplex → Data profiling & quality.
Massgebend ist `rule_passed`. Bei SQL-Assertions nennt `rule_assertion_row_count` die Zahl der Verstösse (0 = bestanden).
`rule_rows_passed_percent` sagt nur bei Zeilenregeln etwas aus; bei Tabellenregeln und SQL-Assertions steht dort 0, auch wenn die Regel bestanden ist.
Scan aktualisieren: `gcloud dataplex datascans update data-quality trips-quality --location=europe-west6 --data-quality-spec-file=checks/trips_quality.yaml`
