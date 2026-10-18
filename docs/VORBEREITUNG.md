# Vorbereitung: Werkzeuge installieren und GCP-Projekt anlegen

Erledige diese Schritte **vor** der ersten GCP-Lektion. Du brauchst etwa 45 Minuten. Am Ende hast du:

- Claude Code installiert und eingeloggt
- die gcloud CLI installiert und mit deinem ZHAW-Google-Konto eingeloggt
- das Kurs-Repo geklont und das Google-Cloud-Plugin für Claude Code installiert
- ein Google-Cloud-Projekt mit Budget-Alarm, angelegt per Prompt
- einen ersten Bucket, angelegt per Prompt und in der Console kontrolliert
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

Beim ersten Start öffnet sich der Browser zum Login. Melde dich mit deinem Claude-Account an. Danach beendest du Claude Code mit `/exit`.

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
1. Führe `gcloud billing accounts list` aus. Nimm das offene Rechnungskonto mit "Education" im Namen und merke dir seine ID. Gibt es keins, stoppe. Gibt es daneben weitere offene Konten, benutze sie nicht, aber nenne sie mir, weil dort eine Kreditkarte hinterlegt sein könnte.
2. Erstelle ein Projekt mit der ID daeng-KÜRZEL-XXXX, wobei XXXX vier zufällige Kleinbuchstaben oder Ziffern sind. Setze es als Standardprojekt, auch für die Application Default Credentials.
3. Verknüpfe das Projekt mit dem Rechnungskonto aus Schritt 1.
4. Aktiviere diese APIs im Projekt: cloudresourcemanager, serviceusage, cloudbilling, billingbudgets, iam, storage, bigquery, run, cloudbuild, artifactregistry, cloudscheduler, logging, monitoring, datalineage, dataplex, dataform (jeweils mit .googleapis.com).
5. Setze europe-west6 als Standardregion für Cloud Run und Compute.
6. Lies mit `gcloud billing accounts describe` die Währung des Rechnungskontos (currencyCode). Erstelle für das Rechnungskonto ein Budget mit dem Namen daeng-budget über 50 in dieser Währung, mit Warnungen bei 50, 90 und 100 Prozent, und mit credit-types-treatment exclude-all-credits, damit das Budget den Verbrauch des Guthabens misst und nicht erst die Kosten danach.
7. Zeige mir zum Schluss: Projekt-ID, Projektnummer, Rechnungskonto-ID und Währung, die Liste der aktivierten APIs und das Budget.
```

Diese Befehle zeigt dir Claude Code nacheinander zur Freigabe. So würdest du sie auch von Hand eingeben. Die IDs sind bei dir andere, die Struktur ist dieselbe:

```bash
gcloud billing accounts list
gcloud projects create daeng-KÜRZEL-XXXX --name="DAENG GCP"
gcloud config set project daeng-KÜRZEL-XXXX
gcloud auth application-default set-quota-project daeng-KÜRZEL-XXXX
gcloud billing projects link daeng-KÜRZEL-XXXX --billing-account=XXXXXX-XXXXXX-XXXXXX
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com cloudbilling.googleapis.com billingbudgets.googleapis.com iam.googleapis.com storage.googleapis.com bigquery.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com cloudscheduler.googleapis.com logging.googleapis.com monitoring.googleapis.com datalineage.googleapis.com dataplex.googleapis.com dataform.googleapis.com
gcloud config set run/region europe-west6
gcloud config set compute/region europe-west6
gcloud billing accounts describe XXXXXX-XXXXXX-XXXXXX
gcloud billing budgets create --billing-account=XXXXXX-XXXXXX-XXXXXX --display-name="daeng-budget" --budget-amount=50USD --credit-types-treatment=exclude-all-credits --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
```

Was die Befehle tun, in einem Satz pro Zeile: Rechnungskonto finden, Projekt anlegen, Projekt als Standard setzen, das Projekt auch für Programme als Standard setzen (brauchen wir in Lektion 2), Projekt mit dem Rechnungskonto verbinden, die Dienste einschalten, die wir im Kurs brauchen (jeder Google-Cloud-Dienst ist eine API, die pro Projekt eingeschaltet wird), die Region Zürich als Standard setzen, die Währung des Rechnungskontos lesen, und das Budget anlegen. Statt 50USD steht bei dir 50CHF, wenn dein Rechnungskonto in Franken abrechnet. Die Option exclude-all-credits ist wichtig: Ohne sie zählt das Budget nur Kosten, die nach Abzug deines Guthabens übrig bleiben, und das sind null, bis das Guthaben weg ist. Mit ihr zählt es, was du vom Guthaben verbrauchst. Die Budget-Warnungen kommen per E-Mail an deine ZHAW-Adresse. Das Budget gilt für dein ganzes Rechnungskonto, nicht nur für dieses Projekt. Das ist Absicht: Falls du aus Versehen ein zweites Projekt anlegst, warnt das Budget trotzdem.

Prüfe das Ergebnis in der Cloud Console unter https://console.cloud.google.com:

1. Oben links in der Projektauswahl steht dein Projekt `daeng-KÜRZEL-XXXX`.
2. Menü **Abrechnung → Budgets und Benachrichtigungen**: das Budget `daeng-budget` über 50 ist da, und bei "Guthaben" ist kein Haken gesetzt.
3. Menü **APIs und Dienste → Aktivierte APIs und Dienste**: BigQuery, Cloud Run, Cloud Storage und Dataform stehen in der Liste.

In der Liste stehen mehr als die 16 angeforderten APIs. Google schaltet mit jedem Dienst Hilfs-APIs mit ein, zum Beispiel bringt BigQuery sieben weitere mit. Das ist normal und kostet nichts, solange niemand sie benutzt.

---

## 5. Smoke-Test: einen Bucket anlegen

Ein Bucket ist ein Ablageort für Dateien in Google Cloud Storage. Wir legen jetzt einen an, um zu prüfen, dass dein Projekt wirklich etwas erstellen darf. In Lektion 1 landen dort die Rohdaten.

Füge den Prompt in Claude Code ein:

```text
Lege im Standardprojekt einen Bucket an. Name: die Projekt-ID plus "-raw", Region europe-west6, einheitlicher Zugriff auf Bucket-Ebene. Zeige mir den Befehl vorher. Danach zeige mir mit `gcloud storage ls` alle Buckets im Projekt.
```

Diesen Befehl zeigt dir Claude Code zur Freigabe:

```bash
gcloud storage buckets create gs://daeng-KÜRZEL-XXXX-raw --location=europe-west6 --uniform-bucket-level-access
```

Ein leerer Bucket kostet nichts. Prüfe in der Console: Menü **Cloud Storage → Buckets**, dein Bucket steht dort mit Standort europe-west6.

---

## 6. Check

Füge diesen Prompt in Claude Code ein. Er ändert nichts, er liest nur:

```text
Prüfe, ob meine Umgebung für den Kurs bereit ist. Führe nur lesende Befehle aus, ändere nichts. Gib am Ende eine Tabelle mit den Spalten Prüfung, Ergebnis (PASS/FAIL) und Detail aus. Bei jedem FAIL nenne zusätzlich den Befehl, der es beheben würde, ohne ihn auszuführen.

