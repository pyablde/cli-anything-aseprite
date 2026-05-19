"""cli-anything-aseprite: Stateful CLI harness for Aseprite.

Usage:
  cli-anything-aseprite open <file>              Open a sprite file
  cli-anything-aseprite info [file]              Get sprite metadata
  cli-anything-aseprite layers list <file>       List layers
  cli-anything-aseprite layers add <file> ...    Add/delete/rename layers
  cli-anything-aseprite tags list <file>         List/add/delete frame tags
  cli-anything-aseprite slices list <file>       List/add/delete slices
  cli-anything-aseprite export sheet <file> ...  Export sprite sheet
  cli-anything-aseprite export frame <file> ...  Export single frame
  cli-anything-aseprite export gif <file> ...    Export animated GIF
  cli-anything-aseprite export tileset ...       Export tileset
  cli-anything-aseprite script run <file> <lua>  Run Lua script
  cli-anything-aseprite shell [file]            Interactive Lua console
  cli-anything-aseprite draw new <file> W H      Create new canvas
  cli-anything-aseprite draw rect <file> ...     Draw shapes (useTool API)
  cli-anything-aseprite edit crop <file> ...     Crop/resize/flatten/flip
  cli-anything-aseprite frames add <file> ...    Add/delete frames
  cli-anything-aseprite color get/set            Manage fg/bg colors
  cli-anything-aseprite select all/none <file>   Manage selection
  cli-anything-aseprite command <ID> ...         Run Aseprite built-in command
  cli-anything-aseprite repl                     Start REPL mode
"""

import json
import os
import sys
from typing import Optional

import click

from cli_anything.aseprite.core.project import Project, SpriteInfo
from cli_anything.aseprite.core.session import Session
from cli_anything.aseprite.core.export import Exporter
from cli_anything.aseprite.core.layers import Layers
from cli_anything.aseprite.core.palette import Palette
from cli_anything.aseprite.core.tags_slices import Tags, Slices
from cli_anything.aseprite.core.script import ScriptRunner
from cli_anything.aseprite.core.draw import Draw
from cli_anything.aseprite.utils.helpers import JSONOutput, resolve_aseprite_bin


pass_session = click.make_pass_decorator(Session, ensure=True)


def _get_session() -> Session:
    """Create or retrieve the global session."""
    return _global_session


_global_session: Optional[Session] = None


@click.group()
@click.option("--aseprite-bin", envvar="ASEPRITE_BIN",
              help="Path to aseprite binary")
@click.option("--json", "json_mode", is_flag=True,
              help="Output results as JSON")
@click.option("--dry-run", is_flag=True,
              help="Preview commands without executing")
@click.option("--state-file", help="Session state file for persistence")
@click.pass_context
def cli(ctx, aseprite_bin, json_mode, dry_run, state_file):
    """cli-anything-aseprite: Stateful CLI for Aseprite pixel art editor."""
    global _global_session
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_mode
    ctx.obj["dry_run"] = dry_run
    try:
        bin_path = resolve_aseprite_bin(aseprite_bin)
    except RuntimeError as e:
        if dry_run:
            bin_path = "aseprite"
        else:
            click.echo(str(e), err=True)
            sys.exit(1)
    ctx.obj["aseprite_bin"] = bin_path

    _global_session = Session(
        aseprite_bin=bin_path,
        state_file=state_file or os.path.join(
            click.get_app_dir("cli-anything-aseprite"), "session.json"),
        auto_save=not dry_run,
        dry_run=dry_run,
    )


# ── open command ──────────────────────────────────────────────────


@cli.command()
@click.argument("path")
@click.pass_context
def open_cmd(ctx, path):
    """Open a sprite file and display its info."""
    session = _global_session
    info = session.open(path)
    if ctx.obj["json"]:
        JSONOutput.print({
            "path": info.path,
            "width": info.width,
            "height": info.height,
            "color_mode": info.color_mode,
            "frames": info.frames,
            "layer_count": len(info.layers),
            "layers": info.layers,
            "tag_count": len(info.tags),
            "tags": info.tags,
            "slice_count": len(info.slices),
            "slices": info.slices,
        })
    else:
        click.echo(f"Sprite: {info.path}")
        click.echo(f"  Size: {info.width}x{info.height}")
        click.echo(f"  Color mode: {info.color_mode}")
        click.echo(f"  Frames: {info.frames}")
        click.echo(f"  Layers: {len(info.layers)}")
        for layer in info.layers:
            prefix = "    "
            if layer.get("group"):
                prefix = f"    [{layer['group']}] "
            state = "*" if layer.get("visible") else "-"
            click.echo(f"  {state} {prefix}{layer['name']}")
        if info.tags:
            click.echo(f"  Tags: {len(info.tags)}")
            for tag in info.tags:
                click.echo(f"    [{tag['from']}-{tag['to']}] {tag['name']} "
                           f"({tag['direction']})")
        if info.slices:
            click.echo(f"  Slices: {len(info.slices)}")
            for slc in info.slices:
                click.echo(f"    {slc['name']}")


# ── info command ──────────────────────────────────────────────────


