-- GTFS listet die Fahrtage eines Dienstes nicht einzeln auf, sondern beschreibt sie als Regel plus
-- Ausnahmen: calendar sagt "montags bis freitags, von Dezember bis Dezember", calendar_dates fügt
-- einzelne Tage hinzu (exception_type 1) oder nimmt sie weg (exception_type 2), etwa an Feiertagen.
-- Das hält den Feed klein, heisst aber: Ob ein Dienst an einem bestimmten Tag fährt, steht nirgends
-- direkt, man muss Regel und Ausnahmen zusammenrechnen. Das tut dieses Modell.
--
-- Wir rechnen nur window_days Tage ab dem Versionsdatum aus (Standard 14, in dbt_project.yml). Das
-- Fahrplanjahr reicht bis Dezember, die Frage gilt aber den nächsten zwei Wochen; ausserdem ändert jede
-- neue Version die fernere Zukunft ohnehin. Ein späteres Tutorial setzt das Fenster auf das ganze
-- Fahrplanjahr, darum ist die Länge eine Variable und keine feste Zahl.

WITH date_window AS (
    -- Alle Staging-Modelle tragen dieselbe Version, darum genügt eine Zeile.
    -- Minus 1, weil das Versionsdatum selbst der erste Tag im Fenster ist.
    SELECT DISTINCT
        feed_version AS window_start,
        DATE_ADD(feed_version, INTERVAL {{ var('window_days') | int - 1 }} DAY) AS window_end
    FROM {{ ref('stg_calendar') }}
),

regular_days AS (
    -- Die Regel: jeder Tag im Fenster, der in der Gültigkeit des Dienstes liegt und dessen
    -- Wochentagsflag gesetzt ist. Liegt der Dienst ganz ausserhalb des Fensters, ist der Anfang
    -- nach dem Ende und GENERATE_DATE_ARRAY liefert eine leere Liste: der Dienst fällt weg.
    SELECT
        c.service_id,
        calendar_day AS service_date,
        c.feed_version
    FROM {{ ref('stg_calendar') }} AS c
    CROSS JOIN date_window AS w
    CROSS JOIN UNNEST(GENERATE_DATE_ARRAY(
        GREATEST(c.start_date, w.window_start),
        LEAST(c.end_date, w.window_end)
    )) AS calendar_day
    -- DAYOFWEEK zählt in BigQuery ab Sonntag = 1.
    WHERE CASE EXTRACT(DAYOFWEEK FROM calendar_day)
        WHEN 1 THEN c.sunday
        WHEN 2 THEN c.monday
        WHEN 3 THEN c.tuesday
        WHEN 4 THEN c.wednesday
        WHEN 5 THEN c.thursday
        WHEN 6 THEN c.friday
        WHEN 7 THEN c.saturday
    END
),

added_days AS (
    SELECT cd.service_id, cd.date AS service_date, cd.feed_version
    FROM {{ ref('stg_calendar_dates') }} AS cd
    CROSS JOIN date_window AS w
    WHERE cd.exception_type = 1
        AND cd.date BETWEEN w.window_start AND w.window_end
),

removed_days AS (
    SELECT cd.service_id, cd.date AS service_date, cd.feed_version
    FROM {{ ref('stg_calendar_dates') }} AS cd
    CROSS JOIN date_window AS w
    WHERE cd.exception_type = 2
        AND cd.date BETWEEN w.window_start AND w.window_end
)

-- Erst Regel und hinzugefügte Tage vereinen, dann die entfernten abziehen. UNION DISTINCT, damit
-- ein Tag, der in der Regel steht und zusätzlich als Ausnahme 1, nur einmal vorkommt.
(
    SELECT service_id, service_date, feed_version FROM regular_days
    UNION DISTINCT
    SELECT service_id, service_date, feed_version FROM added_days
)
EXCEPT DISTINCT
SELECT service_id, service_date, feed_version FROM removed_days
