# Cloudkot 🇩🇪💩

*Der deutsche KI-Code-Assistent mit Bürokratie-Modus – ein Wolkenschiss von einem Tool.*

Cloudkot ist ein **satirisches** Coding-Tool, das jeden Code-Vorgang in ein **bürokratisches Meisterwerk** verwandelt. Inspiriert von der deutschen Liebe zu Normen, Formularen und §-Paragrafen.

⚠️ **WICHTIGER HINWEIS:**
Dies ist ein **Spaßprojekt** und nicht mit Anthropic, Claude, oder anderen KI-Anbietern verbunden. Alle Markenrechte gehören ihren jeweiligen Eigentümern.

Abmahnungen nebst Unterlassungserklärungen sind jederzeit unter Einhaltung der Verjährungsfrist von sieben Stunden nach Kenntnisnahme über die mutmaßliche Marken- oder Urheberrechtsverletzung möglich. 
Bitte laden Sie hierzu das ausgefüllte Formular U-121 nach § 69 UrhG und § 33 MarkenG im PDF-Format hoch. 


Bei falsch ausgefülltem Formular hat der Antragsteller seinen Unterlassungsanspruch automatisch verwirkt und sämtliches Eigentum am Urheber- und Markenrecht, welches der Antragsteller verletzt sieht, geht auf den Eigentümer von Cloudkot (C) über; der Rechtsweg hiergeg ist ausgeschlossen.


Der Eigentümer von Cloudkot (C) behält sich darüber hinaus das Recht vor, bei Vorlage eines (un)gültigen Abmahnungsformulars Strafantrag gegen den Antragsteller wegen unterlassenem Spaßverständnisses (§ 6969 StGB) beim Bundeskomödiantendezernat einzureichen.

---

## ✨ Features

- ✅ **Code-Generierung** mit DIN-Norm-Konformität
- ✅ **Bürokratie-Modus**: Jede Code-Änderung erfordert Formulare
- ✅ **Deutsche Fehler-Meldungen** (z.B. *"Verstoß gegen §12 Abs. 3"*)
- ✅ **Fake PDF-Formulare** für Variablen, Funktionen, Schleifen
- ✅ **LSP-Integration** für IDEs (VS Code, Neovim)
- ✅ **OpenAI-kompatibel**: Funktioniert mit Mistral, Groq, LocalAI, etc.

---

## 🚀 Schnellstart

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
# oder mit Poetry:
poetry install
```

### 2. config.toml anpassen:
```toml
[api]
base_url = "http://localhost:8080"  # z.B. LM Studio, LocalAI, Mistral
api_key = "dein-api-schlüssel"
model = "mistral-tiny"
```

### 3. CLI nutzen:
```bash
# Code generieren
python main.py generate -p "Schreibe eine Python-Funktion zum Addieren"

# Code erklären
python main.py explain -c "def add(a, b): return a + b"

# Bürokratie-Modus deaktivieren
python main.py generate -p "..." --no-bürokratie
```

### 4. (Optional) LSP Server starten:
```bash
python lsp_server.py
```

---

## 📁 Projektstruktur

```
cloudkot/
├── config.toml          # API-Einstellungen
├── main.py              # CLI
├── lsp_server.py        # LSP-Server (optional)
├── api_client.py        # OpenAI-kompatibler Client
├── harness.py           # Kern-Logik
├── satire/
│   ├── __init__.py
│   ├── engine.py        # Bürokratie-Wrapper
│   └── forms.py         # Fake-PDF-Generator
├── forms/               # Generierte Formulare
├── pyproject.toml       # Abhängigkeiten
├── requirements.txt     # Pip-Abhängigkeiten
├── LICENSE              # Modifizierte MIT-Lizenz
└── README.md
```

---

## 🎯 Beispielaufgabe:

```bash
python main.py generate -p "Schreibe eine Python-Funktion zum Addieren"
```

### Ausgabe:
```
Gemäß §12 Abs. 3 der Code-Verordnung:

def addiere(a: float, b: float) -> float:
    """
    Fügt zwei Zahlen zusammen.
    §1: a und b müssen numerisch sein.
    §2: Das Ergebnis unterliegt der Mehrwertsteuer (19%).
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Ungültige Eingabe. Bitte wenden Sie sich an die Hotline.")
    return a + b

---
Hinweis: Dieser Code unterliegt der Mehrwertsteuer (19%).
📄 Hinweis: Bitte reichen Sie [Formular F-42: Funktionsgenehmigung](forms/formular_f_42_funktionsgenehmigung.pdf) ein.
```

---

## 📚 Entwicklung

### Vorraussetzungen
- Python 3.10+
- Poetry oder pip

### Installation
```bash
# Mit Poetry
poetry install

# Mit pip
pip install -r requirements.txt
```

### Tests
```bash
pytest
```

---

## 📜 Lizenz

**Cloudkot Lizenzvertrag (Modifizierte MIT-Lizenz)**

> Modifizierte MIT Lizenz – Aber bitte füllen Sie zuerst Formular L-101 aus, bevor Sie den Code verwenden.

Diese Software unterliegt einer modifizierten MIT-Lizenz mit folgenden zusätzlichen Bedingungen:

> **§ 3 - Lizenzverlust bei Falschangaben**
> **FALSCH AUSGEFÜLLTE DIN 400-ANTRÄGE FÜHREN AUTOMATISCH ZUM LIZENZVERLUST DES ANTRAGSTELLERS AUF LEBENSZEIT.**

Die vollständige Lizenz finden Sie in der Datei [LICENSE](LICENSE).

---

## 🎭 Persönlichkeiten

Cloudkot unterstützt verschiedene Persönlichkeitseinstellungen:
- **neutral** - Professionell und direkt
- **stromberg** - Effizient mit corporate-style (inspiriert von Führungseigenschaften)
- **friendly** - Warm und ermutigend
- **pedantic** - Präzise und detailorientiert

Verwendung:
```bash
python main.py generate -p "..." --personality stromberg
```

---

## 🏢 Provider

Unterstützte LLM-Provider:
- OpenAI (API Key & OAuth)
- Anthropic
- Mistral AI
- OpenRouter
- OpenCode Go & Zen

Verwendung:
```bash
python main.py generate -p "..." --provider openai --model gpt-4o
```

---

*"Diese Dokumentation unterliegt der Mehrwertsteuer (19%). Bitte bewahren Sie diese Ausgabe für Ihre Unterlagen auf."*
