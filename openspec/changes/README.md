# Cloudkot Improvement Changes - OpenSpec Index

This directory contains OpenSpec-compatible change proposals for addressing issues identified in the Cloudkot codebase review.

## Change Overview

| Change ID | Priority | Category | Status | Estimated Effort |
|-----------|----------|----------|--------|-----------------|
| [fix-critical-issues](./fix-critical-issues/) | P0 | Security/Correctness | Not Started | 4-6 hours |
| [fix-high-impact-issues](./fix-high-impact-issues/) | P1 | Performance/Features | Not Started | 5-8 hours |
| [fix-quality-issues](./fix-quality-issues/) | P2 | Maintainability | Not Started | 4-5 hours |

**Total Estimated Effort: 13-19 hours**

---

## Implementation Order

### Phase 1: Critical Fixes (4-6 hours)
**Must be completed first** - These issues affect core functionality and security.

**Change:** [fix-critical-issues](./fix-critical-issues/)
- [Proposal](./fix-critical-issues/proposal.md)
- [Design](./fix-critical-issues/design.md)
- [Tasks](./fix-critical-issues/tasks.md)

**Issues Addressed:**
1. Command injection vulnerability in `run_command` tool
2. Missing `config.example.toml` causing crashes for new users
3. SSE streaming bugs (JSON parsing, argument accumulation)
4. Silent provider config failures

---

### Phase 2: High-Impact Improvements (5-8 hours)
**Should be completed after Phase 1** - These improve accuracy and functionality.

**Change:** [fix-high-impact-issues](./fix-high-impact-issues/)
- [Proposal](./fix-high-impact-issues/proposal.md)
- [Design](./fix-high-impact-issues/design.md)
- [Tasks](./fix-high-impact-issues/tasks.md)

**Issues Addressed:**
1. Inaccurate token counting (use tiktoken)
2. Skills framework integration
3. MCP server authentication options

---

### Phase 3: Quality Improvements (4-5 hours)
**Can be done in parallel with Phase 2** - These improve maintainability.

**Change:** [fix-quality-issues](./fix-quality-issues/)
- [Proposal](./fix-quality-issues/proposal.md)
- [Design](./fix-quality-issues/design.md)
- [Tasks](./fix-quality-issues/tasks.md)

**Issues Addressed:**
1. Duplicated tomllib/tomli imports (create compat.py)
2. CLI code duplication (extract helper functions)
3. TUI event loop cleanup
4. Tool execution timeout
5. Form links extension mismatch
6. Unused dependencies

---

## Quick Start

To begin implementation:

```bash
# Navigate to the change directory
cd openspec/changes/fix-critical-issues

# Review the plan
cat proposal.md
design.md
tasks.md

# Start implementing tasks in order
```

## File Changes Summary

### fix-critical-issues
**Files to Create:**
- `config.example.toml`

**Files to Modify:**
- `tools/builtin.py` (enhanced command safety)
- `main.py` (config auto-creation)
- `api_client.py` (SSE bug fixes, provider error handling)
- `provider_manager.py` (explicit error on missing config)

### fix-high-impact-issues
**Files to Create:**
- `mcp.toml`

**Files to Modify:**
- `context_manager.py` (token counting)
- `harness.py` (skills integration, tool timeout)
- `main.py` (skills CLI option)
- `skills/skill_manager.py` (skills implementation)
- `mcp_server.py` (authentication)

**Dependencies to Add:**
- `tiktoken>=0.7.0` (optional, with fallback)

### fix-quality-issues
**Files to Create:**
- `compat.py`

**Files to Modify:**
- `context_manager.py` (use compat)
- `provider_manager.py` (use compat)
- `personality_manager.py` (use compat)
- `permissions.py` (use compat)
- `lsp_server.py` (use compat)
- `main.py` (use compat, extract helpers)
- `harness.py` (tool timeout)
- `tui.py` (event loop cleanup)
- `satire/engine.py` (form link fix)
- `requirements.txt` (remove unused)
- `pyproject.toml` (remove unused)

**Dependencies to Remove:**
- `fastapi`
- `uvicorn`
- `jinja2`
- `python-multipart`

---

## Testing Strategy

Each change includes verification tasks. After completing all changes:

```bash
# Run all tests
python -m pytest tests/ -v

# Verify key functionality
python main.py generate -p "test prompt"
python main.py explain -c "def f(): pass"
python main.py refactor -c "def f(): pass"

# Verify new features
python main.py generate -p "test" --skills code_generation
python main.py mcp --auth-key mykey
```

---

## Maintainer Notes

Based on maintainer feedback:
1. ✅ `run_command` **is intended** to allow arbitrary shell commands (with safety checks)
2. ✅ LSP server **is currently a joke** - may become useful later, keep as-is
3. ✅ Skills framework **should be integrated** into the main harness
4. ✅ MCP server **should support both** authenticated and unauthenticated options

---

## See Also

- [Code Review Report](../../../CODE_REVIEW.md) (if created)
- [AGENTS.md](../../../AGENTS.md) - Project-specific instructions
- [OpenSpec Documentation](https://github.com/open-sauce-labs/openspec) - OpenSpec methodology
