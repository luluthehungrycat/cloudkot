"""
Form Generator for Cloudkot
Generates fake bureaucratic forms for code-related activities
"""

import random
from pathlib import Path


class FormGenerator:
    def __init__(self, output_dir: str = "./forms"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.az_number = f"CLOUDKOT-2026-{random.randint(1000, 9999)}"

    def generate_form(self, form_type: str, code_snippet: str) -> str:
        """
        Generate a fake bureaucratic form for code.
        Creates a text-based form since PDF generation requires system dependencies.
        """
        filename = f"{form_type.lower().replace(' ', '_').replace(':', '')}.txt"
        filepath = self.output_dir / filename

        template = random.choice([
            "standard",
            "ausfuehrlich",
            "kurz",
        ])

        if template == "standard":
            form_content = self._standard_form(form_type, code_snippet)
        elif template == "ausfuehrlich":
            form_content = self._ausfuehrlich_form(form_type, code_snippet)
        else:
            form_content = self._kurz_form(form_type, code_snippet)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(form_content)

        return filename

    def _standard_form(self, form_type: str, code_snippet: str) -> str:
        sachbearbeiter = random.choice(["Müller", "Schmidt", "Schulze", "Böhme", "Fischer"])
        zimmer = random.choice(["304", "217", "329", "105"])
        return f"""Bundesrepublik Deutschland
=================================

{form_type}

Aktenzeichen: {self.az_number}-{random.choice(['B', 'C', 'D', 'E'])}

Antragsteller: ________________________

Code-Snippet:
-------------
{code_snippet}

Prüfvermerk:
{random.choice([
    "Die Prüfung des Codes ergab keine Beanstandungen.",
    "Nach eingehender Prüfung wurde der Code gemäß DIN 66234-8 als normgerecht eingestuft.",
    "Der Code erfordert eine erneute Vorlage nach Beseitigung der Mängel.",
    "Die Bearbeitung wurde an die zuständige Fachabteilung weitergeleitet.",
])}

Sachbearbeiter: {sachbearbeiter} (Raum {zimmer})

Erklärung:
Ich bestätige, dass ich die DIN-Normen für Code eingesehen habe und die Gebühren
in Höhe von 19% MwSt. akzeptiere. Mir ist bekannt, dass falsche Angaben gemäß
§89 OWiG mit einem Bußgeld geahndet werden können.

_______________________
Unterschrift

Bitte in dreifacher Ausfertigung einreichen. Bearbeitungsdauer: 6-8 Wochen.
Bei Rückfragen: {sachbearbeiter}, Zimmer {zimmer} (Mo-Fr, 08:00-12:00 Uhr).
"""

    def _ausfuehrlich_form(self, form_type: str, code_snippet: str) -> str:
        return f"""Bundesrepublik Deutschland
Der {random.choice(['Bundesbeauftragte', 'Prüfungsausschuss', 'Sachverständigenrat'])}
für IT-Normprüfung

============================================================

{form_type}

Aktenzeichen: {self.az_number}-{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}

Antragsteller: ________________________
Vertreten durch: ______________________
Datum: {random.choice(['03.01.2026', '15.02.2026', '22.03.2026', '07.04.2026', '19.05.2026', '01.06.2026'])}
Eingangsstempel: ______________________

Sachverhalt:
-----------
{code_snippet}

Prüfungsergebnis:
{random.choice([
    "Der vorgelegte Code entspricht nicht den geltenden DIN-Normen.",
    "Nach umfassender Prüfung wurde der Code als bedenkenlos eingestuft.",
    "Es bestehen erhebliche Bedenken hinsichtlich der Normkonformität.",
    "Die Prüfung ergab geringfügige Abweichungen von der Norm.",
    "Der Code muss vollständig überarbeitet und erneut vorgelegt werden.",
])}

Folgende Mängel wurden festgestellt:
(lambda choices: random.choice([
    c.replace('\\n', '\n') for c in choices
]))([
    "- Die Einrückung entspricht nicht §89 der Einrückungsordnung.\\n- Variablenbezeichner sind nicht DIN-konform (§12 Abs. 2).",
    "- Es fehlt die erforderliche Dokumentation gemäß §5 Abs. 2.\\n- Die Kommentierung ist unzureichend.",
    "- Der Code enthält undeklarierte Variablen (Verstoß gegen §7 Abs. 1).\\n- Die Funktionen sind nicht genehmigt.",
    "- Keine Beanstandungen.",
])

Rechtsbehelfsbelehrung:
Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe
Widerspruch eingelegt werden. Der Widerspruch ist schriftlich oder
zur Niederschrift bei der zuständigen Behörde einzureichen.

_________________________________
(Siegel)

_______________________
Unterschrift

Gebühren: Dieser Bescheid unterliegt einer Gebühr von {random.choice(['19,50', '42,00', '12,80', '25,00'])} €
zzgl. 19% MwSt. gemäß §10 UStG.
Bearbeitungsdauer: 8-10 Wochen.
"""

    def _kurz_form(self, form_type: str, code_snippet: str) -> str:
        return f"""BUNDESREPUBLIK DEUTSCHLAND
Kurzbescheid

{form_type} | Az: {self.az_number}-{random.choice(['K', 'L', 'M'])}

Antragsteller: ________________________

Code: {code_snippet[:50]}{'...' if len(code_snippet) > 50 else ''}

{random.choice([
    "Genehmigt.",
    "Abgelehnt (§5 Abs. 1).",
    "An Abteilung 4b weitergeleitet.",
    "Zurückgestellt. Bitte erneute Vorlage.",
    "In Bearbeitung (Priorität: " + random.choice(["niedrig", "normal", "hoch", "eilt!"]) + ").",
])}

Sachbearbeiter: ________________________
Datum: _______________

*Dieser Kurzbescheid ist nur in Verbindung mit dem vollständigen Antrag gültig.
"""

