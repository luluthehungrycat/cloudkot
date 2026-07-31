# Cloudkot — Agent Guide

## Project Overview

Cloudkot is a **satirical German coding assistant** with Bürokratie Mode. It wraps LLM responses in humorous bureaucracy-themed content (DIN-Normen, form references, MwSt.-Hinweise, "Herr Schmidt aus Raum 304"). Underneath the joke is a real multi-provider LLM client with tool-calling, streaming, context management, and multiple interfaces (CLI, TUI, LSP, MCP).

## Architecture

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | CLI entrypoint (Click groups: generate, explain, refactor, tui, mcp, provider, personality, skill, context) |
| `api_client.py` | Async HTTP client for OpenAI-compatible APIs; streaming SSE, tool calling, personality injection |
| `harness.py` | Agent loop: sends messages + tool defs, executes tool calls, feeds results back, iterates (max 10) |
| `tools/__init__.py` | Tool registry + executor |
| `tools/builtin.py` | 5 filesystem tools: `read_file`, `glob_files`, `grep_files`, `run_command`, `list_files` |
| `tui.py` | Terminal UI with chat history, settings, command mode |
| `context_manager.py` | Token-budgeted context window with importance-based compression |
| `satire/engine.py` | Wraps LLM responses in German bureaucracy headers/footers |
| `provider_manager.py` | Reads `providers.toml`; maps provider names → configs |
| `personality_manager.py` | Reads `personalities.toml`; manages system prompt profiles |
| `permissions.py` | Simple allow/deny/ask permission system for tool calls |
| `config.toml` | User config (base_url, api_key, model) — gitignored |
| `providers.toml` | Provider definitions (base_url, api_key_env, models) |
| `personalities.toml` | Personality definitions (system_prompt, temperature) |

### Data Flow

```
User Input → CLI/TUI → CodingHarness.generate_code()
  → _run_agent_loop():
    → system prompt + chat history + tool_defs
    → APIClient.chat()  [POST to LLM API]
    → if tool_calls: execute_tool() → feed result back → loop
    → if text: SatireEngine.wrap_response() → return
```

### Interfaces

- **CLI**: `python main.py generate -p "prompt"` — single-shot generate/explain/refactor
- **TUI**: `python main.py tui` — interactive chat with history, streaming, tool display
- **LSP**: `python main.py lsp` — Language Server Protocol (broken — needs pygls version pin)
- **MCP**: `python main.py mcp` — Model Context Protocol server via websockets

## Critical Pitfalls (Memorize These)

### 1. `api_client.py` base_url `/v1` Duplication

**Problem**: `providers.toml` and `config.toml` often include `/v1` in `base_url` (e.g. `https://api.mistral.ai/v1`). The code appends `/v1/chat/completions` to construct the endpoint URL, producing `https://api.mistral.ai/v1/v1/chat/completions` → 404.

**Fix**: `api_client.py` lines 158-160 strip trailing `/v1` before appending:
```python
base = self.base_url.rstrip('/')
if base.endswith('/v1'):
    base = base[:-3]
```

### 2. SSE Streaming: Blank Lines Reprocess Previous Chunks

**Problem**: SSE responses have blank lines between data messages. If chunk processing code is OUTSIDE the `if line.startswith("data: "):` block, every subsequent blank line re-processes the previous chunk, **doubling all content and tool call arguments**.

**Fix**: ALL `choice`/`delta`/`text`/`reasoning`/`tool_calls` processing must be INSIDE the `if line.startswith("data: "):` block:
```python
if line.startswith("data: "):
    data = line[6:].strip()
    if data == "[DONE]":
        break
    chunk = json.loads(data)
    # PROCESS INSIDE HERE — NOT outside!
    if not chunk.get("choices"):
        continue
    choice = chunk["choices"][0]
    ...
```

### 3. SSE: Empty `choices` Lines

The API sends lines with `"choices":[]` after tool call data (cost info). These cause `IndexError` on `choices[0]`. The guard:
```python
if not chunk.get("choices"):
    continue
```
Must come BEFORE `choices[0]` access.

### 4. `model_dump()` Includes Null Fields

Pydantic's `model_dump()` includes `None` fields by default. The Mistral/OpenAI API rejects messages with `"tool_calls": null` or `"tool_call_id": null` for user messages. **Always use** `model_dump(exclude_none=True)`:
```python
"messages": [msg.model_dump(exclude_none=True) for msg in messages],
```

### 5. Tool Call Argument Accumulation in Streaming

Tool call arguments arrive as partial JSON across multiple SSE chunks. Each chunk contains single-character fragments (e.g., `{`, `"`, `p`, `a`, `t`, `h`, ...). Accumulate by appending:
```python
if tc["function"].get("arguments"):
    tool_calls_acc[idx]["function"]["arguments"] += tc["function"]["arguments"]
```

### 6. Event Loop Management (`asyncio.run` vs persistent loop)

