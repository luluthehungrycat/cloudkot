## ADDED Requirements

### Requirement: MCP authentication is enforced
The MCP server MUST reject a WebSocket connection when authentication is required and the request does not contain the configured bearer token. Authentication checks MUST produce a boolean result and MUST NOT rely on truthiness of an un-awaited coroutine.

#### Scenario: Valid bearer token
- **WHEN** authentication is required and the client sends `Authorization: Bearer <configured-key>`
- **THEN** the connection is accepted

#### Scenario: Missing or invalid bearer token
- **WHEN** authentication is required and the client omits or sends a different bearer token
- **THEN** the server closes the connection with an unauthorized policy status

### Requirement: MCP malformed requests return JSON-RPC errors
The MCP server MUST return a valid JSON-RPC internal-error response for malformed JSON or otherwise invalid request payloads, without raising a secondary exception while constructing the error response.

#### Scenario: Malformed JSON
- **WHEN** the server receives a payload that is not valid JSON
- **THEN** it returns a JSON-RPC error with a null or default request ID and an internal-error code

### Requirement: Context stays within the configured budget
When compression is enabled, the context manager MUST ensure that its retained context plus a newly added item does not exceed `max_tokens`. If one item is larger than the budget, the manager MUST retain no older items and MUST bound the item content to the configured budget. When compression is disabled, the manager MUST preserve uncompressed insertion behavior.

#### Scenario: Existing context exceeds the compression threshold
- **WHEN** adding an item causes the configured compression threshold to be crossed
- **THEN** lower-value older items are removed until the retained token count is within the maximum budget

#### Scenario: Single oversized item
- **WHEN** adding an item whose token count exceeds `max_tokens` while compression is enabled
- **THEN** the resulting context token count is at most `max_tokens`

#### Scenario: Compression disabled
- **WHEN** adding context while `compression_enabled` is false
- **THEN** the manager retains items without truncation or eviction

### Requirement: Built-in command execution uses a constrained policy
The command tool MUST execute only approved non-shell commands with validated arguments, where the executable is a bare approved command name, and MUST reject shell metacharacters, path-qualified executable names, and unapproved executables before execution. Command execution MUST enforce a positive bounded timeout.

#### Scenario: Approved command
- **WHEN** the command is an approved executable with ordinary arguments and a valid timeout
- **THEN** it executes without shell interpretation and returns its output

#### Scenario: Shell injection or destructive command
- **WHEN** the command contains shell operators, an interpreter pipeline, a path-qualified executable, or a destructive/unapproved executable
- **THEN** the tool rejects it without spawning the command

#### Scenario: Invalid timeout
- **WHEN** the caller supplies a non-positive or excessive timeout
- **THEN** the tool rejects the request before execution
