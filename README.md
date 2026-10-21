# Data Engineering auf Google Cloud

Begleitrepo zu den zwei GCP-Lektionen im Modul Data Engineering, ZHAW, HS 2026.

Reihenfolge:
1. [docs/VORBEREITUNG.md](docs/VORBEREITUNG.md), vor der ersten Lektion erledigen
2. [docs/LEKTION-1.md](docs/LEKTION-1.md), Daten rein, wiederholbar
3. [docs/LEKTION-2.md](docs/LEKTION-2.md), von den Rohdaten zur Antwort, jede Woche
4. [docs/SPEC-IM-TEAM.md](docs/SPEC-IM-TEAM.md), wie die Spezifikation im Team aussieht

Ordner:
- `ingest/` Cloud-Run-Job, der die Daten lädt (Lektion 1)
- `transform/` dbt-Projekt, entsteht in Lektion 2 aus `transform/SPEC.md`
- `referenz/` Musterlösungen, zum Beispiel `referenz/transform/` (das getestete dbt-Projekt)
- `checks/` Dataplex Data-Quality-Regeln (Lektion 1 und 2)
- `pipeline/` Workflow (Verkettung mit Qualitätsschranke) und Alarm (Lektion 2)
- `docs/` Tutorials
- `CLAUDE.md` Regeln für Claude Code in diesem Repo
- `.claude/settings.json` welche Befehle Claude Code ohne Rückfrage ausführen darf
