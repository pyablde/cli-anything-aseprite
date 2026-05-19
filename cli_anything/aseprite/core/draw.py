"""Draw: programmatic pixel art creation via Lua script generation."""

import os
from typing import Optional

from cli_anything.aseprite.core.script import ScriptRunner


class Draw:
    """Fluent API for creating pixel art by generating and executing Lua scripts.

    Accumulates drawing commands as Lua code, then executes them in a single
    Aseprite batch call when save() is invoked.

    Usage:
        d = Draw(aseprite_bin="...")
        d.new("output.png", 64, 64)
        d.fill(0, 0, 50, 255)
        d.rect(10, 10, 20, 20, 255, 0, 0)
        d.circle(32, 32, 10, 0, 255, 0)
        d.save()

    Or chain:
        (Draw().new("out.png", 32, 32)
               .fill(0, 0, 50)
               .rect(5, 5, 10, 10, 255, 0, 0)
               .save())
    """

    def __init__(self, aseprite_bin: str = "aseprite"):
        self._aseprite = aseprite_bin
        self._dry_run = False
        self._lua_lines: list = []
        self._sprite_path: Optional[str] = None
        self._width: int = 0
        self._height: int = 0
        self._has_newfile: bool = False

    # ── canvas setup ────────────────────────────────────────────────

    def new(self, path: str, width: int, height: int,
            color_mode: str = "rgb") -> "Draw":
        """Create a new empty canvas."""
        self._sprite_path = os.path.abspath(path)
        self._width = width
        self._height = height
        cm = {"rgba": "rgb", "grayscale": "grayscale", "indexed": "indexed"}
        self._lua_lines = [
            f'app.command.NewFile{{ width={width}, height={height}, '
            f'colorMode="{cm.get(color_mode, "rgb")}" }}',
            'local spr = app.sprites[1]',
            'local img = spr.cels[1].image',
            'local rgba = app.pixelColor.rgba',
        ]
        self._has_newfile = True
        return self

    def open(self, path: str) -> "Draw":
        """Open an existing sprite file for drawing.

        The sprite is opened by Aseprite and img/spr are bound.
        call save() to write changes back.
        """
        self._sprite_path = os.path.abspath(path)
        self._lua_lines = [
            'local spr = app.sprites[1]',
            'local img = spr.cels[1].image',
            'local rgba = app.pixelColor.rgba',
        ]
        self._has_newfile = False
        return self

    # ── drawing primitives ──────────────────────────────────────────

    def _lua(self, code: str) -> "Draw":
        self._lua_lines.append(code)
        return self

    def pixel(self, x: int, y: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a single pixel at (x, y)."""
        return self._lua(f'img:putPixel({x},{y},rgba({r},{g},{b},{a}))')

    def fill(self, r: int, g: int, b: int, a: int = 255) -> "Draw":
        """Fill the entire canvas with a solid color."""
        return self._lua(
            'for y=0,spr.height-1 do '
            'for x=0,spr.width-1 do '
            f'img:putPixel(x,y,rgba({r},{g},{b},{a})) end end')

    def rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int,
             a: int = 255, *, fill: bool = True) -> "Draw":
        """Draw a filled or outlined rectangle."""
        if fill:
            return self._lua(
                f'for _y={y},{y + h - 1} do for _x={x},{x + w - 1} do '
                f'img:putPixel(_x,_y,rgba({r},{g},{b},{a})) end end')
        # outline only
        self._lua(
            f'for _x={x},{x + w - 1} do '
            f'img:putPixel(_x,{y},rgba({r},{g},{b},{a})) '
            f'img:putPixel(_x,{y + h - 1},rgba({r},{g},{b},{a})) end')
        self._lua(
            f'for _y={y},{y + h - 1} do '
            f'img:putPixel({x},_y,rgba({r},{g},{b},{a})) '
            f'img:putPixel({x + w - 1},_y,rgba({r},{g},{b},{a})) end')
        return self

    def circle(self, cx: int, cy: int, radius: int, r: int, g: int, b: int,
               a: int = 255, *, fill: bool = True) -> "Draw":
        """Draw a filled or outlined circle using distance check."""
        if fill:
            cond = f'd <= {radius}'
        else:
            cond = f'd <= {radius} and d >= {radius - 1}'
        return self._lua(
            f'for y=math.max(0,{cy - radius}),math.min(spr.height-1,{cy + radius}) do '
            f'for x=math.max(0,{cx - radius}),math.min(spr.width-1,{cx + radius}) do '
            f'local dx,dy=x-{cx},y-{cy}; local d=math.sqrt(dx*dx+dy*dy); '
            f'if {cond} then img:putPixel(x,y,rgba({r},{g},{b},{a})) end end end')

    def line(self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int,
             a: int = 255) -> "Draw":
        """Draw a line using Bresenham's algorithm in Lua."""
        lua = (
            f'local x,y={x1},{y1}; local dx=math.abs({x2}-{x1}); '
            f'local dy=math.abs({y2}-{y1}); '
            f'local sx=({x1}<{x2})and 1 or -1; '
            f'local sy=({y1}<{y2})and 1 or -1; local err=dx-dy; '
            f'while true do img:putPixel(x,y,rgba({r},{g},{b},{a})); '
            f'if x=={x2} and y=={y2} then break end; '
            f'local e2=2*err; '
            f'if e2>-dy then err=err-dy; x=x+sx end; '
            f'if e2<dx then err=err+dx; y=y+sy end end')
        return self._lua(lua)

    def hline(self, y: int, x1: int, x2: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a horizontal line."""
        return self._lua(
            f'for x={x1},{x2} do img:putPixel(x,{y},rgba({r},{g},{b},{a})) end')

    def vline(self, x: int, y1: int, y2: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a vertical line."""
        return self._lua(
            f'for y={y1},{y2} do img:putPixel({x},y,rgba({r},{g},{b},{a})) end')

    # ── helpers ─────────────────────────────────────────────────────

    def color(self, r: int, g: int, b: int, a: int = 255) -> tuple:
        """Return an RGBA color tuple for use with other methods."""
        return (r, g, b, a)

    def rgb(self, r: int, g: int, b: int, a: int = 255) -> tuple:
        """Alias for color()."""
        return (r, g, b, a)

    def get_size(self) -> tuple:
        """Return current canvas (width, height)."""
        return (self._width, self._height)

    # ── execution ───────────────────────────────────────────────────

    def get_lua(self) -> str:
        """Return the accumulated Lua script without executing."""
        return '\n'.join(self._lua_lines)

    def save(self, path: Optional[str] = None,
             *, close: bool = False) -> dict:
        """Execute all accumulated drawing commands and save the result."""
        output = path or self._sprite_path
        if output is None:
            raise RuntimeError("No output path specified")
        safe = output.replace("\\", "/")
        self._lua_lines.append(f'spr:saveCopyAs("{safe}")')
        lua = '\n'.join(self._lua_lines)

        runner = ScriptRunner(self._aseprite)
        if self._dry_run:
            return {"dry_run": True, "lua": lua, "output": safe}

        if self._has_newfile:
            result = runner.run_inline(lua)
        else:
            result = runner.run_inline(lua, sprite_path=self._sprite_path)

        if result.get("returncode", 0) not in (0, None):
            raise RuntimeError(
                f"Draw failed: {result.get('stderr', 'unknown error')}")
        self._lua_lines = self._lua_lines[:-1]  # remove saveCopyAs line
        return result