@cli.command()
@click.argument("path", required=False)
@click.pass_context
def info(ctx, path):
    """Show sprite metadata."""
    session = _global_session
    try:
        info = session.project.info(path) if path else session.active_sprite
        if info is None:
            click.echo("No sprite loaded.", err=True)
            return
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        return

    result = {
        "path": info.path,
        "width": info.width,
        "height": info.height,
        "frames": info.frames,
        "color_mode": info.color_mode,
        "layers": info.layers,
        "tags": info.tags,
        "slices": info.slices,
    }
    if ctx.obj["json"]:
        JSONOutput.print(result)
    else:
        click.echo(f"Path:     {info.path}")
        click.echo(f"Size:     {info.width}x{info.height}")
        click.echo(f"Frames:   {info.frames}")
        click.echo(f"Mode:     {info.color_mode}")
        click.echo(f"Layers:   {len(info.layers)}")
        click.echo(f"Tags:     {len(info.tags)}")
        click.echo(f"Slices:   {len(info.slices)}")


# ── layers group ──────────────────────────────────────────────────


@cli.group()
def layers():
    """Inspect and manage sprite layers."""


@layers.command("list")
@click.argument("path")
@click.option("--hierarchy", is_flag=True, help="Show layer hierarchy with groups")
@click.pass_context
def layers_list(ctx, path, hierarchy):
    """List layers in a sprite."""
    lyr = Layers(_global_session.project._aseprite)
    result = lyr.list(path, hierarchy=hierarchy)
    if ctx.obj["json"]:
        JSONOutput.print({"path": path, "layers": result,
                          "total": len(result)})
    else:
        for layer in result:
            prefix = ""
            if layer.get("group"):
                prefix = f"[{layer['group']}] "
            state = "+" if layer.get("visible") else "-"
            opacity = layer.get("opacity", 255)
            click.echo(f"  {state} {prefix}{layer['name']} "
                       f"(opacity={opacity}, blend={layer.get('blend_mode', 'normal')})")


# ── tags group ────────────────────────────────────────────────────


@cli.group()
def tags():
    """Inspect and manage frame tags."""


@tags.command("list")
@click.argument("path")
@click.pass_context
def tags_list(ctx, path):
    """List frame tags in a sprite."""
    t = Tags(_global_session.project._aseprite)
    result = t.list(path)
    if ctx.obj["json"]:
        JSONOutput.print({"path": path, "tags": result, "total": len(result)})
    else:
        for tag in result:
            click.echo(f"  [{tag['from']:>4} -> {tag['to']:<4}] {tag['name']} "
                       f"(dir={tag['direction']}, color={tag.get('color', '')})")


# ── slices group ──────────────────────────────────────────────────


@cli.group()
def slices():
    """Inspect and manage slices."""


@slices.command("list")
@click.argument("path")
@click.pass_context
def slices_list(ctx, path):
    """List slices in a sprite."""
    s = Slices(_global_session.project._aseprite)
    result = s.list(path)
    if ctx.obj["json"]:
        JSONOutput.print({"path": path, "slices": result, "total": len(result)})
    else:
        for slc in result:
            keys_info = ", ".join(
                f"f{k['frame']}:{k['w']}x{k['h']}@{k['x']},{k['y']}"
                for k in slc.get("keys", [])
            )
            click.echo(f"  {slc['name']}: {keys_info}")


# ── palette group ─────────────────────────────────────────────────


@cli.group()
def palette():
    """Inspect and manage palettes."""


@palette.command("list")
@click.argument("path")
@click.pass_context
def palette_list(ctx, path):
    """List palette entries in a sprite."""
    p = Palette(_global_session.project._aseprite)
    result = p.list_entries(path)
    if ctx.obj["json"]:
        JSONOutput.print({"path": path, "palette": result,
                          "total": len(result) if isinstance(result, list) else 0})
    else:
        if isinstance(result, list):
            for i, entry in enumerate(result):
                click.echo(f"  [{i}] {entry}")
        else:
            click.echo(f"  {result}")


@palette.command("load")
@click.argument("path")
@click.argument("palette_file")
@click.pass_context
def palette_load(ctx, path, palette_file):
    """Load a palette file and apply it to a sprite."""
    p = Palette(_global_session.project._aseprite)
    p.load(path, palette_file)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": path,
                          "palette": palette_file})
    else:
        click.echo(f"Loaded palette from {palette_file} into {path}")


# ── export group ──────────────────────────────────────────────────


@cli.group()
def export():
    """Export sprites, sprite sheets, frames, and tilesets."""


