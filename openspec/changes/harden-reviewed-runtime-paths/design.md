## Context

The reviewed runtime paths expose filesystem tools, maintain a token-budgeted context, and serve MCP requests over WebSockets. The current implementation has three high-confidence defects: MCP authentication is asynchronous but called synchronously, malformed MCP input can trigger an unbound local in the error handler, and context compression is performed before appending without guaranteeing the final budget. The command tool also invokes `shell=True` behind a regex blacklist, which is not a reliable security boundary.

## Goals / Non-Goals

**Goals:**

- Make MCP authentication synchronous at the call boundary and reject unauthorized clients.
- Make malformed MCP requests return valid JSON-RPC errors.
- Make context insertion budget-aware and preserve the newest item when possible.
- Execute commands without a shell through a small explicit allowlist and bounded timeout.
- Add regression tests for each failure mode.

**Non-Goals:**

- Redesigning the MCP protocol or adding a new authentication mechanism.
- Implementing arbitrary shell syntax safely.
- Introducing a tokenizer or changing the existing token-counting strategy.
- Changing the public shape of API chat messages.

## Decisions

### 1. Use a synchronous authentication predicate

`_check_auth` performs only in-memory header comparison, so it will become synchronous and `handle_connection` will call it directly. This removes the coroutine truthiness bug and keeps the authorization decision explicit. The alternative—awaiting the current method—would work but would preserve unnecessary asynchronous API surface.

### 2. Separate request parsing from error response construction

`handle_message` will initialize a nullable request ID before parsing. Parsing and dispatch remain inside the protected block, while the exception response uses that safe ID. This preserves the existing error contract and prevents malformed input from causing a second exception. A full JSON-RPC parser rewrite is out of scope.

### 3. Enforce context budget after insertion

When `compression_enabled` is true, the manager will treat the incoming item as the newest item and remove lower-scored retained items until the final total fits. For an item larger than the budget, content will be bounded using the existing token-counting function, with a deterministic prefix retained. When compression is disabled, insertion will preserve the existing uncompressed behavior. The implementation will recalculate the token count rather than trusting the pre-truncation value.

### 4. Prefer an executable allowlist and `shell=False`

The command tool will parse with `shlex.split`, reject shell metacharacters and empty input, allow a small set of read-only inspection commands by bare executable name only, and invoke `subprocess.run` with an argument list and `shell=False`. Timeout values will be constrained to a finite range. This is safer than expanding a blacklist, though it intentionally rejects pipes, redirects, and path-qualified executables that were previously permitted.

### 5. Test behavior at the boundary

Tests will call the MCP handlers directly, use temporary context managers with small budgets, and exercise command acceptance/rejection without launching a server. This keeps tests deterministic and targets the security and budgeting contracts.

## Risks / Trade-offs

- [Command compatibility] Existing users may depend on pipes, redirects, or tools outside the allowlist → return a clear rejection message and document the narrower policy in the tool description.
- [Token truncation] Prefix truncation can cut a message mid-token or mid-code construct → retain deterministic content and ensure the recorded count matches the stored content.
- [MCP client variance] Some clients may provide lowercase header names → normalize headers before looking up `Authorization`.

## Migration Plan

No data migration is required. Deploy the code and run the regression suite. If command-tool compatibility issues are discovered, callers must invoke approved commands separately rather than relying on shell composition. Rollback is a normal code rollback; no persisted state format changes.

## Open Questions

None. The reviewed findings provide sufficient acceptance criteria for implementation.
