-- Schützt die Dauer: ein Ende vor dem Beginn ergäbe eine negative Dauer und damit null betroffene
-- Fahrten, die Störung fiele still aus der Entscheidung. Das Modell hat die beiden Zeiten aus dem
-- Text gelesen, die Regel vertraut ihnen nur, wenn sie zusammenpassen.

SELECT alert_id, begin_at, end_at
FROM {{ ref('int_alerts_extracted') }}
WHERE end_at IS NOT NULL
    AND end_at < begin_at