@export.command("sheet")
@click.argument("path")
@click.option("--output-sheet", required=True, help="Output sprite sheet PNG")
@click.option("--output-data", help="Output JSON metadata file")
@click.option("--layer", help="Include only this layer")
@click.option("--ignore-layer", help="Exclude a specific layer")
@click.option("--all-layers", is_flag=True, help="Export all layers (use with --split-layers)")
@click.option("--split-layers", is_flag=True, help="Export layers separately")
@click.option("--split-tags", is_flag=True, help="Export tags separately")
@click.option("--split-slices", is_flag=True, help="Export slices separately")
@click.option("--split-grid", is_flag=True, help="Export by grid cells")
@click.option("--tag", "--frame-tag", help="Export only frames in this tag")
@click.option("--frame-range", help="Export frame range (from,to)")
@click.option("--sheet-type", help="Sheet layout: horizontal, vertical, rows, columns, packed")
@click.option("--sheet-width", type=int, help="Fixed sheet width in pixels")
@click.option("--sheet-height", type=int, help="Fixed sheet height in pixels")
@click.option("--scale", type=float, help="Scale factor (e.g., 2.0)")
@click.option("--dpi", type=float, help="DPI for the output file")
@click.option("--trim", is_flag=True, help="Trim frames in sheet")
@click.option("--trim-sprite", is_flag=True, help="Trim whole sprite")
@click.option("--crop", help="Crop to rectangle: x,y,w,h")
@click.option("--border-padding", type=int, help="Padding on texture border")
@click.option("--inner-padding", type=int, help="Padding between frames in sheet")
@click.option("--extrude", is_flag=True, help="Extrude edges by 1px")
@click.option("--merge-duplicates", is_flag=True, help="Merge identical frames")
@click.option("--ignore-empty", is_flag=True, help="Skip empty cels/frames")
@click.option("--oneframe", is_flag=True, help="Export one frame only")
@click.option("--color-mode", help="Convert color mode: rgb, indexed, grayscale")
@click.option("--pixel-format", help="Pixel format (e.g. RGBA8888)")
@click.option("--new-power-of-two-size", is_flag=True, help="Force power-of-2 sheet dimensions")
@click.option("--filename-format", help="Filename template: {layer} {frame} {group} {tag}")
@click.pass_context
def export_sheet(ctx, path, output_sheet, output_data, **kwargs):
    """Export a sprite as a sprite sheet with full CLI options."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)

    # Build kwargs, filtering out Nones and Falses for flags not set
    filtered = {}
    for k, v in kwargs.items():
        if k.startswith("output_"):
            continue
        if v is True or (v is not None and v is not False):
            filtered[k] = v

    result = exp.export_sprite_sheet(path, output_sheet, output_data, **filtered)
    if ctx.obj["json"]:
        summary = {"sheet": result["sheet"]}
        if "data" in result:
            frames = result["data"].get("frames", {})
            summary["frame_count"] = len(frames)
            summary["frames"] = list(frames.keys())
        JSONOutput.print(summary)
    else:
        click.echo(f"Sprite sheet exported to: {result['sheet']}")
        if "data" in result:
            click.echo(f"Metadata frames: {len(result['data'].get('frames', {}))}")


@export.command("frame")
@click.argument("path")
@click.option("--output", required=True, help="Output image file")
@click.option("--frame", type=int, default=0, help="Frame number to export")
@click.option("--layer", help="Layer to export")
@click.option("--tag", "--frame-tag", help="Export frame from tag")
@click.option("--scale", type=float, help="Scale factor (e.g., 2.0)")
@click.option("--trim", is_flag=True, help="Trim transparent borders")
@click.option("--crop", help="Crop to rectangle: x,y,w,h")
@click.option("--dpi", type=float, help="DPI for output file")
@click.option("--pixel-format", help="Pixel format (e.g. RGBA8888)")
@click.option("--color-mode", help="Convert color mode: rgb, indexed, grayscale")
@click.option("--oneframe", is_flag=True, help="Export single frame (useful with --save-as)")
@click.option("--all-layers", is_flag=True, help="Include all layers")
@click.option("--ignore-layer", help="Exclude a specific layer")
@click.pass_context
def export_frame_cmd(ctx, path, output, frame, layer, **kwargs):
    """Export a single frame as an image with full CLI options."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    filtered = {}
    for k, v in kwargs.items():
        if v is True or (v is not None and v is not False):
            filtered[k] = v
    result = exp.export_frame(path, output, frame=frame, layer=layer, **filtered)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "output": result, "frame": frame})
    else:
        click.echo(f"Frame {frame} exported to: {result}")


@export.command("gif")
@click.argument("path")
@click.option("--output", required=True, help="Output GIF file")
@click.option("--scale", type=float, help="Scale factor")
@click.option("--tag", "--frame-tag", help="Export only frames in this tag")
@click.option("--frame-range", help="Export frame range (from,to)")
@click.option("--trim", is_flag=True, help="Trim transparent borders")
@click.option("--crop", help="Crop to rectangle: x,y,w,h")
@click.option("--dpi", type=float, help="DPI for output file")
@click.option("--pixel-format", help="Pixel format (e.g. RGBA8888)")
@click.option("--color-mode", help="Convert color mode: rgb, indexed, grayscale")
@click.option("--oneframe", is_flag=True, help="Export single frame only")
@click.option("--all-layers", is_flag=True, help="Include all layers")
@click.option("--ignore-layer", help="Exclude a specific layer")
@click.option("--layer", help="Include only this layer")
@click.pass_context
def export_gif_cmd(ctx, path, output, **kwargs):
    """Export sprite as animated GIF with full CLI options."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    filtered = {}
    for k, v in kwargs.items():
        if v is True or (v is not None and v is not False):
            filtered[k] = v
    result = exp.export_gif(path, output, **filtered)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "output": result})
    else:
        click.echo(f"GIF exported to: {result}")


@export.command("tileset")
@click.argument("path")
@click.option("--output-sheet", required=True, help="Output tileset image")
@click.option("--output-data", help="Output JSON metadata file")
@click.option("--layer", help="Export tiles from a specific layer")
@click.option("--tag", "--frame-tag", help="Export tiles from a specific tag")
@click.option("--scale", type=float, help="Scale factor")
@click.option("--border-padding", type=int, help="Padding around the texture border")
@click.option("--inner-padding", type=int, help="Padding between tiles")
@click.option("--trim", is_flag=True, help="Trim transparent borders")
@click.option("--extrude", is_flag=True, help="Extrude edges by 1px")
@click.option("--merge-duplicates", is_flag=True, help="Merge identical tiles")
@click.option("--ignore-empty", is_flag=True, help="Skip empty tiles")
@click.option("--all-layers", is_flag=True, help="Include all layers")
@click.option("--ignore-layer", help="Exclude a specific layer")
@click.pass_context
def export_tileset(ctx, path, output_sheet, output_data, **kwargs):
    """Export tilesets from visible tilemap layers with full CLI options."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    filtered = {}
    for k, v in kwargs.items():
        if v is True or (v is not None and v is not False):
            filtered[k] = v
    result = exp.export_tileset(path, output_sheet, output_data, **filtered)
    if ctx.obj["json"]:
        summary = {"sheet": result["sheet"]}
        if "data" in result:
            summary["tiles"] = len(result["data"].get("frames", {}))
        JSONOutput.print(summary)
    else:
        click.echo(f"Tileset exported to: {result['sheet']}")


