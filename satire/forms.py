from pathlib import Path
import random

class FormGenerator:
    def __init__(self, output_dir: str = "./forms"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_form(self, form_type: str, code_snippet: str) -> str:
        """
        Generate a fake bureaucratic form for code.
        Creates a text-based form since PDF generation requires system dependencies.
        """
        filename = f"{form_type.lower().replace(' ', '_').replace(':', '')}.txt"
        filepath = self.output_dir / filename

        form_content = f"""Bundesrepublik Deutschland
=================================

{form_type}

Aktenzeichen: CLOUDKOT-2026-{random.randint(1000, 9999)}

Antragsteller: ________________________

Code-Snippet:
-------------
{code_snippet}

Erklärung:
Ich bestätige, dass ich die DIN-Normen für Code eingesehen habe und die Gebühren
in Höhe von 19% MwSt. akzeptiere.

_______________________
Unterschrift

Bitte in dreifacher Ausfertigung einreichen. Bearbeitungsdauer: 6-8 Wochen.
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(form_content)

        return filename