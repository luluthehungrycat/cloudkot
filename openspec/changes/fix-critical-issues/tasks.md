# Tasks: Fix Critical Issues

## Task List

### Task 1: Enhance Command Safety
**File:** `tools/builtin.py`
**Priority:** P0 - Critical
**Estimate:** 45 minutes
**Status:** Not Started

#### Description
Replace the simple prefix-based `_is_safe_command()` with regex-based pattern matching that catches destructive commands at any position, including chained commands and piped destructive commands.

#### Steps
1. [ ] Replace `_DESTRUCTIVE_PREFIXES` with `_DANGEROUS_PATTERNS` list of (regex, reason) tuples
2. [ ] Update `_is_safe_command()` to use regex search instead of startswith
3. [ ] Update to return tuple[bool, str] with reason for blocking
4. [ ] Update `run_command_handler()` to use the new return signature
5. [ ] Ensure safe shell features (pipes, redirects) still work

#### Files to Modify
- `tools/builtin.py:17-39` - Replace constants and function
- `tools/builtin.py:148-182` - Update handler to use new function

#### Test Cases
- [ ] `rm -rf /` → Blocked
- [ ] `echo hello; rm -rf /` → Blocked  
- [ ] `ls | grep test` → Allowed
- [ ] `echo hello > output.txt` → Allowed
- [ ] `sudo rm` → Blocked
- [ ] `apt install malicious` → Blocked

---

### Task 2: Create config.example.toml
**File:** `config.example.toml` (new)
**Priority:** P0 - Critical
**Estimate:** 20 minutes
**Status:** Not Started

#### Description
Create an example configuration file with safe defaults and comments explaining all options.

#### Steps
1. [ ] Create `config.example.toml` in repository root
2. [ ] Include all configuration sections: api, context, permissions, personality
3. [ ] Add comments explaining each option
4. [ ] Use safe defaults that work out of the box

#### File Content
```toml
# Cloudkot Configuration Example
# Copy this to config.toml and edit for your setup

[api]
# Option 1: Local LLM (e.g., LM Studio, LocalAI, Ollama)
base_url = "http://localhost:8080"
api_key = ""  # Empty for local
model = "mistral-tiny"

# Option 2: Use a provider (overrides base_url, api_key above)
# provider = "openai"  # openai, anthropic, mistral, openrouter, opencode_go, opencode_zen
# model = "gpt-4o"

[context]
max_tokens = 32768
compression_enabled = true
compression_threshold = 0.8

[permissions]
# tool_calls = "allow"  # allow, deny, ask
# file_access = "ask"
# network_access = "deny"
# execute_code = "ask"

[personality]
active = "neutral"  # neutral, stromberg, friendly, pedantic
```

---

### Task 3: Update load_config to Use Example
**File:** `main.py`
**Priority:** P0 - Critical
**Estimate:** 20 minutes
**Status:** Not Started

#### Description
Update `load_config()` to automatically copy `config.example.toml` to `config.toml` if the latter doesn't exist.

#### Steps
1. [ ] Import `shutil` at top of `main.py`
2. [ ] Update `load_config()` to check for `config.toml`
3. [ ] If missing, check for `config.example.toml`
4. [ ] If example exists, copy it and print helpful message
5. [ ] If neither exists, raise clear error

#### Code Changes
```python
def load_config() -> dict[str, Any]:
    config_path = Path("config.toml")
    if not config_path.exists():
        example_path = Path("config.example.toml")
        if example_path.exists():
            import shutil
            shutil.copy2(example_path, config_path)
            print(
                f"Created config.toml from example. "
                "Please edit it with your API settings."
            )
        else:
            raise FileNotFoundError(
                "Config file not found. "
                "Please create config.toml from config.example.toml."
            )
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
        return dict(raw)
```

---

### Task 4: Fix SSE JSON Parsing
**File:** `api_client.py`
**Priority:** P0 - Critical
**Estimate:** 30 minutes
**Status:** Not Started

#### Description
Add error handling for malformed JSON in SSE streaming responses.

#### Steps
1. [ ] Wrap `json.loads(data)` in try-except block
2. [ ] Skip malformed chunks and continue processing
3. [ ] Optionally notify via callback if available

#### Code Changes
```python
try:
    chunk = json.loads(data)
except json.JSONDecodeError as e:
    if callbacks and hasattr(callbacks, 'on_error') and callbacks.on_error:
        callbacks.on_error(f"Invalid JSON in SSE chunk: {e}")
    continue
```

