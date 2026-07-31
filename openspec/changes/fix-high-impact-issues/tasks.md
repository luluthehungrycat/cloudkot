# Tasks: Fix High-Impact Issues

## Task List

### Task 1: Improve Token Counting Accuracy
**File:** `context_manager.py`
**Priority:** P1 - High
**Estimate:** 1-2 hours
**Status:** Not Started
**Dependency:** None

#### Description
Replace inaccurate word-based token counting with tiktoken-based counting with graceful fallback.

#### Steps
1. [ ] Add `_load_tokenizer()` method to ContextManager
2. [ ] Add `_tokenizer` attribute to ContextManager.__init__
3. [ ] Update `_count_tokens()` to use tiktoken or fallback
4. [ ] Update pyproject.toml to add tiktoken as optional dependency
5. [ ] Update requirements.txt to add tiktoken

#### Code Changes

**In context_manager.py:**
```python
from pathlib import Path
from collections import deque
import hashlib
import time

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pydantic import BaseModel


class ContextItem(BaseModel):
    content: str
    role: str
    token_count: int
    importance: float = 1.0
    timestamp: float = 0.0


class ContextManager:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.max_tokens: int = 32768
        self.compression_enabled: bool = True
        self.compression_threshold: float = 0.8
        self.current_tokens: int = 0
        self.context_window: deque[ContextItem] = deque()
        self.token_counts: dict[str, int] = {}
        self._tokenizer = self._load_tokenizer()  # NEW
        self._load_config()

    def _load_tokenizer(self):
        """Load tiktoken encoder, fall back to None"""
        try:
            import tiktoken
            return tiktoken.get_encoding("cl100k_base")
        except (ImportError, Exception):
            return None

    def _count_tokens(self, text: str) -> int:
        """Count tokens accurately using tiktoken, or approximate"""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Fallback: character-based estimation
        return len(text) // 4
```

**In pyproject.toml:**
```toml
[tool.poetry.dependencies]
# ... existing ...
tiktoken = "^0.7.0"
```

**In requirements.txt:**
```
tiktoken>=0.7.0
```

#### Test Cases
- [ ] Short text: `"Hello world"` → ~2-3 tokens
- [ ] Code snippet: `"def f(x): return x*2"` → ~8-10 tokens
- [ ] Long text: 1000 chars → ~250 tokens
- [ ] Works without tiktoken installed (fallback)

#### Verification Commands
```bash
# Install tiktoken
pip install tiktoken

# Test token counting
python -c "
from context_manager import context_manager
context_manager.clear_context()

# Test with code
code = 'def add(a, b): return a + b'
count = context_manager._count_tokens(code)
print(f'Code: {code}')
print(f'Token count: {count}')
# Expected: ~8-10 tokens

# Test with text
text = 'The quick brown fox jumps over the lazy dog'
count = context_manager._count_tokens(text)
print(f'Text: {text}')
print(f'Token count: {count}')
# Expected: ~9-10 tokens
"

# Test without tiktoken
pip uninstall -y tiktoken
python -c "from context_manager import context_manager; print(context_manager._count_tokens('hello world'))"
# Expected: 2 (5 chars / 4 = 1.25, but integer division gives 1... need to adjust)
```

**Note:** The fallback `len(text) // 4` may need adjustment for very short texts.

---

### Task 2: Integrate Skills Framework
**File:** `harness.py`, `main.py`, `skills/skill_manager.py`
**Priority:** P1 - High
**Estimate:** 2-3 hours
**Status:** Not Started
**Dependency:** None

#### Description
Wire the skills framework into the main harness so skills can be used during code generation.

#### Steps

**Step 2.1: Update harness.py**
1. [ ] Import skill_manager
2. [ ] Add skill_manager to CodingHarness.__init__
3. [ ] Update `_run_agent_loop` to accept skills parameter
4. [ ] Add `_apply_skills_preprocess` method
5. [ ] Add `_apply_skills_postprocess` method
6. [ ] Update generate_code, continue_chat, etc. to accept skills

