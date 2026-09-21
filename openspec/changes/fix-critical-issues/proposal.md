# Change: Fix Critical Issues

## Summary
Fix critical security vulnerabilities, correctness bugs, and setup issues that prevent Cloudkot from working reliably for new users.

## Motivation
Cloudkot currently has several critical issues that must be addressed:
1. **Security vulnerability**: Command injection in `run_command` tool
2. **Setup failure**: Missing `config.example.toml` causes immediate crash for new clones
3. **Streaming bugs**: SSE streaming has JSON parsing and argument accumulation issues
4. **Silent failures**: Provider manager silently fails when config is missing

These issues affect the core functionality and user experience.

## Non-Goals
- Feature enhancements (handled in separate changes)
- Performance optimizations (handled in separate changes)
- Documentation improvements (handled in separate changes)

## Success Criteria
- [ ] `run_command` blocks truly destructive commands while allowing safe ones
- [ ] New repository clones automatically get a working config example
- [ ] SSE streaming handles malformed JSON and None arguments gracefully
- [ ] Provider configuration errors are clear and actionable
- [ ] All existing tests continue to pass

## Risks
- **Breaking changes**: None expected for end users
- **Dependencies**: No new dependencies required
- **Performance**: No performance impact expected

## Open Questions
- Should we allow any shell features (pipes, redirects) in commands, or restrict to simple commands only?
  - *Answer from maintainer*: Yes, allow arbitrary shell commands with safety checks

## Dependencies
- None

## Related Changes
- fix-high-impact-issues (token counting, skills integration, MCP auth)
- fix-quality-issues (code deduplication, imports, etc.)
