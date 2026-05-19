# cli-anything-aseprite

Stateful CLI harness for [Aseprite](https://github.com/aseprite/aseprite) — programmatic control of the pixel art editor.

## What It Does

- **CLI control** — Open, inspect, export, and draw sprites from the terminal
- **JSON output** — All commands support `--json` for agent/script consumption
- **REPL mode** — Interactive session with stateful sprite tracking
- **Lua scripting bridge** — Run scripts and eval inline code
- **Programmatic drawing** — Fluent Python API for creating pixel art via generated Lua

## Install

```bash
pip install -e .
```

Requires Python 3.8+, Click 8.0+, and Aseprite in PATH (or set `ASEPRITE_BIN`).

## Quick Start

```bash
# Inspect a sprite
cli-anything-aseprite open sprite.aseprite

# Export a sprite sheet
cli-anything-aseprite export sheet sprite.aseprite -o output.png --data output.json

# Draw programmatically
cli-anything-aseprite draw new hello.png 64 64
cli-anything-aseprite draw fill hello.png "#3366ff"
cli-anything-aseprite draw circle hello.png 32 32 20 "#ff0000"

# Interactive REPL
cli-anything-aseprite repl
```

## Commands

| Group | Commands |
|-------|----------|
| Sprite | `open`, `info` |
| Layers | `layers list` |
| Tags | `tags list` |
| Slices | `slices list` |
| Palette | `palette list`, `palette load` |
| Export | `export sheet`, `export frame`, `export gif`, `export tileset` |
| Script | `script run`, `script eval` |
| Shell | `shell` |
| Draw | `draw new`, `draw fill`, `draw rect`, `draw circle`, `draw line`, `draw grad` |
| Session | `session state`, `session focus`, `session close` |
| REPL | `repl` |

## Python Drawing API

```python
from cli_anything.aseprite.core.draw import Draw

(Draw()
 .new("art.png", 64, 64)
 .fill(20, 20, 50)
 .rect(10, 10, 44, 44, 255, 0, 0)
 .circle(32, 32, 8, 0, 255, 0)
 .save())
```

## Tests

```bash
cd cli_anything/aseprite/tests
pytest -v
# 83 tests, all passing
```

## Project Structure

```
agent-harness/
├── setup.py
├── ASEPRITE.md                    # Architecture SOP
├── cli_anything/
│   └── aseprite/
│       ├── aseprite_cli.py        # Main CLI entry point
│       ├── core/
│       │   ├── project.py         # Sprite open/create/inspect
│       │   ├── session.py         # Stateful session management
│       │   ├── export.py          # Sprite sheet/frame/GIF export
│       │   ├── layers.py          # Layer listing
│       │   ├── palette.py         # Palette operations
│       │   ├── tags_slices.py     # Tags and slices inspection
│       │   ├── script.py          # Lua script runner
│       │   └── draw.py            # Programmatic drawing API
│       ├── utils/
│       │   └── helpers.py         # Binary resolution, JSON output
│       ├── tests/
│       │   ├── TEST.md            # Test plan and results
│       │   ├── test_core.py       # Unit tests (48 tests)
│       │   └── test_full_e2e.py   # E2E tests (35 tests)
│       └── skills/
│           └── SKILL.md           # AI agent skill definition
└── skills/
    └── cli-anything-aseprite/
        └── SKILL.md               # Canonical skill file
```

## License

MIT
