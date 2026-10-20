-- Schützt vor Lücken im Fenster: Die Verkehrsbetriebe Luzern fahren jeden Tag. Fehlt ein Tag, ist der
-- Kalender falsch ausgewertet (Wochentag verwechselt, Ausnahmen falsch angewendet) oder der Mart zeigt
-- eine andere als die neueste Version. Das Fenster kommt deshalb aus latest_version() und nicht aus dem
-- Mart selbst; so fällt auch ein leerer Mart auf. Jede gelieferte Zeile ist ein fehlender Tag.
-- Dieselbe Variable window_days wie in int_service_dates, damit der Test mitwächst, wenn ein späteres
-- Tutorial das Fenster auf das ganze Fahrplanjahr setzt.

WITH expected_days AS (
    SELECT day_in_window AS service_date
    FROM UNNEST(GENERATE_DATE_ARRAY(
        {{ latest_version() }},
        DATE_ADD({{ latest_version() }}, INTERVAL {{ var('window_days') | int - 1 }} DAY)
    )) AS day_in_window
)

SELECT e.service_date
FROM expected_days AS e
LEFT JOIN (SELECT DISTINCT service_date FROM {{ ref('trips_per_route_day') }}) AS m
    ON m.service_date = e.service_date
WHERE m.service_date IS NULL
