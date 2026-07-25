"""
API Client for Cloudkot
OpenAI-compatible API client with provider support
"""

import os
from typing import Any

import httpx
from pydantic import BaseModel

from context_manager import context_manager
from personality_manager import personality_manager
from provider_manager import provider_manager


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float | None = 0.7
    max_tokens: int | None = 2048
    top_p: float | None = 0.9


class APIClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        personality: str | None = None,
    ):
        # Use provider manager if provider is specified
        if provider:
            provider_config = provider_manager.get_provider(provider)
            self.base_url = base_url or provider_config.base_url
            self.api_key = api_key or os.getenv(provider_config.api_key_env, "")
            self.model = model or provider_config.models[0] if provider_config.models else "gpt-3.5-turbo"
        else:
            self.base_url = base_url or "http://localhost:8080"
            self.api_key = api_key or ""
            self.model = model or "mistral-tiny"

        self.provider = provider
        self.personality = personality
        self.client = httpx.AsyncClient(timeout=30.0)

        # Load personality settings
        self._load_personality_settings()

    def _load_personality_settings(self):
        """Load personality-specific settings"""
        if self.personality:
            try:
                personality = personality_manager.get_personality(self.personality)
                self.temperature = personality.temperature
                self.top_p = personality.top_p
                self.system_prompt = personality.system_prompt
            except Exception:
                # Fallback to defaults
                self.temperature = 0.7
                self.top_p = 0.9
                self.system_prompt = "You are a helpful coding assistant."
        else:
            self.temperature = 0.7
            self.top_p = 0.9
            self.system_prompt = "You are a helpful coding assistant."

    async def chat(self, messages: list[Message], use_context: bool = True) -> str:
        """Send a chat request to the API"""
        # Add system prompt if not already present
        if not any(msg.role == "system" for msg in messages):
            system_message = Message(role="system", content=self.system_prompt)
            messages = [system_message] + messages

        # Add context from context manager if enabled
        if use_context:
            context_messages = context_manager.get_context()
            messages = context_messages + messages

        request = ChatRequest(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2048,
            top_p=self.top_p,
        )

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Some providers use different headers
        if self.provider == "anthropic":
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            # Anthropic uses a different endpoint
            response = await self.client.post(
                f"{self.base_url}/messages",
                json={
                    "model": self.model,
                    "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                    "max_tokens": 2048,
                    "temperature": self.temperature,
                },
                headers=headers,
            )
        else:
            # Standard OpenAI-compatible endpoint
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=request.model_dump(),
                headers=headers,
            )

        response.raise_for_status()

        # Handle different response formats
        if self.provider == "anthropic":
            return response.json()["content"][0]["text"]
        else:
            return response.json()["choices"][0]["message"]["content"]

    async def chat_with_context(self, message: str, role: str = "user") -> str:
        """Send a message with context management"""
        # Add to context
        context_manager.add_context(message, role)

        # Convert context to messages
        messages = context_manager.get_context()

        # Add the new message
        messages.append(Message(role=role, content=message))

        # Get response
        response = await self.chat(messages, use_context=False)

        # Add response to context
        context_manager.add_context(response, "assistant")

        return response

    async def close(self):
        """Close the API client"""
        await self.client.aclose()

    def get_context_stats(self) -> dict[str, Any]:
        """Get context statistics"""
        return {
            "current_tokens": context_manager.get_token_count(),
            "max_tokens": context_manager.max_tokens,
            "utilization": context_manager.get_utilization(),
        }

    def clear_context(self):
        """Clear the context window"""
        context_manager.clear_context()

    def set_personality(self, personality: str):
        """Set the personality for this client"""
        self.personality = personality
        self._load_personality_settings()

    def set_provider(self, provider: str):
        """Set the provider for this client"""
        self.provider = provider
        provider_config = provider_manager.get_provider(provider)
        self.base_url = provider_config.base_url
        self.api_key = os.getenv(provider_config.api_key_env, "")
        self.model = provider_config.models[0] if provider_config.models else "gpt-3.5-turbo"
