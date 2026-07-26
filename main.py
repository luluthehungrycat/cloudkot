"""
Main CLI entrypoint for Cloudkot
Der deutsche KI-Code-Assistent mit B\u00fcrokratie-Modus
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import click

from api_client import APIClient
from context_manager import context_manager
from exceptions import ConfigurationError, ProviderError, CloudkotValidationError
from harness import CodingHarness
from permissions import permission_manager
from personality_manager import personality_manager
from provider_manager import provider_manager
from satire.engine import SatireEngine
from skills.skill_manager import skill_manager


@click.group()
def cli():
    """Cloudkot: Der deutsche KI-Code-Assistent mit B\u00fcrokratie-Modus."""
    pass


def load_config() -> dict[str, Any]:
    """Load configuration from config.toml or create default"""
    config_path = Path("config.toml")
    
    # Check if config exists, otherwise try to copy from example
    if not config_path.exists():
        example_path = Path("config.toml.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, config_path)
            print(f"Created config.toml from {example_path}")
        else:
            # Create minimal default config
            default_config = """[api]
base_url = "http://localhost:8080"
api_key = ""
model = "mistral-tiny"
provider = "local"

[context]
max_tokens = 32768
compression_enabled = true
compression_threshold = 0.8

[personality]
active = "neutral"

[permissions]
tool_calls = "allow"
file_access = "ask"
network_access = "deny"
execute_code = "ask"
"""
            with open(config_path, "w") as f:
                f.write(default_config)
            print(f"Created default config at {config_path}")
    
    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
            return dict(raw)  # type: ignore[return-value]
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}", config_file=str(config_path)) from e


def _resolve_env_refs(value: Any) -> Any:
    """Resolve $VAR and ${VAR} environment variable references in string values."""
    if not isinstance(value, str):
        return value
    def _replace(match):
        var_name = match.group(1) or match.group(2)
        return os.getenv(var_name, "")
    return re.sub(r'\$(\w+)|\$\{(\w+)\}', _replace, value)


def create_api_client(config: dict[str, Any]) -> APIClient:
    """Create an API client from configuration"""
    api_config = config.get("api", {})

    # Check if provider is specified
    provider = api_config.get("provider", "local")

    if provider != "local":
        try:
            provider_config = provider_manager.get_provider(provider)
            api_key = _resolve_env_refs(api_config.get("api_key")) or os.getenv(provider_config.api_key_env)
            return APIClient(
                provider=provider,
                api_key=api_key,
                model=_resolve_env_refs(api_config.get("model", provider_config.models[0] if provider_config.models else "gpt-3.5-turbo")),
            )
        except ProviderError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Available providers:", file=sys.stderr)
            for p in provider_manager.list_providers():
                print(f"  - {p}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Warning: Could not load provider {provider}: {e}", file=sys.stderr)

    # Fallback to local configuration
    return APIClient(
        base_url=_resolve_env_refs(api_config.get("base_url", "http://localhost:8080")),
        api_key=_resolve_env_refs(api_config.get("api_key", "")),
        model=_resolve_env_refs(api_config.get("model", "mistral-tiny")),
    )


@cli.group()
def provider():
    """Provider management commands."""
    pass


@provider.command(name="list")
def provider_list():
    """List all available providers."""
    try:
        providers = provider_manager.list_providers()
        click.echo("Available providers:")
        for provider_name in providers:
            click.echo(f"  - {provider_name}")
    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@provider.command(name="models")
@click.argument("provider_name")
def provider_models(provider_name: str):
    """List models for a specific provider."""
    try:
        models = provider_manager.list_models(provider_name)
        click.echo(f"Models for {provider_name}:")
        for model in models:
            click.echo(f"  - {model}")
    except (ProviderError, ConfigurationError, CloudkotValidationError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def personality():
    """Personality management commands."""
    pass


@personality.command(name="list")
def personality_list():
    """List all available personalities."""
    try:
        personalities = personality_manager.list_personalities()
        click.echo("Available personalities:")
        for personality_name in personalities:
            click.echo(f"  - {personality_name}")
    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


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
    except (CloudkotValidationError, ConfigurationError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


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
@click.option("--no-b\u00fcrokratie", is_flag=True, help="Disable B\u00fcrokratie Mode")
@click.option("--provider", "-P", default=None, help="LLM provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
def generate(
    prompt: str,
    context: str | None,
    no_b\u00fcrokratie: bool,
    provider: str | None,
    model: str | None,
    personality: str | None,
):
    """Generate code with optional B\u00fcrokratie Mode."""
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

    satire = SatireEngine(b\u00fcrokratie_mode=not no_b\u00fcrokratie)
    harness = CodingHarness(api, satire)

    response = asyncio.run(harness.generate_code(prompt, context))
    print(response)


@cli.command()
@click.option("--code", "-c", required=True, help="Code to explain")
@click.option("--provider", "-P", default=None, help="LLM provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
def explain(code: str, provider: str | None, model: str | None, personality: str | None):
    """Explain code with B\u00fcrokratie Mode."""
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
    """Refactor code with B\u00fcrokratie Mode."""
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
    import asyncio

    from mcp_server import mcp_server

    print("Starting Cloudkot MCP server...")
    asyncio.run(mcp_server.start())


@cli.command()
def permissions():
    """Show current permissions."""
    permissions = permission_manager.permissions
    click.echo("Current Permissions:")
    for perm, level in permissions.items():
        click.echo(f"  {perm}: {level.value}")


@cli.command()
def version():
    """Show version information."""
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        version = config.get("tool", {}).get("poetry", {}).get("version", "unknown")
        click.echo(f"Cloudkot version: {version}")
    except Exception:
        click.echo("Cloudkot version: unknown")


if __name__ == "__main__":
    cli()
