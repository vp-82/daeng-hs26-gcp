# pipeline: Verkettung und Alarm

Workflow `gtfs-pipeline` (`workflow.yaml`): startet den Job `ingest-gtfs`, dann den Dataplex-Scan `trips-quality`, und nur wenn der Scan bestanden ist, den Job `transform-gtfs`. Scheitert ein Teil, endet der Workflow mit einem Fehler.
Warum die Schranke: Ohne sie würde dbt auch fehlerhafte Rohdaten in den Mart schreiben; so behält der Mart die letzte gute Version.
Zeitplan: Der Scheduler-Job `gtfs-pipeline-schedule` startet den Workflow Montag und Donnerstag um 11:30 (Europe/Zurich).

Von Hand starten: `gcloud workflows run gtfs-pipeline --location=europe-west6`
Executions mit allen Schritten: Console → Workflows → gtfs-pipeline → Executions; die einzelnen Jobs unter Cloud Run → Jobs.

Alarm (`alert-policy.yaml`): E-Mail, sobald ein Cloud-Run-Job im Projekt oder der Workflow fehlschlägt; der Vorfall steht unter Monitoring → Alerting.
`CHANNEL_ID` in `alert-policy.yaml` ist ein Platzhalter und wird erst beim Anlegen der Richtlinie durch den eigenen E-Mail-Kanal ersetzt.