**Step 2.2: Update main.py**
1. [ ] Add --skills option to generate, explain, refactor commands
2. [ ] Enable requested skills before calling harness

**Step 2.3: Update skill implementations**
1. [ ] Update skills to handle phase parameter
2. [ ] Make skills actually useful

#### Code Changes

**In harness.py:**
```python
from api_client import APIClient, Message
from satire.engine import SatireEngine
from satire.forms import FormGenerator
from tools import execute_tool, get_tool_definitions, list_tools
from skills.skill_manager import skill_manager  # NEW

MAX_TOOL_ITERATIONS = 10


class CodingHarness:
    def __init__(self, api_client: APIClient, satire_engine: SatireEngine):
        self.api = api_client
        self.satire = satire_engine
        self.form_generator = FormGenerator()
        self.skill_manager = skill_manager  # NEW

    async def _run_agent_loop(
        self, 
        messages: list[Message], 
        context: str | None = None, 
        callbacks=None,
        skills: list[str] | None = None  # NEW
    ) -> str:
        """Run the tool-calling agent loop with optional skills."""
        tool_defs = get_tool_definitions()
        available_tools = list_tools()

        # Build system message
        system_msg = Message(
            role="system",
            content=(
                "Sachbearbeiter-KI-Assistent gemäß §28 Abs. 4 der KI-Verordnung (KI-VO). "
                f"Zugelassene Hilfsmittel (§5 Abs. 1): {', '.join(available_tools)}. "
                "Jede Nutzung der Hilfsmittel ist formpflichtig und wird gemäß §12 Abs. 3 protokolliert. "
                "Verwenden Sie die genehmigten Werkzeuge zur Sichtung der Aktenlage. "
                "Der Antragsteller erwartet einen geprüften Bescheid nach DIN 66234-8. "
                "Ordnungswidrigkeiten (§89 OWiG) werden mit einem Formularverweis geahndet. "
                "Bitte legen Sie zu jeder Aktion das entsprechende Formular vor. "
                "Bei Rückfragen wenden Sie sich an Herrn Schmidt, Raum 304."
            )
        )
        if not any(msg.role == "system" for msg in messages):
            messages = [system_msg] + messages

        for iteration in range(MAX_TOOL_ITERATIONS):
            # NEW: Pre-process with skills
            if skills:
                messages = await self._apply_skills_preprocess(
                    messages, context, skills
                )

            if callbacks:
                result = await self.api.chat(messages, use_context=False, tools=tool_defs, stream=True, callbacks=callbacks)
            else:
                result = await self.api.chat(messages, use_context=False, tools=tool_defs)

            if result.tool_calls:
                # ... existing tool call handling ...
                continue

            # No tool calls
            if result.content:
                # NEW: Post-process with skills
                if skills:
                    result.content = await self._apply_skills_postprocess(
                        result.content, messages, context, skills
                    )
                return self.satire.wrap_response(result.content, context)

            return self.satire.wrap_response("(No response generated)", context)

        return self.satire.wrap_response(
            "(Reached maximum tool call iterations without a final response)", context
        )

    # NEW METHOD
    async def _apply_skills_preprocess(
        self, messages: list[Message], context: str | None, skills: list[str]
    ) -> list[Message]:
        """Apply pre-processing skills to messages."""
        for skill_name in skills:
            if self.skill_manager.can_execute_skill(skill_name):
                skill_result = await self.skill_manager.execute_skill(
                    skill_name,
                    messages=messages,
                    context=context,
                    phase="preprocess"
                )
                if skill_result.success and skill_result.output:
                    messages.append(Message(
                        role="system",
                        content=f"[Skill {skill_name} preprocess]: {skill_result.output}"
                    ))
        return messages

    # NEW METHOD
    async def _apply_skills_postprocess(
        self, content: str, messages: list[Message], context: str | None, skills: list[str]
    ) -> str:
        """Apply post-processing skills to LLM output."""
        for skill_name in skills:
            if self.skill_manager.can_execute_skill(skill_name):
                skill_result = await self.skill_manager.execute_skill(
                    skill_name,
                    content=content,
                    messages=messages,
                    context=context,
                    phase="postprocess"
                )
                if skill_result.success and skill_result.output:
                    content += f"\n\n[Skill {skill_name}]: {skill_result.output}"
        return content

    async def generate_code(self, prompt: str, context: str | None = None, skills: list[str] | None = None) -> str:
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, context, skills=skills)

    async def continue_chat(self, messages: list[Message], context: str | None = None, skills: list[str] | None = None) -> str:
        return await self._run_agent_loop(messages, context, skills=skills)

    async def continue_chat_stream(self, messages: list[Message], context: str | None = None, callbacks=None, skills: list[str] | None = None) -> str:
        return await self._run_agent_loop(messages, context, callbacks=callbacks, skills=skills)
```

