# transform: Fahrten pro Linie und Tag

Cloud-Run-Job `transform-gtfs`: führt `dbt build` aus und baut aus der neuesten Feed-Version in `raw` die Fahrten pro Linie und Tag der Verkehrsbetriebe Luzern, `window_days` Tage ab dem Versionsdatum (Standard 14, in `dbt_project.yml`).
Modelle und Tests laufen in Abhängigkeitsreihenfolge; schlägt ein Test fehl, endet der Job mit einem Fehler.

Datasets (in europe-west6, dbt legt sie an): `staging` (`stg_*`, typisiert und auf Luzern gefiltert), `intermediate` (`int_service_dates`), `marts` (`trips_per_route_day`).

Dateien: `models/` (SQL und `schema.yml` mit Tests), `tests/` (eigene Tests), `macros/`, `dbt_project.yml`, `profiles.yml`, `Dockerfile`, `SPEC.md`.

Lokal starten (nach `gcloud auth application-default login`):
`cd transform && python -m venv .venv && .venv/bin/pip install -r requirements.txt && DBT_PROJECT=$(gcloud config get-value project) .venv/bin/dbt build --profiles-dir . --target prod`
