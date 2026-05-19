"""Script runner: execute Lua scripts against sprites."""

import json
import os
import subprocess
import tempfile
from typing import Optional


class ScriptRunner:
    """Execute Aseprite Lua scripts and capture results."""

    def __init__(self, aseprite_bin: str = "aseprite"):
        self._aseprite = aseprite_bin
        self._dry_run = False

    def run(self, script_path: str, sprite_path: Optional[str] = None,
            params: Optional[dict] = None) -> dict:
        """Run a Lua script, optionally on a sprite file.

        If sprite_path is None, the script runs standalone (for creating
        new sprites from scratch via app.command.NewFile).

        Returns stdout captured as text and parsed JSON if possible.
        """
        args = []
        if sprite_path:
            args.append(sprite_path)
        args.extend(["--script", script_path])
        if params:
            for key, value in params.items():
                args.extend(["--script-param", f"{key}={value}"])

        if self._dry_run:
            return {"stdout": "", "stderr": "", "returncode": 0, "dry_run": True}

        result = subprocess.run(
            [self._aseprite, "-b"] + args,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = {"stdout": result.stdout, "stderr": result.stderr,
                  "returncode": result.returncode}
        if result.stdout.strip():
            try:
                output["parsed"] = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                pass
        return output

    def run_inline(self, lua_code: str, sprite_path: Optional[str] = None,
                   params: Optional[dict] = None) -> dict:
        """Run inline Lua code by writing it to a temp script file first.

        sprite_path can be None for standalone scripts that create new sprites.
        """
        with tempfile.NamedTemporaryFile(suffix=".lua", mode="w",
                                         delete=False) as f:
            f.write(lua_code)
            script_path = f.name
        try:
            return self.run(script_path, sprite_path, params)
        finally:
            os.unlink(script_path)
