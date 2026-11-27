"""Erzeugt die SVGs für Lektion 4, Schritt 3, im Stil der Grafiken aus Lektion 3."""

SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, 'DejaVu Sans', sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
INK, GREY, LINE, FILL, BLUE, BLUEFILL = "#1f2328", "#8c959f", "#d0d7de", "#f6f8fa", "#0969da", "#ddf4ff"
W = 1044


def text(x, y, s, size=12, anchor="start", weight=400, mono=False, fill=INK):
    fam = MONO if mono else SANS
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def box(x, y, w, h, title, lines, fill=FILL, stroke=GREY, mono_title=True, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}"{d}/>']
    cx = x + w / 2
    ty = y + 19
    out.append(text(cx, ty, title, 13, "middle", 700, mono=mono_title))
    for i, l in enumerate(lines):
        out.append(text(cx, ty + 17 * (i + 1), l, 12, "middle"))
    return "\n".join(out)


def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, color=GREY):
    out = [f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="2.5"/>']
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    s = 11
    p1 = (x2 - s * math.cos(ang - 0.4), y2 - s * math.sin(ang - 0.4))
    p2 = (x2 - s * math.cos(ang + 0.4), y2 - s * math.sin(ang + 0.4))
    out.append(f'<path d="M{x2} {y2} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} z" fill="{color}"/>')
    if label:
        out.append(text(lx, ly, label, 12, "middle", 400))
    return "\n".join(out)


def frame(h, title, desc, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-labelledby="t d">
<title id="t">{title}</title>
<desc id="d">{desc}</desc>
<rect width="{W}" height="{h}" fill="#ffffff"/>
<rect x="16" y="16" width="{W - 32}" height="{h - 32}" rx="6" fill="#ffffff" stroke="{LINE}"/>
<path d="M16 46 V22 a6 6 0 0 1 6 -6 H{W - 22} a6 6 0 0 1 6 6 V46 Z" fill="{FILL}" stroke="{LINE}"/>
{text(30, 36, title, 13.5, "start", 700)}
{body}
</svg>
'''


# Grafik 1: die vier Teile, die Schleife, die Grenze -------------------------------------------
def schleife():
    b = []
    # Grenze: das Modell liest und zieht Schlüsse (gestrichelter Kasten)
    b.append(f'<rect x="30" y="66" width="700" height="382" rx="8" fill="#ffffff" stroke="{BLUE}" stroke-dasharray="6 5"/>')
    b.append(text(44, 86, "Das Modell liest und zieht Schlüsse. Alles hier drin darf nur lesen.", 12.5, "start", 700, fill=BLUE))
    # Drei Eingaben links
    b.append(box(44, 104, 210, 70, "INSTRUCTION", ["die Methode in fünf Schritten,", "kein Vorfall, keine Ursache"]))
    b.append(box(44, 190, 210, 70, "Diagnose", ["das Schema: 6 Kategorien,", "Fakten getrennt von Schlüssen"]))
    b.append(box(44, 276, 210, 70, "tools.py", ["zehn Werkzeuge + BigQuery,", "Docstrings als Anleitung"]))
    b.append(text(149, 376, "+ ein Satz: \"Execution X ist gescheitert\"", 12, "middle"))
    # Modell in der Mitte
    b.append(box(330, 190, 170, 70, "Modell", ["gemini-3.8-flash", "wählt das nächste Werkzeug"], fill=BLUEFILL, stroke=BLUE, mono_title=False))
    for y in (139, 225, 311):
        b.append(arrow(254, y, 328, 225 if y != 225 else 225))
    # Werkzeug rechts
    b.append(box(560, 190, 150, 70, "Werkzeug", ["läuft, liest, antwortet", "knapp und fest begrenzt"], mono_title=False))
    b.append(arrow(500, 212, 558, 212, "ruft auf", 529, 200))
    b.append(arrow(558, 240, 500, 240, "Antwort in den Prompt", 529, 290))
    b.append(text(529, 272, "bis zu 30 Mal, höchstens 10 Minuten", 11.5, "middle", 400, fill=GREY))
    # Schleifenpfeil nach oben (Rückkopplung)
    b.append(f'<path d="M635 190 V150 H415 V188" fill="none" stroke="{GREY}" stroke-width="2.5"/>')
    b.append(f'<path d="M415 190 l-6 -10 h12 z" fill="{GREY}"/>')
    b.append(text(525, 142, "wieder entscheiden", 12, "middle"))
    # Ende: Schema gefüllt
    b.append(arrow(415, 262, 415, 318))
    b.append(box(300, 320, 230, 68, "Diagnose gefüllt", ["Kategorie, Fakten, Schlüsse,", "Ursache, Vorschlag, Konfidenz"], mono_title=False))
    b.append(text(415, 414, "Das Modell hat kein Werkzeug, das schreibt, deployt, startet oder löscht.", 12, "middle"))
    b.append(text(415, 432, "Das BigQuery-Werkzeug hat die Schreibsperre, der Service-Account kein Schreibrecht auf raw.", 12, "middle"))
    # Ausserhalb der Grenze: das Programm schreibt
    b.append(arrow(530, 354, 770, 354))
    b.append(box(772, 308, 240, 92, "write_row()", ["das Programm, nicht das Modell,", "schreibt eine Zeile nach", "ops.incidents, Status offen"], fill=FILL, stroke=INK))
    b.append(text(892, 426, "Schreibrecht nur hier, in IAM.", 12, "middle", 700))
    b.append(text(892, 444, "Die Grenze steht zweimal: im Code, in IAM.", 12, "middle"))
    # Vier Teile Legende unten
    b.append(f'<path d="M30 462 H1014" stroke="{LINE}" stroke-width="1.5"/>')
    b.append(text(30, 484, "Die vier Teile jedes Agenten:", 12.5, "start", 700))
    b.append(text(232, 484, "Schema (Diagnose)  ·  Anweisung (INSTRUCTION)  ·  Werkzeuge (tools.py)  ·  Lauf (triage() startet die Schleife, ADK führt sie)", 12, "start"))
    return frame(506, "Die Schleife des Agenten, und wo die Grenze steht",
                 "Das Modell liest und zieht Schlüsse. Anweisung, Schema und Werkzeuge gehen ins Modell. Das Modell wählt ein Werkzeug, das Werkzeug liest und antwortet, die Antwort geht in den Prompt, das Modell entscheidet wieder, bis zu 30 Mal und höchstens 10 Minuten, bis das Schema gefüllt ist. Alles im gestrichelten Kasten darf nur lesen. Ausserhalb schreibt write_row(), das Programm, eine Zeile nach ops.incidents. Die Grenze steht zweimal: im Code und in IAM.",
                 "\n".join(b))


# Grafik 2: drei Regeln für Werkzeuge ----------------------------------------------------------
def regeln():
    b = []
    cols = [
        ("Nur bekannte Ressourcen", ["Projekt, Workflow, Scan und die", "erlaubten Jobs stehen in der", "Konfiguration des Jobs, nicht im", "Modell. Es wählt aus dieser Liste", "und kann keine Ressource erfinden."],
         'get_job("ingest-gtfs")  ✓', 'get_job("prod-db")  ✗ unbekannt'),
        ("Knappe Antworten", ["Felder statt Rohtext, feste", "Obergrenzen: 5 Executions,", "40 Logzeilen, 20 Audit-Einträge.", "Jede Antwort wandert in jeden", "weiteren Modellaufruf mit."],
         "Aufruf 1 trägt 5 KB, Aufruf 8 trägt 40 KB:", "jede Antwort zählt jedes Mal neu"),
        ("Kein Absturz", ["Ein Fehler im Werkzeug kommt", "als Ergebnis zurück, nicht als", "Exception. Sonst bricht der Lauf", "ab, und das Modell kann nicht", "anders weitersuchen."],
         '{"status": "ERROR", "error": "403 …"}', "→ das Modell nimmt ein anderes Werkzeug"),
    ]
    x = 30
    for title, lines, ex1, ex2 in cols:
        b.append(f'<rect x="{x}" y="66" width="318" height="196" rx="6" fill="#ffffff" stroke="{GREY}"/>')
        b.append(text(x + 159, 90, title, 13.5, "middle", 700))
        for i, l in enumerate(lines):
            b.append(text(x + 159, 112 + 17 * i, l, 12, "middle"))
        b.append(f'<rect x="{x + 12}" y="204" width="294" height="46" rx="4" fill="{FILL}" stroke="{LINE}"/>')
        b.append(text(x + 159, 223, ex1, 11.5, "middle", 400, mono=True))
        b.append(text(x + 159, 241, ex2, 11.5, "middle", 400, mono=True))
        x += 333
    return frame(280, "Drei Regeln für Werkzeuge, oben in tools.py",
                 "Nur bekannte Ressourcen: das Modell wählt aus der Konfiguration des Jobs, es kann keine erfinden. Knappe Antworten: Felder statt Rohtext und feste Obergrenzen, weil jede Antwort in jeden weiteren Modellaufruf mitwandert. Kein Absturz: Fehler kommen als Ergebnis zurück, damit das Modell anders weitersuchen kann.",
                 "\n".join(b))


if __name__ == "__main__":
    open("lektion-4-schritt-3-schleife.svg", "w").write(schleife())
    open("lektion-4-schritt-3-regeln.svg", "w").write(regeln())
    print("ok")