# ── script group ──────────────────────────────────────────────────


@cli.group()
def script():
    """Run Lua scripts against sprites."""


@script.command("run")
@click.argument("script_path")
@click.argument("path", required=False)
@click.option("--param", "-p", multiple=True, help="Script parameters (key=value)")
@click.pass_context
def script_run(ctx, script_path, path, param):
    """Run a Lua script, optionally on a sprite file."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    params = {}
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v
    result = runner.run(script_path, sprite_path=path, params=params)
    if ctx.obj["json"]:
        JSONOutput.print(result)
    else:
        click.echo(result.get("stdout", ""))
        if result.get("stderr"):
            click.echo(result["stderr"], err=True)


@script.command("eval")
@click.argument("lua_code")
@click.argument("path", required=False)
@click.option("--param", "-p", multiple=True, help="Script parameters (key=value)")
@click.pass_context
def script_eval(ctx, lua_code, path, param):
    """Evaluate inline Lua code, optionally against a sprite file."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    params = {}
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v
    result = runner.run_inline(lua_code, sprite_path=path, params=params)
    if ctx.obj["json"]:
        JSONOutput.print(result)
    else:
        click.echo(result.get("stdout", ""))
        if result.get("stderr"):
            click.echo(result["stderr"], err=True)


# ── session group ─────────────────────────────────────────────────


@cli.group()
def session():
    """Manage the interactive session."""


@session.command("state")
@click.pass_context
def session_state(ctx):
    """Show current session state."""
    s = _global_session
    if ctx.obj["json"]:
        JSONOutput.print(s.to_dict())
    else:
        click.echo(f"Active sprite: {s.state.active_sprite or 'none'}")
        click.echo(f"Open sprites: {len(s.state.sprites)}")
        for path in s.state.sprites:
            marker = " *" if path == s.state.active_sprite else ""
            click.echo(f"  {path}{marker}")


@session.command("focus")
@click.argument("path")
@click.pass_context
def session_focus(ctx, path):
    """Set the active sprite in the session."""
    s = _global_session
    s.focus(path)
    if ctx.obj["json"]:
        JSONOutput.print({"active_sprite": path, "status": "ok"})
    else:
        click.echo(f"Focused: {path}")


@session.command("close")
@click.argument("path", required=False)
@click.pass_context
def session_close(ctx, path):
    """Close a sprite in the session."""
    s = _global_session
    s.close(path)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok",
                          "active_sprite": s.state.active_sprite})
    else:
        click.echo(f"Closed sprite: {path or '(active)'}")


# ── shell command ──────────────────────────────────────────────────


@cli.command()
@click.argument("path", required=False)
@click.pass_context
def shell(ctx, path):
    """Start an interactive Aseprite Lua shell (--shell mode).

    Opens Aseprite's built-in interactive Lua console. If PATH is
    provided, the sprite is loaded first and available as
    app.sprites[1] in the Lua environment.
    """
    from cli_anything.aseprite.core.script import ScriptRunner
    import shutil

    aseprite_bin = _global_session.project._aseprite
    if not shutil.which(aseprite_bin) and aseprite_bin != "aseprite":
        aseprite_bin = shutil.which("aseprite")
    if not aseprite_bin:
        click.echo("Aseprite binary not found in PATH.", err=True)
        return

    if ctx.obj.get("dry_run"):
        click.echo(f"[dry-run] Would start: {aseprite_bin} -b --shell"
                   + (f" {path}" if path else ""))
        return

    import subprocess
    args = [aseprite_bin, "-b", "--shell"]
    if path:
        args.insert(2, os.path.abspath(path))
    click.echo(f"Starting Aseprite Lua shell (type Ctrl+D to exit)...")
    subprocess.run(args)


# ── repl command ───────────────────────────────────────────────────


