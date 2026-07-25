"""Built-in tool implementations for Cloudkot's tool-calling system.

Each tool is an async function that takes keyword arguments and returns a string result.
"""

import fnmatch
import glob
import os
import re
import subprocess
from typing import Any

# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

_DESTRUCTIVE_PREFIXES = (
    "sudo ",
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf $HOME",
    ":(){ :|:& };:",
    "mkfs.",
    "dd if=",
    "> /dev/sd",
    "| sh",
    "| bash",
)


def _is_safe_command(command: str) -> bool:
    """Return False if the command looks destructive."""
    stripped = command.strip()
    low = stripped.lower()
    for prefix in _DESTRUCTIVE_PREFIXES:
        if low.startswith(prefix):
            return False
    return True


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def read_file_handler(path: str) -> str:
    """Read the contents of a file from the filesystem.

    Args:
        path: Path to the file to read.
    """
    # Resolve relative to CWD if not absolute
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except IsADirectoryError:
        return f"Error: Path is a directory, not a file: {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error reading file '{path}': {e}"


async def glob_files_handler(pattern: str) -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g. '**/*.py', 'src/**/*.ts').
    """
    try:
        matches = glob.glob(pattern, recursive=True)
    except Exception as e:
        return f"Error in glob pattern '{pattern}': {e}"

    if not matches:
        return "No matches found."

    # Sort for deterministic output
    matches.sort()

    lines = [f"Found {len(matches)} match(es):", ""]
    for m in matches:
        lines.append(f"  {m}")
    return "\n".join(lines)


async def grep_files_handler(pattern: str, include: str = "*") -> str:
    """Search file contents by regex.

    Walks the current directory recursively, filters files by ``include``
    glob, and reports the first 50 matches.

    Args:
        pattern: Regular expression to search for.
        include: Glob pattern to filter files (default '*').
    """
    max_matches = 50
    results: list[str] = []
    root = os.getcwd()

    try:
        compiled = re.compile(pattern)
    except re.error as e:
        return f"Error in regex pattern '{pattern}': {e}"

    for dirpath, _dirnames, filenames in os.walk(root):
        # Skip hidden directories (like .git, __pycache__, .venv, node_modules)
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""
        parts = rel_dir.split(os.sep) if rel_dir else []
        if any(p.startswith(".") for p in parts):
            continue
        if any(p in ("__pycache__", "node_modules", ".venv", "venv", ".git")
               for p in parts):
            continue

        matched_names = fnmatch.filter(filenames, include)
        for fname in matched_names:
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for lineno, line in enumerate(f, start=1):
                        if compiled.search(line):
                            rel_path = os.path.relpath(fpath, root)
                            results.append(f"{rel_path}:{lineno}: {line.rstrip()}")
                            if len(results) >= max_matches:
                                break
            except (OSError, UnicodeDecodeError):
                continue
            if len(results) >= max_matches:
                break
        if len(results) >= max_matches:
            break

    if not results:
        return "No matches found."

    lines = [f"Found {len(results)} match(es) (showing first {max_matches}):", ""]
    lines.extend(results)
    return "\n".join(lines)


async def run_command_handler(command: str, timeout: int = 30) -> str:
    """Run a shell command and return its output.

    Args:
        command: Shell command to execute.
        timeout: Timeout in seconds (default 30).
    """
    if not _is_safe_command(command):
        return (
            f"Error: Command rejected for safety reasons.\n"
            f"Blocked command: {command}"
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"Error running command: {e}"

    output = result.stdout or result.stderr or "(no output)"
    if result.returncode != 0:
        output = f"(exit code {result.returncode})\n{output}"

    # Truncate to 2000 characters
    if len(output) > 2000:
        output = output[:2000] + "\n... (truncated to 2000 chars)"

    return output


async def list_files_handler(path: str = ".") -> str:
    """List directory contents.

    Args:
        path: Directory path to list (default '.').
    """
    try:
        entries = os.listdir(path)
    except FileNotFoundError:
        return f"Error: Directory not found: {path}"
    except NotADirectoryError:
        return f"Error: Not a directory: {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error listing directory '{path}': {e}"

    entries.sort()

    lines = [f"Contents of {os.path.abspath(path)}:", ""]
    for entry in entries:
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            lines.append(f"  {entry}/")
        elif os.path.islink(full):
            lines.append(f"  {entry}@")
        else:
            lines.append(f"  {entry}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, Any] = {
    "read_file": read_file_handler,
    "glob_files": glob_files_handler,
    "grep_files": grep_files_handler,
    "run_command": run_command_handler,
    "list_files": list_files_handler,
}

# ---------------------------------------------------------------------------
# OpenAI-compatible tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern (e.g. '**/*.py')",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to search for (supports ** recursive wildcard)"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search file contents by regex pattern. Supports filtering by file glob.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regular expression to search for in file contents"
                    },
                    "include": {
                        "type": "string",
                        "description": "Glob pattern to filter which files to search (default: '*')",
                        "default": "*"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return its output. Destructive commands are blocked for safety.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List directory contents with type indicators (/ for directories, @ for symlinks)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: '.')",
                        "default": "."
                    }
                },
                "required": []
            }
        }
    },
]
