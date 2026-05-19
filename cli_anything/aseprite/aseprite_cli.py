"""cli-anything-aseprite: Stateful CLI harness for Aseprite.

Usage:
  cli-anything-aseprite open <file>              Open a sprite file
  cli-anything-aseprite info [file]              Get sprite metadata
  cli-anything-aseprite layers list <file>       List layers
  cli-anything-aseprite tags list <file>         List frame tags
  cli-anything-aseprite slices list <file>       List slices
  cli-anything-aseprite palette list <file>      List palette entries
  cli-anything-aseprite export sheet <file> ...  Export sprite sheet
  cli-anything-aseprite export frame <file> ...  Export single frame
  cli-anything-aseprite script run <file> <lua>  Run Lua script
  cli-anything-aseprite draw new <file> W H      Create new canvas
  cli-anything-aseprite draw rect <file> ...     Draw shapes
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
@click.option("--split-layers", is_flag=True, help="Export layers separately")
@click.option("--split-tags", is_flag=True, help="Export tags separately")
@click.option("--split-slices", is_flag=True, help="Export slices separately")
@click.option("--tag", help="Export only frames in this tag")
@click.option("--frame-range", help="Export frame range (from,to)")
@click.option("--sheet-type", help="Sheet layout: horizontal, vertical, rows, columns, packed")
@click.option("--sheet-width", type=int, help="Fixed sheet width in pixels")
@click.option("--sheet-height", type=int, help="Fixed sheet height in pixels")
@click.option("--scale", type=float, help="Scale factor (e.g., 2.0)")
@click.option("--trim", is_flag=True, help="Trim frames in sheet")
@click.option("--trim-sprite", is_flag=True, help="Trim whole sprite")
@click.option("--border-padding", type=int, help="Padding on texture border")
@click.option("--shape-padding", type=int, help="Padding between frames")
@click.option("--inner-padding", type=int, help="Padding inside each frame")
@click.option("--extrude", is_flag=True, help="Extrude edges by 1px")
@click.pass_context
def export_sheet(ctx, path, output_sheet, output_data, **kwargs):
    """Export a sprite as a sprite sheet."""
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
@click.pass_context
def export_frame_cmd(ctx, path, output, frame, layer):
    """Export a single frame as an image."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    result = exp.export_frame(path, output, frame=frame, layer=layer)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "output": result, "frame": frame})
    else:
        click.echo(f"Frame {frame} exported to: {result}")


@export.command("gif")
@click.argument("path")
@click.option("--output", required=True, help="Output GIF file")
@click.option("--scale", type=float, help="Scale factor")
@click.pass_context
def export_gif_cmd(ctx, path, output, scale):
    """Export sprite as animated GIF."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    kwargs = {}
    if scale:
        kwargs["scale"] = scale
    result = exp.export_gif(path, output, **kwargs)
    if ctx.obj["json"]:
        JSONOutput.print({"status": "ok", "output": result})
    else:
        click.echo(f"GIF exported to: {result}")


@export.command("tileset")
@click.argument("path")
@click.option("--output-sheet", required=True, help="Output tileset image")
@click.option("--output-data", help="Output JSON metadata file")
@click.pass_context
def export_tileset(ctx, path, output_sheet, output_data):
    """Export tilesets from visible tilemap layers."""
    exp = Exporter(_global_session.project._aseprite)
    exp._dry_run = ctx.obj.get("dry_run", False)
    result = exp.export_tileset(path, output_sheet, output_data)
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
        "run <file> <script>": "Run Lua script",
        "eval <file> <code>": "Eval Lua code",
        "draw new <file> W H": "Create new canvas",
        "draw rect <file> X Y W H --color r,g,b": "Draw filled rectangle",
        "draw circle <file> CX CY R --color r,g,b": "Draw filled circle",
        "draw line <file> X1 Y1 X2 Y2 --color r,g,b": "Draw line",
        "draw fill <file> --color r,g,b": "Fill canvas with color",
        "draw grad <file> --from r,g,b --to r,g,b [--direction h|v]": "Gradient fill",
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
        d._lua(
            f'for x=0,spr.width-1 do '
            f'local t=x/(spr.width-1); '
            f'local r={fr}+({tr - fr})*t; '
            f'local g={fg}+({tg - fg})*t; '
            f'local b={fb}+({tb - fb})*t; '
            'for y=0,spr.height-1 do img:putPixel(x,y,rgba(r,g,b,255)) end end')
    else:
        d._lua(
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


def main():
    """Entry point for console_scripts."""
    cli()
