"""
Text User Interface for Cloudkot
Provides a rich terminal interface for the coding assistant
"""

import asyncio
from enum import Enum
from typing import Any


class TUIMode(Enum):
    CHAT = "chat"
    COMMAND = "command"
    SETTINGS = "settings"


class TUI:
    def __init__(self, api_client: Any = None, config: dict[str, Any] | None = None):
        self.api_client = api_client
        self.config = config or {}
        self.mode = TUIMode.CHAT
        self.history: list[dict[str, str]] = []
        self.current_input = ""
        self.running = False

        # Setup readline for history
        self._setup_readline()

    def _setup_readline(self):
        """Setup readline for command history"""
        try:
            import readline as rl

            rl.parse_and_bind("tab: complete")
            rl.set_history_length(100)
        except ImportError:
            pass

    def start(self):
        """Start the TUI"""
        self.running = True
        print("Cloudkot TUI - Der deutsche KI-Code-Assistent")
        print("Tip: Type '/help' for commands, '/exit' to quit")
        print()

        while self.running:
            try:
                self._run_loop()
            except KeyboardInterrupt:
                print("\nUse '/exit' to quit")
            except EOFError:
                print("\nGoodbye!")
                self.running = False

    def _run_loop(self):
        """Main TUI loop"""
        if self.mode == TUIMode.CHAT:
            self._chat_mode()
        elif self.mode == TUIMode.COMMAND:
            self._command_mode()
        elif self.mode == TUIMode.SETTINGS:
            self._settings_mode()

    def _chat_mode(self):
        """Handle chat mode"""
        try:
            user_input = input("💬 > ").strip()

            if not user_input:
                return

            if user_input.startswith("/"):
                self._handle_command(user_input[1:])
                return

            # Process as chat message
            self._process_chat_message(user_input)

        except EOFError:
            raise

    def _command_mode(self):
        """Handle command mode"""
        print("Command mode - Type commands or '/chat' to return to chat")
        while self.mode == TUIMode.COMMAND:
            try:
                cmd = input("📝 > ").strip()
                if cmd == "chat":
                    self.mode = TUIMode.CHAT
                    break
                self._handle_command(cmd)
            except EOFError:
                raise

    def _settings_mode(self):
        """Handle settings mode"""
        print("Settings mode - Configure Cloudkot")
        print("Available settings: provider, model, personality, bürokratie")
        print("Type '/back' to return")

        while self.mode == TUIMode.SETTINGS:
            try:
                cmd = input("⚙️ > ").strip()
                if cmd == "back":
                    self.mode = TUIMode.CHAT
                    break
                self._handle_setting(cmd)
            except EOFError:
                raise

    def _handle_command(self, command: str):
        """Handle a command"""
        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        commands = {
            "help": self._cmd_help,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
            "clear": self._cmd_clear,
            "history": self._cmd_history,
            "settings": self._cmd_settings,
            "command": self._cmd_command,
            "chat": self._cmd_chat,
            "providers": self._cmd_providers,
            "personalities": self._cmd_personalities,
        }

        if cmd in commands:
            commands[cmd](*args)
        else:
            print(f"Unknown command: {cmd}. Type '/help' for available commands.")

    def _handle_setting(self, setting: str):
        """Handle a setting change"""
        parts = setting.split("=", 1)
        if len(parts) != 2:
            print("Usage: setting=value")
            return

        key, value = parts[0].strip(), parts[1].strip()

        settings = {
            "provider": self._set_provider,
            "model": self._set_model,
            "personality": self._set_personality,
            "bürokratie": self._set_bürokratie,
        }

        if key in settings:
            settings[key](value)
        else:
            print(f"Unknown setting: {key}")

    def _process_chat_message(self, message: str):
        """Process a chat message using the actual LLM"""
        # Add to history
        self.history.append({"role": "user", "content": message})

        # Display user message
        print(f"👤 User: {message}")

        # Get response from the actual LLM via harness
        response = self._get_llm_response(message)

        self.history.append({"role": "assistant", "content": response})
        print(f"🤖 Assistant: {response}")
        print()

    def _get_llm_response(self, message: str) -> str:
        """Get a response from the LLM via the harness, preserving conversation history."""
        if not self.api_client:
            return "No API client configured. Use /settings to configure."

        from api_client import Message
        from harness import CodingHarness
        from satire.engine import SatireEngine

        # Lazily create harness once and reuse it
        if not hasattr(self, '_harness'):
            satire = SatireEngine(
                bürokratie_mode=self.config.get("bürokratie", True)
            )
            self._harness = CodingHarness(self.api_client, satire)

        # Build messages from accumulated history + the new prompt
        msgs = [Message(role=entry["role"], content=entry["content"])
                for entry in self.history]
        msgs.append(Message(role="user", content=message))

        # Use a persistent event loop instead of asyncio.run()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(self._harness.continue_chat(msgs))
        except Exception as e:
            return f"Error generating response: {e}"

    def _cmd_help(self, *args):
        """Show help"""
        print("Available commands:")
        print("  /help          - Show this help")
        print("  /exit, /quit   - Exit the TUI")
        print("  /clear         - Clear chat history")
        print("  /history       - Show chat history")
        print("  /settings      - Enter settings mode")
        print("  /command       - Enter command mode")
        print("  /chat          - Return to chat mode")
        print("  /providers     - List available providers")
        print("  /personalities - List available personalities")

    def _cmd_exit(self, *args):
        """Exit the TUI"""
        print("Goodbye!")
        self.running = False

    def _cmd_clear(self, *args):
        """Clear chat history"""
        self.history.clear()
        print("Chat history cleared.")

    def _cmd_history(self, *args):
        """Show chat history"""
        if not self.history:
            print("No history yet.")
            return

        print("Chat History:")
        for i, msg in enumerate(self.history[-10:], 1):  # Show last 10 messages
            role = msg["role"]
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"  {i}. [{role}] {content}")

    def _cmd_settings(self, *args):
        """Enter settings mode"""
        self.mode = TUIMode.SETTINGS

    def _cmd_command(self, *args):
        """Enter command mode"""
        self.mode = TUIMode.COMMAND

    def _cmd_chat(self, *args):
        """Return to chat mode"""
        self.mode = TUIMode.CHAT

    def _cmd_providers(self, *args):
        """List available providers"""
        try:
            from provider_manager import provider_manager

            providers = provider_manager.list_providers()
            print("Available providers:")
            for provider in providers:
                print(f"  - {provider}")
        except Exception as e:
            print(f"Error listing providers: {e}")

    def _cmd_personalities(self, *args):
        """List available personalities"""
        try:
            from personality_manager import personality_manager

            personalities = personality_manager.list_personalities()
            print("Available personalities:")
            for personality in personalities:
                print(f"  - {personality}")
        except Exception as e:
            print(f"Error listing personalities: {e}")

    def _set_provider(self, value: str):
        """Set the provider"""
        self.config["provider"] = value
        print(f"Provider set to: {value}")

    def _set_model(self, value: str):
        """Set the model"""
        self.config["model"] = value
        print(f"Model set to: {value}")

    def _set_personality(self, value: str):
        """Set the personality"""
        self.config["personality"] = value
        print(f"Personality set to: {value}")

    def _set_bürokratie(self, value: str):
        """Set Bürokratie mode"""
        self.config["bürokratie"] = value.lower() in ["true", "1", "yes", "on"]
        print(f"Bürokratie mode set to: {self.config['bürokratie']}")


# Singleton instance

def create_tui(api_client: Any = None, config: dict[str, Any] | None = None) -> TUI:
    """Create and return a TUI instance"""
    return TUI(api_client, config)
