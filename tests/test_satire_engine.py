"""
Unit tests for SatireEngine
"""

import pytest

from satire.engine import SatireEngine


@pytest.fixture
def satire_engine():
    """Create a SatireEngine instance for testing"""
    return SatireEngine(bürokratie_mode=True)


@pytest.fixture
def neutral_engine():
    """Create a SatireEngine instance with Bürokratie mode disabled"""
    return SatireEngine(bürokratie_mode=False)


class TestSatireEngine:
    """Tests for SatireEngine class"""

    def test_bürokratie_mode_on(self, satire_engine):
        """Test that Bürokratie mode wraps responses"""
        response = "def add(a, b): return a + b"
        wrapped = satire_engine.wrap_response(response, "function")

        # Should contain bureaucratic elements
        assert any(header in wrapped for header in [
            "Gemäß §12 Abs. 3",
            "Nach Rücksprache mit Abteilung",
            "Laut DIN 66234-8",
            "Aufgrund Ihres Antrags",
            "Sach- und Aktenlage",
            "Az:",
            "Prüfstelle",
            "Datenschutzbeauftragten",
        ])

        # Should contain the original response
        assert response in wrapped

        # Should contain a footer
        assert any(footer in wrapped for footer in [
            "Mehrwertsteuer (19%)",
            "Bitte bewahren Sie diese Ausgabe",
            "Genehmigt durch",
            "Antragsnummer:",
            "Fachreferat",
            "Gebührenbescheid",
            "Widerspruch ist innerhalb",
            "Sachbearbeiter:",
            "Ausfertigung",
            "Formular gültig",
        ])

    def test_bürokratie_mode_off(self, neutral_engine):
        """Test that Bürokratie mode off returns raw response"""
        response = "def add(a, b): return a + b"
        wrapped = neutral_engine.wrap_response(response, "function")

        # Should be exactly the same as input
        assert wrapped == response

    def test_form_hint_for_function(self, satire_engine):
        """Test that form hints are added for function context"""
        response = "def add(a, b): return a + b"
        wrapped = satire_engine.wrap_response(response, "function")

        # Should contain form hint for function
        assert "Formular F-42" in wrapped or "Funktionsgenehmigung" in wrapped

    def test_form_hint_for_variable(self, satire_engine):
        """Test that form hints are added for variable context"""
        response = "x = 42"
        wrapped = satire_engine.wrap_response(response, "variable")

        # Should contain form hint for variable
        assert "Formular V-12" in wrapped or "Variable Deklarationsantrag" in wrapped

    def test_form_hint_for_loop(self, satire_engine):
        """Test that form hints are added for loop context"""
        response = "for i in range(10): print(i)"
        wrapped = satire_engine.wrap_response(response, "loop")

        # Should contain form hint for loop
        assert "Formular L-89" in wrapped or "Schleifen-Zulassung" in wrapped

    def test_no_form_hint_without_context(self, satire_engine):
        """Test that no form hint is added without context"""
        response = "def add(a, b): return a + b"
        wrapped = satire_engine.wrap_response(response, None)

        # Should not contain form hints
        assert "Formular" not in wrapped

    def test_error_messages(self, satire_engine):
        """Test error message generation"""
        # Test known errors
        assert "§12 Abs. 3" in satire_engine.generate_error("SyntaxError")
        assert "DIN 42000" in satire_engine.generate_error("TypeError")
        assert "Formular V-12" in satire_engine.generate_error("NameError")
        assert "§89" in satire_engine.generate_error("IndentationError")

    def test_unknown_error(self, satire_engine):
        """Test unknown error handling"""
        error_msg = satire_engine.generate_error("UnknownError")
        assert "Unbekannter Fehler: UnknownError" in error_msg
        assert "Hotline" in error_msg

    def test_random_headers(self, satire_engine):
        """Test that headers are randomly selected"""
        response = "test"
        headers = set()

        # Generate multiple responses to test randomness
        # Use a larger number to account for random chance
        for _ in range(20):
            wrapped = satire_engine.wrap_response(response)
            # Extract the header (first line)
            header = wrapped.split('\n')[0]
            headers.add(header)

        # Should have multiple different headers (at least 2 out of 3 possible)
        assert len(headers) >= 2

    def test_random_footers(self, satire_engine):
        """Test that footers are randomly selected"""
        response = "test"
        footers = set()

        # Generate multiple responses to test randomness
        for _ in range(10):
            wrapped = satire_engine.wrap_response(response)
            # Extract the footer (last line)
            footer = wrapped.split('\n')[-1]
            footers.add(footer)

        # Should have multiple different footers
        assert len(footers) > 1