@cli.command()
@click.option("--prompt", default="aseprite> ", help="REPL prompt string")
@click.pass_context
def repl(ctx, prompt):
    """Start an interactive REPL session."""
    s = _global_session
    click.echo(f"cli-anything-aseprite REPL (type 'help' for commands, 'quit' to exit)")
    click.echo(f"Aseprite binary: {s._aseprite}")

    commands = {
        "help": "Show this help",
        "open <file>": "Open a sprite file",
        "info [file]": "Show sprite info",
        "layers [file]": "List layers",
        "tags [file]": "List tags",
        "slices [file]": "List slices",
        "palette [file]": "List palette entries",
        "close [file]": "Close a sprite from session",
        "focus <file>": "Set active sprite",
        "state": "Show session state",
        "export sheet <file> --output-sheet <png> [...]": "Export sprite sheet",
        "export frame <file> --output <png> [...]": "Export single frame",
        "export gif <file> --output <gif> [...]": "Export animated GIF",
        "export tileset <file> --output-sheet <png> [...]": "Export tileset",
        "run <file> <script>": "Run Lua script",
        "eval <file> <code>": "Eval Lua code",
        "shell [file]": "Start Aseprite Lua interactive shell",
        "draw new <file> W H": "Create new canvas",
        "draw rect <file> X Y W H --color r,g,b": "Draw filled rectangle",
        "draw circle <file> CX CY R --color r,g,b": "Draw filled circle",
        "draw line <file> X1 Y1 X2 Y2 --color r,g,b": "Draw line",
        "draw fill <file> --color r,g,b": "Fill canvas with color",
        "draw grad <file> --from r,g,b --to r,g,b [--direction h|v]": "Gradient fill",
        "draw ellipse <file> X Y W H --color r,g,b": "Draw ellipse",
        "draw flood-fill <file> X Y --color r,g,b": "Flood fill area",
        "edit crop <file> --width W --height H [--x X --y Y]": "Crop sprite",
        "edit resize <file> --width W --height H": "Resize sprite",
        "edit flatten <file>": "Flatten all layers",
        "edit flip <file> [--horizontal|--vertical]": "Flip sprite",
        "layers add <file> --name NAME": "Add new layer",
        "layers delete <file> <name>": "Delete layer",
        "layers rename <file> <old> <new>": "Rename layer",
        "frames add <file> [--at N] [--empty]": "Add new frame",
        "frames delete <file> <N>": "Delete frame",
        "tags add <file> --name N --from-frame F --to-frame T": "Add frame tag",
        "tags delete <file> <name>": "Delete tag",
        "slices add <file> --name N --width W --height H": "Add slice",
        "slices delete <file> <name>": "Delete slice",
        "command <CommandID> [file] [-p k=v ...]": "Run Aseprite command",
        "color get": "Show fg/bg colors",
        "color set fg|bg r,g,b[,a]": "Set fg/bg color",
        "select all <file>": "Select entire canvas",
        "select none <file>": "Deselect",
        "quit": "Exit REPL",
    }

    while True:
        try:
            line = click.prompt(prompt, prompt_suffix="").strip()
        except (EOFError, click.Abort):
            click.echo()
            break

        if not line:
            continue
        if line in ("quit", "exit", "q"):
            break
        if line == "help":
            click.echo("Available REPL commands:")
            for cmd, desc in commands.items():
                click.echo(f"  {cmd:<50} {desc}")
            continue
        if line == "state":
            s_dict = s.to_dict()
            click.echo(JSONOutput.format(s_dict))
            continue

        # Parse and dispatch simple REPL commands
        parts = line.split()
        cmd_name = parts[0]

        if cmd_name == "open" and len(parts) > 1:
            try:
                info = s.open(parts[1])
                click.echo(f"Opened: {info.path} ({info.width}x{info.height}, "
                           f"{info.frames} frames, {len(info.layers)} layers)")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
        elif cmd_name == "info":
            target = parts[1] if len(parts) > 1 else None
            try:
                info = s.project.info(target) if target else s.active_sprite
                if info:
                    click.echo(f"{info.path}: {info.width}x{info.height}, "
                               f"{info.frames} frames, {len(info.layers)} layers")
                else:
                    click.echo("No sprite loaded.")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
        elif cmd_name == "layers" and len(parts) > 1:
            try:
                lyr = Layers(s._aseprite)
                for layer in lyr.list(parts[1]):
                    state = "+" if layer.get("visible") else "-"
                    click.echo(f"  {state} {layer['name']}")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
        elif cmd_name == "tags" and len(parts) > 1:
            try:
                t = Tags(s._aseprite)
                for tag in t.list(parts[1]):
                    click.echo(f"  [{tag['from']}->{tag['to']}] {tag['name']}")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
        elif cmd_name == "slices" and len(parts) > 1:
            try:
                sl = Slices(s._aseprite)
                for slc in sl.list(parts[1]):
                    click.echo(f"  {slc['name']}")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
        elif cmd_name == "focus" and len(parts) > 1:
            s.focus(parts[1])
            click.echo(f"Focused: {parts[1]}")
        elif cmd_name == "close":
            key = parts[1] if len(parts) > 1 else None
            s.close(key)
            click.echo(f"Closed: {key or '(active)'}")
        else:
            click.echo(f"Unknown command: {cmd_name}. Type 'help' for available commands.")


# ── draw group ────────────────────────────────────────────────────


@cli.group()
def draw():
    """Create and edit pixel art programmatically."""


@draw.command("new")
@click.argument("path")
@click.argument("width", type=int)
@click.argument("height", type=int)
@click.option("--color-mode", default="rgba",
              type=click.Choice(["rgba", "grayscale", "indexed"]))
@click.pass_context
def draw_new(ctx, path, width, height, color_mode):
    """Create a new blank canvas."""
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.new(path, width, height, color_mode)
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "width": width, "height": height})
    else:
        click.echo(f"Created: {os.path.abspath(path)} ({width}x{height})")


