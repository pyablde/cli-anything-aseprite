"""Draw: programmatic pixel art creation via app.useTool() Lua API.

Uses Aseprite's native drawing tools (pencil, line, rectangle, ellipse,
paint_bucket, etc.) executed via app.useTool() in a single batch Lua script.
This is vastly faster than pixel-by-pixel loops — a single useTool call
replaces thousands of img:putPixel() calls.
"""

import os
from typing import Optional

from cli_anything.aseprite.core.script import ScriptRunner


class Draw:
    """Fluent API for creating pixel art via Aseprite native drawing tools.

    Accumulates drawing commands as Lua code, then executes them in a single
    Aseprite batch call when save() is invoked. Uses app.useTool() for all
    drawing operations — orders of magnitude faster than pixel loops.

    Usage:
        d = Draw(aseprite_bin="...")
        d.new("output.png", 64, 64)
        d.fill(0, 0, 50, 255)
        d.rect(10, 10, 20, 20, 255, 0, 0)
        d.circle(32, 32, 10, 0, 255, 0)
        d.line(0, 0, 63, 63, 255, 255, 255)
        d.save()

    Or chain:
        (Draw().new("out.png", 32, 32)
               .fill(0, 0, 50)
               .rect(5, 5, 10, 10, 255, 0, 0)
               .save())
    """

    # Brush size for pixel-level operations
    _PENCIL_BRUSH = 1

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
        ]
        self._has_newfile = True
        return self

    def open(self, path: str) -> "Draw":
        """Open an existing sprite file for drawing."""
        self._sprite_path = os.path.abspath(path)
        self._lua_lines = ['local spr = app.sprites[1]']
        self._has_newfile = False
        return self

    # ── useTool helpers ──────────────────────────────────────────────

    def _color_lua(self, r: int, g: int, b: int, a: int = 255) -> str:
        """Build a Lua Color(...) expression."""
        return f"Color({r},{g},{b},{a})"

    def _point_lua(self, x: int, y: int) -> str:
        return f"Point({x},{y})"

    def _usetool(self, tool: str, points: list, color: Optional[str] = None,
                 brush: int = 1, opacity: int = 255) -> "Draw":
        """Append an app.useTool{} call."""
        pt_list = ", ".join(points)
        color_expr = color or "app.fgColor"
        lua = (
            f'app.useTool{{ tool="{tool}", '
            f'points={{ {pt_list} }}, '
            f'brush=Brush({brush}), '
            f'color={color_expr}, '
            f'opacity={opacity} }}'
        )
        self._lua_lines.append(lua)
        return self

    # ── drawing primitives ──────────────────────────────────────────

    def pixel(self, x: int, y: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a single pixel at (x, y)."""
        c = self._color_lua(r, g, b, a)
        p = self._point_lua(x, y)
        return self._usetool("pencil", [p], color=c, brush=self._PENCIL_BRUSH)

    def fill(self, r: int, g: int, b: int, a: int = 255) -> "Draw":
        """Fill the entire canvas with a solid color.

        Uses a filled rectangle covering the whole canvas.
        """
        c = self._color_lua(r, g, b, a)
        topleft = self._point_lua(0, 0)
        botright = self._point_lua(self._width - 1, self._height - 1)
        return self._usetool("filled_rectangle", [topleft, botright], color=c,
                             brush=max(self._width, self._height))

    def rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int,
             a: int = 255, *, fill: bool = True) -> "Draw":
        """Draw a filled or outlined rectangle."""
        c = self._color_lua(r, g, b, a)
        p1 = self._point_lua(x, y)
        p2 = self._point_lua(x + w - 1, y + h - 1)
        tool = "filled_rectangle" if fill else "rectangle"
        return self._usetool(tool, [p1, p2], color=c)

    def circle(self, cx: int, cy: int, radius: int, r: int, g: int, b: int,
               a: int = 255, *, fill: bool = True) -> "Draw":
        """Draw a filled or outlined circle (ellipse)."""
        c = self._color_lua(r, g, b, a)
        p1 = self._point_lua(cx - radius, cy - radius)
        p2 = self._point_lua(cx + radius - 1, cy + radius - 1)
        tool = "filled_ellipse" if fill else "ellipse"
        return self._usetool(tool, [p1, p2], color=c)

    def ellipse(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int,
                a: int = 255, *, fill: bool = True) -> "Draw":
        """Draw a filled or outlined ellipse within bounding rectangle."""
        c = self._color_lua(r, g, b, a)
        p1 = self._point_lua(x, y)
        p2 = self._point_lua(x + w - 1, y + h - 1)
        tool = "filled_ellipse" if fill else "ellipse"
        return self._usetool(tool, [p1, p2], color=c)

    def line(self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int,
             a: int = 255) -> "Draw":
        """Draw a line between two points (native tool, fast)."""
        c = self._color_lua(r, g, b, a)
        p1 = self._point_lua(x1, y1)
        p2 = self._point_lua(x2, y2)
        return self._usetool("line", [p1, p2], color=c)

    def hline(self, y: int, x1: int, x2: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a horizontal line."""
        return self.line(x1, y, x2, y, r, g, b, a)

    def vline(self, x: int, y1: int, y2: int, r: int, g: int, b: int,
              a: int = 255) -> "Draw":
        """Draw a vertical line."""
        return self.line(x, y1, x, y2, r, g, b, a)

    def flood_fill(self, x: int, y: int, r: int, g: int, b: int,
                   a: int = 255, *, tolerance: int = 0) -> "Draw":
        """Flood-fill an area starting from (x, y)."""
        c = self._color_lua(r, g, b, a)
        p = self._point_lua(x, y)
        lua = (
            f'app.useTool{{ tool="paint_bucket", '
            f'points={{ {p} }}, '
            f'brush=Brush(1), '
            f'color={c}, '
            f'opacity={a}, '
            f'tolerance={tolerance} }}'
        )
        self._lua_lines.append(lua)
        return self

    def erase(self, x: int, y: int, w: int, h: int) -> "Draw":
        """Erase a rectangular region (uses eraser tool)."""
        p1 = self._point_lua(x, y)
        p2 = self._point_lua(x + w - 1, y + h - 1)
        return self._usetool("eraser", [p1, p2], color="Color(0,0,0,0)",
                             brush=max(w, h))

    def polyline(self, points: list, r: int, g: int, b: int,
                 a: int = 255) -> "Draw":
        """Draw a polyline through a list of (x, y) points.

        Uses the contour tool (continuous freehand/polyline) for efficiency.
        """
        c = self._color_lua(r, g, b, a)
        pt_list = ", ".join(self._point_lua(x, y) for x, y in points)
        lua = (
            f'app.useTool{{ tool="contour", '
            f'points={{ {pt_list} }}, '
            f'brush=Brush(1), '
            f'color={c}, '
            f'opacity={a} }}'
        )
        self._lua_lines.append(lua)
        return self

    # ── raw Lua injection ───────────────────────────────────────────

    def raw(self, lua_code: str) -> "Draw":
        """Append raw Lua code to the script. For advanced/custom drawing."""
        self._lua_lines.append(lua_code)
        return self

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
