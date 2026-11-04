# Data Engineering auf Google Cloud

Begleitrepo zu den GCP-Lektionen im Modul Data Engineering, ZHAW, HS 2026.

Reihenfolge:
1. [docs/VORBEREITUNG.md](docs/VORBEREITUNG.md), vor der ersten Lektion erledigen
2. [docs/LEKTION-1.md](docs/LEKTION-1.md), Daten rein, wiederholbar
3. [docs/LEKTION-2.md](docs/LEKTION-2.md), von den Rohdaten zur Antwort, jede Woche
4. [docs/SPEC-IM-TEAM.md](docs/SPEC-IM-TEAM.md), wie die Spezifikation im Team aussieht
5. [docs/LEKTION-3.md](docs/LEKTION-3.md), ein Sprachmodell als Funktion in der Pipeline

Ordner:
- `ingest/` Cloud-Run-Job, der die Daten lädt (Lektion 1)
- `alerts/` Cloud-Run-Job, der die Bahnverkehrsinformationen der SBB lädt (Lektion 3)
- `transform/` dbt-Projekt, entsteht in Lektion 2 aus `transform/SPEC.md` und wächst in Lektion 3 um `transform/SPEC-ALERTS.md`
- `referenz/` Musterlösungen: `referenz/transform/` (Lektion 2) und `referenz/transform-alerts/` (Lektion 3)
- `checks/` Dataplex Data-Quality-Regeln (Lektion 1 und 2)
- `pipeline/` Workflows (Verkettung mit Qualitätsschranke, zweite Kette für die Meldungen) und Alarm (Lektion 2 und 3)
- `docs/` Tutorials
- `CLAUDE.md` Regeln für Claude Code in diesem Repo
- `.claude/settings.json` welche Befehle Claude Code ohne Rückfrage ausführen darf
