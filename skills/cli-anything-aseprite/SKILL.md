---
name: cli-anything-aseprite
description: Stateful CLI harness for Aseprite pixel art editor — full Lua API coverage: draw with app.useTool(), edit sprites, manage layers/frames/tags/slices, export with all native options, run Lua scripts, interactive REPL.
metadata:
  category: cli-harness
  target: aseprite
  version: "0.3.0"
---

# cli-anything-aseprite

Stateful CLI harness for [Aseprite](https://github.com/aseprite/aseprite) with full Lua API coverage.

## Requirements

- Python 3.8+
- Click 8.0+
- Aseprite installed and available in PATH (or set `ASEPRITE_BIN`)

## Installation

```bash
pip install cli-anything-aseprite
```

Or from source:

```bash
cd agent-harness && pip install -e .
```

## Global Options

| Option | Description |
|--------|-------------|
| `--aseprite-bin PATH` | Path to aseprite binary (or env `ASEPRITE_BIN`) |
| `--json` | Output results as JSON for programmatic consumption |
| `--dry-run` | Preview commands without executing |
| `--state-file PATH` | Custom session state file path |
| `--help` | Show help |

## Command Groups

### open — Open and inspect a sprite

```
cli-anything-aseprite open <file>
```

### info — Show sprite metadata

```
cli-anything-aseprite info [file]
```

### layers — Inspect and manage sprite layers

```
cli-anything-aseprite layers list <file> [--hierarchy]
cli-anything-aseprite layers add <file> --name <name>
cli-anything-aseprite layers delete <file> <name>
cli-anything-aseprite layers rename <file> <old_name> <new_name>
```

### tags — Inspect and manage frame tags

```
cli-anything-aseprite tags list <file>
cli-anything-aseprite tags add <file> --name <name> --from-frame <N> --to-frame <N>
cli-anything-aseprite tags delete <file> <name>
```

### slices — Inspect and manage slices

```
cli-anything-aseprite slices list <file>
cli-anything-aseprite slices add <file> --name <name> --x <X> --y <Y> --width <W> --height <H>
cli-anything-aseprite slices delete <file> <name>
```

### frames — Manage animation frames

```
cli-anything-aseprite frames add <file> [--at <N>] [--empty]
cli-anything-aseprite frames delete <file> <frame_number>
```

### palette — Inspect and manage palettes

```
cli-anything-aseprite palette list <file>
cli-anything-aseprite palette load <file> <palette_file>
```

### export — Export sprites (full native CLI support)

```
cli-anything-aseprite export sheet <file> --output-sheet <png> [30+ options...]
cli-anything-aseprite export frame <file> --output <png> [options...]
cli-anything-aseprite export gif <file> --output <gif> [options...]
cli-anything-aseprite export tileset <file> --output-sheet <png> [options...]
```

Sprite sheet options: `--sheet-type`, `--sheet-width`, `--sheet-height`, `--split-layers`, `--split-tags`, `--split-slices`, `--split-grid`, `--all-layers`, `--ignore-layer`, `--layer`, `--tag`/`--frame-tag`, `--frame-range`, `--scale`, `--dpi`, `--trim`, `--trim-sprite`, `--crop x,y,w,h`, `--border-padding`, `--inner-padding`, `--extrude`, `--merge-duplicates`, `--ignore-empty`, `--oneframe`, `--color-mode`, `--pixel-format`, `--new-power-of-two-size`, `--filename-format`.

Frame/GIF/Tileset exports also support their complete native option sets.

### edit — Edit sprites

```
cli-anything-aseprite edit crop <file> --width <W> --height <H> [--x <X> --y <Y>]
cli-anything-aseprite edit resize <file> --width <W> --height <H>
cli-anything-aseprite edit flatten <file>
cli-anything-aseprite edit flip <file> [--horizontal|--vertical]
```

### draw — Programmatic pixel art (useTool-powered)

```
cli-anything-aseprite draw new <file> <width> <height> [--color-mode rgba|grayscale|indexed]
cli-anything-aseprite draw fill <file> --color r,g,b[,a]
cli-anything-aseprite draw rect <file> <x> <y> <w> <h> --color r,g,b[,a] [--outline]
cli-anything-aseprite draw circle <file> <cx> <cy> <radius> --color r,g,b[,a] [--outline]
cli-anything-aseprite draw ellipse <file> <x> <y> <w> <h> --color r,g,b[,a] [--outline]
cli-anything-aseprite draw line <file> <x1> <y1> <x2> <y2> --color r,g,b[,a]
cli-anything-aseprite draw grad <file> --from-color r,g,b --to-color r,g,b [--direction h|v]
cli-anything-aseprite draw flood-fill <file> <x> <y> --color r,g,b[,a] [--tolerance N]
```

All drawing uses Aseprite's native `app.useTool()` API (pencil, filled_rectangle, rectangle, filled_ellipse, ellipse, line, paint_bucket, eraser, contour) — sub-millisecond vs. old pixel-by-pixel loops.

Python API:

```python
from cli_anything.aseprite.core.draw import Draw
(Draw().new("art.png", 64, 64)
       .fill(20, 20, 50)
       .rect(10, 10, 44, 44, 255, 0, 0)
       .circle(32, 32, 12, 0, 255, 0)
       .flood_fill(16, 16, 255, 255, 0)
       .save())
```

### script — Run Lua scripts

```
cli-anything-aseprite script run <file> <script.lua> [-p key=value ...]
cli-anything-aseprite script eval <file> <lua_code> [-p key=value ...]
```

### shell — Interactive Lua console

```
cli-anything-aseprite shell [file]
```

### command — Run Aseprite built-in commands

```
cli-anything-aseprite command <CommandID> [file] [-p key=value ...]
```

Examples: `command InvertMask`, `command OpenFile --param filename="other.aseprite"`

### color — Manage colors

```
cli-anything-aseprite color get
cli-anything-aseprite color set fg|bg r,g,b[,a]
```

### select — Manage selection

```
cli-anything-aseprite select all <file>
cli-anything-aseprite select none <file>
```

### session — Manage interactive session

```
cli-anything-aseprite session state
cli-anything-aseprite session focus <file>
cli-anything-aseprite session close [file]
```

### repl — Interactive mode

```
cli-anything-aseprite repl
```

Full REPL command set: `open`, `info`, `layers`, `tags`, `slices`, `palette`, `focus`, `close`, `state`, `export sheet/frame/gif/tileset`, `run`, `eval`, `shell`, `draw new/fill/rect/circle/ellipse/line/grad/flood-fill`, `edit crop/resize/flatten/flip`, `layers add/delete/rename`, `frames add/delete`, `tags add/delete`, `slices add/delete`, `command`, `color get/set`, `select all/none`, `help`, `quit`.

## JSON Output Examples

```bash
$ cli-anything-aseprite --json info character.aseprite
{
  "path": "character.aseprite",
  "width": 64,
  "height": 64,
  "frames": 8,
  "color_mode": "rgba",
  "layers": [
    {"name": "Body", "opacity": 255, "blend_mode": "normal", "visible": true},
    {"name": "Eyes", "opacity": 255, "blend_mode": "normal", "visible": true}
  ],
  "tags": [
    {"name": "idle", "from": 0, "to": 3, "direction": "forward"},
    {"name": "walk", "from": 4, "to": 7, "direction": "ping-pong"}
  ],
  "slices": [
    {"name": "icon", "keys": [{"frame": 0, "x": 0, "y": 0, "w": 32, "h": 32}]}
  ]
}
```

## Agent Guidance

- Use `--json` for all programmatic consumption to get structured output
- Use `--dry-run` to preview commands before execution
- For batch processing, chain commands: `open` → `layers add` → `draw ...` → `export` → `close`
- Drawing via `app.useTool()` is orders of magnitude faster than pixel-by-pixel Lua loops
- `command <ID>` unlocks ALL Aseprite built-in commands — use for anything not yet wrapped
- Lua scripts can extract data not available via CLI flags; use `script eval` for one-liners
- Session auto-saves state on exit; use `--state-file` to share state between processes
- Export commands support the complete set of native Aseprite CLI flags
- `edit crop/resize/flatten/flip` modify sprites in-place via Lua API
- `shell` gives direct access to Aseprite's interactive Lua console
