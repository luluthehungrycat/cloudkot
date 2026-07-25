from pygls.server import LanguageServer
from pygls.lsp.types import (
    Diagnostic, DiagnosticSeverity, Range, Position,
    CodeAction, CodeActionKind, TextEdit, WorkspaceEdit
)
from harness import CodingHarness
from api_client import APIClient
from satire.engine import SatireEngine
import tomllib
from pathlib import Path

def load_config() -> dict:
    config_path = Path("config.toml")
    with open(config_path, "rb") as f:
        return tomllib.load(f)

config = load_config()
api = APIClient(
    base_url=config["api"]["base_url"],
    api_key=config["api"]["api_key"],
    model=config["api"]["model"]
)
satire = SatireEngine()
harness = CodingHarness(api, satire)

server = LanguageServer("cloudkot-lsp", "v0.1")

@server.feature("textDocument/publishDiagnostics")
def on_diagnostics(ls, params):
    uri = params.text_document.uri
    text = ls.workspace.get_document(uri).source
    diagnostics = []
    for i, line in enumerate(text.split("\n")):
        if not line.strip().endswith(";"):
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=i, character=0),
                    end=Position(line=i, character=len(line))
                ),
                message="Fehlendes Semikolon (§12 Abs. 3). Bitte Formular S-1 einreichen.",
                severity=DiagnosticSeverity.Warning,
                source="Cloudkot Bürokratie"
            ))
        if "TODO" in line:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=i, character=0),
                    end=Position(line=i, character=len(line))
                ),
                message="TODO gefunden. Bitte bis zum 01.01.2027 erledigen (§42).",
                severity=DiagnosticSeverity.Information,
                source="Cloudkot Bürokratie"
            ))
    ls.publish_diagnostics(uri, diagnostics)

@server.feature("textDocument/codeAction")
def on_code_action(ls, params):
    actions = []
    for diagnostic in params.context.diagnostics:
        if "Semikolon" in diagnostic.message:
            actions.append(CodeAction(
                title="Semikolon hinzufügen (Formular S-1)",
                kind=CodeActionKind.QuickFix,
                edit=WorkspaceEdit(document_changes={
                    params.text_document.uri: [TextEdit(
                        range=diagnostic.range,
                        new_text=diagnostic.range.end.character + ";"
                    )]
                }),
                diagnostics=[diagnostic]
            ))
    return actions

server.start_io()