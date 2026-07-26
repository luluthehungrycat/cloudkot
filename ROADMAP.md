# Cloudkot Roadmap

> *Der deutsche KI-Code-Assistent mit B\u00fcrokratie-Modus - Entwicklungsplan*

---

## \u26a1\ufe0f Vision

Cloudkot soll ein **vollwertiger, installierbarer KI-Code-Assistent** werden, der sich durch:
- **Deutsche B\u00fcrokratie-Satire** als Alleinstellungsmerkmal auszeichnet
- **Modularit\u00e4t** durch Profile, Agenten und Plugins bietet
- **Benutzerfreundlichkeit** durch klare CLI/TUI-Unterschiede erreicht
- **Erweiterbarkeit** f\u00fcr Custom-Agenten und Workflows erm\u00f6glicht

---

## \ud83c\udfaf Phasen & Meilensteine

### \ud83d\udcca Phase 1: Grundlagen (Aktuell - v0.2.0)
**Ziel:** Stabilisierung der Kernfunktionalit\u00e4t

#### \u2705 Abgeschlossen
- [x] Custom Exception Hierarchie
- [x] Verbessertes Error Handling
- [x] API-Client mit Retry-Logik
- [x] Metrics Tracking
- [x] Tiktoken-Integration
- [x] Testabdeckung (87 Tests)
- [x] GitHub Actions CI/CD

#### \ud83d\udcb6 Geplant
- [ ] **Profile f\u00fcr prim\u00e4re Agenten**
  - `plan`-Profil: Code-Planung, Architektur-Design
  - `build`-Profil: Code-Generierung, Implementierung
  - `review`-Profil: Code-Review, Qualit\u00e4tssicherung
  - `debug`-Profil: Fehleranalyse, Troubleshooting
  - Jedes Profil mit **voreingestellten Permissions**
- [ ] **Custom-Agenten-Unterst\u00fctzung**
  - Markdown-basierte Agenten-Definitionen in `.agents/`
  - Dynamisches Laden von Agenten aus CWD
  - Kompatibilit\u00e4t mit `.agents/`-Struktur
- [ ] **Installierbare CLI**
  - `uv tool install -e .` Unterst\u00fctzung
  - Installationsskript (`install.sh`)
  - PyPI-Paket mit Entry Points

---

### \ud83d\udcc9 Phase 2: Benutzererfahrung (v0.3.0 - v0.4.0)
**Ziel:** Professionelle CLI/TUI-Trennung

#### \u26a1\ufe0f TUI vs CLI Kl\u00e4rung

| Feature | **CLI Modus** (aktuell `tui.py`) | **TUI Modus** (neu) |
|---------|--------------------------------|---------------------|
| **Zweck** | Interaktive Shell/REPL | Vollwertige Text-UI |
| **Vergleichbar mit** | Python REPL, bash | OpenCode, Hermes, Claude Code |
| **Start** | `cloudkot cli` oder `cloudkot` | `cloudkot tui` |
| **Interaktion** | Zeilenbasiert, Befehle | Men\u00fcs, Auswahlen, Multiline |
| **Use Cases** | Schnelle Anfragen, Skripting | Komplexe Workflows, Session-Management |
| **Technologie** | click, prompt-toolkit (einfach) | Textual, Rich, oder custom |

#### \ud83d\udca1 Aufgaben

1. **CLI Modus umbenennen & verbessern**
   - Aktuelles `tui.py` \u2192 `cli_shell.py`
   - Entry Point: `cloudkot cli` oder `cloudkot` (default)
   - Features:
     - Command History (\u2191/\u2193 Navigation)
     - Tab-Completion f\u00fcr Befehle
     - Persistente Sessions
     - Kontext-Management per Befehl

