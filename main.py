import asyncio
import click
from typing import Optional
from api_client import APIClient
from satire.engine import SatireEngine
from harness import CodingHarness
import tomllib
from pathlib import Path

@click.group()
def cli():
    """Cloudkot: Der deutsche KI-Code-Assistent mit Bürokratie-Modus."""
    pass

def load_config() -> dict:
    config_path = Path("config.toml")
    if not config_path.exists():
        raise FileNotFoundError(
            "Config file not found. Please create config.toml from the template."
        )
    with open(config_path, "rb") as f:
        return tomllib.load(f)

@cli.command()
@click.option("--prompt", "-p", required=True, help="Your coding prompt")
@click.option("--context", "-c", default=None, help="Context for satire (e.g., 'function')")
@click.option("--no-bürokratie", is_flag=True, help="Disable Bürokratie Mode")
def generate(prompt: str, context: Optional[str], no_bürokratie: bool):
    """Generate code with optional Bürokratie Mode."""
    config = load_config()
    api = APIClient(
        base_url=config["api"]["base_url"],
        api_key=config["api"]["api_key"],
        model=config["api"]["model"]
    )
    satire = SatireEngine(bürokratie_mode=not no_bürokratie)
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.generate_code(prompt, context))
    print(response)

@cli.command()
@click.option("--code", "-c", required=True, help="Code to explain")
def explain(code: str):
    """Explain code with Bürokratie Mode."""
    config = load_config()
    api = APIClient(
        base_url=config["api"]["base_url"],
        api_key=config["api"]["api_key"],
        model=config["api"]["model"]
    )
    satire = SatireEngine()
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.explain_code(code))
    print(response)

@cli.command()
@click.option("--code", "-c", required=True, help="Code to refactor")
def refactor(code: str):
    """Refactor code with Bürokratie Mode."""
    config = load_config()
    api = APIClient(
        base_url=config["api"]["base_url"],
        api_key=config["api"]["api_key"],
        model=config["api"]["model"]
    )
    satire = SatireEngine()
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.refactor_code(code))
    print(response)

if __name__ == "__main__":
    cli()