**In main.py (generate command only, similar for explain/refactor):**
```python
@cli.command()
@click.option("--prompt", "-p", required=True, help="Your coding prompt")
@click.option("--context", "-c", default=None, help="Context for satire")
@click.option("--no-bürokratie", is_flag=True, help="Disable Bürokratie Mode")
@click.option("--provider", "-P", default=None, help="LLM provider")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-L", default=None, help="Personality to use")
@click.option("--skills", "-s", multiple=True, help="Skills to enable (can specify multiple)")
def generate(
    prompt: str,
    context: str | None,
    no_bürokratie: bool,
    provider: str | None,
    model: str | None,
    personality: str | None,
    skills: tuple[str, ...],
):
    """Generate code with optional Bürokratie Mode and skills."""
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

    satire = SatireEngine(bürokratie_mode=not no_bürokratie)
    harness = CodingHarness(api, satire)

    # Enable requested skills
    for skill_name in skills:
        skill_manager.enable_skill(skill_name)

    response = asyncio.run(
        harness.generate_code(prompt, context, skills=list(skills))
    )
    print(response)
```

**In skills/skill_manager.py:**
Update existing skills to handle phase parameter:
```python
class CodeGenerationSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="code_generation",
            description="Generate code from natural language descriptions",
            required_permissions=["tool_calls"],
        )

    async def execute(self, **kwargs: Any) -> SkillResult:
        phase = kwargs.get("phase")
        messages = kwargs.get("messages", [])
        
        if phase == "preprocess":
            # Could analyze messages and provide context
            return SkillResult(
                success=True,
                output="Code generation context prepared",
                skill_name=self.name,
            )
        elif phase == "postprocess":
            content = kwargs.get("content", "")
            # Could enhance the generated code
            return SkillResult(
                success=True,
                output=f"Code generation complete. Length: {len(content)} chars",
                skill_name=self.name,
            )
        
        return SkillResult(
            success=False,
            error=f"Unknown phase: {phase}",
            skill_name=self.name,
        )
```

#### Test Cases
- [ ] Generate with --skills code_generation
- [ ] Generate with multiple skills
- [ ] Generate with non-existent skill (should error gracefully)
- [ ] Verify skill output appears in response

#### Verification Commands
```bash
# List skills
python main.py skill list

# Test with skills
python main.py generate -p "write a python function" --skills code_generation

# Test with multiple skills
python main.py generate -p "write and explain a python function" --skills code_generation code_explanation
```

---

### Task 3: Add MCP Authentication Options
**File:** `mcp_server.py`, `main.py`
**Priority:** P1 - High
**Estimate:** 1-2 hours
**Status:** Not Started
**Dependency:** None

#### Description
Add support for both authenticated and unauthenticated MCP server connections.

#### Steps

**Step 3.1: Create mcp.toml**
1. [ ] Create default mcp.toml with auth disabled

**Step 3.2: Update MCPServer**
1. [ ] Add auth_key and auth_required parameters
2. [ ] Add authentication check in handle_connection
3. [ ] Add from_config class method

**Step 3.3: Update CLI**
1. [ ] Add --auth-key option to mcp command
2. [ ] Update help text

#### Code Changes

