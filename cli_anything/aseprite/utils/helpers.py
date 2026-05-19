"""Utility helpers for JSON output, path resolution, and error formatting."""

import json
import sys
from functools import wraps
from typing import Any, Optional


class JSONOutput:
    """Mixin-like helper for JSON-formatted output."""

    @staticmethod
    def format(obj: Any) -> str:
        """Format any object as indented JSON."""
        return json.dumps(obj, indent=2, default=str)

    @staticmethod
    def print(data: Any, file=None):
        """Print JSON to stdout."""
        print(JSONOutput.format(data), file=file or sys.stdout)


def json_output(func):
    """Decorator: if --json flag is set, print result as JSON."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        json_mode = kwargs.pop("_json", False)
        result = func(*args, **kwargs)
        if json_mode and result is not None:
            JSONOutput.print(result)
            return None
        elif result is not None and isinstance(result, (list, dict)):
            JSONOutput.print(result)
            return None
        return result
    return wrapper


def resolve_aseprite_bin(override: Optional[str] = None) -> str:
    """Resolve the aseprite binary path."""
    if override:
        return override
    import shutil
    found = shutil.which("aseprite")
    if found:
        return found
    raise RuntimeError(
        "Aseprite binary not found in PATH. Please install Aseprite or "
        "provide the path via --aseprite-bin."
    )