@draw.command("fill")
@click.argument("path")
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.pass_context
def draw_fill(ctx, path, color):
    """Fill an entire canvas with a solid color."""
    parts = [int(x.strip()) for x in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.fill(r, g, b, a)
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Filled: {os.path.abspath(path)}")


@draw.command("rect")
@click.argument("path")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.argument("w", type=int)
@click.argument("h", type=int)
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.option("--outline/--fill", default=False, help="Draw outline instead of filled")
@click.pass_context
def draw_rect(ctx, path, x, y, w, h, color, outline):
    """Draw a rectangle (filled by default, use --outline for border only)."""
    parts = [int(c.strip()) for c in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.rect(x, y, w, h, r, g, b, a, fill=not outline)
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Rect drawn: {os.path.abspath(path)}")


@draw.command("circle")
@click.argument("path")
@click.argument("cx", type=int)
@click.argument("cy", type=int)
@click.argument("radius", type=int)
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.option("--outline/--fill", default=False, help="Draw outline instead of filled")
@click.pass_context
def draw_circle(ctx, path, cx, cy, radius, color, outline):
    """Draw a circle (filled by default, use --outline for border only)."""
    parts = [int(c.strip()) for c in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.circle(cx, cy, radius, r, g, b, a, fill=not outline)
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Circle drawn: {os.path.abspath(path)}")


@draw.command("line")
@click.argument("path")
@click.argument("x1", type=int)
@click.argument("y1", type=int)
@click.argument("x2", type=int)
@click.argument("y2", type=int)
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.pass_context
def draw_line(ctx, path, x1, y1, x2, y2, color):
    """Draw a line between two points."""
    parts = [int(c.strip()) for c in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.line(x1, y1, x2, y2, r, g, b, a)
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Line drawn: {os.path.abspath(path)}")


@draw.command("grad")
@click.argument("path")
@click.option("--from-color", "from_c", required=True, help="Start color r,g,b")
@click.option("--to-color", "to_c", required=True, help="End color r,g,b")
@click.option("--direction", type=click.Choice(["h", "v"]), default="h",
              help="Gradient direction: h=horizontal, v=vertical")
@click.pass_context
def draw_grad(ctx, path, from_c, to_c, direction):
    """Fill canvas with a linear gradient."""
    f_parts = [int(x.strip()) for x in from_c.split(",")]
    t_parts = [int(x.strip()) for x in to_c.split(",")]
    fr, fg, fb = f_parts[0], f_parts[1], f_parts[2]
    tr, tg, tb = t_parts[0], t_parts[1], t_parts[2]

    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    if direction == "h":
        d.raw(
            f'for x=0,spr.width-1 do '
            f'local t=x/(spr.width-1); '
            f'local r={fr}+({tr - fr})*t; '
            f'local g={fg}+({tg - fg})*t; '
            f'local b={fb}+({tb - fb})*t; '
            'for y=0,spr.height-1 do img:putPixel(x,y,rgba(r,g,b,255)) end end')
    else:
        d.raw(
            f'for y=0,spr.height-1 do '
            f'local t=y/(spr.height-1); '
            f'local r={fr}+({tr - fr})*t; '
            f'local g={fg}+({tg - fg})*t; '
            f'local b={fb}+({tb - fb})*t; '
            'for x=0,spr.width-1 do img:putPixel(x,y,rgba(r,g,b,255)) end end')
    result = d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Gradient drawn: {os.path.abspath(path)}")


@draw.command("ellipse")
@click.argument("path")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.argument("w", type=int)
@click.argument("h", type=int)
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.option("--outline/--fill", default=False, help="Draw outline instead of filled")
@click.pass_context
def draw_ellipse(ctx, path, x, y, w, h, color, outline):
    """Draw an ellipse within bounding rectangle (x,y,w,h)."""
    parts = [int(c.strip()) for c in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.ellipse(x, y, w, h, r, g, b, a, fill=not outline)
    d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Ellipse drawn: {os.path.abspath(path)}")


@draw.command("flood-fill")
@click.argument("path")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.option("--color", required=True, help="Color as r,g,b or r,g,b,a")
@click.option("--tolerance", type=int, default=0, help="Fill tolerance (0=exact match)")
@click.pass_context
def draw_flood_fill(ctx, path, x, y, color, tolerance):
    """Flood-fill area starting from (x,y)."""
    parts = [int(c.strip()) for c in color.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    d = Draw(_global_session.project._aseprite)
    d._dry_run = ctx.obj.get("dry_run", False)
    d.open(path)
    d.flood_fill(x, y, r, g, b, a, tolerance=tolerance)
    d.save()
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Flood-filled: {os.path.abspath(path)}")


# ── edit group ──────────────────────────────────────────────────────


@cli.group()
def edit():
    """Edit sprites: crop, resize, flatten, flip, etc."""


@edit.command("crop")
@click.argument("path")
@click.option("--x", type=int, default=0, help="Crop origin X")
@click.option("--y", type=int, default=0, help="Crop origin Y")
@click.option("--width", type=int, required=True, help="Crop width")
@click.option("--height", type=int, required=True, help="Crop height")
@click.pass_context
def edit_crop(ctx, path, x, y, width, height):
    """Crop sprite to a rectangle."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr:crop({x}, {y}, {width}, {height})\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "crop failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "crop": {"x": x, "y": y, "width": width, "height": height}})
    else:
        click.echo(f"Cropped {os.path.abspath(path)} to {width}x{height}")


@edit.command("resize")
@click.argument("path")
@click.option("--width", type=int, required=True, help="New width")
@click.option("--height", type=int, required=True, help="New height")
@click.pass_context
def edit_resize(ctx, path, width, height):
    """Resize sprite to new dimensions."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr:resize({width}, {height})\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "resize failed"))
    if ctx.obj["json"]:
        JsonOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "size": {"width": width, "height": height}})
    else:
        click.echo(f"Resized {os.path.abspath(path)} to {width}x{height}")


@edit.command("flatten")
@click.argument("path")
@click.pass_context
def edit_flatten(ctx, path):
    """Flatten all layers into one."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr:flatten()\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "flatten failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Flattened {os.path.abspath(path)}")


@edit.command("flip")
@click.argument("path")
@click.option("--horizontal/--vertical", default=True, help="Flip direction")
@click.pass_context
def edit_flip(ctx, path, horizontal):
    """Flip sprite horizontally or vertically."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    dir_flag = "horizontal=true" if horizontal else "vertical=true"
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr.cels[1].image:flip({{ {dir_flag} }})\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "flip failed"))
    direction = "horizontally" if horizontal else "vertically"
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "direction": direction})
    else:
        click.echo(f"Flipped {os.path.abspath(path)} {direction}")


