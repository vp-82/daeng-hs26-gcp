-- Welche Linien der Verkehrsbetriebe Luzern an welcher Haltestelle aus der Seed-Tabelle halten.
--
-- Das steht nur in stop_times, der grössten Tabelle im Feed: 42 Millionen Zeilen pro Version,
-- rund 2 GB. Darum liest dieses Modell die Quelle direkt, mit Partitionsfilter und sofort auf
-- unsere Fahrten und Haltestellen eingeschränkt, statt eine Staging-Kopie anzulegen, die so
-- gross wäre wie das Original. Einmal pro Lauf, als Tabelle: danach kostet die Frage "welche
-- Linien halten an Luzern, Bahnhof" nichts mehr.

SELECT DISTINCT
    s.stop_name,
    r.route_id,
    r.route_short_name,
    r.feed_version
FROM {{ source('gtfs', 'stop_times') }} AS st
JOIN {{ ref('stg_stops') }} AS s ON s.stop_id = st.stop_id
JOIN {{ ref('stg_trips') }} AS t ON t.trip_id = st.trip_id
JOIN {{ ref('stg_routes') }} AS r ON r.route_id = t.route_id
WHERE st._PARTITIONDATE = {{ latest_version() }}
