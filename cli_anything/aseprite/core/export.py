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

    @staticmethod
    def _build_args(kwargs: dict) -> list:
        """Convert a kwargs dict to Aseprite CLI flags.

        Underscores are converted to dashes. Bool True values become bare
        flags. Non-bool values become --key value pairs. Special keys like
        'crop' that take a tuple/list are joined with commas.
        """
        args = []
        for key, value in kwargs.items():
            flag = "--" + key.replace("_", "-")
            if value is True:
                args.append(flag)
            elif value is not False and value is not None:
                if isinstance(value, (list, tuple)):
                    args.extend([flag, ",".join(str(v) for v in value)])
                else:
                    args.extend([flag, str(value)])
        return args

    # ── sprite sheet ────────────────────────────────────────────────

    def export_sprite_sheet(self, sprite_path: str, output_sheet: str,
                            output_data: Optional[str] = None,
                            **kwargs) -> dict:
        """Export a sprite as a sprite sheet.

        Args:
            sprite_path: Path to the input .ase/.aseprite file
            output_sheet: Path for the output sprite sheet PNG
            output_data: Path for JSON metadata output
            **kwargs: Additional export options matching Aseprite CLI flags.
                      Supports: layer, split_layers, split_tags, split_slices,
                      split_grid, all_layers, ignore_layer, tag, frame_range,
                      frame_tag, sheet_type, sheet_width, sheet_height,
                      scale, trim, trim_sprite, crop, extrude,
                      border_padding, inner_padding, shape_padding,
                      merge_duplicates, ignore_empty, oneframe,
                      color_mode, pixel_format, dpi, new_power_of_two_size,
                      filename_format

        Returns:
            dict with output paths and metadata
        """
        args = [sprite_path]
        args.extend(["--sheet", output_sheet])

        if output_data:
            args.extend(["--data", output_data])

        args.extend(self._build_args(kwargs))
        self._run(args)

        result = {"sheet": output_sheet}
        if output_data and os.path.exists(output_data):
            with open(output_data, "r") as f:
                result["data"] = json.load(f)
        return result

    # ── single frame ─────────────────────────────────────────────────

    def export_frame(self, sprite_path: str, output_path: str,
                     frame: int = 0, layer: Optional[str] = None,
                     **kwargs) -> str:
        """Export a single frame as an image.

        Additional kwargs are passed as Aseprite CLI flags (e.g. scale,
        trim, crop, color_mode, dpi, pixel_format, tag, frame_tag,
        oneframe, all_layers, ignore_layer).
        """
        args = [sprite_path, "--save-as", output_path]
        if frame > 0:
            args.extend(["--frame-range", f"{frame},{frame}"])
        if layer:
            args.extend(["--layer", layer])
        args.extend(self._build_args(kwargs))
        self._run(args)
        return output_path

    # ── animated GIF ─────────────────────────────────────────────────

    def export_gif(self, sprite_path: str, output_path: str,
                   **kwargs) -> str:
        """Export as animated GIF.

        Additional kwargs are passed as Aseprite CLI flags (e.g. scale,
        frame_range, tag, frame_tag, color_mode, dpi, oneframe,
        all_layers, ignore_layer).
        """
        args = [sprite_path, "--save-as", output_path]
        args.extend(self._build_args(kwargs))
        self._run(args)
        return output_path

    # ── tileset ──────────────────────────────────────────────────────

    def export_tileset(self, sprite_path: str, output_sheet: str,
                       output_data: Optional[str] = None,
                       **kwargs) -> dict:
        """Export a tileset as a sprite sheet.

        Additional kwargs are passed as Aseprite CLI flags (e.g. scale,
        border_padding, inner_padding, trim, extrude, merge_duplicates,
        ignore_empty, all_layers, ignore_layer).
        """
        args = [sprite_path, "--export-tileset", "--sheet", output_sheet]
        if output_data:
            args.extend(["--data", output_data])
        args.extend(self._build_args(kwargs))
        self._run(args)
        result = {"sheet": output_sheet}
        if output_data and os.path.exists(output_data):
            with open(output_data, "r") as f:
                result["data"] = json.load(f)
        return result
