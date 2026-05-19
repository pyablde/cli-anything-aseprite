# ASEPRITE.md — Software-Specific SOP

## Application Overview

Aseprite is a pixel art tool for creating animated sprites and pixel graphics. It supports:
- Layered sprites with blend modes and opacity
- Frame-based animation with tags for organizing frame ranges
- Color palettes (RGBA, Grayscale, Indexed)
- Slices for defining export regions
- Tilemap layers and tilesets
- Lua scripting for automation
- Sprite sheet export with configurable layouts

## Architecture

### Data Model
- **Sprite** — The top-level container: dimensions, color mode, pixel ratio
- **Layer** — Stacked compositing elements, each with blend mode, opacity, visibility
- **Cel** — A layer's content at a specific frame (the actual pixel data)
- **Frame** — A single animation frame containing cels from visible layers
- **Tag** — Named frame range with playback direction (forward, reverse, ping-pong)
- **Slice** — Named rectangular region with per-frame keyframes
- **Palette** — Indexed color table (256 entries max)
- **Tileset** — Collection of tiles for tilemap layers

### Existing CLI Capabilities
Aseprite's native CLI (via `--batch` / `-b`) supports:
- Opening sprite files (positional arguments)
- `--save-as <file>` — Save with format conversion
- `--sheet <file>` — Export sprite sheet
- `--data <file>` — Export JSON metadata
- `--sheet-type <type>` — Layout algorithm (horizontal, vertical, rows, columns, packed)
- `--sheet-width`, `--sheet-height` — Fixed sheet dimensions
- `--split-layers`, `--split-tags`, `--split-slices`, `--split-grid`
- `--layer <name>`, `--ignore-layer <name>` — Layer filtering for export
- `--tag <name>`, `--frame-range <from>,<to>` — Frame selection
- `--scale <factor>` — Resize during export
- `--color-mode <mode>` — Convert color mode
- `--palette <file>` — Apply palette
- `--trim`, `--trim-sprite` — Trim transparent pixels
- `--crop <x,y,w,h>` — Crop to rectangle
- `--slice <name>` — Crop to slice bounds
- `--list-layers`, `--list-tags`, `--list-slices` — Metadata inspection
- `--script <file>` — Run Lua script
- `--script-param <key=value>` — Pass parameters to scripts
- `--verbose`, `--debug` — Logging levels

### This Harness

The `cli-anything-aseprite` Python CLI wraps Aseprite's batch mode with:
1. **Stateful sessions** — Track open sprites across multiple commands
2. **JSON-first output** — All commands support `--json` for agent/programmatic consumption
3. **REPL mode** — Interactive exploration and chaining of operations
4. **Auto-save** — Session state persists to disk automatically
5. **Dry-run** — Preview commands without execution
6. **Lua scripting bridge** — Run and eval Lua scripts with parameter passing
7. **Structured metadata** — Parsed layer/tag/slice/palette information

## Command Design

Commands mirror Aseprite's domain model:
- `open`, `info` — Sprite inspection
- `layers list` — Layer queries (names, visibility, opacity, blend mode)
- `tags list` — Animation tag queries (frame ranges, direction)
- `slices list` — Slice region queries (keyframes, bounds)
- `palette list`, `palette load` — Color palette operations
- `export sheet`, `export frame`, `export gif`, `export tileset` — All export variants
- `script run`, `script eval` — Lua scripting bridge
- `session state`, `session focus`, `session close` — Session management
- `repl` — Interactive mode

## Error Handling

- Missing aseprite binary → exit with message suggesting install or `--aseprite-bin`
- File not found → `FileNotFoundError` with path
- Aseprite CLI errors → `RuntimeError` with stderr from the subprocess
- `--dry-run` suppresses all execution and returns synthetic success output
