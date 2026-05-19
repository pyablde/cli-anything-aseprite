# cli-anything-aseprite

Stateful CLI harness for [Aseprite](https://github.com/aseprite/aseprite) — the animated sprite editor and pixel art tool.

## Installation

```bash
pip install -e .
```

Requires Aseprite to be installed and available in PATH, or set `ASEPRITE_BIN` environment variable.

## Quick Start

```bash
# Open a sprite and view its info
cli-anything-aseprite open sprite.aseprite

# List layers
cli-anything-aseprite layers list sprite.aseprite

# List frame tags
cli-anything-aseprite tags list sprite.aseprite

# Export a sprite sheet
cli-anything-aseprite export sheet sprite.aseprite \
  --output-sheet output.png \
  --output-data output.json \
  --sheet-type packed

# Export a single frame
cli-anything-aseprite export frame sprite.aseprite \
  --output frame0.png --frame 0

# Export as GIF
cli-anything-aseprite export gif sprite.aseprite \
  --output animation.gif --scale 2.0

# Run a Lua script
cli-anything-aseprite script run sprite.aseprite my_script.lua

# Eval inline Lua
cli-anything-aseprite script eval sprite.aseprite \
  'app.activeSprite.width'

# Programmatic drawing
cli-anything-aseprite draw new output.png 64 64
cli-anything-aseprite draw fill output.png "#ff0000"
cli-anything-aseprite draw circle output.png 32 32 20 "#00ff0080"
cli-anything-aseprite draw line output.png 0 0 63 63 "#ffffff"

# JSON output mode (for agent/script consumption)
cli-anything-aseprite --json info sprite.aseprite

# Dry-run (preview commands without executing)
cli-anything-aseprite --dry-run draw new test.png 32 32

# Interactive REPL
cli-anything-aseprite repl
```

## Command Overview

| Command | Description |
|---------|-------------|
| `open <file>` | Open and inspect a sprite |
| `info [file]` | Show sprite metadata |
| `layers list <file>` | List sprite layers |
| `tags list <file>` | List frame tags |
| `slices list <file>` | List sprite slices |
| `palette list <file>` | List palette entries |
| `palette load <file> <pal>` | Load palette into sprite |
| `export sheet <file> ...` | Export sprite sheet with full options |
| `export frame <file> ...` | Export single frame |
| `export gif <file> ...` | Export animated GIF |
| `export tileset <file> ...` | Export tileset |
| `script run <file> <lua>` | Run Lua script on sprite |
| `script eval <file> <code>` | Evaluate inline Lua code |
| `draw new <file> W H` | Create new canvas for drawing |
| `draw fill <file> <color>` | Fill canvas with solid color |
| `draw rect <file> X Y W H <color>` | Draw filled/outlined rectangle |
| `draw circle <file> CX CY R <color>` | Draw filled/outlined circle |
| `draw line <file> X1 Y1 X2 Y2 <color>` | Draw Bresenham line |
| `draw grad <file> <from> <to> <dir>` | Draw gradient pattern |
| `session state` | Show session state |
| `session focus <file>` | Set active sprite |
| `session close [file]` | Close a sprite |
| `repl` | Start interactive REPL |

## Python Drawing API

```python
from cli_anything.aseprite.core.draw import Draw

d = Draw(aseprite_bin="/path/to/aseprite")
d.new("output.png", 64, 64)
d.fill(0, 0, 50, 255)          # dark blue fill
d.rect(10, 10, 20, 20, 255, 0, 0)   # red rect
d.circle(32, 32, 10, 0, 255, 0)     # green circle
d.line(0, 0, 63, 63, 255, 255, 255)  # white diagonal
d.save()

# Or chain:
(Draw().new("out.png", 32, 32)
       .fill(0, 0, 50)
       .rect(5, 5, 10, 10, 255, 0, 0)
       .save())
```

## Global Options

| Option | Description |
|--------|-------------|
| `--aseprite-bin PATH` | Path to aseprite binary |
| `--json` | Output results as JSON |
| `--dry-run` | Preview commands without executing |
| `--state-file PATH` | Custom session state file |
| `--help` | Show help |

## Environment Variables

- `ASEPRITE_BIN` — Path to the aseprite binary

## Requirements

- Python 3.8+
- Click 8.0+
- Aseprite installed and available on PATH
