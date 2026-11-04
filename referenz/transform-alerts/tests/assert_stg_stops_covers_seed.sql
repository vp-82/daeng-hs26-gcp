-- Schützt die Seed-Tabelle: jede Bus-Haltestelle, die darin steht, muss im Feed vorkommen. Sonst
-- ist ein Name verschrieben oder der Publisher hat ihn geändert, und die Linien an diesem
-- Bahnhof fehlen in jeder Entscheidung, ohne dass es jemand merkt.

SELECT b.bahnhof, b.bushalt
FROM {{ ref('vbl_bahnhoefe') }} AS b
WHERE b.bushalt NOT IN (SELECT stop_name FROM {{ ref('stg_stops') }})
