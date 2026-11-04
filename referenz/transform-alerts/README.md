# transform-alerts: Musterlösung für Lektion 3

Die Modelle, die Lektion 3 zum dbt-Projekt aus Lektion 2 hinzufügt. Sie setzen `transform/SPEC-ALERTS.md`
um und erwarten ein Projekt, das `transform/SPEC.md` erfüllt (`stg_routes`, `stg_trips`,
`trips_per_route_day`, Makro `latest_version()`).

Nur neue Dateien, nichts aus Lektion 2 wird überschrieben. Darum eigene Dateinamen für Quellen und
Tests (`sources_alerts.yml`, `schema_alerts.yml`) und Variablen mit Standardwert im SQL statt in
`dbt_project.yml`.

Hinein ins eigene Projekt, falls die eigene Fassung nicht baut (nur die drei Ordner, damit
`transform/README.md` und der Rest aus Lektion 2 unberührt bleiben):

```bash
cp -R referenz/transform-alerts/models referenz/transform-alerts/seeds referenz/transform-alerts/tests transform/
```

Dateien:
- `seeds/vbl_bahnhoefe.csv`: welcher Bahnhof zu welcher Bus-Haltestelle gehört, von Hand gepflegt
- `models/staging/stg_alerts.sql`: eine Zeile pro Meldung, Zeiten korrigiert, Text ohne HTML
- `models/staging/stg_stops.sql`: die Haltestellen aus der Seed-Tabelle
- `models/intermediate/int_routes_per_stop.sql`: welche Linie an welcher Haltestelle hält (liest stop_times)
- `models/intermediate/int_alerts_extracted.sql`: hier liest das Sprachmodell, inkrementell, nie zweimal pro Meldung
- `models/marts/alert_decisions.sql`: die Regel, eine Stufe pro Meldung mit Begründung
- `models/sources_alerts.yml`, `models/schema_alerts.yml`, `tests/*.sql`: Quellen und Tests

Variablen (Standardwerte im SQL): `alerts_from` und `alerts_to` (Fenster, Standard Oktober 2026),
`vertex_connection` (Standard `vertex-ai`), `gemini_model` (Standard `gemini-3.8-flash`),
`decision_major` und `decision_minor` (Schwellen der Regel, Standard 100 und 10). Beispiel:
`dbt build --vars '{alerts_from: "2026-11-01", alerts_to: "2026-11-30"}'`

Voraussetzungen im Projekt: Dataset `raw` mit `alerts`, `stops`, `stop_times`, eine
BigQuery-Verbindung `vertex-ai` in europe-west6, deren Service-Account Agent Platform User ist,
und für den Job `transform-gtfs` die Rolle BigQuery Connection User auf `transform-sa`.
