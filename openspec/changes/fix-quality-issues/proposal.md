# Change: Fix Code Quality Issues

## Summary
Improve Cloudkot's code quality, maintainability, and consistency by addressing duplicated code, import patterns, and minor correctness issues.

## Motivation
These issues affect developer experience and code maintainability:
1. **Duplicated tomllib/tomli imports** - Same pattern in 6 files
2. **CLI code duplication** - generate/explain/refactor commands duplicate logic
3. **Event loop management** - TUI doesn't clean up properly on failure
4. **Tool execution timeout** - Tools can hang indefinitely
5. **Form links mismatch** - Satire references .pdf but forms are .txt
6. **Unused dependencies** - requirements.txt has packages not used in code

## Non-Goals
- Critical bug fixes (handled in fix-critical-issues)
- High-impact functionality (handled in fix-high-impact-issues)
- New features

## Success Criteria
- [ ] tomllib/tomli import centralized in compat module
- [ ] CLI commands use shared helper for harness creation
- [ ] TUI event loop properly cleaned up on failure
- [ ] Tool execution has timeout
- [ ] Form links point to correct file extensions
- [ ] Unused dependencies removed
- [ ] All existing tests continue to pass

## Risks
- **Breaking changes**: Minimal - all changes are internal
- **Dependencies**: Removing unused packages may affect users who installed them
- **Performance**: No performance impact expected

## Open Questions
None

## Dependencies
- fix-critical-issues (should be completed first)
- fix-high-impact-issues (can be done in parallel)

## Related Changes
- fix-critical-issues (prerequisite)
- fix-high-impact-issues (can be done in parallel)