2. **Echte TUI implementieren**
   - Neue Datei: `tui.py` (ersetzt aktuelles)
   - Entry Point: `cloudkot tui`
   - Features:
     - **Men\u00fcsystem** mit Tastatursteuerung
     - **Session-Management** (Speichern/Laden von Chats)
     - **Multi-Pane Layout** (Code, Chat, Logs)
     - **Syntax Highlighting** f\u00fcr Code-Bl\u00f6cke
     - **Tool-Calling Visualisierung**
     - **Themes** (Hell/Dunkel Modus)
   - Technologie-Optionen:
     - **Textual** (empfohlen - modern, aktiv)
     - **Rich** (einfacher, aber weniger Features)
     - **Custom mit curses** (maximale Kontrolle)

3. **Profile-System**
   - **Prim\u00e4re Profile:**
     ```toml
     # profiles.toml
     [profiles.plan]
     name = "Plan"
     description = "Code-Planung und Architektur-Design"
     model = "gpt-4o"
     temperature = 0.3
     permissions = { tool_calls = "allow", file_access = "allow", network_access = "deny" }
     system_prompt = "Du bist ein erfahrener Software-Architekt..."
     
     [profiles.build]
     name = "Build"
     description = "Code-Implementierung"
     model = "claude-3-5-sonnet"
     temperature = 0.7
     permissions = { tool_calls = "allow", file_access = "allow", network_access = "ask" }
     system_prompt = "Du bist ein pr\u00e4ziser Code-Generator..."
     
     [profiles.review]
     name = "Review"
     description = "Code-Review und Qualit\u00e4tssicherung"
     model = "gpt-4o"
     temperature = 0.1
     permissions = { tool_calls = "allow", file_access = "allow", network_access = "allow" }
     system_prompt = "Du bist ein strenger Code-Reviewer..."
     
     [profiles.debug]
     name = "Debug"
     description = "Fehleranalyse und Troubleshooting"
     model = "gpt-4o"
     temperature = 0.5
     permissions = { tool_calls = "allow", file_access = "allow", network_access = "allow" }
     system_prompt = "Du bist ein systematischer Debugger..."
     ```
   - **Custom Profile:**
     - Benutzer k\u00f6nnen eigene Profile in `~/.cloudkot/profiles.toml` definieren
     - Profile k\u00f6nnen per CLI-Argument gew\u00e4hlt werden: `--profile plan`

---

### \ud83d\udcc8 Phase 3: Erweiterbarkeit (v0.5.0 - v0.6.0)
**Ziel:** Plugin-System & Agenten-Marktplatz

#### \ud83d\udc80 Custom-Agenten in Markdown

**Konzept:** Agenten werden als Markdown-Dateien in `.agents/` definiert

```markdown
# .agents/my-agent.md

---
name: My Custom Agent
description: Ein benutzerdefinierter Agent f\u00fcr spezielle Aufgaben
author: Max Mustermann
version: 1.0.0
---

## Konfiguration

```toml
model = "gpt-4o"
temperature = 0.8
permissions = { tool_calls = "allow", file_access = "ask" }
```

## System Prompt

Du bist ein hilfreicher Assistent, der...

## Beispiele

- "Erkl\u00e4re mir Python-Dekoratoren"
- "Schreibe einen Unit-Test f\u00fcr diese Funktion"

## Tools

- read_file
- glob_files
- grep_files
```

**Lade-Mechanismus:**
1. Suche nach `.agents/` im aktuellen Verzeichnis
2. Lade alle `.md`-Dateien als Agenten
3. Parse Frontmatter f\u00fcr Konfiguration
4. Extrahiere System Prompt aus dem Inhalt

#### \ud83d\udc81 Agenten-Registry
- **Lokale Agenten:** `.agents/` im Projekt
- **Globale Agenten:** `~/.cloudkot/agents/`
- **Community-Agenten:** \u00dfer GitHub-Repository (zuk\u00fcnftig)

---

### \ud83c\udf08 Phase 4: Enterprise-Features (v0.7.0+)
**Ziel:** Team-Kollaboration & Unternehmenstauglichkeit

- **Projekt-Konfiguration** (`cloudkot.yml`)
  ```yaml
  version: "0.7.0"
  default_profile: "build"
  agents:
    - path: ".agents/"
    - url: "https://github.com/org/cloudkot-agents"
  permissions:
    default: "ask"
    overrides:
      file_access: "allow"
  ```

