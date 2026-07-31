# Design: Critical Issues Fixes

## Overview
This design document outlines the technical approach to fixing Cloudkot's critical issues.

## Components

### 1. Command Safety Enhancement

#### Current State
- Uses `subprocess.run()` with `shell=True`
- Basic prefix-based blocking in `_is_safe_command()`
- Patterns checked: `rm -rf /`, `sudo`, `dd`, `mkfs`, etc.

#### Problems
- Only checks for specific prefixes
- Commands like `echo hello; rm -rf /` pass the check
- `shell=True` is inherently dangerous

#### Solution: Enhanced Pattern Matching

**Approach**: Replace simple prefix matching with regex-based pattern detection that catches:
- Destructive commands at any position
- Chained commands with semicolons
- Piped destructive commands
- System file writes
- Privilege escalation attempts

**Implementation**:
```python
_DANGEROUS_PATTERNS = [
    # Destructive operations
    (r'\brm\s+', 'rm command'),
    (r'\bdd\s+', 'dd command'),
    (r'\bmkfs\b', 'mkfs command'),
    # Chained commands
    (r';\s*rm', 'chained rm'),
    (r'\|\s*(rm|dd|mkfs)', 'piped destructive'),
    # System modification
    (r'>\s*/(dev|proc|sys)', 'write to system'),
    # Privilege escalation
    (r'\bsudo\b', 'sudo'),
    (r'\b(apt|yum|dnf|pacman|pip)\s+(install|remove)', 'package manager'),
]

def _is_safe_command(command: str) -> tuple[bool, str]:
    """Return (is_safe, reason_if_unsafe)"""
    stripped = command.strip()
    for pattern, reason in _DANGEROUS_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return False, f"Blocked: {reason} detected"
    return True, ""
```

**Trade-offs**:
- Allows safe pipes and redirects (e.g., `ls | grep test`, `echo hello > output.txt`)
- Maintains backward compatibility for non-destructive complex commands
- Still uses `shell=True` but with comprehensive blocking

**Alternative considered**: Using `shell=False` and `shlex.split()`
- Rejected: Would break commands that rely on shell features (pipes, redirects, globbing)
- Maintainer confirmed: arbitrary shell commands with safety checks are intended

---

### 2. Configuration Example File

#### Current State
- `config.toml` is gitignored
- No example file provided
- New clones crash with FileNotFoundError

#### Solution: Create config.example.toml

**Approach**:
1. Create `config.example.toml` with safe, commented defaults
2. Update `load_config()` to copy example to `config.toml` if missing
3. Add helpful message pointing users to edit the file

**File Location**: Repository root

**Content Structure**:
```toml
[api]
# Option 1: Local LLM
base_url = "http://localhost:8080"
api_key = ""
model = "mistral-tiny"

# Option 2: Use a provider
# provider = "openai"
# model = "gpt-4o"

[context]
max_tokens = 32768
compression_enabled = true
compression_threshold = 0.8

[permissions]
# tool_calls = "allow"
# file_access = "ask"
# network_access = "deny"
# execute_code = "ask"

[personality]
active = "neutral"
```

**Behavior**:
- If `config.toml` missing → copy from `config.example.toml` and inform user
- If `config.example.toml` missing → raise clear error

---

### 3. SSE Streaming Bug Fixes

#### Current State
- JSON parsing without validation
- None arguments cause TypeError on concatenation
- Empty choices arrays cause IndexError

#### Problems
1. **JSON parsing**: `json.loads(data)` crashes on malformed JSON
2. **Argument accumulation**: `None + str` raises TypeError
3. **Empty choices**: `chunk["choices"][0]` fails when choices is empty

#### Solution

**Problem 1: JSON Parsing**
```python
try:
    chunk = json.loads(data)
except json.JSONDecodeError as e:
    if callbacks and callbacks.on_error:
        callbacks.on_error(f"Invalid JSON in SSE chunk: {e}")
    continue
```

**Problem 2: Argument Accumulation**
```python
arguments = func_data.get("arguments")
if arguments is not None:
    tool_calls_acc[idx]["function"]["arguments"] += arguments
```

**Problem 3: Empty Choices**
```python
if not chunk.get("choices"):
    continue
```

**Files to Modify**:
- `api_client.py` lines 190-236

---

### 4. Provider Config Error Handling

#### Current State
- `_load_providers()` silently returns if file missing
- Later code fails with confusing "Unknown provider" error

#### Solution
```python
def _load_providers(self):
    if not self.config_path.exists():
        raise FileNotFoundError(
            f"Provider configuration file not found: {self.config_path}. "
            "Please ensure providers.toml exists."
        )
    # ... rest of loading logic
```

**Files to Modify**:
- `provider_manager.py` lines 35-45
- `api_client.py` lines 81-85 (add try-catch for provider loading)

---

## File Changes Summary

| File | Lines | Change Type |
|------|-------|-------------|
| `tools/builtin.py` | 17-39, 148-182 | Modify |
| `main.py` | 36-45 | Modify |
| `api_client.py` | 190-236, 81-85 | Modify |
| `provider_manager.py` | 35-45 | Modify |
| `config.example.toml` | new file | Create |

## Testing Strategy
1. **Command safety**: Test various dangerous command patterns are blocked
2. **New clone**: Test fresh clone creates config from example
3. **SSE streaming**: Test with mock SSE responses containing edge cases
4. **Provider errors**: Test clear error messages when config missing
