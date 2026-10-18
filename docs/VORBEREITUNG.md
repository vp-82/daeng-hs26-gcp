# Vorbereitung: Werkzeuge installieren und GCP-Projekt anlegen

Erledige diese Schritte **vor** der ersten GCP-Lektion. Du brauchst etwa 40 Minuten. Am Ende hast du:

- Claude Code installiert und eingeloggt
- die gcloud CLI installiert und mit deinem ZHAW-Google-Konto eingeloggt
- das Kurs-Repo geklont und das Google-Cloud-Plugin für Claude Code installiert
- ein Google-Cloud-Projekt mit Budget-Alarm, angelegt per Prompt
- einen Check, der READY sagt

**Voraussetzung:** Du hast ein Google-Konto mit deiner ZHAW-Adresse und den Education-Coupon eingelöst ([Anleitung auf Moodle](https://moodle.zhaw.ch/mod/forum/discuss.php?d=209024)). Gib nirgends eine Kreditkarte ein. Alles in diesem Kurs läuft über das Education-Guthaben.

---

## 1. Claude Code installieren

Claude Code ist der Coding-Agent, den wir im Kurs benutzen. Er läuft im Terminal und führt Befehle für dich aus, aber nur nach deiner Freigabe.

Öffne ein Terminal und führe den Befehl für dein System aus:

macOS, Linux, WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Der Installer zeigt keinen Fortschritt an, das ist normal. Öffne danach ein **neues** Terminalfenster und prüfe:

```bash
claude --version
```

Du siehst eine Versionsnummer. Falls `claude` nicht gefunden wird: Terminal schliessen, neu öffnen, nochmals probieren.

Zum Einloggen startest du Claude Code einmal in einem beliebigen Ordner:

```bash
claude
```

Beim ersten Start öffnet sich der Browser zum Login. Welchen Claude-Account du dafür verwendest, ist dir überlassen. Danach beendest du Claude Code mit `/exit`.

---

## 2. gcloud CLI installieren und einloggen

Die gcloud CLI ist das Kommandozeilen-Werkzeug für Google Cloud. Claude Code wird damit arbeiten, du musst die Befehle nicht selbst kennen. Installieren und einloggen musst du aber selbst, weil das Login einen Klick im Browser braucht.

macOS mit Homebrew:

```bash
brew install --cask google-cloud-sdk
```

Windows und Linux: Installer von https://cloud.google.com/sdk/docs/install herunterladen und ausführen.

Neues Terminal öffnen und prüfen:

```bash
gcloud --version
```

Jetzt einloggen. Der Browser öffnet sich, wähle dort dein **ZHAW-Google-Konto**:

```bash
gcloud auth login
```

Prüfen, dass das richtige Konto aktiv ist (der Stern markiert das aktive Konto):

```bash
gcloud auth list
```

Ein zweites Login brauchen wir für Programme, die später aus dem Repo heraus auf Google Cloud zugreifen. Wieder Browser, wieder ZHAW-Konto:

```bash
gcloud auth application-default login
```

Führe **nicht** `gcloud init` aus. Dieser Befehl will interaktiv ein Projekt auswählen oder anlegen. Das machen wir in Schritt 4 mit Claude Code.

---

## 3. Repo klonen und Plugin installieren

```bash
git clone https://github.com/vp-82/daeng-hs26-gcp.git
cd daeng-hs26-gcp
```

Jetzt das Google-Cloud-Plugin für Claude Code installieren. Ein Plugin gibt dem Agenten Anleitungen für ein bestimmtes Werkzeug, hier für Google Cloud. Die zwei Befehle laufen im Terminal, nicht in Claude Code:

```bash
claude plugin marketplace add google/skills
claude plugin install google-cloud-developer@google-plugins
```

Starte Claude Code im Repo-Ordner:

```bash
claude
```

Tippe `/plugin` und prüfe, dass `google-cloud-developer` unter den installierten Plugins steht. Lass Claude Code offen für Schritt 4.

---

## 4. Projekt per Prompt anlegen

Ein Projekt ist in Google Cloud der Behälter für alles, was du anlegst, und die Einheit, an der die Rechnung hängt. Wir lassen Claude Code das Projekt anlegen und kontrollieren jeden Schritt in der Cloud Console.

So funktioniert das Zusammenspiel: Claude Code zeigt dir vor jedem Befehl, was es ausführen will, und wartet auf deine Freigabe. Lies den Befehl. Vergleiche ihn mit der Liste unter dem Prompt. Wenn er dem entspricht, gib frei. Wenn nicht, frag im Chat nach, bevor du freigibst.

Ersetze `KÜRZEL` im Prompt durch dein ZHAW-Kürzel in Kleinbuchstaben und füge den Prompt in Claude Code ein:

```text
Lege mein Google-Cloud-Projekt für den Kurs an. Halte dich an diese Regeln:
- Zeige mir jeden Befehl, bevor du ihn ausführst, und erkläre ihn in einem Satz.
- Erstelle kein Rechnungskonto, starte keinen Free Trial, frage nie nach Kreditkartendaten.
- Wenn ein Schritt nicht das erwartete Ergebnis liefert, stoppe und frag mich.

Mein Kürzel: KÜRZEL

Schritte:
1. Führe `gcloud billing accounts list` aus. Es muss genau ein offenes Rechnungskonto geben. Merke dir seine ID. Gibt es keins oder mehrere, stoppe.
2. Erstelle ein Projekt mit der ID daeng-KÜRZEL-XXXX, wobei XXXX vier zufällige Kleinbuchstaben oder Ziffern sind. Setze es als Standardprojekt.
3. Verknüpfe das Projekt mit dem Rechnungskonto aus Schritt 1.
4. Aktiviere diese APIs im Projekt: cloudresourcemanager, serviceusage, cloudbilling, billingbudgets, iam, storage, bigquery, run, cloudbuild, artifactregistry, cloudscheduler, logging, monitoring, datalineage, dataplex, dataform (jeweils mit .googleapis.com).
5. Setze europe-west6 als Standardregion für Cloud Run und Compute.
6. Erstelle für das Rechnungskonto ein Budget mit dem Namen daeng-budget über 50 USD mit Warnungen bei 50, 90 und 100 Prozent.
7. Zeige mir zum Schluss: Projekt-ID, Projektnummer, Rechnungskonto-ID, die Liste der aktivierten APIs und das Budget.
```

So sollten die Befehle ungefähr aussehen. Die IDs sind bei dir andere, die Struktur ist dieselbe:

```bash
gcloud billing accounts list
gcloud projects create daeng-KÜRZEL-XXXX --name="DAENG GCP"
gcloud config set project daeng-KÜRZEL-XXXX
gcloud billing projects link daeng-KÜRZEL-XXXX --billing-account=XXXXXX-XXXXXX-XXXXXX
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com cloudbilling.googleapis.com billingbudgets.googleapis.com iam.googleapis.com storage.googleapis.com bigquery.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com cloudscheduler.googleapis.com logging.googleapis.com monitoring.googleapis.com datalineage.googleapis.com dataplex.googleapis.com dataform.googleapis.com
gcloud config set run/region europe-west6
gcloud config set compute/region europe-west6
gcloud billing budgets create --billing-account=XXXXXX-XXXXXX-XXXXXX --display-name="daeng-budget" --budget-amount=50USD --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
```

Was die Befehle tun, in einem Satz pro Zeile: Rechnungskonto finden, Projekt anlegen, Projekt als Standard setzen, Projekt mit dem Rechnungskonto verbinden, die Dienste einschalten, die wir im Kurs brauchen (jeder Google-Cloud-Dienst ist eine API, die pro Projekt eingeschaltet wird), die Region Zürich als Standard setzen, und das Budget anlegen. Die Budget-Warnungen kommen per E-Mail an deine ZHAW-Adresse.

Prüfe das Ergebnis in der Cloud Console unter https://console.cloud.google.com:

1. Oben links in der Projektauswahl steht dein Projekt `daeng-KÜRZEL-XXXX`.
2. Menü **Abrechnung → Budgets und Benachrichtigungen**: das Budget `daeng-budget` über 50 USD ist da.
3. Menü **APIs und Dienste → Aktivierte APIs und Dienste**: BigQuery, Cloud Run, Cloud Storage und Dataform stehen in der Liste.

---

## 5. Check

Füge diesen Prompt in Claude Code ein. Er ändert nichts, er liest nur:

```text
Prüfe, ob meine Umgebung für den Kurs bereit ist. Führe nur lesende Befehle aus, ändere nichts. Gib am Ende eine Tabelle mit den Spalten Prüfung, Ergebnis (PASS/FAIL) und Detail aus. Bei jedem FAIL nenne zusätzlich den Befehl, der es beheben würde, ohne ihn auszuführen.

1. gcloud --version und claude --version
2. gcloud auth list: genau ein aktives Konto, und es ist eine ZHAW-Adresse
3. gcloud config get-value project, dann gcloud projects describe für dieses Projekt: es existiert
4. gcloud billing projects describe für dieses Projekt: billingEnabled ist true
5. gcloud billing accounts list: genau ein offenes Rechnungskonto
6. gcloud billing budgets list für dieses Rechnungskonto: mindestens ein Budget
7. gcloud services list --enabled: keine dieser APIs fehlt: cloudresourcemanager, serviceusage, cloudbilling, billingbudgets, iam, storage, bigquery, run, cloudbuild, artifactregistry, cloudscheduler, logging, monitoring, datalineage, dataplex, dataform
8. gcloud config get-value run/region: europe-west6
9. git status: wir sind im Kurs-Repo, und die Datei CLAUDE.md existiert

Letzte Zeile: READY oder NOT READY, mit der Anzahl FAILs.
```

Steht am Ende READY, bist du fertig. Steht NOT READY, führe die vorgeschlagenen Befehle aus oder melde dich mit der Tabelle bei mir.

---

## Wenn etwas schiefgeht

- **`claude` oder `gcloud` wird nicht gefunden:** Terminal schliessen und neu öffnen. Die Installer tragen den Pfad erst für neue Terminals ein.
- **`gcloud billing accounts list` ist leer:** Der Education-Coupon ist nicht eingelöst oder du bist mit dem falschen Google-Konto eingeloggt. `gcloud auth list` zeigt dir, welches aktiv ist.
- **Die Projekt-ID ist schon vergeben:** Projekt-IDs sind weltweit eindeutig. Sag Claude Code, es soll eine andere Zufallsendung nehmen.
- **Permission denied beim Budget:** Die API `billingbudgets` war noch nicht aktiv, als der Befehl lief. Sag Claude Code, es soll Schritt 4 wiederholen und dann Schritt 6.
- **Claude Code will etwas ausführen, das nicht in der Liste steht:** Nicht freigeben. Frag im Chat, warum. Das ist genau die Arbeitsweise, die wir im Kurs üben.