**Problem**: Calling `asyncio.run()` on each TUI message creates and destroys an event loop. The `httpx.AsyncClient` connection gets disrupted, causing `"Event loop is closed"`.

**Fix** (in `tui.py`): Use a persistent loop:
```python
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
if loop.is_closed():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
result = loop.run_until_complete(harness.continue_chat_stream(msgs, callbacks=callbacks))
```

### 7. TUI Session History

The TUI maintains `self.history` (list of `{"role", "content"}` dicts). To preserve conversation context across turns, convert history to `Message` objects and use `harness.continue_chat()` / `continue_chat_stream()` rather than `generate_code()` (which starts fresh each time):
```python
msgs = [Message(role=entry["role"], content=entry["content"])
        for entry in self.history]
msgs.append(Message(role="user", content=message))
result = await self._harness.continue_chat_stream(msgs, callbacks=callbacks)
```

### 8. Stream Request Must Include `"stream": true` in JSON Body

Without `"stream": true` in the request body, the API returns a normal non-streaming JSON response even if using httpx's `.stream()` method. The SSE parser will find no data lines and return an empty result.

### 9. MockAPIClient in Tests

The `test_integration.py` mock must match the updated `chat()` signature:
```python
class MockAPIClient:
    async def chat(self, messages, use_context=True, tools=None):
        from api_client import ChatResult
        return ChatResult(content="Mock response")
    async def close(self):
        pass
```

### 10. `_resolve_env_refs` for Config

`config.toml` values can reference environment variables as `$VAR` or `${VAR}`. The `_resolve_env_refs()` function in `main.py` expands these. Without it, a config like `api_key = "$OPENAI_API_KEY"` sends the literal string `"$OPENAI_API_KEY"` as the API key.

## Streaming Architecture

### SSE Event Types

| Field | When Present | Meaning |
|-------|--------------|---------|
| `delta.content` | Non-null | Text response content (streamed character by character) |
| `delta.reasoning_content` | Non-null | Model's internal reasoning (DeepSeek-specific) |
| `delta.tool_calls[].function.arguments` | Non-null | Partial tool call arguments (accumulate across chunks) |
| `delta.tool_calls[].id` | First chunk only | Tool call ID |
| `delta.tool_calls[].function.name` | First chunk only | Tool function name |
| `finish_reason` | Last chunk | `"stop"` (text complete) or `"tool_calls"` (tool call complete) |
| `choices` | Sometimes empty | Cost/info lines with empty choices array — must be skipped |

### StreamCallbacks

Defined in `api_client.py`:
```python
@dataclass
class StreamCallbacks:
    on_text: Callable[[str], None] | None = None
    on_reasoning: Callable[[str], None] | None = None
    on_tool_call: Callable[[str, dict], None] | None = None
    on_tool_result: Callable[[str, str], None] | None = None
```

## Common Workflows

### Add a new tool
1. Add handler function to `tools/builtin.py`
2. Register in `TOOL_REGISTRY` dict
3. Add definition to `TOOL_DEFINITIONS` list (OpenAI-compatible schema)

### Add a new provider
1. Add entry to `providers.toml` (base_url, api_key_env, models)
2. Provider is auto-discovered via `provider_manager`

### Run tests
```bash
python -m pytest tests/ -v
```

### Lint
```bash
ruff check .
ruff check --fix .
```

## Known Issues

- **LSP Server**: Uses `pygls.lsp.types` which doesn't match pygls ≥2.x API. Needs version pin or API migration. Also hardcoded to check for missing semicolons (Python doesn't use them) — part of the satire but confusing in practice.
- **MCP Server**: Has no client to connect to it. WebSocket server exists but nothing talks to it.
- **Skills framework**: Skills (`skills/`) are dummy implementations — never called by the actual harness.
- **Token counting**: `context_manager._count_tokens` uses `len(text.split())` — very inaccurate.
- **Package structure**: `pyproject.toml` references `cloudkot/` package but files are at repo root.
- **prompt-toolkit**: Listed as dependency but never imported.
- **tomli/tomllib import duplicated**: The `try: import tomllib / except: import tomli as tomllib` pattern appears in 6 files. Should be centralized in a compat module.
- **forms/ format mismatch**: `satire/forms.py` generates `.txt` files, but satire footers link to `.pdf` files (e.g., `forms/formular_f_42_funktionsgenehmigung.pdf`). Links are dead.
- **requirements.txt vs pyproject.toml drift**: `requirements.txt` lists `fastapi`, `uvicorn`, `jinja2`, `python-multipart` — none of these are used anywhere in the codebase.
- **No config.example.toml**: `config.toml` is gitignored and required at runtime. New clones crash immediately. Should ship a `config.example.toml` with safe defaults.

## Git & PR Workflow

- Branch naming: `feat/description`, `fix/description`
- PRs via `gh pr create`
- CI runs on main + PRs (test, lint, type-check)
- The codebase is on GitHub at `luluthehungrycat/cloudkot`

Refer to project-level skills in .agents/skills/ for access to reusable workflows specific to this project.
