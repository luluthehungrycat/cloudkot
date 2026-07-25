"""Cloudkot's tool-calling system — filesystem context tools for the assistant.

Provides OpenAI-compatible tool definitions and an async executor for
built-in filesystem tools (read, glob, grep, command, list directory).
"""

from .builtin import TOOL_DEFINITIONS, TOOL_REGISTRY

__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_REGISTRY",
    "execute_tool",
    "get_tool_definitions",
    "list_tools",
]


def get_tool_definitions():
    """Return the list of OpenAI-compatible tool definition dicts."""
    return TOOL_DEFINITIONS


def list_tools():
    """Return a list of available tool names."""
    return list(TOOL_REGISTRY.keys())


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with the given arguments.

    Args:
        name: Tool name (must exist in TOOL_REGISTRY).
        arguments: Keyword arguments to pass to the tool handler.

    Returns:
        String result of the tool execution. Errors are returned as
        descriptive error strings, not raised as exceptions.
    """
    if name not in TOOL_REGISTRY:
        return f"Error: Unknown tool '{name}'. Available tools: {', '.join(list_tools())}"

    try:
        handler = TOOL_REGISTRY[name]
        result = await handler(**arguments)
        return str(result)
    except Exception as e:
        return f"Error executing tool '{name}': {e}"
