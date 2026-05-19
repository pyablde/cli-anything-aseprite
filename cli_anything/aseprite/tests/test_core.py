"""Unit tests for cli-anything-aseprite core modules.

Uses synthetic data and mocks; no external dependencies or real files required.
"""

import json
import os
import sys
import tempfile
from unittest import mock
from unittest.mock import patch, MagicMock

import pytest

from cli_anything.aseprite.core.project import Project, SpriteInfo
from cli_anything.aseprite.core.session import Session, SessionState
from cli_anything.aseprite.core.export import Exporter
from cli_anything.aseprite.core.layers import Layers
from cli_anything.aseprite.core.palette import Palette
from cli_anything.aseprite.core.tags_slices import Tags, Slices
from cli_anything.aseprite.core.script import ScriptRunner


# ── Fixtures ──────────────────────────────────────────────────────

SAMPLE_JSON_DATA = {
    "frames": {
        "sprite 0": {
            "frame": {"x": 0, "y": 0, "w": 32, "h": 32},
            "sourceSize": {"w": 32, "h": 32},
        },
        "sprite 1": {
            "frame": {"x": 32, "y": 0, "w": 32, "h": 32},
            "sourceSize": {"w": 32, "h": 32},
        },
    },
    "meta": {
        "size": {"w": 64, "h": 32},
        "layers": [
            {"name": "Background", "opacity": 255, "blendMode": "normal", "visible": True},
            {"name": "Character", "opacity": 200, "blendMode": "normal", "visible": True},
            {"name": "Effects", "opacity": 128, "blendMode": "addition", "visible": False},
        ],
        "frameTags": [
            {"name": "idle", "from": 0, "to": 3, "direction": "forward", "color": "#00ff00"},
            {"name": "walk", "from": 4, "to": 7, "direction": "ping-pong", "color": "#ff0000"},
        ],
        "slices": [
            {
                "name": "head",
                "color": "#0000ff",
                "keys": [
                    {"frame": 0, "bounds": {"x": 8, "y": 0, "w": 16, "h": 16}},
                    {"frame": 1, "bounds": {"x": 8, "y": 0, "w": 16, "h": 16}},
                ],
            },
            {
                "name": "body",
                "color": "#ff00ff",
                "keys": [
                    {"frame": 0, "bounds": {"x": 0, "y": 16, "w": 32, "h": 16}},
                ],
            },
        ],
    },
}


