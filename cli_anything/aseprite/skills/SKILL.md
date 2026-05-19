---
name: cli-anything-aseprite
description: Stateful CLI harness for Aseprite pixel art editor — inspect sprites, layers, tags, slices, palettes, export sprite sheets, and run Lua scripts from the command line.
metadata:
  category: cli-harness
  target: aseprite
  version: "0.1.0"
---

# cli-anything-aseprite

Stateful CLI harness for [Aseprite](https://github.com/aseprite/aseprite) — the animated sprite editor and pixel art tool.

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

Reads sprite metadata (size, frames, layers, tags, slices) and stores it in the session. With `--json`, outputs structured JSON.

### info — Show sprite metadata

```
cli-anything-aseprite info [file]
```

Shows width, height, color mode, frame count, layer/tag/slice counts. Uses active session sprite if no file given.

### layers — Inspect sprite layers

```
cli-anything-aseprite layers list <file> [--hierarchy]
```

Lists layers with name, opacity, blend mode, visibility. `--hierarchy` shows grouped layer tree.

### tags — Inspect frame tags

```
cli-anything-aseprite tags list <file>
```

Lists frame tags with from/to range, direction, and color.

### slices — Inspect slices

```
cli-anything-aseprite slices list <file>
```

Lists slices with per-frame keyframe bounds.

### palette — Inspect and manage palettes

```
cli-anything-aseprite palette list <file>
cli-anything-aseprite palette load <file> <palette_file>
```

Lists palette entries or loads a palette file into a sprite.

### export — Export sprites and sprite sheets

```
cli-anything-aseprite export sheet <file> --output-sheet <png> [options...]
cli-anything-aseprite export frame <file> --output <png> [--frame N] [--layer NAME]
cli-anything-aseprite export gif <file> --output <gif> [--scale F]
cli-anything-aseprite export tileset <file> --output-sheet <png> [--output-data <json>]
```

Sprite sheet options: `--sheet-type`, `--sheet-width`, `--sheet-height`, `--split-layers`, `--split-tags`, `--split-slices`, `--layer`, `--tag`, `--frame-range`, `--scale`, `--trim`, `--trim-sprite`, `--border-padding`, `--shape-padding`, `--inner-padding`, `--extrude`.

### script — Run Lua scripts

```
cli-anything-aseprite script run <file> <script.lua> [-p key=value ...]
cli-anything-aseprite script eval <file> <lua_code> [-p key=value ...]
```

Runs Lua scripts or inline code against a sprite. Parameters passed via `--script-param`. JSON stdout from scripts is auto-parsed.

### session — Manage interactive session

```
cli-anything-aseprite session state
cli-anything-aseprite session focus <file>
cli-anything-aseprite session close [file]
```

Session persists across commands. `state` shows open sprites and the active one.

### repl — Interactive mode

```
cli-anything-aseprite repl
```

Starts an interactive REPL with commands: `open`, `info`, `layers`, `tags`, `slices`, `palette`, `focus`, `close`, `state`, `export`, `run`, `eval`, `help`, `quit`.

## JSON Output Examples

```bash
# Get sprite info as JSON
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
- Use `--dry-run` to preview commands before execution — useful for validation
- For batch processing, chain commands: `open` → `export` → `close`
- Lua scripts can extract data not available via CLI flags; use `script eval` for one-liners
- Session auto-saves state on exit; use `--state-file` to share state between processes
- When exporting sprite sheets, always provide `--output-data` to get frame metadata JSON
- The `--list-layers` / `--list-tags` / `--list-slices` flags on native aseprite are wrapped by the corresponding commands
