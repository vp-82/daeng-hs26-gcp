-- Schützt die Brücke zum Fahrplan: jeder Bahnhof, den das Modell als Abschnitt oder Linienende
-- liefert, sollte im Feed existieren. Ein erfundener oder verschriebener Name ("Lucerne") fände in
-- der Seed-Tabelle keinen Partner, und die Störung fiele still aus der Entscheidung.
--
-- Warnung statt Fehler: ein unbekannter Name betrifft genau diese eine Meldung und soll nicht
-- die Entscheidungen aller anderen aufhalten. Die Warnung steht im Log des Jobs, und die
-- Meldung bekommt die Stufe "keine", bis jemand nachsieht.
--
-- Direkt gegen raw.stops der neuesten Version, denn stg_stops hält nur die Haltestellen aus der
-- Seed-Tabelle, hier geht es um alle Bahnhöfe der Schweiz.

{{ config(severity='warn') }}

WITH stations AS (
    SELECT e.alert_id, station
    FROM {{ ref('int_alerts_extracted') }} AS e
    CROSS JOIN UNNEST([e.section_from, e.section_to, e.line_from, e.line_to]) AS station
    WHERE station IS NOT NULL
)

SELECT s.alert_id, s.station
FROM stations AS s
WHERE s.station NOT IN (
    SELECT stop_name
    FROM {{ source('gtfs', 'stops') }}
    WHERE _PARTITIONDATE = {{ latest_version() }}
        AND stop_name IS NOT NULL
)