**New file: mcp.toml**
```toml
# MCP Server Configuration
# Set auth_required = true and api_key to enable authentication

[default]
host = "localhost"
port = 8080
auth_required = false
# api_key = "your-secret-key"  # Uncomment and set if auth_required = true
```

**In mcp_server.py:**
```python
class MCPServer:
    def __init__(self, host: str = "localhost", port: int = 8080, auth_key: str | None = None):
        self.host = host
        self.port = port
        self.auth_key = auth_key
        self.auth_required = auth_key is not None  # NEW
        self.server: websockets.WebSocketServer | None = None
        self.connections: list[websockets.WebSocketServerProtocol] = []
        self.tools: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}

    async def handle_connection(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ):
        """Handle a new WebSocket connection with optional auth"""
        # NEW: Check authentication if required
        if self.auth_required:
            auth_header = websocket.request_headers.get("Authorization", "")
            # Support both "Bearer <key>" and just "<key>" formats
            provided_key = auth_header.replace("Bearer ", "").strip()
            
            if not provided_key or provided_key != self.auth_key:
                await websocket.close(code=1008, reason="Unauthorized")
                return
        
        self.connections.append(websocket)
        print(f"MCP client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                response = await self.handle_message(message)
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            print("MCP client disconnected")
        finally:
            if websocket in self.connections:
                self.connections.remove(websocket)

    @classmethod
    def from_config(cls, config_path: str = "mcp.toml"):
        """Create server from configuration file"""
        from pathlib import Path
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        
        config_path = Path(config_path)
        if not config_path.exists():
            return cls()  # Return default unauthenticated server
        
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        
        mcp_config = config.get("default", {})
        auth_required = mcp_config.get("auth_required", False)
        auth_key = mcp_config.get("api_key") if auth_required else None
        
        return cls(
            host=mcp_config.get("host", "localhost"),
            port=mcp_config.get("port", 8080),
            auth_key=auth_key
        )
```

**In main.py:**
```python
@cli.command()
def mcp():
    """Start the MCP server."""
    import asyncio
    from mcp_server import MCPServer

    print("Starting Cloudkot MCP server...")
    
    # Use from_config to support both config file and CLI options
    # For now, keep simple - just use defaults
    # TODO: Add CLI options for host, port, auth-key
    server = MCPServer.from_config()
    
    if server.auth_required:
        print("Authentication required")
    else:
        print("No authentication (open access)")
    
    asyncio.run(server.start())
```

**Updated main.py mcp command with options:**
```python
@cli.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", "-p", type=int, default=8080, help="Port to listen on")
@click.option("--auth-key", default=None, help="API key for authentication (enables auth)")
def mcp(host: str, port: int, auth_key: str | None):
    """Start the MCP server with optional authentication."""
    import asyncio
    from mcp_server import MCPServer

    print(f"Starting Cloudkot MCP server on {host}:{port}...")
    if auth_key:
        print("Authentication required")
    else:
        print("No authentication (open access)")
    
    server = MCPServer(host=host, port=port, auth_key=auth_key)
    asyncio.run(server.start())
```

#### Test Cases
- [ ] Start MCP server without auth
- [ ] Connect without auth (should work)
- [ ] Start MCP server with --auth-key
- [ ] Connect without key (should fail)
- [ ] Connect with correct key (should work)
- [ ] Connect with wrong key (should fail)

#### Verification Commands
```bash
# Test without auth
python main.py mcp --port 8081 &
sleep 1
# Use MCP client to connect to ws://localhost:8081
# Expected: Connection succeeds

# Test with auth
python main.py mcp --port 8082 --auth-key mysecretkey &
sleep 1
# Use MCP client to connect to ws://localhost:8082 without auth
# Expected: Connection fails with "Unauthorized"
# Use MCP client with Authorization: Bearer mysecretkey header
# Expected: Connection succeeds
```

---

## Acceptance Checklist

- [ ] Token counting is accurate (within 10% of actual)
- [ ] Skills can be enabled via CLI
- [ ] Skills execute and affect output
- [ ] MCP server works with and without authentication
- [ ] All existing tests pass
- [ ] No new warnings or errors in normal operation