1. gcloud --version und claude --version
2. gcloud auth list: genau ein aktives Konto, und es ist eine ZHAW-Adresse
3. gcloud config get-value project, dann gcloud projects describe für dieses Projekt: es existiert
4. gcloud billing projects describe für dieses Projekt: billingEnabled ist true
5. gcloud billing accounts list: genau ein offenes Rechnungskonto mit "Education" im Namen, und das Kursprojekt hängt an diesem Konto. Weitere offene Konten sind kein FAIL, aber nenne sie im Detail mit dem Hinweis, dass dort eine Kreditkarte hinterlegt sein könnte.
6. gcloud billing budgets list für dieses Rechnungskonto, dann gcloud billing budgets describe für daeng-budget: das Budget existiert und creditTypesTreatment ist EXCLUDE_ALL_CREDITS
7. gcloud services list --enabled: keine dieser APIs fehlt: cloudresourcemanager, serviceusage, cloudbilling, billingbudgets, iam, storage, bigquery, run, cloudbuild, artifactregistry, cloudscheduler, logging, monitoring, datalineage, dataplex, dataform
8. gcloud config get-value run/region: europe-west6
9. git status: wir sind im Kurs-Repo, und die Datei CLAUDE.md existiert
10. gcloud storage ls: es gibt genau einen Bucket, sein Name ist die Projekt-ID plus "-raw", und gcloud storage buckets describe zeigt location EUROPE-WEST6

Letzte Zeile: READY oder NOT READY, mit der Anzahl FAILs.
```

Steht am Ende READY, bist du fertig. Steht NOT READY, führe die vorgeschlagenen Befehle aus oder melde dich mit der Tabelle bei mir.

---

## Wenn etwas schiefgeht

- **`claude` oder `gcloud` wird nicht gefunden:** Terminal schliessen und neu öffnen. Die Installer tragen den Pfad erst für neue Terminals ein.
- **Der Check sagt, das aktive Konto sei keine ZHAW-Adresse:** Du hast gcloud schon früher mit einem anderen Google-Konto benutzt. `gcloud config set account DEINE-ADRESSE@zhaw.ch` macht das ZHAW-Konto aktiv. Danach den Check nochmals laufen lassen.
- **`gcloud billing accounts list` ist leer:** Der Education-Coupon ist nicht eingelöst oder du bist mit dem falschen Google-Konto eingeloggt. `gcloud auth list` zeigt dir, welches aktiv ist.
- **Die Projekt-ID ist schon vergeben:** Projekt-IDs sind weltweit eindeutig. Sag Claude Code, es soll eine andere Zufallsendung nehmen.
- **Fehler beim Budget:** Entweder war die API `billingbudgets` noch nicht aktiv, als der Befehl lief (Claude Code soll Punkt 4 und danach Punkt 6 aus dem Prompt wiederholen), oder die Währung stimmt nicht mit dem Rechnungskonto überein (Claude Code soll die Währung mit `gcloud billing accounts describe` prüfen und den Befehl mit dieser Währung wiederholen).
- **Claude Code sagt, ein Budget-Befehl sei blockiert:** Claude Code hat eine eingebaute Sperre für Änderungen an Rechnungskonten und schlägt dir stattdessen den Befehl zum Selbst-Ausführen vor. Lies ihn, vergleiche ihn mit der Budget-Zeile aus Schritt 4, und führe ihn dann mit einem `!` davor direkt im Prompt aus. Das `!` heisst: du führst den Befehl aus, nicht Claude Code, und Claude Code sieht die Ausgabe. Danach den Check in Schritt 6 nochmals laufen lassen.
- **Claude Code will etwas ausführen, das nicht in der Liste steht:** Nicht freigeben. Frag im Chat, warum. Das ist genau die Arbeitsweise, die wir im Kurs üben.
