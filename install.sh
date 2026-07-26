#!/bin/bash

# Cloudkot Installationsskript
# Der deutsche KI-Code-Assistent mit B\u00fcrokratie-Modus
# 
# Verwendung:
#   curl -sSL https://raw.githubusercontent.com/luluthehungrycat/cloudkot/main/install.sh | bash
#   ODER
#   ./install.sh

set -euo pipefail

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# B\u00fcrokratie-Modus
BUREAUCRACY_MODE=${BUREAUCRACY_MODE:-false}

# Funktion zum Ausgeben von B\u00fcrokratie-Nachrichten
bureaucracy_echo() {
    if [ "$BUREAUCRACY_MODE" = true ]; then
        echo -e "${BLUE}[\u2714 B\u00fcrokratie-Modus]${NC} $1"
        echo -e "      Gem\u00e4\u00df \u00a712 Abs. 3 der Installationsverordnung"
    else
        echo -e "$1"
    fi
}

# Willkommensnachricht
clear
echo ""
echo -e "${GREEN}
  ██████╗ ██╗      ██████╗ ██████╗ ███████╗ ██████╗ ██████╗
  ██╔══██╗██║     ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗
  ██████╔╝██║     ██║   ██║██████╔╝█████╗  ██║   ██║██████╔╝
  ██╔═══╝ ██║     ██║   ██║██╔══██╗██╔══╝  ██║   ██║██╔══██╗
  ██║     ███████╗╚██████╔╝██║  ██║███████╗╚██████╔╝██║  ██║
  ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
${NC}"
echo -e "${YELLOW}Cloudkot - Der deutsche KI-Code-Assistent mit B\u00fcrokratie-Modus${NC}"
echo ""

# Pr\u00fcfung der Abh\u00e4ngigkeiten
bureaucracy_echo "\u2705 Pr\u00fcfung der Systemanforderungen..."

# Python-Version pr\u00fcfen
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1-2)
if [ -z "$PYTHON_VERSION" ]; then
    echo -e "${RED}Fehler: Python 3.10+ wird ben\u00f6tigt!${NC}"
    echo "Bitte installieren Sie Python 3.10 oder h\u00f6her."
    exit 1
fi

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo -e "${RED}Fehler: Python 3.10+ wird ben\u00f6tigt (gefunden: $PYTHON_VERSION)!${NC}"
    exit 1
fi

bureaucracy_echo "Python $PYTHON_VERSION - \u2714 Kompatibel"

# pip pr\u00fcfen
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Fehler: pip wird ben\u00f6tigt!${NC}"
    exit 1
fi

bureaucracy_echo "pip - \u2714 Verf\u00fcgbar"

# Installationsmethode ausw\u00e4hlen
echo ""
echo -e "${YELLOW}W\u00e4hlen Sie die Installationsmethode:${NC}"
echo ""
echo "1) Editable Install (f\u00fcr Entwicklung) - uv tool install -e ."
echo "2) Editable Install (f\u00fcr Entwicklung) - pip install -e ."
echo "3) Regul\u00e4re Install (f\u00fcr Produktion) - pip install ."
echo "4) Nur Abh\u00e4ngigkeiten installieren"
echo "5) Abbrechen"
echo ""

read -p "Auswahl [1-5, Default: 1]: " choice
choice=${choice:-1}

echo ""

case $choice in
    1)
        # Editable Install mit uv
        bureaucracy_echo "\u2705 Installiere mit uv (editable mode)..."
        
        if ! command -v uv &> /dev/null; then
            echo -e "${YELLOW}uv nicht gefunden. Installiere uv...${NC}"
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
        
        uv tool install -e .
        bureaucracy_echo "\u2714 Cloudkot wurde mit uv installiert (editable)"
        ;;
    2)
        # Editable Install mit pip
        bureaucracy_echo "\u2705 Installiere mit pip (editable mode)..."
        pip install -e .
        bureaucracy_echo "\u2714 Cloudkot wurde mit pip installiert (editable)"
        ;;
    3)
        # Regul\u00e4re Install
        bureaucracy_echo "\u2705 Installiere mit pip (regul\u00e4r)..."
        pip install .
        bureaucracy_echo "\u2714 Cloudkot wurde mit pip installiert"
        ;;
    4)
        # Nur Abh\u00e4ngigkeiten
        bureaucracy_echo "\u2705 Installiere nur Abh\u00e4ngigkeiten..."
        pip install -r pyproject.toml
        bureaucracy_echo "\u2714 Abh\u00e4ngigkeiten wurden installiert"
        ;;
    5)
        echo -e "${YELLOW}Installation abgebrochen.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Ung\u00fcltige Auswahl!${NC}"
        exit 1
        ;;
esac

echo ""

# Konfiguration erstellen
bureaucracy_echo "\u2705 Erstelle Beispiel-Konfiguration..."
if [ ! -f "config.toml" ] && [ -f "config.toml.example" ]; then
    cp config.toml.example config.toml
    echo -e "${GREEN}Beispiel-Konfiguration erstellt: config.toml${NC}"
    echo "Bitte passen Sie die Konfiguration an:"
    echo "  - API-Key eintragen"
    echo "  - Standard-Provider ausw\u00e4hlen"
    echo "  - Modell konfigurieren"
else
    echo -e "${YELLOW}config.toml existiert bereits oder config.toml.example nicht gefunden.${NC}"
fi

echo ""

# Erfolg!
echo -e "${GREEN}\u2714 Installation erfolgreich!${NC}"
echo ""
echo "Verf\u00fcgbare Befehle:"
echo ""
echo -e "  ${YELLOW}cloudkot${NC}           - CLI starten (interaktive Shell)"
echo -e "  ${YELLOW}cloudkot --help${NC}    - Alle Befehle anzeigen"
echo -e "  ${YELLOW}cloudkot generate -p \"...\"${NC} - Code generieren"
echo -e "  ${YELLOW}cloudkot explain -c \"...\"${NC}   - Code erkl\u00e4ren"
echo -e "  ${YELLOW}cloudkot tui${NC}        - Text-UI starten (zuk\u00fcnftig)"
echo ""

if [ "$BUREAUCRACY_MODE" = true ]; then
    echo -e "${BLUE}---
Hinweis: Dieser Code unterliegt der Mehrwertsteuer (19%).
Bitte bewahren Sie diese Ausgabe f\u00fcr Ihre Unterlagen auf.
Formular I-15 (Installationsgenehmigung) wurde automatisch eingereicht.
Az: CLOUDKOT-INSTALL-$(date +%Y)-$(shuf -i 10000-99999 -n 1)${NC}"
fi

echo ""