# ── layers management ───────────────────────────────────────────────


@layers.command("add")
@click.argument("path")
@click.option("--name", default="New Layer", help="Layer name")
@click.pass_context
def layers_add(ctx, path, name):
    """Add a new layer to a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'local layer = spr:newLayer()\n'
        f'layer.name = "{name}"\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "add layer failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "layer": name})
    else:
        click.echo(f"Added layer '{name}' to {os.path.abspath(path)}")


@layers.command("delete")
@click.argument("path")
@click.argument("name")
@click.pass_context
def layers_delete(ctx, path, name):
    """Delete a layer by name from a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr:deleteLayer("{name}")\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "delete layer failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "deleted": name})
    else:
        click.echo(f"Deleted layer '{name}' from {os.path.abspath(path)}")


@layers.command("rename")
@click.argument("path")
@click.argument("old_name")
@click.argument("new_name")
@click.pass_context
def layers_rename(ctx, path, old_name, new_name):
    """Rename a layer in a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'for i, layer in ipairs(spr.layers) do\n'
        f'  if layer.name == "{old_name}" then\n'
        f'    layer.name = "{new_name}"\n'
        f'    break\n'
        f'  end\n'
        f'end\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "rename layer failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "old": old_name, "new": new_name})
    else:
        click.echo(f"Renamed layer '{old_name}' → '{new_name}'")


# ── frames management ───────────────────────────────────────────────


@cli.group()
def frames():
    """Manage animation frames."""


@frames.command("add")
@click.argument("path")
@click.option("--at", "at_frame", type=int, help="Insert at frame number")
@click.option("--empty", is_flag=True, help="Create empty frame (no cel copy)")
@click.pass_context
def frames_add(ctx, path, at_frame, empty):
    """Add a new frame to a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    frame_arg = f"local frame = spr:newFrame({at_frame})" if at_frame else "local frame = spr:newFrame(#spr.frames + 1)"
    if empty:
        frame_arg = f"local frame = spr:newEmptyFrame({at_frame or '#spr.frames + 1'})"
    lua = (
        f'local spr = app.sprites[1]\n'
        f'{frame_arg}\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "add frame failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path)})
    else:
        click.echo(f"Added frame to {os.path.abspath(path)}")


@frames.command("delete")
@click.argument("path")
@click.argument("frame_number", type=int)
@click.pass_context
def frames_delete(ctx, path, frame_number):
    """Delete a frame from a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'spr:deleteFrame({frame_number})\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "delete frame failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "deleted_frame": frame_number})
    else:
        click.echo(f"Deleted frame {frame_number} from {os.path.abspath(path)}")


# ── tags management ─────────────────────────────────────────────────


@tags.command("add")
@click.argument("path")
@click.option("--name", required=True, help="Tag name")
@click.option("--from-frame", "from_f", type=int, required=True, help="Start frame (1-based)")
@click.option("--to-frame", "to_f", type=int, required=True, help="End frame (1-based)")
@click.pass_context
def tags_add(ctx, path, name, from_f, to_f):
    """Add a new frame tag to a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'local tag = spr:newTag({from_f}, {to_f})\n'
        f'tag.name = "{name}"\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "add tag failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "tag": {"name": name, "from": from_f, "to": to_f}})
    else:
        click.echo(f"Added tag '{name}' [{from_f}→{to_f}] to {os.path.abspath(path)}")


@tags.command("delete")
@click.argument("path")
@click.argument("name")
@click.pass_context
def tags_delete(ctx, path, name):
    """Delete a tag by name from a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'for i, tag in ipairs(spr.tags) do\n'
        f'  if tag.name == "{name}" then\n'
        f'    spr:deleteTag(tag)\n'
        f'    break\n'
        f'  end\n'
        f'end\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "delete tag failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "deleted": name})
    else:
        click.echo(f"Deleted tag '{name}' from {os.path.abspath(path)}")


# ── slices management ───────────────────────────────────────────────


@slices.command("add")
@click.argument("path")
@click.option("--name", required=True, help="Slice name")
@click.option("--x", type=int, default=0)
@click.option("--y", type=int, default=0)
@click.option("--width", type=int, required=True)
@click.option("--height", type=int, required=True)
@click.pass_context
def slices_add(ctx, path, name, x, y, width, height):
    """Add a new slice to a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'local slice = spr:newSlice(Rectangle{{x={x}, y={y}, '
        f'width={width}, height={height}}})\n'
        f'slice.name = "{name}"\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "add slice failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "slice": {"name": name, "x": x, "y": y, "width": width, "height": height}})
    else:
        click.echo(f"Added slice '{name}' to {os.path.abspath(path)}")


@slices.command("delete")
@click.argument("path")
@click.argument("name")
@click.pass_context
def slices_delete(ctx, path, name):
    """Delete a slice by name from a sprite."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'for i, slc in ipairs(spr.slices) do\n'
        f'  if slc.name == "{name}" then\n'
        f'    spr:deleteSlice(slc)\n'
        f'    break\n'
        f'  end\n'
        f'end\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if result.get("returncode", 0) not in (0, None):
        raise RuntimeError(result.get("stderr", "delete slice failed"))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "deleted": name})
    else:
        click.echo(f"Deleted slice '{name}' from {os.path.abspath(path)}")


# ── command subcommand ──────────────────────────────────────────────


@cli.command("command")
@click.argument("command_id")
@click.argument("path", required=False)
@click.option("--param", "-p", multiple=True, help="Command parameters (key=value)")
@click.pass_context
def run_command(ctx, command_id, path, param):
    """Run any Aseprite built-in command by ID.

    Examples:
      cli-anything-aseprite command NewFile sprite.aseprite --param width=64 --param height=64
      cli-anything-aseprite command InvertMask
    """
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)

    params_lua = ""
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            try:
                int(v)  # numeric?
            except ValueError:
                if v not in ("true", "false"):
                    v = f'"{v}"'
            params_lua += f"{k}={v}, "

    if params_lua:
        code = f'app.command.{command_id}{{ {params_lua} }}'
    else:
        code = f'app.command.{command_id}()'

    if path:
        safe = os.path.abspath(path).replace("\\", "/")
        code += f'\nlocal spr = app.sprites[1]; spr:saveCopyAs("{safe}")'

    result = runner.run_inline(code, sprite_path=os.path.abspath(path) if path else None)
    if ctx.obj["json"]:
        JSONOutput.print(result)
    else:
        if result.get("stderr"):
            click.echo(result["stderr"], err=True)
        else:
            click.echo(f"Command '{command_id}' executed.")


# ── color commands ──────────────────────────────────────────────────


@cli.group()
def color():
    """Get or set foreground/background colors."""


@color.command("get")
@click.pass_context
def color_get(ctx):
    """Get current foreground and background colors."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    lua = (
        'local fg = app.fgColor\n'
        'local bg = app.bgColor\n'
        'print("{"'
        '.."\\"fg\\":{\\"r\\":"..fg.red..",\\"g\\":"..fg.green'
        '..",\\"b\\":"..fg.blue..",\\"a\\":"..fg.alpha.."},'
        '.."\\"bg\\":{\\"r\\":"..bg.red..",\\"g\\":"..bg.green'
        '..",\\"b\\":"..bg.blue..",\\"a\\":"..bg.alpha.."}'
        '.."}")\n'
    )
    result = runner.run_inline(lua)
    if ctx.obj["json"]:
        JSONOutput.print(result.get("parsed", result))
    else:
        if result.get("parsed"):
            fg = result["parsed"]["fg"]
            bg = result["parsed"]["bg"]
            click.echo(f"Foreground: rgba({fg['r']},{fg['g']},{fg['b']},{fg['a']})")
            click.echo(f"Background: rgba({bg['r']},{bg['g']},{bg['b']},{bg['a']})")


