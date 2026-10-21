SPEZIFIKATION

Ziel: Ein Cloud Workflow gtfs-pipeline führt die drei Teile der Pipeline in der richtigen Reihenfolge aus, und zwar nur dann weiter, wenn der vorige Teil gelungen ist: erst der Ingest-Job, dann der Dataplex-Scan trips-quality, und nur wenn der Scan bestanden ist, der Transform-Job. Der Zeitplan startet künftig den Workflow statt den Ingest-Job. Ein Alarm schickt eine E-Mail, wenn ein Job oder der Workflow fehlschlägt. Alles ist Lehrmaterial: Studierende lesen das YAML. Deutsche Kommentare, die sagen warum.

pipeline/workflow.yaml:
- Projekt und Region kommen zur Laufzeit aus der Umgebung (sys.get_env GOOGLE_CLOUD_PROJECT_ID und GOOGLE_CLOUD_LOCATION), nie aus der Datei. Die Namen ingest-gtfs, transform-gtfs und trips-quality stehen als Konstanten am Anfang in einem Schritt init.
- Schritt run_ingest: startet den Cloud-Run-Job ingest-gtfs über den Workflows-Connector für Cloud Run v2 (jobs.run) und wartet auf das Ende. Schlägt die Execution fehl, bricht der Workflow hier ab.
- Schritt run_quality_scan: startet den Dataplex-Scan trips-quality (Connector googleapis.dataplex.v1 dataScans.run, falls es ihn gibt, sonst http.post auf die REST-API mit OAuth2-Auth). Schritt wait_for_scan: fragt den Scan-Job alle 15 Sekunden ab (view FULL), bis sein Zustand SUCCEEDED, FAILED oder CANCELLED ist, höchstens 15 Minuten. Schritt check_gate: ist der Zustand nicht SUCCEEDED oder dataQualityResult.passed nicht true, wirft der Workflow einen Fehler, dessen Text die nicht bestandenen Regeln nennt. Kommentar: Das ist die Qualitätsschranke, schlechte Rohdaten erreichen den Mart nicht.
- Schritt run_transform: startet transform-gtfs über denselben Connector und wartet.
- Schritt done: gibt ein Dict zurück mit den Namen der Ingest-Execution, des Scan-Jobs, passed, und der Transform-Execution.
- Keine Wiederholungen, keine Parallelität.

pipeline/alert-policy.yaml: eine Alarmrichtlinie "gtfs-pipeline fehlgeschlagen" mit zwei Bedingungen, verbunden mit ODER, beide metrikbasiert, keine Log-Filter: (1) run.googleapis.com/job/completed_task_attempt_count mit result=failed, Summe über 5 Minuten grösser als 0, für alle Jobs im Projekt, (2) workflows.googleapis.com/finished_execution_count mit status=FAILED, Summe über 5 Minuten grösser als 0. Prüfe die genauen Label-Namen der beiden Metriken vorher über die Monitoring-API (metricDescriptors), gcloud hat dafür keinen Befehl. Benachrichtigungskanal: E-Mail an die Adresse des aktiven gcloud-Kontos (gcloud config get-value account), der Kanal wird in der AUSFÜHRUNG angelegt und seine ID in die Richtlinie eingesetzt. Dokumentation in der Richtlinie: zwei Sätze auf Deutsch, was zu tun ist (Execution in der Console öffnen, Logs lesen).

pipeline/README.md, zehn Zeilen: was der Workflow tut, warum die Schranke, wie man ihn von Hand startet, wo man Executions sieht, was der Alarm meldet.

Nicht tun: keine Projekt-IDs oder Regionen in den YAML-Dateien, keine Retries, kein Pub/Sub, kein Cloud Composer, keine Schlüsseldateien.
