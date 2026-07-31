# Design: High-Impact Issues Fixes

## Overview
This design document outlines the technical approach to fixing Cloudkot's high-impact issues: token counting accuracy, skills framework integration, and MCP authentication.

## Components

### 1. Accurate Token Counting

#### Current State
- `_count_tokens(text)` uses `len(text.split())`
- This counts words, not tokens
- For code: typically 3-4x undercount (code has many sub-word tokens like `{`, `}`, `.`, etc.)

#### Problems
- Context window can overflow if actual tokens exceed estimated
- Context compression may trigger too late or too early
- Utilization reporting is inaccurate

#### Solution: Use tiktoken with Fallback

**Approach**:
1. Try to load `tiktoken` (OpenAI's BPE tokenizer)
2. Use `cl100k_base` encoding (works for most models)
3. Fall back to character-based estimation if tiktoken unavailable

**Why tiktoken?**:
- It's the industry standard for OpenAI-compatible APIs
- Handles all special tokens (newlines, code symbols, etc.)
- Lightweight and fast
- MIT licensed

**Why cl100k_base?**:
- Used by many models (Mistral, some OpenAI models)
- Good general-purpose encoding
- Works reasonably well across different model types

**Implementation**:
```python
# In context_manager.py

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
    """Load tiktoken encoder, fall back to approximation"""
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
    # ~4 characters per token on average for English/code
    return len(text) // 4
```

**Trade-offs**:
- Pro: Much more accurate token counting
- Pro: Works offline (no API calls)
- Pro: Optional dependency (falls back gracefully)
- Con: Adds ~1MB dependency (tiktoken)
- Con: Slightly slower than word counting (but still very fast)

**Alternatives considered**:
1. Use model-specific tokenizers - Rejected: too complex, requires knowing the model
2. Use sentencepiece - Rejected: heavier dependency, more complex
3. API-based counting - Rejected: requires network, slow, not reliable

---

### 2. Skills Framework Integration

#### Current State
- Skills exist in `skills/` directory
- SkillManager singleton exists
- Skills have execute() methods
- **But**: Never called by the main harness

#### Problems
- Dead code
- Users can't access skills
- CLI has skill commands but they don't affect the main workflow

#### Solution: Wire Skills into Agent Loop

**Approach**:
1. Pass skills list through the harness methods
2. Execute skills at appropriate points in the agent loop
3. Allow pre-processing (before LLM call) and post-processing (after LLM response)

**Integration Points**:

**Option A: Pre-LLM Processing**
- Skills can pre-process the prompt/messages
- Useful for: code analysis, context enrichment

**Option B: Post-LLM Processing**  
- Skills can enhance the LLM response
- Useful for: code formatting, documentation generation, validation

**Option C: Both**
- Maximize flexibility
- Skills can choose to implement pre-processing, post-processing, or both

**Implementation**:
```python
# In harness.py

class CodingHarness:
    def __init__(self, api_client: APIClient, satire_engine: SatireEngine):
        self.api = api_client
        self.satire = satire_engine
        self.form_generator = FormGenerator()
        self.skill_manager = skill_manager  # Use singleton

    async def _run_agent_loop(
        self, 
        messages: list[Message], 
        context: str | None = None, 
        callbacks=None,
        skills: list[str] | None = None
    ) -> str:
        """Run the agent loop with optional skills."""
        
        # ... existing setup code ...

        for iteration in range(MAX_TOOL_ITERATIONS):
            # NEW: Pre-process with skills
            if skills:
                messages = await self._apply_skills_preprocess(
                    messages, context, skills
                )
            
            # ... existing chat logic ...
            
            if result.content:
                # NEW: Post-process with skills
                if skills:
                    result.content = await self._apply_skills_postprocess(
                        result.content, messages, context, skills
                    )
                return self.satire.wrap_response(result.content, context)

    async def _apply_skills_preprocess(
        self, messages: list[Message], context: str | None, skills: list[str]
    ) -> list[Message]:
        """Apply pre-processing skills to messages."""
        for skill_name in skills:
            if self.skill_manager.can_execute_skill(skill_name):
                skill = self.skill_manager.get_skill(skill_name)
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
```

**CLI Integration**:
```python
# In main.py generate command:
@click.option("--skills", "-s", multiple=True, help="Skills to enable")
def generate(..., skills: tuple[str, ...]):
    # ... existing code ...
    harness = CodingHarness(api, satire)
    response = asyncio.run(
        harness.generate_code(prompt, context, skills=list(skills))
    )
```

**Skill Updates**:
Update existing dummy skills to be useful:
```python
class CodeReviewSkill(BaseSkill):
    async def execute(self, **kwargs) -> SkillResult:
        phase = kwargs.get("phase")
        content = kwargs.get("content")
        
        if phase == "postprocess" and content:
            # Analyze the code and provide feedback
            feedback = self._analyze_code(content)
            return SkillResult(
                success=True,
                output=feedback,
                skill_name=self.name
            )
        return SkillResult(success=False, error="Invalid phase", skill_name=self.name)
```

**Trade-offs**:
- Pro: Skills become useful and integrated
- Pro: Flexible architecture supports different skill types
- Con: Slightly more complex agent loop
- Con: Need to update skill implementations

---

### 3. MCP Server Authentication

#### Current State
- MCP server accepts all connections
- No authentication mechanism
- All tools/resources are accessible to anyone

#### Problems
- No way to secure the MCP server
- Cannot prevent unauthorized access
- Not suitable for production or multi-user environments

#### Solution: Configurable Authentication

**Approach**:
1. Add optional `auth_key` parameter to MCPServer
2. Add `auth_required` flag
3. Check Authorization header on connection
4. Support both authenticated and unauthenticated modes
5. Add configuration via `mcp.toml`

**Implementation**:

**New Configuration File**: `mcp.toml`
```toml
[default]
host = "localhost"
port = 8080
auth_required = false
# api_key = "your-secret-key"  # Only used if auth_required = true
```

**Updated MCPServer**:
```python
class MCPServer:
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 8080, 
        auth_key: str | None = None
    ):
        self.host = host
        self.port = port
        self.auth_key = auth_key
        self.auth_required = auth_key is not None
        # ... existing attributes ...

    async def handle_connection(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ):
        """Handle connection with optional auth check."""
        # Check authentication if required
        if self.auth_required:
            auth_header = websocket.request_headers.get("Authorization", "")
            # Support both "Bearer <key>" and just "<key>" formats
            provided_key = auth_header.replace("Bearer ", "").strip()
            
            if not provided_key or provided_key != self.auth_key:
                await websocket.close(code=1008, reason="Unauthorized")
                return
        
        # ... existing connection handling ...

    @classmethod
    def from_config(cls, config_path: str = "mcp.toml"):
        """Create server from configuration file."""
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

**Updated CLI Command**:
```python
@cli.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", "-p", type=int, default=8080, help="Port to listen on")
@click.option("--auth-key", default=None, help="API key for authentication")
def mcp(host: str, port: int, auth_key: str | None):
    """Start the MCP server with optional authentication."""
    from mcp_server import MCPServer
    
    print(f"Starting Cloudkot MCP server on {host}:{port}")
    if auth_key:
        print("Authentication required")
    else:
        print("No authentication (open access)")
    
    server = MCPServer(host=host, port=port, auth_key=auth_key)
    
    import asyncio
    asyncio.run(server.start())
```

**Trade-offs**:
- Pro: Both modes supported
- Pro: Easy to configure
- Pro: Backward compatible (default is no auth)
- Con: API key sent in header (not encrypted without TLS)
- Con: Still need TLS for production use

**Security Notes**:
- For production, users should:
  1. Use TLS (wss:// instead of ws://)
  2. Use strong API keys
  3. Consider network-level security (firewall, VPN)
- This implementation provides basic auth, not end-to-end security

---

## File Changes Summary

| File | Lines | Change Type |
|------|-------|-------------|
| `context_manager.py` | 57-60, 29-31 | Modify |
| `harness.py` | 17-20, 22-29, 50-54 | Modify |
| `main.py` | 201-237, 245-265, 273-293 | Modify |
| `skills/skill_manager.py` | 140-180 | Modify |
| `mcp_server.py` | 22-30, 219-233, 235-248 | Modify |
| `mcp.toml` | new file | Create |

## Testing Strategy
1. **Token counting**: Verify accuracy with various text/code inputs
2. **Skills integration**: Test CLI with --skills flag, verify skills execute
3. **MCP auth**: Test both authenticated and unauthenticated connections
