## Why

The code review found that two safety-critical runtime paths are not enforcing their advertised guarantees: MCP authentication currently accepts unauthorized connections, and context compression can exceed the configured token budget. The shell tool also relies on a fragile blacklist while executing commands through a shell. These issues should be fixed before the reviewed runtime changes are relied on.

## What Changes

- Enforce MCP authentication for every connection and return valid JSON-RPC errors for malformed requests.
- Make context compression enforce the configured maximum, including oversized incoming messages, while preserving disabled-compression behavior.
- Replace unrestricted shell execution with a constrained command policy that does not invoke a shell by default and rejects path-based executable bypasses.
- Add regression tests for authentication, malformed MCP input, budget enforcement, and command safety.

## Capabilities

### New Capabilities

- `runtime-safety`: Defines safe command execution and resource-budget behavior for built-in tools and context management.

### Modified Capabilities

- `mcp-server`: Authentication and malformed JSON-RPC request handling now have explicit, enforced behavior.

## Impact

Affected code includes `mcp_server.py`, `context_manager.py`, `tools/builtin.py`, and their tests. The command tool behavior becomes more restrictive: shell metacharacters and commands outside the approved policy will be rejected rather than executed. No external API or data schema changes are required.
