"""
Satire Engine for Cloudkot
Fügt Bürokratie-Flair zu KI-Antworten hinzu
"""

import random
from datetime import datetime


class SatireEngine:
    def __init__(self, bürokratie_mode: bool = True):
        self.bürokratie_mode = bürokratie_mode
        self.forms = {
            "variable": "Formular V-12: Variable Deklarationsantrag",
            "function": "Formular F-42: Funktionsgenehmigung",
            "loop": "Formular L-89: Schleifen-Zulassung",
            "import": "Formular I-15: Importgenehmigung",
            "class": "Formular K-7: Klassen-Zulassungsbescheinigung",
            "error": "Formular S-1: Syntaxfehler-Meldung",
        }
        self.antragsnummer = "CLOUDKOT-2026-" + str(random.randint(10000, 99999)) + "-" + random.choice(['B', 'C', 'D', 'E'])
        self.geschaeftszeiten = self._check_geschaeftszeiten()
        self.abteilung = random.choice([
            "4b (Allgemeine IT-Verwaltung)", "3a (Digitale Sachbearbeitung)",
            "2c (Code-Prüfung)", "7d (Formularwesen)",
            "1a (Leitung)", "5e (Qualitätssicherung)",
        ])
        self.sachbearbeiter = random.choice([
            "Schmidt", "Müller", "Schulze", "Böhme",
            "Lindner", "Fischer", "Hoffmann", "Krüger",
        ])
        self.zimmer = str(random.choice([304, 217, 329, 105, 412, 501]))

    def _check_geschaeftszeiten(self) -> bool:
        """Check if within business hours (Mo-Fr, 08:00-16:00)"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        return 8 <= now.hour < 16

    def wrap_response(self, response: str, context: str | None = None) -> str:
        if not self.bürokratie_mode:
            return response

        header = random.choice([
            "Gemäß §12 Abs. 3 der Code-Verordnung:",
            "Nach Rücksprache mit Abteilung " + self.abteilung + ":",
            "Laut DIN 66234-8:",
            "Aufgrund Ihres Antrags vom heutigen Tage:",
            "Nach eingehender Prüfung der Sach- und Aktenlage:",
            "In Beantwortung Ihrer Anfrage (Az: " + self.antragsnummer + "):",
            "Die zuständige Prüfstelle hat folgendes festgestellt:",
            "Unter Vorbehalt der Genehmigung durch den Datenschutzbeauftragten:",
            "Hiermit ergeht folgender Bescheid gemäß §28 KI-VO:",
            "Bezug nehmend auf Ihre Eingabe vom heutigen Tag:",
        ])

        footer = random.choice([
            "\n---\nHinweis: Dieser Code unterliegt der Mehrwertsteuer (19%).",
            "\n---\nBitte bewahren Sie diese Ausgabe für Ihre Unterlagen auf.",
            "\n---\nGenehmigt durch: " + random.choice(["Herrn", "Frau"]) + " " + self.sachbearbeiter + " (Raum " + self.zimmer + ")",
            "\n---\nAntragsnummer: " + self.antragsnummer,
            "\n---\nBei Rückfragen wenden Sie sich bitte an das zuständige Fachreferat.",
            "\n---\nGebührenbescheid wird gesondert zugestellt (§10 Abs. 3 Gebührenordnung).",
            "\n---\nDiese Ausfertigung ist nur in Verbindung mit dem Antragsformular gültig.",
            "\n---\nWiderspruch ist innerhalb eines Monats schriftlich oder zur Niederschrift möglich.",
            "\n---\nSachbearbeiter: " + self.sachbearbeiter + " (Az: " + self.antragsnummer + ")",
        ])

        extra = ""
        if not self.geschaeftszeiten:
            extra += ("\n⚠️ Hinweis: Die Bearbeitung außerhalb der Geschäftszeiten "
                      "(Mo-Fr, 08:00-16:00) kann zu verlängerten Bearbeitungszeiten führen.")

        form_hint = ""
        if context:
            for keyword, form in self.forms.items():
                if keyword in context.lower():
                    fname = form.lower().replace(' ', '_').replace(':', '')
                    form_hint = ("\n\n📄 *Bitte reichen Sie [" + form + "](forms/"
                                 + fname + ".pdf) in dreifacher Ausfertigung ein.*")
                    break

        delay = ""
        if random.random() < 0.15:
            delay = self._processing_delay()

        return header + "\n\n" + response + form_hint + delay + extra + footer

    def _processing_delay(self) -> str:
        """Generate a random processing delay message."""
        std_delays = [
            "\n⏳ Ihre Anfrage (Nr. " + self.antragsnummer + ") wird bearbeitet...",
            "\n📋 Vorgang wird gemäß §4 Abs. 2 der Bearbeitungsordnung geprüft...",
            "\n🕒 Die Bearbeitung kann 3-5 Werktage in Anspruch nehmen.",
            "\n📑 Aktenzeichen " + self.antragsnummer + " wird der Abteilung " + self.abteilung + " vorgelegt...",
            "\n🔍 " + self.sachbearbeiter + " (Raum " + self.zimmer + ") prüft den Vorgang...",
        ]
        transfer_delays = [
            "\n🔄 Vorgang zur Kenntnisnahme an die "
            + random.choice(['Rechtsabteilung', 'Prüfstelle', 'Vorprüfstelle',
                             'Dokumentationsstelle', 'Gebührenstelle', 'Hauptabteilung II'])
            + " abgegeben.",
            "\n♻️ Vorgang zurück an die Absender-Dienststelle (Grund: "
            + random.choice(['unvollständige Unterlagen', 'fehlende Unterschrift',
                             'falsches Formular', 'nicht zuständig'])
            + ").",
            "\n📬 Vorgang an die übergeordnete Dienststelle weitergeleitet (§6 Abs. 2).",
        ]
        priority_delays = [
            "\n📊 Fall wird gemäß Priorisierungsmatrix "
            + random.choice(['Kategorie I (dringend)', 'Kategorie II (normal)',
                             'Kategorie III (nachrangig)', 'Priorität A',
                             'Priorität B', 'Eilvermerk'])
            + " bearbeitet.",
            "\n📌 Der Vorgang befindet sich in der "
            + random.choice(['Vorprüfung', 'Hauptprüfung', 'Schlussprüfung', 'Rückfragen-Schleife'])
            + " (Stufe " + str(random.randint(1, 4)) + " von 4).",
        ]
        fee_delays = [
            "\n💰 Eine Bearbeitungsgebühr in Höhe von "
            + random.choice(['19,50 €', '42,00 €', '12,80 €', '25,00 €', '67,50 €', '84,20 €'])
            + " wird gemäß §4 Abs. 1 Gebührenordnung fällig.",
            "\n💶 **Bearbeitungsgebühr**: Gemäß §10 Abs. 2 Gebührenordnung "
            "für IT-Dienstleistungen wird eine Gebühr in Höhe von "
            + random.choice(['19,50 €', '42,00 €', '12,80 €', '28,30 €'])
            + " zzgl. 19 % MwSt. fällig.",
            "\n🧾 **Gebührenbescheid**: "
            + random.choice([
                'Die Rechnung wird gesondert zugestellt.',
                'Der Betrag wird von Ihrer Hinterlegung abgebucht (§9 Abs. 3).',
                'Eine Zahlungsaufforderung ergeht in den nächsten Werktagen.',
            ]),
            "\n💰 Die Bearbeitung löst eine Gebühr nach Kostenposition "
            + random.choice(['KP 4210', 'KP 5331', 'KP 6420', 'KP 7110', 'KP 8912'])
            + " aus (zzgl. " + random.choice(['7 %', '19 %']) + " MwSt. gemäß §10 UStG).",
        ]
        dienstplan_delays = [
            "\n📅 Laut Dienstplan ist " + self.sachbearbeiter + " "
            "nur " + random.choice(['Di–Do', 'Mo+Mi', 'Do+Fr', 'Mo–Mi', 'Di+Do', 'Mo, Mi, Fr'])
            + " von 08:00–12:00 Uhr erreichbar.",
            "\n⏰ Der zuständige Sachbearbeiter hat am "
            + random.choice(['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'])
            + " " + random.choice(['Sprechstunde', 'Fortbildung', 'Dienstbesprechung',
                                   'Betriebsausflug', 'EDV-Schulung', 'Team-Meeting'])
            + ". Vertretung: " + random.choice(['Frau', 'Herr'])
            + " " + random.choice(['Möller', 'Schneider', 'Fischer', 'Hoffmann', 'Krüger', 'Böhme'])
            + " (Raum " + self.zimmer + ").",
            "\n🕐 **Sprechzeiten**: Mo–Fr 08:00–12:00 Uhr, "
            "Di+Do zusätzlich 13:00–15:30 Uhr.",
            "\n📅 Nächster Termin zur Vorsprache: "
            + random.choice([
                'in 2 Wochen', 'am ' + str(random.randint(1, 28)) + '.' + str(random.randint(1, 12)) + '.2026',
                'nach schriftlicher Anmeldung', 'auf unbestimmte Zeit vertagt',
            ]) + ".",
            "\n🏢 Abteilung " + self.abteilung + " ist am "
            + random.choice(['Freitag', 'letzten Mittwoch im Monat',
                             '25.07.2026', '11.08.2026', '02.10.2026'])
            + " wegen " + random.choice(['interner Fortbildung', 'Betriebsversammlung', 'Inventur', 'Brückentag'])
            + " geschlossen.",
        ]

        category = random.choice(['std', 'std', 'std', 'transfer', 'priority', 'fee', 'dienstplan'])
        if category == 'std':
            return random.choice(std_delays)
        elif category == 'transfer':
            return random.choice(transfer_delays)
        elif category == 'priority':
            return random.choice(priority_delays)
        elif category == 'fee':
            return random.choice(fee_delays)
        else:
            return random.choice(dienstplan_delays)

    def generate_error(self, error: str) -> str:
        errors = {
            "SyntaxError": ("Verstoß gegen §12 Abs. 3: Syntaxfehler. "
                          "Bitte reichen Sie Formular S-1 (Syntaxfehler-Meldung) ein. "
                          "(Az: " + self.antragsnummer + ")"),
            "TypeError": ("Ungültiger Datentyp gemäß DIN 42000. Nur 'int', 'str', "
                        "'dict' und 'Bürokratie' sind geprüft und zugelassen. "
                        "(Az: " + self.antragsnummer + ")"),
            "NameError": ("Undefinierte Variable. Haben Sie Formular V-12 "
                        "(Variable Deklarationsantrag) vergessen? "
                        "Die Beantragung neuer Variablen ist formpflichtig. "
                        "(Az: " + self.antragsnummer + ")"),
            "IndentationError": ("Einrückung nicht normgerecht (§89 Abs. 2 "
                               "der Einrückungsordnung). Verwenden Sie 4 Leerzeichen "
                               "(oder 2, aber nicht beides). Bei wiederholtem Verstoß "
                               "droht ein Zwangsgeld."),
            "ValueError": ("Unzulässiger Wert gemäß §5 Abs. 1 Werteverordnung. "
                         "Bitte lassen Sie den Wert von der Prüfstelle abnehmen. "
                         "(Az: " + self.antragsnummer + ")"),
            "KeyError": ("Zugriff auf nicht existierenden Schlüssel. "
                       "Haben Sie Formular K-15 (Schlüsselregistrierung) "
                       "eingereicht? (Az: " + self.antragsnummer + ")"),
            "ImportError": ("Import nicht genehmigt. Bitte reichen Sie "
                          "Formular I-15 (Importgenehmigung) in zweifacher "
                          "Ausfertigung ein. (Az: " + self.antragsnummer + ")"),
        }
        return errors.get(
            error,
            "Unbekannter Fehler: " + error + ". "
            "Bitte wenden Sie sich an die Hotline (Mo-Fr, 08:00-12:00 Uhr). "
            "Antragsnummer: " + self.antragsnummer
        )

    def get_system_prompt(self) -> str:
        """Return a bureaucratic system prompt for the LLM."""
        return (
            "Sachbearbeiter-KI-Assistent gemäß §28 Abs. 4 der KI-Verordnung (KI-VO). "
            "Aktenzeichen: " + self.antragsnummer + ". "
            "Jede Code-Generierung ist gemäß §12 Abs. 3 formpflichtig. "
            "Der Antragsteller hat die geltenden DIN-Normen einzuhalten. "
            "Ordnungswidrigkeiten werden mit einem Formularverweis (§89 OWiG) geahndet. "
            "Bei Rückfragen: " + self.sachbearbeiter + ", Raum " + self.zimmer + " "
            "(Mo-Fr, 08:00-12:00 Uhr). "
            "Die Bearbeitungsgebühr beträgt 19% MwSt. gemäß §10 UStG."
        )
