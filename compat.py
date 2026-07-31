"""
Compatibility utilities for Cloudkot.
Centralizes Python version compatibility shims.
"""

# tomllib/tomli compatibility
# Python 3.11+ has tomllib in stdlib, earlier versions need tomli
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

__all__ = ["tomllib"]
