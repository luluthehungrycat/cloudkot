## 1. MCP Safety

- [x] 1.1 Make MCP authentication a synchronous boolean predicate and normalize authorization header lookup.
- [x] 1.2 Update connection handling to reject unauthorized clients with the existing WebSocket policy close code.
- [x] 1.3 Make malformed MCP payloads return valid JSON-RPC errors without referencing an uninitialized request object.
- [x] 1.4 Add direct regression tests for valid, missing, invalid, and case-variant authorization headers plus malformed JSON.

## 2. Context Budget Enforcement

- [x] 2.1 Refactor context insertion/compression so the final retained token count includes the new item and does not exceed `max_tokens`.
- [x] 2.2 Bound an individual oversized item deterministically and recalculate its stored token count.
- [x] 2.3 Add regression tests for threshold-triggered compression and an item larger than the configured budget.

- [x] 2.4 Preserve uncompressed insertion behavior when `compression_enabled` is false.

## 3. Constrained Command Execution

- [x] 3.1 Replace shell-based execution and blacklist matching with `shlex` parsing, an explicit read-only executable allowlist, and shell-metacharacter rejection.
- [x] 3.2 Validate command input and enforce a finite timeout range before spawning a process.
- [x] 3.3 Update the tool description to document the constrained behavior.
- [x] 3.4 Add regression tests proving approved commands run without shell interpretation and unsafe commands/timeouts are rejected.
- [x] 3.5 Reject path-qualified forms of otherwise allowlisted executables and test the bypass case.

## 4. Verification

- [x] 4.1 Run focused MCP, context, and tool tests.
- [x] 4.2 Run the full pytest suite and fix regressions.
- [x] 4.3 Run Ruff and compile checks; resolve issues introduced by this change.
