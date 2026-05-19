"""Tag and slice inspection."""

import json
import os
import subprocess
import tempfile
from typing import Optional


class Tags:
    """Inspect frame tags in a sprite."""

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

    def list(self, sprite_path: str) -> list:
        """List frame tags in a sprite."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            data_path = f.name
        try:
            self._run([sprite_path, "--list-tags", "--data", data_path,
                       "--sheet", os.devnull if os.name == "posix" else "NUL"])
            with open(data_path, "r") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            tags = []
            for tag in meta.get("frameTags", []):
                tags.append({
                    "name": tag.get("name", ""),
                    "from": tag.get("from", 0),
                    "to": tag.get("to", 0),
                    "direction": tag.get("direction", "forward"),
                    "color": tag.get("color", ""),
                })
            return tags
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)


class Slices:
    """Inspect slices in a sprite."""

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

    def list(self, sprite_path: str) -> list:
        """List slices in a sprite."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            data_path = f.name
        try:
            self._run([sprite_path, "--list-slices", "--data", data_path,
                       "--sheet", os.devnull if os.name == "posix" else "NUL"])
            with open(data_path, "r") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            slices = []
            for slc in meta.get("slices", []):
                keys = []
                for k in slc.get("keys", []):
                    bounds = k.get("bounds", {})
                    keys.append({
                        "frame": k.get("frame", 0),
                        "x": bounds.get("x", 0),
                        "y": bounds.get("y", 0),
                        "w": bounds.get("w", 0),
                        "h": bounds.get("h", 0),
                    })
                slices.append({
                    "name": slc.get("name", ""),
                    "color": slc.get("color", ""),
                    "keys": keys,
                })
            return slices
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)
