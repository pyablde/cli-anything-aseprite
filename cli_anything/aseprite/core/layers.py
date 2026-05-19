"""Layer management: inspect and manipulate sprite layers."""

import json
import os
import subprocess
import tempfile
from typing import Optional


class Layers:
    """Inspect and query sprite layers via CLI."""

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

    def list(self, sprite_path: str, hierarchy: bool = False) -> list:
        """List layers in a sprite."""
        flag = "--list-layer-hierarchy" if hierarchy else "--list-layers"
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            data_path = f.name
        try:
            self._run([sprite_path, flag, "--data", data_path,
                       "--sheet", os.devnull if os.name == "posix" else "NUL"])
            with open(data_path, "r") as f:
                data = json.load(f)
            layers = []
            meta = data.get("meta", {})
            for layer in meta.get("layers", []):
                entry = {
                    "name": layer.get("name", ""),
                    "group": layer.get("group", ""),
                    "opacity": layer.get("opacity", 255),
                    "blend_mode": layer.get("blendMode", "normal"),
                    "visible": layer.get("visible", True),
                }
                layers.append(entry)
            return layers
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)

    def list_names(self, sprite_path: str) -> list:
        """Return just layer names."""
        return [layer["name"] for layer in self.list(sprite_path)]