#### Location
- `api_client.py:195` - Around the `chunk = json.loads(data)` line

---

### Task 5: Fix Argument Accumulation
**File:** `api_client.py`
**Priority:** P0 - Critical
**Estimate:** 20 minutes
**Status:** Not Started

#### Description
Prevent TypeError when tool call arguments are None during accumulation.

#### Steps
1. [ ] Check if arguments is not None before concatenation
2. [ ] Ensure tool_calls_acc is properly initialized with empty strings

#### Code Changes
```python
# In initialization (around line 220):
if idx not in tool_calls_acc:
    tool_calls_acc[idx] = {
        "id": tc.get("id") or "",
        "type": tc.get("type", "function"),
        "function": {
            "name": tc.get("function", {}).get("name") or "",
            "arguments": tc.get("function", {}).get("arguments") or "",
        }
    }

# In accumulation (around line 234):
arguments = tc["function"].get("arguments")
if arguments is not None:
    tool_calls_acc[idx]["function"]["arguments"] += arguments
```

#### Location
- `api_client.py:219-236` - Tool call accumulation logic

---

### Task 6: Ensure Empty Choices Guard
**File:** `api_client.py`
**Priority:** P0 - Critical
**Estimate:** 15 minutes
**Status:** Not Started

#### Description
Ensure the guard for empty choices arrays is present and correctly placed.

#### Steps
1. [ ] Verify the guard `if not chunk.get("choices"): continue` exists
2. [ ] Ensure it's placed BEFORE accessing `chunk["choices"][0]`
3. [ ] Test with empty choices array

#### Code Changes
```python
# This should already exist around line 197-198:
if not chunk.get("choices"):
    continue
choice = chunk["choices"][0]
```

#### Location
- `api_client.py:196-199`

---

### Task 7: Fix Provider Config Error Handling
**File:** `provider_manager.py`
**Priority:** P0 - Critical
**Estimate:** 20 minutes
**Status:** Not Started

#### Description
Make provider configuration errors explicit instead of silent failures.

#### Steps
1. [ ] Update `_load_providers()` to raise FileNotFoundError if file missing
2. [ ] Update `APIClient.__init__()` to catch and re-raise with context

#### Code Changes
```python
# In provider_manager.py:
def _load_providers(self):
    if not self.config_path.exists():
        raise FileNotFoundError(
            f"Provider configuration file not found: {self.config_path}. "
            "Please ensure providers.toml exists in the project root."
        )
    with open(self.config_path, "rb") as f:
        config = tomllib.load(f)
    if "providers" in config:
        for provider_name, provider_data in config["providers"].items():
            self.providers[provider_name] = ProviderConfig(**provider_data)
```

```python
# In api_client.py, around line 81-85:
if provider:
    try:
        provider_config = provider_manager.get_provider(provider)
        self.base_url = base_url or provider_config.base_url
        self.api_key = api_key or os.getenv(provider_config.api_key_env, "")
        self.model = model or provider_config.models[0] if provider_config.models else "gpt-3.5-turbo"
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(
            f"Could not load provider '{provider}': {e}. "
            "Please ensure providers.toml exists and contains the provider."
        ) from e
```

---

## Verification Tasks

### Verification 1: Command Safety
```bash
# Test blocking
python -c "from tools.builtin import run_command_handler; import asyncio; asyncio.run(run_command_handler('rm -rf /'))"
# Expected: Error message about blocked command

# Test allowing
python -c "from tools.builtin import run_command_handler; import asyncio; asyncio.run(run_command_handler('echo hello'))"
# Expected: "hello" output

# Test pipes
python -c "from tools.builtin import run_command_handler; import asyncio; asyncio.run(run_command_handler('ls | head -5'))"
# Expected: List of files
```

### Verification 2: Config Creation
```bash
# Remove config.toml
rm -f config.toml

# Run Cloudkot
python main.py generate -p "test"
# Expected: config.toml created from example, helpful message printed

# Verify content
diff config.toml config.example.toml
# Expected: Files should match (except config.toml may have been edited)
```

### Verification 3: Existing Tests
```bash
python -m pytest tests/ -v
# Expected: All existing tests pass
```

---

## Acceptance Checklist

- [ ] All command safety tests pass
- [ ] Config example file created and works
- [ ] SSE streaming handles edge cases
- [ ] Provider errors are clear
- [ ] All existing tests pass
- [ ] No new warnings or errors in normal operation