@pytest.fixture
def sample_json_path():
    """Write sample JSON to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(SAMPLE_JSON_DATA, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for all tests."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


# ── Project Tests ─────────────────────────────────────────────────


class TestProject:
    """Unit tests for Project class."""

    def test_init(self):
        p = Project()
        assert p.sprite is None
        assert p._aseprite == "aseprite"

    def test_init_custom_bin(self):
        p = Project(aseprite_bin="/custom/aseprite")
        assert p._aseprite == "/custom/aseprite"

    def test_open_file_not_found(self):
        p = Project()
        with pytest.raises(FileNotFoundError):
            p.open("/nonexistent/file.aseprite")

    def test_dry_run_no_execution(self):
        p = Project()
        p._dry_run = True
        result = p._run(["test.aseprite", "--list-layers"])
        assert result.returncode == 0

    def test_gather_info_parses_json(self, sample_json_path, mock_subprocess_run):
        """Test that _gather_info correctly parses JSON metadata."""
        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stderr = ""

        def side_effect(*args, **kwargs):
            # Find the --data argument and write sample JSON there
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                with open(data_path, "w") as f:
                    json.dump(SAMPLE_JSON_DATA, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        p = Project()
        info = p._gather_info(sample_json_path)

        assert info.width == 32
        assert info.height == 32
        assert info.frames == 2
        assert len(info.layers) == 3
        assert len(info.tags) == 2
        assert len(info.slices) == 2
        assert info.layers[0]["name"] == "Background"
        assert info.tags[0]["name"] == "idle"
        assert info.slices[0]["name"] == "head"

    def test_extract_layers(self):
        p = Project()
        layers = p._extract_layers(SAMPLE_JSON_DATA)
        assert len(layers) == 3
        assert layers[0]["name"] == "Background"
        assert layers[0]["visible"] is True
        assert layers[2]["visible"] is False
        assert layers[2]["blend_mode"] == "addition"

    def test_extract_tags(self):
        p = Project()
        tags = p._extract_tags(SAMPLE_JSON_DATA, SAMPLE_JSON_DATA["frames"])
        assert len(tags) == 2
        assert tags[0]["name"] == "idle"
        assert tags[0]["from"] == 0
        assert tags[0]["to"] == 3
        assert tags[1]["direction"] == "ping-pong"

    def test_extract_slices(self):
        p = Project()
        slices = p._extract_slices(SAMPLE_JSON_DATA)
        assert len(slices) == 2
        assert slices[0]["name"] == "head"
        assert len(slices[0]["keys"]) == 2
        assert slices[0]["keys"][0]["frame"] == 0
        assert slices[0]["keys"][0]["w"] == 16

    def test_close_clears_sprite(self):
        p = Project()
        p._sprite = SpriteInfo(path="test.aseprite")
        p.close()
        assert p.sprite is None

    def test_save_no_sprite_raises(self):
        p = Project()
        with pytest.raises(RuntimeError, match="No sprite loaded"):
            p.save()

    def test_info_no_sprite_no_path_raises(self):
        p = Project()
        with pytest.raises(RuntimeError, match="No sprite loaded"):
            p.info()


# ── Session Tests ─────────────────────────────────────────────────


class TestSession:
    """Unit tests for Session class."""

    def test_init(self):
        s = Session(auto_save=False)
        assert s.state is not None
        assert s.active_sprite is None
        assert s.state.sprites == {}

    def test_init_dry_run(self):
        s = Session(dry_run=True)
        assert s._dry_run is True
        assert s.project._dry_run is True

    def test_to_dict_empty(self):
        s = Session(auto_save=False)
        d = s.to_dict()
        assert d["active_sprite"] is None
        assert d["sprites"] == {}
        assert d["export_presets"] == {}

    def test_to_json_empty(self):
        s = Session(auto_save=False)
        j = s.to_json()
        data = json.loads(j)
        assert data["active_sprite"] is None

    def test_list_sprites_empty(self):
        s = Session(auto_save=False)
        assert s.list_sprites() == []

    def test_session_state_dataclass(self):
        state = SessionState()
        assert state.active_sprite is None
        assert state.sprites == {}
        assert state.export_presets == {}
        assert state.recent_exports == []

        state.sprites["/a.aseprite"] = SpriteInfo(
            path="/a.aseprite", width=32, height=32, frames=4
        )
        state.active_sprite = "/a.aseprite"
        assert state.active_sprite == "/a.aseprite"
        assert len(state.sprites) == 1


# ── Exporter Tests ────────────────────────────────────────────────


class TestExporter:
    """Unit tests for Exporter class."""

    def test_init(self):
        e = Exporter()
        assert e._aseprite == "aseprite"
        assert e._dry_run is False

    def test_dry_run_no_execution(self):
        e = Exporter()
        e._dry_run = True
        result = e._run(["test.aseprite", "--sheet", "out.png"])
        assert result.returncode == 0

    def test_export_frame_args(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_frame("sprite.aseprite", "out.png", frame=5, layer="Character")
        call_args = mock_subprocess_run.call_args[0][0]
        assert "sprite.aseprite" in call_args
        assert "--save-as" in call_args
        assert "--frame-range" in call_args

    def test_export_sheet_builds_args(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_sprite_sheet(
            "sprite.aseprite", "sheet.png", "data.json",
            sheet_type="packed", scale=2.0, trim=True
        )
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--sheet" in call_args
        assert "--data" in call_args
        assert "--sheet-type" in call_args
        assert "--scale" in call_args
        assert "--trim" in call_args

    def test_export_sheet_with_crop(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_sprite_sheet("s.aseprite", "sheet.png",
                              crop=(10, 20, 100, 200))
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--crop" in call_args
        crop_idx = call_args.index("--crop")
        assert call_args[crop_idx + 1] == "10,20,100,200"

    def test_export_sheet_all_options(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_sprite_sheet("s.aseprite", "sheet.png", "data.json",
                              all_layers=True, split_layers=True,
                              split_grid=True, merge_duplicates=True,
                              ignore_empty=True, oneframe=True,
                              extrude=True, new_power_of_two_size=True,
                              color_mode="indexed", pixel_format="RGBA8888",
                              dpi=300, scale=2.0, border_padding=4,
                              inner_padding=2, sheet_type="packed",
                              sheet_width=1024, sheet_height=1024,
                              filename_format="{layer}_{frame}.png")
        call_args = mock_subprocess_run.call_args[0][0]
        flags = ["--all-layers", "--split-layers", "--split-grid",
                 "--merge-duplicates", "--ignore-empty", "--oneframe",
                 "--extrude", "--new-power-of-two-size",
                 "--color-mode", "--pixel-format", "--dpi",
                 "--scale", "--border-padding", "--inner-padding",
                 "--sheet-type", "--sheet-width", "--sheet-height",
                 "--filename-format"]
        for flag in flags:
            assert flag in call_args, f"Expected {flag} in call args"

    def test_export_frame_with_kwargs(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_frame("s.aseprite", "out.png", frame=3,
                       scale=2.0, trim=True, color_mode="indexed")
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--scale" in call_args
        assert "--trim" in call_args
        assert "--color-mode" in call_args

    def test_export_gif_with_options(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_gif("s.aseprite", "out.gif",
                     scale=2.0, frame_range="0,9",
                     tag="walk", color_mode="indexed", dpi=72)
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--scale" in call_args
        assert "--frame-range" in call_args
        assert "--tag" in call_args
        assert "--color-mode" in call_args
        assert "--dpi" in call_args

    def test_export_tileset_with_kwargs(self, mock_subprocess_run):
        e = Exporter()
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stderr="", stdout="")
        e.export_tileset("s.aseprite", "tiles.png", "tiles.json",
                         scale=2.0, border_padding=2, inner_padding=1,
                         trim=True, extrude=True, merge_duplicates=True,
                         ignore_empty=True, all_layers=True)
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--export-tileset" in call_args
        assert "--scale" in call_args
        assert "--border-padding" in call_args
        assert "--inner-padding" in call_args
        assert "--trim" in call_args
        assert "--extrude" in call_args
        assert "--merge-duplicates" in call_args
        assert "--ignore-empty" in call_args
        assert "--all-layers" in call_args

    def test_build_args_static_method(self):
        kwargs = {
            "crop": (10, 20, 30, 40),
            "scale": 2.0,
            "trim": True,
            "color_mode": "rgb",
            "sheet_width": 512,
        }
        result = Exporter._build_args(kwargs)
        assert "--crop" in result
        assert result[result.index("--crop") + 1] == "10,20,30,40"
        assert "--scale" in result
        assert result[result.index("--scale") + 1] == "2.0"
        assert "--trim" in result  # bare flag, no value after it


# ── Layers Tests ──────────────────────────────────────────────────


class TestLayers:
    """Unit tests for Layers class."""

    def test_list_parses_json(self, mock_subprocess_run):
        l = Layers()
        completed = mock.MagicMock(returncode=0, stderr="")

        def side_effect(*args, **kwargs):
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                with open(data_path, "w") as f:
                    json.dump(SAMPLE_JSON_DATA, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        result = l.list("test.aseprite")
        assert len(result) == 3
        assert result[0]["name"] == "Background"
        assert result[2]["visible"] is False

    def test_list_names(self, mock_subprocess_run):
        l = Layers()
        completed = mock.MagicMock(returncode=0, stderr="")

        def side_effect(*args, **kwargs):
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                with open(data_path, "w") as f:
                    json.dump(SAMPLE_JSON_DATA, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        names = l.list_names("test.aseprite")
        assert names == ["Background", "Character", "Effects"]


# ── Tags Tests ────────────────────────────────────────────────────


class TestTagsClass:
    """Unit tests for Tags class."""

    def test_list_parses_json(self, mock_subprocess_run):
        t = Tags()
        completed = mock.MagicMock(returncode=0, stderr="")

        def side_effect(*args, **kwargs):
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                with open(data_path, "w") as f:
                    json.dump(SAMPLE_JSON_DATA, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        result = t.list("test.aseprite")
        assert len(result) == 2
        assert result[0]["name"] == "idle"
        assert result[0]["from"] == 0
        assert result[0]["to"] == 3
        assert result[0]["direction"] == "forward"


# ── Slices Tests ──────────────────────────────────────────────────


class TestSlicesClass:
    """Unit tests for Slices class."""

    def test_list_parses_json(self, mock_subprocess_run):
        s = Slices()
        completed = mock.MagicMock(returncode=0, stderr="")

        def side_effect(*args, **kwargs):
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                with open(data_path, "w") as f:
                    json.dump(SAMPLE_JSON_DATA, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        result = s.list("test.aseprite")
        assert len(result) == 2
        assert result[0]["name"] == "head"
        assert len(result[0]["keys"]) == 2


# ── Palette Tests ─────────────────────────────────────────────────


class TestPaletteClass:
    """Unit tests for Palette class."""

    def test_list_entries_empty(self, mock_subprocess_run):
        p = Palette()
        completed = mock.MagicMock(returncode=0, stderr="")

        def side_effect(*args, **kwargs):
            cmd_args = args[0]
            try:
                data_idx = cmd_args.index("--data")
                data_path = cmd_args[data_idx + 1]
                no_palette = {"meta": {}}
                with open(data_path, "w") as f:
                    json.dump(no_palette, f)
            except (ValueError, IndexError):
                pass
            return completed

        mock_subprocess_run.side_effect = side_effect

        result = p.list_entries("test.aseprite")
        assert result == []


# ── Script Runner Tests ───────────────────────────────────────────


class TestScriptRunner:
    """Unit tests for ScriptRunner class."""

    def test_run_with_params(self, mock_subprocess_run):
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stdout="42", stderr="")
        runner = ScriptRunner()
        result = runner.run("script.lua", "sprite.aseprite",
                            params={"key": "value"})
        assert result["returncode"] == 0
        assert result["stdout"] == "42"
        call_args = mock_subprocess_run.call_args[0][0]
        assert "--script" in call_args
        assert "--script-param" in call_args
        assert "key=value" in call_args

    def test_run_parses_json_stdout(self, mock_subprocess_run):
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stdout='{"width": 32, "height": 32}', stderr="")
        runner = ScriptRunner()
        result = runner.run("info.lua", "sprite.aseprite")
        assert result["parsed"] == {"width": 32, "height": 32}

    def test_run_dry_run(self):
        runner = ScriptRunner()
        runner._dry_run = True
        result = runner.run("script.lua", "sprite.aseprite")
        assert result["dry_run"] is True

    def test_run_inline_writes_temp_file(self, mock_subprocess_run):
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=0, stdout="", stderr="")
        runner = ScriptRunner()
        result = runner.run_inline(
            "print(app.activeSprite.width)", "sprite.aseprite")
        assert result["returncode"] == 0
        # Verify the --script arg contains a temp .lua file
        call_args = mock_subprocess_run.call_args[0][0]
        lua_files = [a for a in call_args if a.endswith(".lua")]
        assert len(lua_files) == 1

    def test_run_stderr_captured(self, mock_subprocess_run):
        mock_subprocess_run.return_value = mock.MagicMock(
            returncode=1, stdout="", stderr="Script error: bad syntax")
        runner = ScriptRunner()
        result = runner.run("bad.lua", "sprite.aseprite")
        assert result["returncode"] == 1
        assert "Script error" in result["stderr"]


# ── Draw Tests ────────────────────────────────────────────────────


class TestDrawClass:
    """Unit tests for Draw class (useTool-based Lua script generation)."""

    def test_init(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        assert d._aseprite == "aseprite"
        assert d._dry_run is False
        assert d._lua_lines == []

    def test_new_builds_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/tmp/test.png", 32, 24, "rgba")
        lua = d.get_lua()
        assert 'app.command.NewFile' in lua
        assert 'width=32' in lua
        assert 'height=24' in lua
        assert 'local spr = app.sprites[1]' in lua
        assert d._has_newfile is True

    def test_pixel_uses_usetool_pencil(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.pixel(10, 20, 255, 128, 64, 200)
        lua = d.get_lua()
        assert 'app.useTool' in lua
        assert 'tool="pencil"' in lua
        assert 'Point(10,20)' in lua
        assert 'Color(255,128,64,200)' in lua

    def test_fill_uses_filled_rectangle(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 8, 8)
        d.fill(100, 150, 200)
        lua = d.get_lua()
        assert 'app.useTool' in lua
        assert 'tool="filled_rectangle"' in lua
        assert 'Color(100,150,200,255)' in lua

    def test_rect_fill_and_outline(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 32, 32)
        d.rect(5, 5, 10, 10, 255, 0, 0, fill=True)
        lua_fill = d.get_lua()
        assert 'tool="filled_rectangle"' in lua_fill
        assert 'Point(5,5)' in lua_fill
        assert 'Point(14,14)' in lua_fill

        d2 = Draw()
        d2.new("/t2.png", 32, 32)
        d2.rect(5, 5, 10, 10, 255, 0, 0, fill=False)
        lua_outline = d2.get_lua()
        assert 'tool="rectangle"' in lua_outline

    def test_circle_uses_usetool_ellipse(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 64, 64)
        d.circle(32, 32, 10, 0, 255, 0, fill=True)
        lua = d.get_lua()
        assert 'app.useTool' in lua
        assert 'tool="filled_ellipse"' in lua
        assert 'Point(22,22)' in lua  # cx - radius, cy - radius
        assert 'Point(41,41)' in lua  # cx + radius - 1, cy + radius - 1

    def test_line_uses_usetool_line(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 32, 32)
        d.line(0, 0, 10, 10, 255, 255, 255)
        lua = d.get_lua()
        assert 'app.useTool' in lua
        assert 'tool="line"' in lua
        assert 'Point(0,0)' in lua
        assert 'Point(10,10)' in lua

    def test_flood_fill_generates_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 32, 32)
        d.flood_fill(16, 16, 255, 0, 0, tolerance=5)
        lua = d.get_lua()
        assert 'tool="paint_bucket"' in lua
        assert 'tolerance=5' in lua

    def test_ellipse_generates_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 64, 64)
        d.ellipse(10, 10, 40, 30, 0, 255, 0, fill=True)
        lua = d.get_lua()
        assert 'tool="filled_ellipse"' in lua
        assert 'Point(10,10)' in lua
        assert 'Point(49,39)' in lua  # 10+40-1, 10+30-1

    def test_chain_builds_script(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/out.png", 16, 16)
        d.fill(0, 0, 0)
        d.pixel(8, 8, 255, 255, 255)
        d.rect(2, 2, 4, 4, 255, 0, 0)
        d.line(0, 0, 15, 15, 0, 255, 0)
        lua = d.get_lua()
        lines = lua.split('\n')
        assert len(lines) >= 5  # prologue + fill + pixel + rect + line
        assert lua.count('app.useTool') >= 4

    def test_dry_run_no_execution(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d._dry_run = True
        d.new("/out.png", 8, 8)
        result = d.save()
        assert result["dry_run"] is True
        assert "lua" in result

    def test_save_no_path_raises(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        with pytest.raises(RuntimeError, match="output path"):
            d.save()

    def test_get_lua_returns_string(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/x.png", 4, 4)
        lua = d.get_lua()
        assert isinstance(lua, str)
        assert lua.startswith('app.command.NewFile')

    def test_erase_generates_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 32, 32)
        d.erase(5, 5, 10, 10)
        lua = d.get_lua()
        assert 'tool="eraser"' in lua

    def test_polyline_generates_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.new("/t.png", 32, 32)
        d.polyline([(0, 0), (10, 10), (20, 5)], 255, 0, 0)
        lua = d.get_lua()
        assert 'tool="contour"' in lua
        assert 'Point(0,0)' in lua
        assert 'Point(20,5)' in lua

    def test_raw_adds_arbitrary_lua(self):
        from cli_anything.aseprite.core.draw import Draw
        d = Draw()
        d.raw("-- custom comment")
        d.raw("app.command.Something()")
        lua = d.get_lua()
        assert '-- custom comment' in lua
        assert 'app.command.Something()' in lua


# ── Helpers Tests ─────────────────────────────────────────────────


class TestHelpers:
    """Unit tests for utility helpers."""

    def test_resolve_aseprite_bin_override(self):
        from cli_anything.aseprite.utils.helpers import resolve_aseprite_bin
        result = resolve_aseprite_bin("/custom/bin/aseprite")
        assert result == "/custom/bin/aseprite"

    def test_resolve_aseprite_bin_not_found(self):
        from cli_anything.aseprite.utils.helpers import resolve_aseprite_bin
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="aseprite"):
                resolve_aseprite_bin()

    def test_resolve_aseprite_bin_from_path(self):
        from cli_anything.aseprite.utils.helpers import resolve_aseprite_bin
        with patch("shutil.which", return_value="/usr/bin/aseprite"):
            result = resolve_aseprite_bin()
            assert result == "/usr/bin/aseprite"

    def test_json_output_format(self):
        from cli_anything.aseprite.utils.helpers import JSONOutput
        data = {"key": "value", "list": [1, 2, 3]}
        formatted = JSONOutput.format(data)
        parsed = json.loads(formatted)
        assert parsed == data
        # Verify it's indented
        assert "\n" in formatted
