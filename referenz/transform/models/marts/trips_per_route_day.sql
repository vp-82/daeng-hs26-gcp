-- Die Antwort auf die Kursfrage: wie viele Fahrten jede Linie der Verkehrsbetriebe Luzern pro Tag fährt.
--
-- Der Mart bildet immer genau eine Version ab, die neueste, und wird bei jedem Lauf ganz ersetzt.
-- Ein Mart über mehrere Versionen würde Fahrten doppelt zählen: dieselbe Fahrt am selben Tag steht
-- in jeder Version, die diesen Tag abdeckt. Wer die Antwort über die Zeit vergleichen will, baut
-- daraus eine Snapshot-Tabelle; das ist hier nicht Teil der Lektion.

-- Geclustert nach service_date: Abfragen filtern fast immer nach Tagen und lesen dann weniger.
{{ config(cluster_by=['service_date']) }}

SELECT
    sd.service_date,
    FORMAT_DATE('%A', sd.service_date) AS weekday,
    r.route_id,
    r.route_short_name,
    r.route_desc,
    r.route_type,
    a.agency_name,
    -- Jede Fahrt kommt pro Tag, an dem ihr Dienst verkehrt, genau einmal vor.
    COUNT(t.trip_id) AS n_trips,
    sd.feed_version
FROM {{ ref('int_service_dates') }} AS sd
JOIN {{ ref('stg_trips') }} AS t ON t.service_id = sd.service_id
JOIN {{ ref('stg_routes') }} AS r ON r.route_id = t.route_id
JOIN {{ ref('stg_agency') }} AS a ON a.agency_id = r.agency_id
GROUP BY
    sd.service_date,
    weekday,
    r.route_id,
    r.route_short_name,
    r.route_desc,
    r.route_type,
    a.agency_name,
    sd.feed_version
