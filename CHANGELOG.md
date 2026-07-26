# Cloudkot Changelog

> *\u00c4nderungsprotokoll f\u00fcr den deutschen KI-Code-Assistenten mit B\u00fcrokratie-Modus*

---

## \ud83d\udce2 Format

Dieses Changelog folgt den [Keep a Changelog](https://keepachangelog.com/) Richtlinien.

### Kategorien
- **\u2705 Added** - Neue Features
- **\ud83d\udc80 Changed** - \u00c4nderungen an bestehenden Features
- **\ud83d\udcf2 Fixed** - Bugfixes
- **\ud83d\udcd1 Deprecated** - Veraltete Features
- **\u274c Removed** - Entfernte Features
- **\ud83d\udc89 Security** - Sicherheitsrelevante \u00c4nderungen
- **\ud83d\udca1 Performance** - Performance-Verbesserungen

---

## \u2728 [Unreleased]

### \u2705 Added
- `ROADMAP.md` - Entwicklungsplan mit Phasen und Meilensteinen
- `CHANGELOG.md` - Dieses \u00c4nderungsprotokoll
- Custom Exception Hierarchie (`exceptions.py`)
  - `CloudkotError` als Basis-Klasse
  - `APIError`, `ProviderError`, `ConfigurationError`
  - `TokenLimitError`, `CloudkotValidationError`
  - `SkillError`, `ToolExecutionError`, `PermissionError`
- `config.toml.example` - Beispiel-Konfiguration f\u00fcr einfache Einrichtung
- GitHub Actions Workflows:
  - `lint.yml` - Ruff, Black, mypy Checks
  - `test.yml` - Tests mit Coverage
  - `release.yml` - Build & Publish

### \ud83d\udc80 Changed
- `requirements.txt` entfernt, nur noch `pyproject.toml` wird verwendet
- API-Client verbessert:
  - Retry-Logik mit Tenacity (3 Versuche, exponentieller Backoff)
  - Metrics Tracking (Requests, Errors, Latency)
  - Bessere Error-Handling mit Custom Exceptions
  - API-Key-Validierung basierend auf Provider
- Kontext-Manager:
  - Tiktoken-Unterst\u00fctzung f\u00fcr genaues Token-Counting
  - Verbesserte Kontext-Kompression
- Provider-Manager & Personality-Manager:
  - Custom Exceptions statt generischer Errors
  - Bessere Fehler messages
- `pyproject.toml`:
  - Vollst\u00e4ndige Metadaten (Homepage, Repository, Classifiers)
  - Neue Abh\u00e4ngigkeiten: `tiktoken`, `tenacity`

### \u2705 Added (Tests)
- `tests/test_api_client.py` - 19 neue Tests f\u00fcr APIClient
  - Initialisierungstests
  - API-Key-Validierung
  - Chat-Funktionalit\u00e4t (Streaming & Non-Streaming)
  - Error-Handling
  - Metrics-Tracking
  - Tool-Calls

### \ud83d\udcf2 Fixed
- Zirkul\u00e4re Importe in einigen Modulen behoben
- Test-Fixtures in `test_api_client.py` korrigiert
- Syntax-Error in `test_satire_engine.py` behoben
- Import-Probleme in Test-Dateien gel\u00f6st

### \ud83d\udca1 Performance
- Genaues Token-Counting mit Tiktoken (falls verfg\u00fcbar)
- Caching f\u00fcr Provider-Konfigurationen
- Optimierte Kontext-Kompression

---

## \ud83d\udcdd [0.1.0] - 2026-07-XX

### \u2705 Added
- Erste stabile Version von Cloudkot
- B\u00fcrokratie-Satire-Engine mit Formularen
- Multi-Provider-Unterst\u00fctzung:
  - OpenAI (ChatGPT)
  - Anthropic (Claude)
  - Mistral AI
  - OpenRouter
  - OpenCode (Go & Zen)
  - Local (LM Studio, LocalAI)
- Personality-System:
  - `neutral` - Professionell und direkt
  - `stromberg` - Corporate-Style
  - `friendly` - Warm und ermutigend
  - `pedantic` - Pr\u00e4zise und detailorientiert
- Tool-Calling-System:
  - `read_file` - Dateien lesen
  - `glob_files` - Dateien suchen
  - `grep_files` - In Dateien suchen
  - `run_command` - Shell-Befehle ausf\u00fchren
  - `list_files` - Verzeichnisinhalte auflisten
- Kontext-Management mit Token-Limits
- Permission-System
- Skill-System
- LSP-Server f\u00fcr IDE-Integration
- MCP-Server f\u00fcr Model Context Protocol
- TUI (Text User Interface)
- CLI mit Click

---

## \ud83d\udc89 Mitwirkende

Danke an alle, die zu Cloudkot beigetragen haben!

---

## \ud83d\udcdc Richtlinien f\u00fcr Mitwirkende

### Wann sollte das CHANGELOG aktualisiert werden?

Das **CHANGELOG.md** sollte bei **jeder substanziellen \u00c4nderung** aktualisiert werden, insbesondere bei:

1. **Neuen Features** (\u2705 Added)
   - Neue Module, Klassen, Funktionen
   - Neue CLI-Befehle oder Optionen
   - Neue Provider oder Integrationen

2. **\u00c4nderungen an bestehenden Features** (\ud83d\udc80 Changed)
   - API-\u00c4nderungen (auch interne)
   - Ver\u00e4nderte Standardwerte
   - Verbesserungen an bestehenden Funktionen

3. **Bugfixes** (\ud83d\udcf2 Fixed)
   - Alle behobenen Bugs (auch kleine)
   - Sicherheitsfixes (\ud83d\udc89 Security)

4. **Performance-Verbesserungen** (\ud83d\udca1 Performance)
   - Optimierungen, die die Performance messbar verbessern

5. **Breaking Changes** (\u274c Removed, \ud83d\udcd1 Deprecated)
   - **Immer** dokumentieren!
   - Migration-Hinweise hinzuf\u00fcgen

### Wann ist es optional?

Kleine \u00c4nderungen k\u00f6nnen weggelassen werden:
- Dokumentations-Typos
- Kommentar-Anpassungen
- Whitespace-\u00c4nderungen
- Test-Refactorings ohne Funktions\u00e4nderung

### Formatierung

- **\u00c4nderungen gruppieren** nach Kategorie
- **Chronologische Reihenfolge** (neueste zuerst)
- **Klare, pr\u00e4zise Beschreibungen**
- **Links zu Issues/PRs** falls vorhanden
- **Breaking Changes** immer mit **!** markieren

### Beispiel-Eintr\u00e4ge

```markdown
### \u2705 Added
- Neue Funktion `generate_documentation()` f\u00fcr automatische Docstring-Generierung
- Unterst\u00fctzung f\u00fcr Python 3.12

### \ud83d\udc80 Changed
- `api_client.py`: Standard-Timeout von 30s auf 60s erh\u00f6ht
- Konfiguration wird jetzt aus `config.toml` statt `settings.json` geladen

### \ud83d\udcf2 Fixed
- Bug in Token-Counting behoben, der bei leeren Strings zu negativen Werten f\u00fchrte
- Memory-Leak in Context-Manager gefixt

### \u274c Removed
- Veraltete Funktion `old_api_call()` entfernt (ersetzt durch `new_api_call()`)

### \ud83d\udc89 Security
- API-Key-Validierung versch\u00e4rft
```

### Automatisierung

F\u00fcr die Zukunft k\u00f6nnte ein Skript erstellt werden, das:
1. Commit-Messages parst
2. Automatisch CHANGELOG-Eintr\u00e4ge generiert
3. Vor dem Merge eine Erinnerung ausgibt

---

*\"Dieses Changelog unterliegt der Mehrwertsteuer (19%). Bitte bewahren Sie diese Ausgabe f\u00fcr Ihre Unterlagen auf.\"*
