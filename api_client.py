"""
API Client for Cloudkot
OpenAI-compatible API client with provider support
"""

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import tenacity
from pydantic import BaseModel

from context_manager import context_manager
from exceptions import APIError, ConfigurationError, ProviderError, CloudkotValidationError
from personality_manager import personality_manager
from provider_manager import provider_manager


class Message(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str | None = None  # Allow None for assistant messages with tool_calls
    tool_call_id: str | None = None  # For tool result messages
    name: str | None = None  # Tool name for tool result messages
    tool_calls: list[dict] | None = None  # For assistant messages with tool calls


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float | None = 0.7
    max_tokens: int | None = 2048
    top_p: float | None = 0.9
    tools: list[dict] | None = None  # Tool definitions for tool calling


class ToolCallResult(BaseModel):
    """Result of a tool call from the API response"""
    id: str
    name: str
    arguments: dict[str, Any]


class ChatResult(BaseModel):
    """Structured result from a chat completion"""
    content: str | None = None
    tool_calls: list[ToolCallResult] | None = None


def _safe_parse_json(response):
    """Try to parse JSON response, with helpful error on failure."""
    try:
        return response.json()
    except Exception:
        body_preview = response.text[:500] if response.text else "(empty body)"
        raise ValueError(
            f"API returned non-JSON response (status {response.status_code}). "
            f"Body preview: {body_preview}"
        )


@dataclass
class StreamCallbacks:
    """Callbacks for real-time streaming of model responses."""
    on_text: Callable[[str], None] | None = None
    on_reasoning: Callable[[str], None] | None = None
    on_tool_call: Callable[[str, dict], None] | None = None
    on_tool_result: Callable[[str, str], None] | None = None


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
            try:
                provider_config = provider_manager.get_provider(provider)
                self.base_url = base_url or provider_config.base_url
                self.api_key = api_key or os.getenv(provider_config.api_key_env, "")
                self.model = model or (provider_config.models[0] if provider_config.models else "gpt-3.5-turbo")
            except Exception as e:
                raise ProviderError(f"Failed to load provider {provider}", provider=provider) from e
        else:
            self.base_url = base_url or "http://localhost:8080"
            self.api_key = api_key or ""
            self.model = model or "mistral-tiny"

        self.provider = provider
        self.personality = personality
        
        # Validate API key format if provided
        if self.api_key and not self._validate_api_key_format():
            raise CloudkotValidationError(f"Invalid API key format for provider {self.provider or 'local'}")
        
        self.client = httpx.AsyncClient(timeout=30.0)

        # Ensure api_key is always a string for header construction
        assert isinstance(self.api_key, str)

        # Load personality settings
        self._load_personality_settings()
        
        # Metrics tracking
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "tokens_used": 0,
            "latency": [],
        }

    def _validate_api_key_format(self) -> bool:
        """Basic validation of API key format based on provider"""
        if not self.api_key:
            return True  # Empty is allowed (might use env var later)
        
        if self.provider == "openai":
            return self.api_key.startswith("sk-") and len(self.api_key) > 40
        elif self.provider == "anthropic":
            return self.api_key.startswith("sk-ant-") and len(self.api_key) > 40
        elif self.provider == "mistral":
            return len(self.api_key) > 20
        elif self.provider in ("openrouter", "opencode_go", "opencode_zen"):
            return len(self.api_key) > 20
        return len(self.api_key) > 10

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

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def chat(
        self,
        messages: list[Message],
        use_context: bool = True,
        tools: list[dict] | None = None,
        stream: bool = False,
        callbacks: StreamCallbacks | None = None,
    ) -> ChatResult:
        """Send a chat request to the API"""
        import time
        start_time = time.time()
        self.metrics["requests"] += 1

        try:
            # Add system prompt if not already present
            if not any(msg.role == "system" for msg in messages):
                system_message = Message(role="system", content=self.system_prompt)
                messages = [system_message] + messages

            # Add context from context manager if enabled
            if use_context:
                context_messages = context_manager.get_context()
                # Convert context dicts to Message objects
                context_msg_objects = [Message(**m) for m in context_messages]
                messages = context_msg_objects + messages

            headers = {"Authorization": f"Bearer {self.api_key or ''}"}

            # Some providers use different headers
            if self.provider == "anthropic":
                headers = {
                    "x-api-key": self.api_key or "",
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
                response.raise_for_status()
                data = _safe_parse_json(response)
                self.metrics["latency"].append(time.time() - start_time)
                return ChatResult(content=str(data["content"][0]["text"]))
            else:
                # Standard OpenAI-compatible endpoint
                request_dict = {
                    "model": self.model,
                    "messages": [msg.model_dump(exclude_none=True) for msg in messages],
                    "temperature": self.temperature,
                    "max_tokens": 2048,
                    "top_p": self.top_p,
                }
                if tools:
                    request_dict["tools"] = tools
                # Normalize base_url: strip trailing /v1 if present to avoid duplication
                base = self.base_url.rstrip('/')
                if base.endswith('/v1'):
                    base = base[:-3]

                if stream:
                    request_dict["stream"] = True
                    # Streaming mode
                    async with self.client.stream(
                        "POST", f"{base}/v1/chat/completions",
                        json=request_dict, headers=headers
                    ) as response:
                        response.raise_for_status()
                        content_chunks = []
                        tool_calls_acc: dict[int, dict] = {}
                        finish_reason = None

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:].strip()
                                if data == "[DONE]":
                                    break
                                chunk = json.loads(data)
                                # Skip lines with empty choices (e.g. cost info)
                                if not chunk.get("choices"):
                                    continue
                                choice = chunk["choices"][0]
                                delta = choice.get("delta", {})
                                finish_reason = choice.get("finish_reason")

                                # Text content
                                text = delta.get("content")
                                if text and callbacks and callbacks.on_text:
                                    callbacks.on_text(text)
                                    content_chunks.append(text)

                                # Reasoning content
                                reasoning = delta.get("reasoning_content")
                                if reasoning and callbacks and callbacks.on_reasoning:
                                    callbacks.on_reasoning(reasoning)

                                # Tool calls
                                tool_calls_delta = delta.get("tool_calls")
                                if tool_calls_delta:
                                    for tc in tool_calls_delta:
                                        idx = tc["index"]
                                        if idx not in tool_calls_acc:
                                            tool_calls_acc[idx] = {
                                                "id": tc.get("id", ""),
                                                "type": tc.get("type", "function"),
                                                "function": {
                                                    "name": tc.get("function", {}).get("name", ""),
                                                    "arguments": tc.get("function", {}).get("arguments", ""),
                                                }
                                            }
                                        else:
                                            # Accumulate function arguments across chunks
                                            if "function" in tc:
                                                if tc["function"].get("name"):
                                                    tool_calls_acc[idx]["function"]["name"] = tc["function"]["name"]
                                                if tc["function"].get("arguments"):
                                                    tool_calls_acc[idx]["function"]["arguments"] += tc["function"]["arguments"]
                                                if tc.get("id"):
                                                    tool_calls_acc[idx]["id"] = tc["id"]

                        # Build ChatResult from accumulated data
                        full_content = "".join(content_chunks)

                        if finish_reason == "tool_calls" and tool_calls_acc:
                            tool_calls_result = []
                            for idx in sorted(tool_calls_acc.keys()):
                                tc = tool_calls_acc[idx]
                                tool_calls_result.append(ToolCallResult(
                                    id=tc["id"],
                                    name=tc["function"]["name"],
                                    arguments=json.loads(tc["function"]["arguments"]),
                                ))
                            self.metrics["latency"].append(time.time() - start_time)
                            return ChatResult(content=full_content or None, tool_calls=tool_calls_result)

                        self.metrics["latency"].append(time.time() - start_time)
                        return ChatResult(content=full_content or None)
                else:
                    # Non-streaming mode (existing logic)
                    response = await self.client.post(
                        f"{base}/v1/chat/completions",
                        json=request_dict,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = _safe_parse_json(response)
                    self.metrics["latency"].append(time.time() - start_time)
                    message = data["choices"][0]["message"]
                    content = message.get("content")
                    tool_calls_raw = message.get("tool_calls")
                    tool_calls = None
                    if tool_calls_raw:
                        tool_calls = []
                        for tc in tool_calls_raw:
                            tool_calls.append(ToolCallResult(
                                id=tc["id"],
                                name=tc["function"]["name"],
                                arguments=json.loads(tc["function"]["arguments"]),
                            ))
                    return ChatResult(content=content, tool_calls=tool_calls)
        except httpx.HTTPStatusError as e:
            self.metrics["errors"] += 1
            raise APIError(
                f"API request failed: {e.response.status_code} - {e.response.text[:200]}",
                status_code=e.response.status_code,
                provider=self.provider
            ) from e
        except httpx.TimeoutException as e:
            self.metrics["errors"] += 1
            raise APIError(
                f"API request timed out",
                status_code=408,
                provider=self.provider
            ) from e
        except Exception as e:
            self.metrics["errors"] += 1
            raise APIError(
                f"API request failed: {str(e)}",
                provider=self.provider
            ) from e

    async def chat_with_context(self, message: str, role: str = "user") -> str:
        """Send a message with context management"""
        # Add the new message to context first
        context_manager.add_context(message, role)

        # Convert context to Message objects (already includes the new message)
        messages = [Message(**m) for m in context_manager.get_context()]

        # Get response
        response = await self.chat(messages, use_context=False)
        response_text = response.content if response.content else ""

        # Add response to context
        context_manager.add_context(response_text, "assistant")

        return response_text

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
        try:
            provider_config = provider_manager.get_provider(provider)
            self.base_url = provider_config.base_url
            self.api_key = os.getenv(provider_config.api_key_env, "")
            self.model = provider_config.models[0] if provider_config.models else "gpt-3.5-turbo"
        except Exception as e:
            raise ProviderError(f"Failed to set provider {provider}", provider=provider) from e

    def get_metrics(self) -> dict[str, Any]:
        """Get API client metrics"""
        return {
            **self.metrics,
            "avg_latency": sum(self.metrics["latency"]) / len(self.metrics["latency"]) if self.metrics["latency"] else 0,
            "provider": self.provider,
            "model": self.model,
        }


# Import ValidationError for backward compatibility
from pydantic import BaseModel
