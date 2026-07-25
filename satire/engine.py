import random
from typing import Optional

class SatireEngine:
    def __init__(self, bürokratie_mode: bool = True):
        self.bürokratie_mode = bürokratie_mode
        self.forms = {
            "variable": "Formular V-12: Variable Deklarationsantrag",
            "function": "Formular F-42: Funktionsgenehmigung",
            "loop": "Formular L-89: Schleifen-Zulassung",
        }

    def wrap_response(self, response: str, context: Optional[str] = None) -> str:
        if not self.bürokratie_mode:
            return response

        header = random.choice([
            "Gemäß §12 Abs. 3 der Code-Verordnung:",
            "Nach Rücksprache mit Abteilung 4b:",
            "Laut DIN 66234-8:",
        ])
        footer = random.choice([
            "\n---\nHinweis: Dieser Code unterliegt der Mehrwertsteuer (19%).",
            "\n---\nBitte bewahren Sie diese Ausgabe für Ihre Unterlagen auf.",
            "\n---\nGenehmigt durch: Herr Schmidt (Raum 304)",
        ])

        form_hint = ""
        if context:
            for keyword, form in self.forms.items():
                if keyword in context.lower():
                    form_hint = f"\n\n📄 *Hinweis: Bitte reichen Sie [{form}](forms/{form.lower().replace(' ', '_').replace(':', '')}.pdf) ein.*"
                    break

        return f"{header}\n\n{response}{form_hint}{footer}"

    def generate_error(self, error: str) -> str:
        errors = {
            "SyntaxError": "Verstoß gegen §12 Abs. 3: Syntaxfehler. Bitte Formular S-1 einreichen.",
            "TypeError": "Ungültiger Datentyp gem. DIN 42000. Nur 'int', 'str', und 'Bürokratie' sind erlaubt.",
            "NameError": "Undefinierte Variable. Haben Sie Formular V-12 vergessen?",
            "IndentationError": "Einrückung nicht normgerecht (§89). Nutzen Sie bitte 4 Leerzeichen (oder 2, aber nicht beides).",
        }
        return errors.get(error, f"Unbekannter Fehler: {error}. Bitte wenden Sie sich an die Hotline (Mo-Fr, 08:00-12:00 Uhr).")