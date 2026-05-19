"""Project management: open, create, save, and inspect Aseprite sprites."""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpriteInfo:
    """Metadata about a loaded sprite."""

    path: str
    width: int = 0
    height: int = 0
    color_mode: str = "rgba"
    frames: int = 0
    layers: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    slices: list = field(default_factory=list)
    palette_entries: int = 0


class Project:
    """Manages a single Aseprite project/sprite file."""

    def __init__(self, aseprite_bin: str = "aseprite"):
        self._aseprite = aseprite_bin
        self._sprite: Optional[SpriteInfo] = None
        self._dry_run = False

    @property
    def sprite(self) -> Optional[SpriteInfo]:
        return self._sprite

    def _run(self, args: list, capture: bool = True) -> subprocess.CompletedProcess:
        """Run an aseprite command."""
        if self._dry_run:
            return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")
        result = subprocess.run(
            [self._aseprite, "-b"] + args,
            capture_output=capture,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 and result.stderr:
            raise RuntimeError(result.stderr.strip())
        return result

    def open(self, path: str) -> SpriteInfo:
        """Open a sprite file and return its info."""
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Sprite file not found: {abs_path}")

        info = self._gather_info(abs_path)
        self._sprite = info
        return info

    def create(self, path: str, width: int, height: int,
               color_mode: str = "rgba", bg_color: str = "transparent") -> SpriteInfo:
        """Create a new sprite file via Lua scripting."""
        from cli_anything.aseprite.core.script import ScriptRunner

        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)

        color_modes = {"rgba": "rgb", "grayscale": "grayscale", "indexed": "indexed"}
        cm = color_modes.get(color_mode, "rgb")
        safe_path = abs_path.replace("\\", "/")

        runner = ScriptRunner(self._aseprite)
        lua = (
            f'app.command.NewFile{{ width={width}, height={height}, colorMode="{cm}" }}\n'
            f'local spr = app.sprites[1]\n'
            f'spr:saveCopyAs("{safe_path}")\n'
        )
        result = runner.run_inline(lua)
        if result["returncode"] != 0:
            raise RuntimeError(f"Failed to create sprite: {result.get('stderr', 'unknown error')}")
        return self.open(abs_path)

    def save(self, path: Optional[str] = None) -> str:
        """Save the current sprite."""
        if self._sprite is None:
            raise RuntimeError("No sprite loaded")
        out = path or self._sprite.path
        self._run([self._sprite.path, "--save-as", out])
        if path:
            self._sprite.path = out
        return self._sprite.path

    def save_as(self, path: str) -> str:
        """Save sprite to a new path."""
        return self.save(path)

    def info(self, path: Optional[str] = None) -> SpriteInfo:
        """Return sprite info for a file or the current project."""
        target = path or (self._sprite.path if self._sprite else None)
        if target is None:
            raise RuntimeError("No sprite loaded and no path provided")
        return self._gather_info(target)

    def _gather_info(self, path: str) -> SpriteInfo:
        """Gather sprite metadata via CLI inspection."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            data_path = f.name
        try:
            self._run([
                path,
                "--data", data_path,
                "--list-layers",
                "--list-tags",
                "--list-slices",
                "--sheet", os.devnull if os.name == "posix" else "NUL",
            ])
            with open(data_path, "r") as f:
                data = json.load(f)

            frames_data = data.get("frames", {})
            frame_count = len(frames_data)
            w, h = 0, 0
            if frames_data:
                first = next(iter(frames_data.values()))
                src_size = first.get("sourceSize", {})
                w = src_size.get("w", 0)
                h = src_size.get("h", 0)

            layers = self._extract_layers(data)
            tags = self._extract_tags(data, frames_data)
            slices = self._extract_slices(data)
            palette = self._extract_palette(data)

            return SpriteInfo(
                path=path,
                width=w,
                height=h,
                color_mode="rgba",
                frames=frame_count,
                layers=layers,
                tags=tags,
                slices=slices,
                palette_entries=palette,
            )
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)

    def _extract_layers(self, data: dict) -> list:
        layers = []
        meta = data.get("meta", {})
        layer_data = meta.get("layers", [])
        for layer in layer_data:
            layers.append({
                "name": layer.get("name", ""),
                "group": layer.get("group", ""),
                "opacity": layer.get("opacity", 255),
                "blend_mode": layer.get("blendMode", "normal"),
                "visible": layer.get("visible", True),
            })
        return layers

    def _extract_tags(self, data: dict, frames_data: dict) -> list:
        tags = []
        meta = data.get("meta", {})
        frame_tags = meta.get("frameTags", [])
        for tag in frame_tags:
            tags.append({
                "name": tag.get("name", ""),
                "from": tag.get("from", 0),
                "to": tag.get("to", 0),
                "direction": tag.get("direction", "forward"),
                "color": tag.get("color", ""),
            })
        return tags

    def _extract_slices(self, data: dict) -> list:
        slices = []
        meta = data.get("meta", {})
        slice_data = meta.get("slices", [])
        for slc in slice_data:
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

    def _extract_palette(self, data: dict) -> int:
        """Return palette entry count from metadata."""
        meta = data.get("meta", {})
        # Aseprite doesn't directly include palette in data JSON;
        # palette info would come from a saved .ase file inspection
        return 0

    def _temp_json(self) -> str:
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        name = f.name
        f.close()
        return name

    def _temp_png(self) -> str:
        f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        name = f.name
        f.close()
        return name

    def close(self):
        """Release the current sprite."""
        self._sprite = None
