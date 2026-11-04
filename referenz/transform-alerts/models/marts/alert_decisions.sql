-- Die Entscheidung: Was bedeutet eine Bahnstörung für die Verkehrsbetriebe Luzern?
--
-- Hier entscheidet eine Regel, kein Modell. Das Modell hat in int_alerts_extracted Fakten
-- geliefert, der Fahrplan liefert die Fahrten pro Linie, die Seed-Tabelle sagt, welcher Bahnhof
-- welche Bus-Haltestelle betrifft. Die Regel verbindet das zu einer von drei Stufen.
--
-- Die Regel fragt dreierlei. Wo: Liegt der gestörte Abschnitt selbst im Gebiet der
-- Verkehrsbetriebe (Meggen - Immensee), fahren dort keine Züge, und Ersatzverkehr ist eine
-- echte Frage. Endet nur die betroffene Linie in Luzern (Lenzburg - Beinwil am See auf der
-- Linie Lenzburg - Luzern), kommen Züge verspätet oder gar nicht an, das ist ein Hinweis für
-- die Planung. Was: Ausfall oder Ersatzverkehr, oder nur Verspätung. Wie lange: unter
-- min_duration_minutes (Standard 30) bekommt eine Störung keine Stufe, so kurz plant niemand um.
-- Die Dauer ist die einzige Schwelle, und sie ist eine Variable, die jemand begründen kann.
--
-- Die Schätzung der betroffenen Fahrten zählt nur die Linien an den Haltestellen, die die Stufe
-- entscheiden: bei einer Störung im Abschnitt die Haltestellen im Abschnitt, sonst das
-- Linienende. Fahrten pro Tag dieser Linien, mal Dauer in Stunden, durch 24, als ob nachts gleich
-- viel führe wie am Mittag. Grob, aber nachvollziehbar, und sie steht in der Begründung.
--
-- Der Mart hält alle extrahierten Meldungen im Fenster, auch die ohne Bezug zu Luzern, damit
-- man sieht, was die Regel ausgeschlossen hat. Er wird bei jedem Lauf ganz ersetzt.

WITH affected_stations AS (
    -- Welche Bahnhöfe aus der Seed-Tabelle die Meldung nennt, und ob im Abschnitt oder nur als
    -- Ende der Linie.
    SELECT DISTINCT
        e.alert_id,
        b.bahnhof,
        b.bushalt,
        COALESCE(station IN (e.section_from, e.section_to), FALSE) AS in_section
    FROM {{ ref('int_alerts_extracted') }} AS e
    CROSS JOIN UNNEST([e.section_from, e.section_to, e.line_from, e.line_to]) AS station
    JOIN {{ ref('vbl_bahnhoefe') }} AS b ON b.bahnhof = station
),

deciding_stations AS (
    -- Liegt ein Bahnhof im Abschnitt, zählen nur die Haltestellen im Abschnitt. Sonst das
    -- Linienende. So zählt eine Störung in Emmenbrücke die zwei Linien dort, nicht die 26 am
    -- Bahnhof Luzern, in dem die Linie endet.
    SELECT alert_id, bahnhof, bushalt, in_section
    FROM affected_stations
    QUALIFY in_section OR NOT LOGICAL_OR(in_section) OVER (PARTITION BY alert_id)
),

trips_per_day AS (
    -- Aus dem Mart von Lektion 2: Fahrten pro Linie und Tag, gemittelt über sein Fenster.
    SELECT
        route_id,
        AVG(n_trips) AS trips_per_day
    FROM {{ ref('trips_per_route_day') }}
    GROUP BY route_id
),

affected_routes AS (
    -- Jede Linie pro Meldung einmal, auch wenn sie an zwei genannten Haltestellen hält.
    SELECT
        s.alert_id,
        r.route_id,
        r.route_short_name,
        s.bushalt,
        s.in_section,
        t.trips_per_day
    FROM deciding_stations AS s
    JOIN {{ ref('int_routes_per_stop') }} AS r ON r.stop_name = s.bushalt
    JOIN trips_per_day AS t ON t.route_id = r.route_id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.alert_id, r.route_id ORDER BY s.bushalt) = 1
),