- **Session-Management**
  - Speichern von Chat-Verl\u00e4ufen
  - Export/Import von Sessions
  - Session-Suche und Filter

- **Team-Features**
  - Geteilte Agenten-Konfigurationen
  - Projekt-spezifische Profile
  - Audit-Logging

- **Sicherheit**
  - API-Key-Verschl\u00fcsselung
  - Permission-Granularit\u00e4t
  - Audit-Trails

---

### \ud83c\udf88 Phase 5: \u00d0berlegungen (v1.0.0+)
**Ziel:** Vollwertige IDE-Integration

- **LSP-Server Verbesserungen**
  - Code-Completion
  - Hover-Dokumentation
  - Diagnostics (B\u00fcrokratie-Warnungen!)

- **VS Code Extension**
  - Native Integration
  - Sidebar f\u00fcr Cloudkot-Features
  - Formular-Preview

- **Web-Interface**
  - React-basierte UI
  - Echtzeit-Kollaboration
  - Cloud-Hosting-Option

- **KI-Marktplatz**
  - Agenten teilen
  - Profile bewerten
  - Community-Features

---

## \ud83d\udcc5 Technische Architektur

```
cloudkot/
├── cloudkot/                  # Core Package
│   ├── __init__.py
│   ├── cli/                   # CLI Modus (Shell)
│   │   ├── __init__.py
│   │   ├── shell.py          # REPL-\u00e4hnliche Umgebung
│   │   └── commands.py       # CLI-Befehle
│   ├── tui/                   # TUI Modus (Text-UI)
│   │   ├── __init__.py
│   │   ├── app.py            # Haupt-TUI-Anwendung
│   │   ├── components/       # TUI-Komponenten
│   │   │   ├── chat.py
│   │   │   ├── code.py
│   │   │   └── tools.py
│   │   └── themes.py         # Farbschemata
│   ├── profiles/              # Profile-System
│   │   ├── __init__.py
│   │   ├── loader.py         # Profile laden
│   │   └── builtin/          # Eingebaute Profile
│   │       ├── plan.toml
│   │       ├── build.toml
│   │       ├── review.toml
│   │       └── debug.toml
│   ├── agents/               # Agenten-System
│   │   ├── __init__.py
│   │   ├── loader.py         # Markdown-Agenten laden
│   │   └── registry.py       # Agenten-Registry
│   └── ...                  # Bestehende Module
├── .agents/                  # Custom-Agenten (CWD)
│   └── my-agent.md
├── pyproject.toml
├── ROADMAP.md               # Diese Datei
├── CHANGELOG.md              # \u00c4nderungsprotokoll
└── AGENTS.md                # Entwickler-Richtlinien
```

---

## \ud83d\udc68 Priorit\u00e4ten & Zeitplan

| Phase | Version | Dauer | Priorit\u00e4t |
|-------|---------|-------|------------|
| 1 | v0.2.0 | 2-4 Wochen | \u26a1\ufe0f Hoch |
| 2 | v0.3.0 | 4-6 Wochen | \u26a1\ufe0f Hoch |
| 3 | v0.5.0 | 6-8 Wochen | \ud83d\udcca Mittel |
| 4 | v0.7.0 | 8-12 Wochen | \ud83d\udcc9 Niedrig |
| 5 | v1.0.0 | 3-6 Monate | \ud83c\udf88 Zukunft |

---

## \ud83d\udc89 Mitwirkende gesucht!

Wir suchen Hilfe bei:
- **TUI-Entwicklung** (Textual/Rich-Experten)
- **Plugin-System Design**
- **Dokumentation** (besonders auf Deutsch!)
- **Testing** (Integrationstests, E2E)
- **UI/UX-Design** f\u00fcr TUI

Interessiert? \u00d6ffne einen PR oder Issue!

---

*\"Diese Roadmap unterliegt der Mehrwertsteuer (19%). Bitte bewahren Sie diese Ausgabe f\u00fcr Ihre Unterlagen auf.\"*
