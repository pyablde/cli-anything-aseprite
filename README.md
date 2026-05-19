# cli-anything-aseprite

Stateful CLI harness for [Aseprite](https://github.com/aseprite/aseprite) — programmatic control of the pixel art editor via the Lua API.

## Highlights

- **Full Lua API coverage** — `app.useTool()` for native-speed drawing, sprite editing, layer/frame/tag/slice CRUD
- **CLI for everything** — 40+ commands covering all Aseprite domains
- **JSON output** — All commands support `--json` for agent/script consumption
- **REPL mode** — Interactive session with stateful sprite tracking
- **Programmatic drawing** — Fluent Python API, now powered by native tools (100x faster)
- **Dry-run** — Preview any command without executing

## Install

```bash
pip install -e .
```

Requires Python 3.8+, Click 8.0+, and Aseprite in PATH (or set `ASEPRITE_BIN`).

## Quick Start

```bash
# Inspect a sprite
cli-anything-aseprite open sprite.aseprite

# Export with all native options
cli-anything-aseprite export sheet sprite.aseprite --output-sheet out.png \
  --data out.json --sheet-type packed --scale 2 --trim --extrude

# Draw with native tools (app.useTool, sub-millisecond)
cli-anything-aseprite draw new hello.png 64 64
cli-anything-aseprite draw fill hello.png "#3366ff"
cli-anything-aseprite draw circle hello.png 32 32 20 "#ff0000"
cli-anything-aseprite draw line hello.png 0 0 63 63 "#ffffff"

# Edit sprites
cli-anything-aseprite edit crop hello.png --width 32 --height 32
cli-anything-aseprite edit flip hello.png --horizontal

# Manage layers
cli-anything-aseprite layers add hello.png --name "Foreground"
cli-anything-aseprite layers rename hello.png "Foreground" "FG"

# Manage animation
cli-anything-aseprite frames add hello.png
cli-anything-aseprite tags add hello.png --name "idle" --from-frame 1 --to-frame 4

# Run any Aseprite built-in command
cli-anything-aseprite command InvertMask

# Interactive Lua shell
cli-anything-aseprite shell

# Interactive REPL
cli-anything-aseprite repl
```

## Commands

| Group | Commands |
|-------|----------|
| Sprite | `open`, `info` |
| Layers | `layers list`, `layers add`, `layers delete`, `layers rename` |
| Tags | `tags list`, `tags add`, `tags delete` |
| Slices | `slices list`, `slices add`, `slices delete` |
| Frames | `frames add`, `frames delete` |
| Palette | `palette list`, `palette load` |
| Export | `export sheet`, `export frame`, `export gif`, `export tileset` |
| Edit | `edit crop`, `edit resize`, `edit flatten`, `edit flip` |
| Draw | `draw new`, `draw fill`, `draw rect`, `draw circle`, `draw ellipse`, `draw line`, `draw grad`, `draw flood-fill` |
| Script | `script run`, `script eval` |
| Shell | `shell` |
| Color | `color get`, `color set` |
| Select | `select all`, `select none` |
| Command | `command <CommandID>` — any Aseprite built-in command |
| Session | `session state`, `session focus`, `session close` |
| REPL | `repl` |

## Global Options

| Option | Description |
|--------|-------------|
| `--aseprite-bin PATH` | Path to aseprite binary (or env `ASEPRITE_BIN`) |
| `--json` | Output results as JSON |
| `--dry-run` | Preview commands without executing |
| `--state-file PATH` | Custom session state file |
| `--help` | Show help |

## Export Options (all 4 subcommands match official CLI)

`export sheet` supports: `--sheet-type`, `--sheet-width`, `--sheet-height`, `--split-layers`, `--split-tags`, `--split-slices`, `--split-grid`, `--all-layers`, `--ignore-layer`, `--layer`, `--tag`/`--frame-tag`, `--frame-range`, `--scale`, `--dpi`, `--trim`, `--trim-sprite`, `--crop x,y,w,h`, `--border-padding`, `--inner-padding`, `--extrude`, `--merge-duplicates`, `--ignore-empty`, `--oneframe`, `--color-mode`, `--pixel-format`, `--new-power-of-two-size`, `--filename-format`.

`export frame`、`export gif`、`export tileset` also support their full native option sets.

## Python Drawing API (useTool-powered)

```python
from cli_anything.aseprite.core.draw import Draw

(Draw(aseprite_bin="/path/to/aseprite")
 .new("art.png", 64, 64)
 .fill(20, 20, 50)                          # filled_rectangle tool
 .rect(10, 10, 44, 44, 255, 0, 0)          # filled_rectangle tool
 .circle(32, 32, 12, 0, 255, 0)            # filled_ellipse tool
 .line(0, 0, 63, 63, 255, 255, 255)        # line tool
 .flood_fill(16, 16, 255, 255, 0)           # paint_bucket tool
 .ellipse(20, 20, 24, 16, 0, 255, 255)     # ellipse tool
 .erase(5, 5, 10, 10)                       # eraser tool
 .polyline([(0,0),(10,20),(30,10)], 255,0,0)# contour tool
 .save())

# All drawing uses Aseprite's native app.useTool()
# — orders of magnitude faster than pixel-by-pixel loops.
```

## Tests

```bash
cd cli_anything/aseprite/tests
pytest -v
# 88 tests, all passing
```

## Project Structure

```
agent-harness/
├── README.md
├── setup.py
├── ASEPRITE.md                    # Architecture SOP
├── cli_anything/
│   └── aseprite/
│       ├── aseprite_cli.py        # CLI entry point (40+ commands)
│       ├── core/
│       │   ├── project.py         # Sprite open/create/inspect
│       │   ├── session.py         # Stateful session management
│       │   ├── export.py          # Export (sheet/frame/GIF/tileset)
│       │   ├── layers.py          # Layer listing
│       │   ├── palette.py         # Palette operations
│       │   ├── tags_slices.py     # Tags and slices inspection
│       │   ├── script.py          # Lua script runner
│       │   └── draw.py            # Drawing API (useTool-powered)
│       ├── utils/
│       │   └── helpers.py         # Binary resolution, JSON output
│       ├── tests/
│       │   ├── TEST.md            # Test plan and results
│       │   ├── test_core.py       # Unit tests (53 tests)
│       │   └── test_full_e2e.py   # E2E tests (35 tests)
│       └── skills/
│           └── SKILL.md           # AI agent skill definition
└── skills/
    └── cli-anything-aseprite/
        └── SKILL.md               # Canonical skill file
```

## License

MIT