per_alert AS (
    SELECT
        alert_id,
        COUNT(*) AS n_routes,
        STRING_AGG(route_short_name, ', ' ORDER BY SAFE_CAST(REGEXP_EXTRACT(route_short_name, r'\d+') AS INT64), route_short_name) AS routes,
        STRING_AGG(DISTINCT bushalt, ', ') AS bus_stops,
        LOGICAL_OR(in_section) AS in_section,
        SUM(trips_per_day) AS trips_per_day
    FROM affected_routes
    GROUP BY alert_id
),

facts AS (
    SELECT
        e.alert_id,
        a.title,
        a.start_at,
        a.end_at,
        e.begin_at,
        e.end_at AS extracted_end_at,
        e.cause,
        e.effect,
        e.severity,
        e.replacement_bus,
        e.lines,
        p.bus_stops,
        p.n_routes,
        p.routes,
        p.in_section,
        p.trips_per_day,
        -- Dauer aus den extrahierten Zeiten. Fehlt das Ende, nehmen wir das Ende aus der Quelle.
        TIMESTAMP_DIFF(COALESCE(e.end_at, a.end_at), e.begin_at, MINUTE) AS duration_minutes
    FROM {{ ref('int_alerts_extracted') }} AS e
    JOIN {{ ref('stg_alerts') }} AS a USING (alert_id)
    LEFT JOIN per_alert AS p USING (alert_id)
),

estimate AS (
    SELECT
        *,
        -- Ohne Ende keine Dauer: dann 0, damit Begründung und Tests nicht an NULL scheitern.
        COALESCE(duration_minutes, 0) / 60.0 AS duration_hours,
        CAST(ROUND(COALESCE(trips_per_day, 0) * GREATEST(COALESCE(duration_minutes, 0), 0) / 1440) AS INT64) AS affected_trips
    FROM facts
)

SELECT
    alert_id,
    title,
    start_at,
    begin_at,
    extracted_end_at AS end_at,
    duration_hours,
    cause,
    effect,
    severity,
    replacement_bus,
    lines,
    -- Wo die Störung liegt: im Gebiet (Abschnitt) oder nur auf einer Linie dorthin (Linienende).
    CASE
        WHEN n_routes IS NULL THEN NULL
        WHEN in_section THEN 'Abschnitt'
        ELSE 'Linienende'
    END AS location_kind,
    bus_stops,
    n_routes,
    routes,
    affected_trips,
    -- Die Regel: wo, was, wie lange.
    CASE
        WHEN n_routes IS NULL THEN 'keine'
        WHEN COALESCE(duration_minutes, 0) < {{ var('min_duration_minutes', 30) }} THEN 'keine'
        WHEN in_section AND effect IN ('Ausfall', 'Ersatzverkehr') THEN 'Ersatzverkehr prüfen'
        ELSE 'Planungshinweis'
    END AS decision,
    -- Die Begründung in einem Satz, damit die Entscheidung ohne SQL nachvollziehbar ist.
    CASE
        WHEN n_routes IS NULL THEN 'kein Bahnhof im Gebiet der Verkehrsbetriebe Luzern genannt'
        WHEN COALESCE(duration_minutes, 0) < {{ var('min_duration_minutes', 30) }}
            THEN FORMAT('nur %d Minuten, unter der Mindestdauer', COALESCE(duration_minutes, 0))
        ELSE FORMAT(
            '%s %s, %d Linien an %s, %.1f h, ca. %d Fahrten',
            effect,
            IF(in_section, 'im Abschnitt', 'auf einer Linie nach Luzern'),
            n_routes, bus_stops, duration_hours, affected_trips
        )
    END AS reason
FROM estimate
