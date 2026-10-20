-- Schützt davor, dass Linien ohne Fahrten als Zeile mit 0 im Mart stehen. Heute verhindern das die
-- inneren Joins; würde jemand daraus einen LEFT JOIN machen, zählte jede Linie an jedem Tag mit, auch
-- wenn sie nicht fährt, und Durchschnitte über den Mart wären falsch. Jede gelieferte Zeile ist ein Fehler.

SELECT service_date, route_id, n_trips
FROM {{ ref('trips_per_route_day') }}
WHERE n_trips <= 0
