"""Export module: sprite sheet and image export."""

import json
import os
import subprocess
import tempfile
from typing import Optional


class Exporter:
    """Handles Aseprite sprite sheet and file export."""

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
            timeout=300,
        )
        if result.returncode != 0 and result.stderr:
            raise RuntimeError(result.stderr.strip())
        return result

    def export_sprite_sheet(self, sprite_path: str, output_sheet: str,
                            output_data: Optional[str] = None,
                            **kwargs) -> dict:
        """Export a sprite as a sprite sheet.

        Args:
            sprite_path: Path to the input .ase/.aseprite file
            output_sheet: Path for the output sprite sheet PNG
            output_data: Path for JSON metadata output
            **kwargs: Additional export options matching aseprite CLI flags

        Returns:
            dict with output paths and metadata
        """
        args = [sprite_path]
        args.extend(["--sheet", output_sheet])

        if output_data:
            args.extend(["--data", output_data])

        for key, value in kwargs.items():
            flag = "--" + key.replace("_", "-")
            if value is True:
                args.append(flag)
            elif value is not False and value is not None:
                args.extend([flag, str(value)])

        self._run(args)

        result = {"sheet": output_sheet}
        if output_data and os.path.exists(output_data):
            with open(output_data, "r") as f:
                result["data"] = json.load(f)
        return result

    def export_frame(self, sprite_path: str, output_path: str,
                     frame: int = 0, layer: Optional[str] = None) -> str:
        """Export a single frame as an image."""
        args = [sprite_path, "--save-as", output_path]
        if frame > 0:
            args.extend(["--frame-range", f"{frame},{frame}"])
        if layer:
            args.extend(["--layer", layer])
        self._run(args)
        return output_path

    def export_gif(self, sprite_path: str, output_path: str,
                   **kwargs) -> str:
        """Export as animated GIF."""
        args = [sprite_path, "--save-as", output_path]
        for key, value in kwargs.items():
            flag = "--" + key.replace("_", "-")
            if value is True:
                args.append(flag)
            elif value is not False and value is not None:
                args.extend([flag, str(value)])
        self._run(args)
        return output_path

    def export_tileset(self, sprite_path: str, output_sheet: str,
                       output_data: Optional[str] = None) -> dict:
        """Export a tileset as a sprite sheet."""
        args = [sprite_path, "--export-tileset", "--sheet", output_sheet]
        if output_data:
            args.extend(["--data", output_data])
        self._run(args)
        result = {"sheet": output_sheet}
        if output_data and os.path.exists(output_data):
            with open(output_data, "r") as f:
                result["data"] = json.load(f)
        return result
