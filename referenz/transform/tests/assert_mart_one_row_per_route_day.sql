-- Schützt die Körnung des Marts: eine Zeile pro Tag und Linie. Zwei Zeilen für dieselbe Linie am
-- selben Tag entstehen, wenn eine Spalte im GROUP BY mehrere Werte hat (etwa zwei Versionen oder zwei
-- Agenturnamen), und dann summiert jede Auswertung darüber die Fahrten doppelt.

SELECT service_date, route_id, COUNT(*) AS n_rows
FROM {{ ref('trips_per_route_day') }}
GROUP BY service_date, route_id
HAVING COUNT(*) > 1