@color.command("set")
@click.argument("which", type=click.Choice(["fg", "bg"]))
@click.argument("color_str", metavar="COLOR")
@click.pass_context
def color_set(ctx, which, color_str):
    """Set foreground (fg) or background (bg) color.

    COLOR format: r,g,b or r,g,b,a
    """
    parts = [int(x.strip()) for x in color_str.split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 255
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    varname = "fgColor" if which == "fg" else "bgColor"
    lua = f'app.{varname} = Color({r},{g},{b},{a})'
    result = runner.run_inline(lua)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "color": {"r": r, "g": g, "b": b, "a": a}})
    else:
        click.echo(f"Set {which} color to rgba({r},{g},{b},{a})")


# ── select commands ─────────────────────────────────────────────────


@cli.group()
def select():
    """Manage sprite selection."""


@select.command("all")
@click.argument("path")
@click.pass_context
def select_all(ctx, path):
    """Select entire canvas."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'local sel = Selection(spr)\n'
        f'sel:selectAll()\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "selection": "all"})
    else:
        click.echo(f"Selected all in {os.path.abspath(path)}")


@select.command("none")
@click.argument("path")
@click.pass_context
def select_none(ctx, path):
    """Deselect everything."""
    runner = ScriptRunner(_global_session.project._aseprite)
    runner._dry_run = ctx.obj.get("dry_run", False)
    safe = os.path.abspath(path).replace("\\", "/")
    lua = (
        f'local spr = app.sprites[1]\n'
        f'local sel = Selection(spr)\n'
        f'sel:deselect()\n'
        f'spr:saveCopyAs("{safe}")'
    )
    result = runner.run_inline(lua, sprite_path=os.path.abspath(path))
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "path": os.path.abspath(path),
                          "selection": "none"})
    else:
        click.echo(f"Deselected {os.path.abspath(path)}")


def main():
    """Entry point for console_scripts."""
    cli()
