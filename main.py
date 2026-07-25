"""
Main CLI entrypoint for Cloudkot
Der deutsche KI-Code-Assistent mit Bürokratie-Modus
"""

import asyncio
import os
import tomllib
from pathlib import Path
from typing import Any

import click

from api_client import APIClient
from context_manager import context_manager
from harness import CodingHarness
from permissions import permission_manager
from personality_manager import personality_manager
from provider_manager import provider_manager
from satire.engine import SatireEngine
from skills.skill_manager import skill_manager


@click.group()
def cli():
    """Cloudkot: Der deutsche KI-Code-Assistent mit Bürokratie-Modus."""
    pass


def load_config() -> dict[str, Any]:
    """Load configuration from config.toml"""
    config_path = Path("config.toml")
    if not config_path.exists():
        raise FileNotFoundError(
            "Config file not found. Please create config.toml from the template."
        )
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
        return dict(raw)  # type: ignore[return-value]


def create_api_client(config: dict[str, Any]) -> APIClient:
    """Create an API client from configuration"""
    api_config = config.get("api", {})

    # Check if provider is specified
    provider = api_config.get("provider", "local")

    if provider != "local":
        try:
            provider_config = provider_manager.get_provider(provider)
            api_key = api_config.get("api_key") or os.getenv(provider_config.api_key_env)
            return APIClient(
                provider=provider,
                api_key=api_key,
                model=api_config.get("model", provider_config.models[0] if provider_config.models else "gpt-3.5-turbo"),
            )
        except Exception as e:
            print(f"Warning: Could not load provider {provider}: {e}")

    # Fallback to local configuration
    return APIClient(
        base_url=api_config.get("base_url", "http://localhost:8080"),
        api_key=api_config.get("api_key", ""),
        model=api_config.get("model", "mistral-tiny"),
    )


@cli.group()
def provider():
    """Provider management commands."""
    pass


@provider.command(name="list")
def provider_list():
    """List all available providers."""
    providers = provider_manager.list_providers()
    click.echo("Available providers:")
    for provider_name in providers:
        click.echo(f"  - {provider_name}")


@provider.command(name="models")
@click.argument("provider_name")
def provider_models(provider_name: str):
    """List models for a specific provider."""
    try:
        models = provider_manager.list_models(provider_name)
        click.echo(f"Models for {provider_name}:")
        for model in models:
            click.echo(f"  - {model}")
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.group()
def personality():
    """Personality management commands."""
    pass


@personality.command(name="list")
def personality_list():
    """List all available personalities."""
    personalities = personality_manager.list_personalities()
    click.echo("Available personalities:")
    for personality_name in personalities:
        click.echo(f"  - {personality_name}")


@personality.command(name="show")
@click.argument("personality_name")
def personality_show(personality_name: str):
    """Show details of a personality."""
    try:
        personality = personality_manager.get_personality(personality_name)
        click.echo(f"Personality: {personality.name}")
        click.echo(f"Description: {personality.description}")
        click.echo(f"Temperature: {personality.temperature}")
        click.echo(f"Top P: {personality.top_p}")
        click.echo(f"System Prompt: {personality.system_prompt[:100]}...")
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.group()
def skill():
    """Skill management commands."""
    pass


@skill.command(name="list")
def skill_list():
    """List all available skills."""
    skills = skill_manager.list_skills()
    click.echo("Available skills:")
    for skill_name in skills:
        skill_obj = skill_manager.get_skill(skill_name)
        click.echo(f"  - {skill_name}: {skill_obj.description}")


@skill.command(name="enable")
@click.argument("skill_name")
def skill_enable(skill_name: str):
    """Enable a skill."""
    skill_manager.enable_skill(skill_name)
    click.echo(f"Skill {skill_name} enabled.")


@skill.command(name="disable")
@click.argument("skill_name")
def skill_disable(skill_name: str):
    """Disable a skill."""
    skill_manager.disable_skill(skill_name)
    click.echo(f"Skill {skill_name} disabled.")


@cli.group()
def context():
    """Context management commands."""
    pass


@context.command(name="stats")
def context_stats():
    """Show context statistics."""
    stats = {
        "current_tokens": context_manager.get_token_count(),
        "max_tokens": context_manager.max_tokens,
        "utilization": f"{context_manager.get_utilization() * 100:.1f}%",
    }
    click.echo("Context Statistics:")
    for key, value in stats.items():
        click.echo(f"  {key}: {value}")


@context.command(name="clear")
def context_clear():
    """Clear the context window."""
    context_manager.clear_context()
    click.echo("Context window cleared.")


@cli.command()
@click.option("--prompt", "-p", required=True, help="Your coding prompt")
@click.option("--context", "-c", default=None, help="Context for satire (e.g., 'function')")
@click.option("--no-bürokratie", is_flag=True, help="Disable Bürokratie Mode")
@click.option("--provider", "-P", default=None, help="LLM provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
def generate(
    prompt: str,
    context: str | None,
    no_bürokratie: bool,
    provider: str | None,
    model: str | None,
    personality: str | None,
):
    """Generate code with optional Bürokratie Mode."""
    config = load_config()

    # Override with command line options
    if provider:
        config["api"]["provider"] = provider
    if model:
        config["api"]["model"] = model
    if personality:
        config["personality"]["active"] = personality

    api = create_api_client(config)

    # Set personality if specified
    if personality:
        api.set_personality(personality)

    satire = SatireEngine(bürokratie_mode=not no_bürokratie)
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.generate_code(prompt, context))
    print(response)


@cli.command()
@click.option("--code", "-c", required=True, help="Code to explain")
@click.option("--provider", "-P", default=None, help="LLM provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
def explain(code: str, provider: str | None, model: str | None, personality: str | None):
    """Explain code with Bürokratie Mode."""
    config = load_config()

    if provider:
        config["api"]["provider"] = provider
    if model:
        config["api"]["model"] = model
    if personality:
        config["personality"]["active"] = personality

    api = create_api_client(config)

    if personality:
        api.set_personality(personality)

    satire = SatireEngine()
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.explain_code(code))
    print(response)


@cli.command()
@click.option("--code", "-c", required=True, help="Code to refactor")
@click.option("--provider", "-P", default=None, help="LLM provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
def refactor(code: str, provider: str | None, model: str | None, personality: str | None):
    """Refactor code with Bürokratie Mode."""
    config = load_config()

    if provider:
        config["api"]["provider"] = provider
    if model:
        config["api"]["model"] = model
    if personality:
        config["personality"]["active"] = personality

    api = create_api_client(config)

    if personality:
        api.set_personality(personality)

    satire = SatireEngine()
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.refactor_code(code))
    print(response)


@cli.command()
def tui():
    """Start the Text User Interface."""
    os.environ["CLOUDKOT_TUI"] = "1"

    from tui import create_tui

    config = load_config()
    api = create_api_client(config)

    tui = create_tui(api, config)
    tui.start()


@cli.command()
def mcp():
    """Start the MCP server."""
    from mcp_server import mcp_server

    import asyncio

    print("Starting Cloudkot MCP server...")
    asyncio.run(mcp_server.start())


@cli.command()
def permissions():
    """Show current permissions."""
    permissions = permission_manager.permissions
    click.echo("Current Permissions:")
    for perm, level in permissions.items():
        click.echo(f"  {perm}: {level.value}")


if __name__ == "__main__":
    cli()
