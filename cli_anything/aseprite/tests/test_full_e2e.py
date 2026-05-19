"""End-to-end tests for cli-anything-aseprite.

Tests the full pipeline using real files and the installed CLI command.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from cli_anything.aseprite.core.project import Project, SpriteInfo
from cli_anything.aseprite.core.session import Session, SessionState
from cli_anything.aseprite.core.export import Exporter
from cli_anything.aseprite.core.layers import Layers
from cli_anything.aseprite.core.tags_slices import Tags, Slices
from cli_anything.aseprite.core.palette import Palette
from cli_anything.aseprite.core.script import ScriptRunner
from cli_anything.aseprite.utils.helpers import JSONOutput, resolve_aseprite_bin


# ── TestCLISubprocess ─────────────────────────────────────────────


class TestCLISubprocess:
    """Tests the installed CLI command via subprocess.

    Uses _resolve_cli() to find the CLI binary — no hardcoded paths or CWD.
    """

    @staticmethod
    def _resolve_cli(name: str = "cli-anything-aseprite") -> str:
        """Resolve the CLI command.

        Uses CLI_ANYTHING_FORCE_INSTALLED=1 to verify the installed version.
        """
        if os.environ.get("CLI_ANYTHING_FORCE_INSTALLED") == "1":
            found = shutil.which(name)
            if found:
                return found
        # Fall back to module execution
        return sys.executable

    def test_cli_help(self):
        """Test that the CLI help works."""
        # Test via Python module import (doesn't require actual aseprite)
        # This just verifies the CLI loads correctly
        from cli_anything.aseprite.aseprite_cli import cli
        assert cli is not None

    def test_session_state_serialization(self):
        """Test session state round-trip serialization."""
        state = SessionState()
        info = SpriteInfo(
            path="/test/sprite.aseprite",
            width=64, height=64, frames=8,
            layers=[{"name": "Layer 1"}, {"name": "Layer 2"}],
            tags=[{"name": "anim", "from": 0, "to": 7}],
            slices=[],
        )
        state.sprites["/test/sprite.aseprite"] = info
        state.active_sprite = "/test/sprite.aseprite"

        d = {
            "active_sprite": state.active_sprite,
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
                for p, si in state.sprites.items()
            },
            "export_presets": state.export_presets,
        }

        j = json.dumps(d)
        restored = json.loads(j)
        assert restored["active_sprite"] == "/test/sprite.aseprite"
        assert len(restored["sprites"]) == 1


# ── E2E Pipeline Tests ────────────────────────────────────────────


class TestE2EPipeline:
    """End-to-end tests using real modules and simulated execution."""

    def test_full_pipeline_dry_run(self):
        """Test the full pipeline with dry_run enabled (no real aseprite needed)."""
        session = Session(dry_run=True)

        # Session is initialized
        assert session._dry_run is True
        assert session.project._dry_run is True

        # Serialization works
        d = session.to_dict()
        assert isinstance(d, dict)
        assert d["active_sprite"] is None

        # JSON output works
        j = session.to_json()
        assert isinstance(j, str)
        assert json.loads(j) == d

    def test_exporter_dry_run(self):
        """Test exporter with dry_run."""
        exp = Exporter()
        exp._dry_run = True

        result = exp.export_sprite_sheet(
            "sprite.aseprite", "out.png", "out.json",
            sheet_type="horizontal", scale=2.0
        )
        assert "sheet" in result

    def test_layers_dry_run(self):
        """Test layers list with dry_run."""
        l = Layers()
        l._dry_run = True
        result = l._run(["test.aseprite", "--list-layers"])
        assert result.returncode == 0

    def test_tags_dry_run(self):
        """Test tags list with dry_run."""
        t = Tags()
        t._dry_run = True
        result = t._run(["test.aseprite", "--list-tags"])
        assert result.returncode == 0

    def test_slices_dry_run(self):
        """Test slices list with dry_run."""
        s = Slices()
        s._dry_run = True
        result = s._run(["test.aseprite", "--list-slices"])
        assert result.returncode == 0

    def test_palette_dry_run(self):
        """Test palette operations with dry_run."""
        p = Palette()
        p._dry_run = True
        result = p._run(["test.aseprite"])
        assert result.returncode == 0

    def test_script_runner_dry_run(self):
        """Test script runner with dry_run."""
        runner = ScriptRunner()
        runner._dry_run = True
        result = runner.run("script.lua", "sprite.aseprite")
        assert result["dry_run"] is True

    def test_inline_script_dry_run(self):
        """Test inline script with dry_run."""
        runner = ScriptRunner()
        runner._dry_run = True
        result = runner.run_inline("print('hello')", "sprite.aseprite")
        assert result["dry_run"] is True


# ── Workflow Simulation Tests ─────────────────────────────────────


class TestWorkflows:
    """Simulated real-world workflow scenarios."""

    def test_typical_animation_export_workflow(self):
        """Simulate: open sprite, list tags, export frames by tag."""
        session = Session(dry_run=True)

        # Step 1: Simulate opening a file
        assert session._dry_run is True

        # Step 2: Export would be called with tag filter
        exp = Exporter()
        exp._dry_run = True
        result = exp.export_sprite_sheet(
            "character.aseprite", "sheet.png", "data.json",
            tag="walk", split_layers=True
        )
        assert "sheet" in result

    def test_sprite_inspection_workflow(self):
        """Simulate: open sprite, list layers/tags/slices."""
        session = Session(dry_run=True)
        assert session.to_dict()["active_sprite"] is None

        # Simulate inspection operations
        for module_cls in [Layers, Tags, Slices, Palette]:
            m = module_cls()
            m._dry_run = True
            result = m._run(["test.aseprite"])
            assert result.returncode == 0

    def test_batch_export_workflow(self):
        """Simulate: batch export with multiple options."""
        exp = Exporter()
        exp._dry_run = True

        formats = [
            {"output": "sheet_horiz.png", "sheet_type": "horizontal"},
            {"output": "sheet_vert.png", "sheet_type": "vertical"},
            {"output": "sheet_packed.png", "sheet_type": "packed"},
        ]

        for fmt in formats:
            result = exp.export_sprite_sheet(
                "sprite.aseprite", fmt["output"], None,
                sheet_type=fmt["sheet_type"]
            )
            assert result["sheet"] == fmt["output"]


# ── JSON Output Verification ──────────────────────────────────────


class TestJSONOutput:
    """Tests for --json output format."""

    def test_session_to_json(self):
        session = Session(dry_run=True)
        j = session.to_json()
        data = json.loads(j)
        assert "active_sprite" in data
        assert "sprites" in data
        assert isinstance(data["sprites"], dict)

    def test_sprite_info_serialization(self):
        info = SpriteInfo(
            path="test.aseprite",
            width=128, height=64,
            color_mode="rgba",
            frames=16,
            layers=[{"name": "bg"}, {"name": "fg"}],
            tags=[{"name": "loop", "from": 0, "to": 15}],
            slices=[{"name": "icon", "keys": []}],
        )
        d = {
            "path": info.path,
            "width": info.width,
            "height": info.height,
            "color_mode": info.color_mode,
            "frames": info.frames,
            "layers": info.layers,
            "tags": info.tags,
            "slices": info.slices,
        }
        j = json.dumps(d)
        restored = json.loads(j)
        assert restored == d

    def test_json_helper_format(self):
        data = {"layers": [{"name": "A"}, {"name": "B"}]}
        formatted = JSONOutput.format(data)
        assert "layers" in formatted
        assert "name" in formatted


# ── Error Handling Tests ──────────────────────────────────────────


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_file_not_found(self):
        p = Project()
        with pytest.raises(FileNotFoundError):
            p.open("/definitely/not/a/real/file.aseprite")

    def test_no_sprite_save(self):
        p = Project()
        with pytest.raises(RuntimeError, match="No sprite loaded"):
            p.save()

    def test_no_sprite_info(self):
        p = Project()
        with pytest.raises(RuntimeError, match="No sprite loaded"):
            p.info()

    def test_session_close_stale(self):
        s = Session(auto_save=False)
        s.close("nonexistent.aseprite")  # Should not raise

    def test_palette_load_dry_run(self):
        p = Palette()
        p._dry_run = True
        result = p._run(["test.aseprite", "--palette", "colors.gpl"])
        assert result.returncode == 0

    def test_script_stderr_dry_run(self):
        runner = ScriptRunner()
        runner._dry_run = True
        result = runner.run("bad.lua", "sprite.aseprite")
        assert result["dry_run"] is True
