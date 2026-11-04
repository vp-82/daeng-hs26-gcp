-- Die Bus-Haltestellen aus der Seed-Tabelle vbl_bahnhoefe, neueste Feed-Version.
--
-- In GTFS ist "Luzern" der Bahnhof und "Luzern, Bahnhof" die Bus-Haltestelle davor, zwei
-- getrennte Stationen, rund 60 Meter auseinander. Die Meldungen der SBB nennen den Bahnhof, der
-- Fahrplan der Verkehrsbetriebe Luzern kennt nur die Bus-Haltestelle. Die Seed-Tabelle ist die
-- Brücke, und sie ist eine Datei im Repo, die ein Mensch pflegt: welcher Bahnhof zu welcher
-- Haltestelle gehört, ist Fachwissen, kein Modellergebnis.
--
-- Eine Haltestelle hat in GTFS mehrere Einträge mit demselben Namen (die Station und jede Kante).
-- Wir behalten alle, weil stop_times auf die Kanten zeigt.

SELECT
    stop_id,
    stop_name,
    _PARTITIONDATE AS feed_version
FROM {{ source('gtfs', 'stops') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    AND stop_name IN (SELECT bushalt FROM {{ ref('vbl_bahnhoefe') }})
