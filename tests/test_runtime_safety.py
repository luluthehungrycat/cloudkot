import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from context_manager import ContextManager
from mcp_server import MCPServer
from tools.builtin import run_command_handler


class TestMCPServerSafety:
    def test_authentication_requires_matching_bearer_token(self):
        server = MCPServer(auth_required=True, auth_key="secret")

        assert server._check_auth({"Authorization": "Bearer secret"}) is True
        assert server._check_auth({"authorization": "Bearer secret"}) is True
        assert server._check_auth({"Authorization": "Bearer wrong"}) is False
        assert server._check_auth({}) is False

    def test_configured_mcp_key_enables_authentication(self, tmp_path):
        config_path = tmp_path / "mcp.toml"
        config_path.write_text("[default]\napi_key = \"secret\"\n", encoding="utf-8")

        server = MCPServer.from_config(config_path)

        assert server.auth_required is True
        assert server._check_auth({"Authorization": "Bearer secret"}) is True
        assert server._check_auth({}) is False

    def test_cli_mcp_key_enables_authentication(self, monkeypatch):
        import main

        captured = {}

        async def fake_start(server, config_path=None):
            captured["server"] = server

        monkeypatch.setattr(MCPServer, "start", fake_start)
        result = CliRunner().invoke(main.cli, ["mcp", "--auth-key", "secret"])

        assert result.exit_code == 0, result.output
        assert captured["server"].auth_key == "secret"
        assert captured["server"].auth_required is True

    def test_requirements_pin_legacy_websockets_api(self):
        requirements = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(
            encoding="utf-8"
        )

        assert "websockets>=12.0,<13.0" in requirements

    @pytest.mark.asyncio
    async def test_malformed_message_returns_json_rpc_error(self):
        response = json.loads(await MCPServer().handle_message("{"))

        assert response["jsonrpc"] == "2.0"
        assert response["id"] is None
        assert response["error"]["code"] == -32603


class TestContextBudget:
    def test_oversized_item_is_bounded(self):
        manager = ContextManager()
        manager.max_tokens = 10
        manager.clear_context()

        manager.add_context("A very long message that cannot fit in the budget", "user")

        assert manager.get_token_count() <= manager.max_tokens

    def test_new_item_evicts_old_items_until_it_fits(self):
        manager = ContextManager()
        manager.max_tokens = 10
        manager.clear_context()
        manager.add_context("old context", "assistant")

        manager.add_context("new context that requires the old item to be removed", "user")

        assert manager.get_token_count() <= manager.max_tokens
        assert manager.context_window[-1].role == "user"

    def test_disabled_compression_preserves_items(self):
        manager = ContextManager()
        manager.max_tokens = 2
        manager.compression_enabled = False
        manager.clear_context()

        manager.add_context("first item", "user")
        manager.add_context("second item", "assistant")

        assert len(manager.context_window) == 2
        assert manager.context_window[0].content == "first item"



class TestCommandSafety:
    @pytest.mark.asyncio
    async def test_approved_command_runs_without_shell(self):
        result = await run_command_handler("echo hello")

        assert result.strip() == "hello"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("command", [
        "echo safe; echo injected",
        "echo safe | sh",
        "rm -rf /",
        "sudo ls",
        "/bin/ls",
    ])
    async def test_shell_or_destructive_commands_are_rejected(self, command):
        result = await run_command_handler(command)

        assert result.startswith("Error: Command rejected for safety reasons.")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", [0, -1, 121, True, "30"])
    async def test_invalid_timeout_is_rejected(self, timeout):
        result = await run_command_handler("echo hello", timeout=timeout)

        assert "timeout must be an integer" in result
