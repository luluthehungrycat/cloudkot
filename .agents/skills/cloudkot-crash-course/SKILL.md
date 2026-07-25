# Cloudkot Crash Course for Agents

## About

Cloudkot is a **satirical German coding assistant** with Bürokratie Mode. It wraps LLM responses in German bureaucracy humor (DIN-Normen, form references, MwSt.-Hinweise) while being a functional multi-provider LLM client with tool-calling, streaming, and multiple interfaces.

**Load this skill when** starting work on the Cloudkot project to avoid the 10 critical pitfalls that cost hours to discover.

## Architecture in 30 Seconds

```
main.py → CodingHarness.generate_code()
  → _run_agent_loop() [max 10 iterations]
    → APIClient.chat(messages, tools=tool_defs)
    → if tool_calls: execute_tool() → feed back → loop
    → if text: SatireEngine.wrap_response() → return
```

| File | Purpose |
|------|---------|
| `api_client.py` | HTTP client, streaming SSE, tool calling |
| `harness.py` | Agent loop — tool iteration |
| `tools/` | 5 filesystem tools (read, glob, grep, run_command, list) |
| `tui.py` | Terminal UI with streaming display |
| `config.toml` | User config (gitignored!) |
| `providers.toml` | Provider definitions |

## 10 Pitfalls (Must Read Before Editing)

### 1. `/v1` Duplication
Provider base_urls already include `/v1` (e.g. `https://api.mistral.ai/v1`). Code appends `/v1/chat/completions`. Result: `/v1/v1/chat/completions` → 404.
**Fix**: Strip trailing `/v1` before appending.

### 2. Chunk Processing Outside `data:` Handler
SSE responses have blank lines between messages. If the `choice/delta/text/tool_calls` processing is OUTSIDE the `if line.startswith("data: "):` block, each blank line re-processes the previous chunk → **doubled content and tool call arguments**.
**Fix**: ALL processing must be inside the `if data:` block.

### 3. Empty `choices` Lines
API sends `{"choices":[]}` lines (cost info). Crash on `choices[0]`.
**Fix**: `if not chunk.get("choices"): continue` before `choices[0]`.

### 4. `model_dump(exclude_none=True)`
Pydantic includes `None` fields by default. API rejects `"tool_calls": null`. **Always** use `exclude_none=True`.

### 5. Tool Call Argument Accumulation
Tool call arguments arrive as partial JSON across SSE chunks (character by character). Accumulate with `+=`. Never `=`.

### 6. Event Loop in TUI
`asyncio.run()` destroys the loop after each call, disrupting httpx connections. Use persistent loop with `get_event_loop()` / `run_until_complete()`.

### 7. TUI Session History
TUI maintains `self.history`. Use `continue_chat_stream(msgs, callbacks)` to preserve context (NOT `generate_code()` which starts fresh).

### 8. Stream Needs `"stream": True` in Body
httpx `.stream()` method alone doesn't work — must include `"stream": True` in the JSON request body.

### 9. MockAPIClient in Tests
The `test_integration.py` mock must match `chat(self, messages, use_context=True, tools=None)` signature and return `ChatResult`.

### 10. `_resolve_env_refs` for `$VAR`
Config values like `$OPENAI_API_KEY` are literal strings without `_resolve_env_refs()` in `create_api_client()`. The function in `main.py` expands `$VAR`/`${VAR}`.

## Quick Reference

### Add a Tool
1. Add handler to `tools/builtin.py`
2. Register in `TOOL_REGISTRY` dict
3. Add definition to `TOOL_DEFINITIONS`

### Run Tests
```bash
python -m pytest tests/ -v
```

### Lint
```bash
ruff check .
ruff check --fix .
```

### Known Codebase Issues

| Issue | Details |
|-------|---------|
| LSP Server | Uses `pygls.lsp.types` — incompatible with pygls ≥2.x. Semicolon check on Python files is satire but invasive. |
| MCP Server | WebSocket server exists but nothing connects to it. No client implementation. |
| Skills framework | `skills/` are dummy stubs — never called by the actual `CodingHarness`. |
| Token counting | `len(text.split())` — wildly inaccurate for context management. |
| Package structure | `pyproject.toml` references `cloudkot/` package but files are at repo root. Won't build. |
| tomli/tomllib | `try: import tomllib / except: import tomli as tomllib` duplicated in 6 files. |
| forms/ mismatch | Generates `.txt` files but footers link to `.pdf`. Links are dead. |
| requirements.txt drift | Lists `fastapi`, `uvicorn`, `jinja2`, `python-multipart` — none imported anywhere. |
| prompt-toolkit | Listed as dependency but never used. TUI uses plain `input()`. |
| No config.example.toml | `config.toml` is gitignored and required. New clones crash without it. |

### Make a PR
```bash
git checkout -b feat/description
# make changes
git commit -m "feat: description"
git push -u origin feat/description
gh pr create --base main --head feat/description
```
