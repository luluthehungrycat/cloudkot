# Design: Code Quality Improvements

## Overview
This design document outlines the technical approach to improving Cloudkot's code quality through refactoring and consistency improvements.

## Components

### 1. Centralized TOML Import (compat.py)

#### Current State
The following pattern appears in 6 files:
```python
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
```

Files affected:
- `main.py:10-13`
- `api_client.py` (doesn't have it, but imports from files that do)
- `context_manager.py:9-12`
- `provider_manager.py:8-11`
- `personality_manager.py:6-9`
- `permissions.py:8-11`

#### Problems
- Violation of DRY principle
- Maintenance burden (changing the pattern requires changes in 6 files)
- Slight performance overhead (each file does the try/except)

#### Solution: Create compat.py Module

**Approach**:
1. Create a new `compat.py` module
2. Centralize the tomllib/tomli import there
3. Export `tomllib` from the module
4. Update all files to import from `compat` instead

**Implementation**:

New file: `compat.py`
```python
"""
Compatibility module for Cloudkot.
Centralizes version-specific imports and workarounds.
"""

# TOML support for Python < 3.11
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

# Re-export for convenience
__all__ = ["tomllib"]
```

**Updates to existing files**:
Replace:
```python
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
```

With:
```python
from compat import tomllib
```

**Files to modify**:
- `context_manager.py`
- `provider_manager.py`
- `personality_manager.py`
- `permissions.py`
- `lsp_server.py` (also has this pattern)

**Note**: `main.py` already imports `tomllib` differently (for config loading), but it should also use the compat module.

**Trade-offs**:
- Pro: DRY compliance
- Pro: Single point of maintenance
- Pro: Cleaner imports
- Con: One more file to maintain
- Con: Slight import overhead (negligible)

---

### 2. CLI Code Deduplication

#### Current State
The `generate`, `explain`, and `refactor` commands in `main.py` all follow the same pattern:
1. Load config
2. Override with CLI options
3. Create API client
4. Set personality if specified
5. Create satire engine
6. Create harness
7. Call harness method
8. Print result

Each command duplicates ~20 lines of nearly identical code.

#### Problems
- Violation of DRY principle
- Maintenance burden (changing the pattern requires changes in 3 places)
- Inconsistency risk (bugs fixed in one may be missed in others)

#### Solution: Extract Helper Function

**Approach**:
1. Create a helper function `_create_harness()` that handles common setup
2. Create a helper function `_run_with_harness()` that runs the harness method
3. Refactor the three commands to use these helpers

**Implementation**:
```python
def _create_api_client_from_config(config: dict[str, Any]) -> APIClient:
    """Create API client from configuration with overrides."""
    return create_api_client(config)


def _create_harness(
    config: dict[str, Any],
    personality: str | None = None,
    no_bürokratie: bool = False,
) -> CodingHarness:
    """Create and configure a CodingHarness instance."""
    api = create_api_client(config)
    
    if personality:
        api.set_personality(personality)
    
    satire = SatireEngine(bürokratie_mode=not no_bürokratie)
    return CodingHarness(api, satire)


async def _run_generation(
    harness: CodingHarness,
    method_name: str,
    prompt_or_code: str,
) -> str:
    """Run a generation method on the harness."""
    method = getattr(harness, method_name)
    return await method(prompt_or_code)
```

**Updated commands**:
```python
@cli.command()
@click.option("--prompt", "-p", required=True, help="Your coding prompt")
@click.option("--context", "-c", default=None, help="Context for satire")
@click.option("--no-bürokratie", is_flag=True, help="Disable Bürokratie Mode")
@click.option("--provider", "-P", default=None, help="LLM provider")
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
    
    if provider:
        config["api"]["provider"] = provider
    if model:
        config["api"]["model"] = model
    if personality:
        config["personality"]["active"] = personality
    
    harness = _create_harness(config, personality, no_bürokratie)
    
    response = asyncio.run(harness.generate_code(prompt, context))
    print(response)


@cli.command()
@click.option("--code", "-c", required=True, help="Code to explain")
@click.option("--provider", "-P", default=None, help="LLM provider")
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
    
    harness = _create_harness(config, personality)
    
    response = asyncio.run(harness.explain_code(code))
    print(response)


@cli.command()
@click.option("--code", "-c", required=True, help="Code to refactor")
@click.option("--provider", "-P", default=None, help="LLM provider")
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
    
    harness = _create_harness(config, personality)
    
    response = asyncio.run(harness.refactor_code(code))
    print(response)
```

**Further improvement**: The config override pattern could also be extracted:
```python
def _apply_cli_overrides(config: dict[str, Any], provider: str | None, model: str | None, personality: str | None) -> dict[str, Any]:
    """Apply CLI overrides to configuration."""
    if provider:
        config["api"]["provider"] = provider
    if model:
        config["api"]["model"] = model
    if personality:
        config["personality"]["active"] = personality
    return config
```

**Trade-offs**:
- Pro: DRY compliance
- Pro: Easier to maintain
- Pro: More consistent behavior
- Con: Slightly less explicit code flow

---

### 3. TUI Event Loop Cleanup

#### Current State
```python
# In tui.py _get_llm_response():
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

if loop.is_closed():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

try:
    return loop.run_until_complete(
        self._harness.continue_chat_stream(msgs, callbacks=callbacks)
    )
except Exception as e:
    return f"Error generating response: {e}"
```

#### Problems
- Loop may be left in bad state if exception occurs
- No cleanup of loop resources
- Subsequent calls may fail

#### Solution: Proper Loop Management

**Approach**:
1. Store loop as instance variable
2. Reuse the same loop across calls
3. Proper cleanup on failure
4. Ensure loop is always set back

**Implementation**:
```python
# In TUI.__init__:
def __init__(self, api_client: Any = None, config: dict[str, Any] | None = None):
    self.api_client = api_client
    self.config = config or {}
    self.mode = TUIMode.CHAT
    self.history: list[dict[str, str]] = []
    self.current_input = ""
    self.running = False
    self._loop = None  # NEW: Store the event loop
    self._setup_readline()

# In _get_llm_response:
def _get_llm_response(self, message: str) -> str:
    """Get a response from the LLM with real-time streaming display."""
    if not self.api_client:
        return "No API client configured. Use /settings to configure."

    from api_client import Message, StreamCallbacks
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

    # Create streaming callbacks for real-time display
    callbacks = StreamCallbacks(
        on_text=lambda text: print(text, end="", flush=True),
        on_reasoning=lambda text: print(f"\033[90m{text}\033[0m", end="", flush=True),
        on_tool_call=lambda name, args: print(f"\n  \033[36m🔧 {name}({args})\033[0m", flush=True),
        on_tool_result=lambda name, result: print(
            f"  \033[32m✅ {name} → {result[:200]}{'...' if len(result) > 200 else ''}\033[0m",
            flush=True
        ),
    )

    # Get or create the persistent event loop
    loop = self._get_or_create_loop()

    try:
        return loop.run_until_complete(
            self._harness.continue_chat_stream(msgs, callbacks=callbacks)
        )
    except Exception as e:
        # Ensure loop is still valid for next call
        if loop.is_closed():
            self._loop = None
        return f"Error generating response: {e}"

# NEW METHOD
def _get_or_create_loop(self):
    """Get or create a persistent event loop."""
    if self._loop is None or self._loop.is_closed():
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
    return self._loop
```

**Trade-offs**:
- Pro: Proper resource management
- Pro: Better error recovery
- Con: Slightly more complex code

---

### 4. Tool Execution Timeout

#### Current State
```python
# In harness.py _run_agent_loop:
tool_output = await execute_tool(tc.name, tc.arguments)
```

#### Problems
- No timeout on tool execution
- A hanging tool blocks the entire agent loop
- No way to recover from stuck tools

#### Solution: Add Timeout to Tool Execution

**Approach**:
1. Wrap `execute_tool()` with `asyncio.wait_for()`
2. Use a reasonable default timeout (e.g., 30 seconds)
3. Handle timeout gracefully

**Implementation**:
```python
# In harness.py, around line 78:
try:
    tool_output = await asyncio.wait_for(
        execute_tool(tc.name, tc.arguments),
        timeout=30.0
    )
except asyncio.TimeoutError:
    tool_output = f"Error: Tool '{tc.name}' timed out after 30 seconds"
except Exception as e:
    tool_output = f"Error executing tool '{tc.name}': {e}"
```

**Note**: The builtin tools already have their own timeouts (e.g., `run_command_handler` has a 30s timeout). This adds an additional layer of protection.

**Trade-offs**:
- Pro: Prevents indefinite hangs
- Pro: Better user experience
- Con: May cut off long-running but legitimate operations
- Mitigation: 30 second timeout is reasonable for most operations

---

### 5. Form Links Extension Mismatch

#### Current State
- `satire/forms.py` generates forms as `.txt` files (line 21: `filename = f"{form_type...}.txt"`)
- `satire/engine.py` references forms as `.pdf` files (line 80-81: `f"(forms/{fname}.pdf)"`)

#### Problems
- Links in satire output point to non-existent files
- Dead links in the UI

#### Solution: Fix Extension Consistency

**Option A**: Generate PDFs (complex, requires dependencies)
**Option B**: Update references to use .txt (simple, already works)

**Decision**: Option B - Update references to use .txt

**Implementation**:
```python
# In satire/engine.py, line 80:
form_hint = (
    "\n\n📄 *Bitte reichen Sie [" + form + "](forms/"
    + fname + ".txt) in dreifacher Ausfertigung ein.*"  # Changed .pdf to .txt
)
```

**Trade-offs**:
- Pro: Simple fix
- Pro: Links actually work
- Con: Less "official" looking than PDF
- Mitigation: The satire is intentional, .txt is fine

---

### 6. Remove Unused Dependencies

#### Current State
`requirements.txt` and `pyproject.toml` include:
- `fastapi` - Not imported anywhere
- `uvicorn` - Not imported anywhere
- `jinja2` - Not imported anywhere
- `python-multipart` - Not imported anywhere

#### Verification
```bash
cd /home/moritz/agent/repos/cloudkot
grep -r "import fastapi\|from fastapi" --include="*.py" .
grep -r "import uvicorn\|from uvicorn" --include="*.py" .
grep -r "import jinja2\|from jinja2" --include="*.py" .
grep -r "import python_multipart\|from python_multipart" --include="*.py" .
```

All return no results - these packages are not used.

#### Solution: Remove Unused Dependencies

**In requirements.txt**:
Remove lines:
```
fastapi>=0.109.0
uvicorn>=0.27.0
jinja2>=3.1.3
python-multipart>=0.0.6
```

**In pyproject.toml**:
Remove from `[tool.poetry.dependencies]`:
```toml
fastapi = "^0.109.0"
uvicorn = "^0.27.0"
jinja2 = "^3.1.3"
python-multipart = "^0.0.6"
```

**Note**: `prompt-toolkit` is also listed but not used. However, the AGENTS.md mentions it as a known issue, so we may leave it for now as it might be intended for future TUI enhancements.

**Trade-offs**:
- Pro: Smaller dependency footprint
- Pro: Faster installation
- Pro: Less confusion
- Con: May affect users who installed these for other reasons
- Mitigation: These are development dependencies, not runtime critical

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `compat.py` | Create | New compatibility module |
| `context_manager.py` | Modify | Use compat.tomllib |
| `provider_manager.py` | Modify | Use compat.tomllib |
| `personality_manager.py` | Modify | Use compat.tomllib |
| `permissions.py` | Modify | Use compat.tomllib |
| `lsp_server.py` | Modify | Use compat.tomllib |
| `main.py` | Modify | Use compat.tomllib, extract helper functions |
| `harness.py` | Modify | Add timeout to tool execution |
| `tui.py` | Modify | Improve event loop management |
| `satire/engine.py` | Modify | Fix form link extensions |
| `requirements.txt` | Modify | Remove unused dependencies |
| `pyproject.toml` | Modify | Remove unused dependencies |

## Testing Strategy
1. **Compat module**: Verify all imports work with and without tomli
2. **CLI refactoring**: Verify all commands still work
3. **TUI loop**: Test multiple rapid messages, verify no crashes
4. **Tool timeout**: Test with a slow tool, verify timeout works
5. **Form links**: Verify links in output point to .txt files
6. **Dependencies**: Verify installation still works after removing unused packages
