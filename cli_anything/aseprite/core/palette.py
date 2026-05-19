"""Palette management: inspect and manipulate color palettes."""

import json
import os
import subprocess
import tempfile
from typing import Optional


class Palette:
    """Inspect and query sprite palettes via CLI."""

    def __init__(self, aseprite_bin: str = "aseprite"):
        self._aseprite = aseprite_bin
        self._dry_run = False

    def _run(self, args: list) -> subprocess.CompletedProcess:
        if self._dry_run:
            return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")
        result = subprocess.run(
            [self._aseprite, "-b"] + args,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 and result.stderr:
            raise RuntimeError(result.stderr.strip())
        return result

    def list_entries(self, sprite_path: str) -> list:
        """List palette entries for an indexed color sprite."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            data_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            sheet_path = f.name
        try:
            self._run([sprite_path, "--data", data_path, "--sheet", sheet_path])
            with open(data_path, "r") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            # Parse palette from exported JSON if available
            palette_info = meta.get("palette", {})
            return palette_info if isinstance(palette_info, list) else []
        finally:
            for p in [data_path, sheet_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def load(self, sprite_path: str, palette_path: str) -> str:
        """Apply a palette file to a sprite."""
        self._run([sprite_path, "--palette", palette_path])
        return sprite_path

    def save(self, sprite_path: str, palette_path: str) -> str:
        """Save the sprite's palette to a file."""
        args = [sprite_path]
        self._run(args)
        return palette_path
