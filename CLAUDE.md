# Regeln für Claude Code in diesem Repo

Kurs: ZHAW Data Engineering, GCP-Lektionen. Die Person, mit der du arbeitest, hat wenig Erfahrung mit Google Cloud. Erkläre jeden Befehl in einem Satz, bevor du ihn ausführst. Antworte auf Deutsch und sprich die Person mit du an.

## Abrechnung
- Benutze nur das Rechnungskonto mit "Education" im Namen (Education-Guthaben). Andere Rechnungskonten fasst du nicht an.
- Erstelle nie ein Rechnungskonto, starte nie einen Free Trial, frage nie nach Kreditkartendaten.
- Aktiviere keine anderen Dienste als die in der Liste unten.

## Befehle
- Zeige jeden Befehl, der etwas erstellt, ändert oder löscht, bevor du ihn ausführst.
- Vor jeder BigQuery-Abfrage auf eine Tabelle, die wir nicht selbst angelegt haben: zuerst `bq query --dry_run`, und nenne die Bytes.
- Lösche nichts ohne ausdrückliche Bestätigung in diesem Chat. Keine --quiet Flags bei Lösch-Befehlen.
- Wenn ein Befehl fehlschlägt: zeige die Fehlermeldung, erkläre sie, schlage einen Fix vor, führe ihn nicht automatisch aus.
- Lies den Ordner `referenz/` nur, wenn die Person es ausdrücklich verlangt.

## Projekt
- Standardprojekt: das Ergebnis von `gcloud config get-value project`. Region: europe-west6. BigQuery-Location: europe-west6.
- Erlaubte APIs: cloudresourcemanager, serviceusage, cloudbilling, billingbudgets, iam, storage, bigquery, run, cloudbuild, artifactregistry, cloudscheduler, logging, monitoring, datalineage, dataplex, dataform.
- Kein Dataflow, Composer, Dataproc, Datastream, keine Compute-Engine-VMs. Wenn du meinst, eines davon sei nötig, sag es und stoppe.

## Ordner
- `ingest/` Cloud-Run-Job, der die Daten lädt
- `transform/` dbt-Projekt, entsteht in Lektion 2 aus transform/SPEC.md
- `referenz/` Musterlösungen. Lies diesen Ordner nur, wenn die Person es ausdrücklich verlangt.
- `checks/` Dataplex Data-Quality-Regeln
- `docs/` Tutorials
