"""Session module: stateful multi-sprite session with auto-save and --dry-run."""

import json
import os
import atexit
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Any

from cli_anything.aseprite.core.project import Project, SpriteInfo


@dataclass
class SessionState:
    """Serializable session state."""

    sprites: dict = field(default_factory=dict)  # path -> SpriteInfo
    active_sprite: Optional[str] = None
    export_presets: dict = field(default_factory=dict)
    recent_exports: list = field(default_factory=list)


class Session:
    """Stateful session that tracks open sprites and supports auto-save + --dry-run."""

    def __init__(self, aseprite_bin: str = "aseprite",
                 state_file: Optional[str] = None,
                 auto_save: bool = True,
                 dry_run: bool = False):
        self._aseprite = aseprite_bin
        self._state_file = state_file
        self._auto_save = auto_save
        self._dry_run = dry_run
        self._state = SessionState()
        self._project = Project(aseprite_bin)
        self._project._dry_run = dry_run

        if state_file and os.path.exists(state_file):
            self._load_state()
        if auto_save and not dry_run:
            atexit.register(self._auto_save_state)

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def project(self) -> Project:
        return self._project

    @property
    def active_sprite(self) -> Optional[SpriteInfo]:
        if self._state.active_sprite:
            return self._state.sprites.get(self._state.active_sprite)
        return None

    def open(self, path: str) -> SpriteInfo:
        """Open a sprite and add it to the session."""
        abs_path = os.path.abspath(path)
        if abs_path in self._state.sprites:
            return self._state.sprites[abs_path]
        info = self._project._gather_info(abs_path)
        self._state.sprites[abs_path] = info
        if self._state.active_sprite is None:
            self._state.active_sprite = abs_path
        return info

    def close(self, path: Optional[str] = None):
        """Close a sprite from the session."""
        key = path or self._state.active_sprite
        if key and key in self._state.sprites:
            del self._state.sprites[key]
            if self._state.active_sprite == key:
                self._state.active_sprite = next(iter(self._state.sprites), None)

    def focus(self, path: str):
        """Set the active sprite."""
        abs_path = os.path.abspath(path)
        if abs_path not in self._state.sprites:
            self.open(abs_path)
        else:
            self._state.active_sprite = abs_path

    def list_sprites(self) -> list:
        """List all open sprites."""
        return [
            {"path": p, "active": p == self._state.active_sprite}
            for p in self._state.sprites
        ]

    def export(self, path: str, **kwargs) -> str:
        """Export the active sprite with options."""
        if self.active_sprite is None:
            raise RuntimeError("No sprite loaded in session")
        return self._project.export(path, **kwargs)

    def run_script(self, script_path: str, params: Optional[dict] = None) -> dict:
        """Run a Lua script on the active sprite and return result."""
        from cli_anything.aseprite.core.script import ScriptRunner
        runner = ScriptRunner(self._aseprite)
        return runner.run(script_path, self._state.active_sprite, params)

    def to_dict(self) -> dict:
        """Serialize session state for --json output."""
        return {
            "active_sprite": self._state.active_sprite,
            "sprites": {
                p: {
                    "path": si.path,
                    "width": si.width,
                    "height": si.height,
                    "color_mode": si.color_mode,
                    "frames": si.frames,
                    "layer_count": len(si.layers),
                    "tag_count": len(si.tags),
                    "slice_count": len(si.slices),
                }
                for p, si in self._state.sprites.items()
            },
            "export_presets": self._state.export_presets,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def _auto_save_state(self):
        """Save state on process exit."""
        if self._state_file and not self._dry_run:
            self._save_state()

    def _load_state(self):
        """Load session state from disk."""
        try:
            with open(self._state_file, "r") as f:
                data = json.load(f)
            for path_str, info_dict in data.get("sprites", {}).items():
                if os.path.exists(path_str):
                    self._state.sprites[path_str] = self._project._gather_info(path_str)
            active = data.get("active_sprite")
            if active and active in self._state.sprites:
                self._state.active_sprite = active
            self._state.export_presets = data.get("export_presets", {})
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_state(self):
        """Save session state to disk."""
        if self._state_file:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            with open(self._state_file, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
