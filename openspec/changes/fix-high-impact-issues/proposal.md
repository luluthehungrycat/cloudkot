# Change: Fix High-Impact Issues

## Summary
Improve Cloudkot's accuracy, functionality, and usability by fixing token counting, integrating the skills framework, and adding MCP authentication options.

## Motivation
These issues affect core functionality and user experience:
1. **Token counting inaccuracy** - Context management uses `len(text.split())` which is ~4x inaccurate for code
2. **Skills framework unused** - Skills exist but are never called by the main harness
3. **MCP server lacks authentication** - No way to secure the MCP server for production use

## Non-Goals
- Critical bug fixes (handled in fix-critical-issues)
- Code quality improvements (handled in fix-quality-issues)
- New features beyond the scope of existing capabilities

## Success Criteria
- [ ] Token counting is accurate within 10% of actual token count
- [ ] Skills can be enabled and executed via CLI
- [ ] MCP server supports both authenticated and unauthenticated modes
- [ ] All existing tests continue to pass

## Risks
- **Dependencies**: Adding tiktoken as optional dependency
- **Breaking changes**: None expected for end users
- **Performance**: Token counting may be slightly slower with tiktoken (but more accurate)

## Open Questions
None - all clarified with maintainer.

## Dependencies
- fix-critical-issues (should be completed first)

## Related Changes
- fix-critical-issues (prerequisite)
- fix-quality-issues (can be done in parallel)
