# TEST.md — Test Plan and Results for cli-anything-aseprite

## Test Strategy

- **Unit tests** (`test_core.py`): Synthetic data, mocked subprocess, no external deps
- **E2E tests** (`test_full_e2e.py`): Real modules in dry-run mode, workflow simulations
- **CLI tests**: Subprocess invocation via `_resolve_cli()` with `CLI_ANYTHING_FORCE_INSTALLED=1`

## Test Plan

### Unit Tests (test_core.py)

| # | Test | Module | Description |
|---|------|--------|-------------|
| 1 | `TestProject::test_init` | project | Project initializes with default bin |
| 2 | `TestProject::test_init_custom_bin` | project | Custom binary path accepted |
| 3 | `TestProject::test_open_file_not_found` | project | FileNotFound raised for missing files |
| 4 | `TestProject::test_dry_run_no_execution` | project | Dry run returns synthetic success |
| 5 | `TestProject::test_gather_info_parses_json` | project | JSON metadata parsed into SpriteInfo |
| 6 | `TestProject::test_extract_layers` | project | Layer list extracted from JSON |
| 7 | `TestProject::test_extract_tags` | project | Frame tags extracted from JSON |
| 8 | `TestProject::test_extract_slices` | project | Slices extracted from JSON |
| 9 | `TestProject::test_close_clears_sprite` | project | Close() releases sprite |
| 10 | `TestProject::test_save_no_sprite_raises` | project | Save without sprite raises |
| 11 | `TestProject::test_info_no_sprite_no_path_raises` | project | Info without sprite raises |
| 12 | `TestSession::test_init` | session | Session initializes empty |
| 13 | `TestSession::test_init_dry_run` | session | Dry run propagates to project |
| 14 | `TestSession::test_to_dict_empty` | session | Empty session serializes correctly |
| 15 | `TestSession::test_to_json_empty` | session | Empty session JSON is valid |
| 16 | `TestSession::test_list_sprites_empty` | session | Empty session lists no sprites |
| 17 | `TestSession::test_session_state_dataclass` | session | State dataclass works |
| 18 | `TestExporter::test_init` | export | Exporter initializes |
| 19 | `TestExporter::test_dry_run_no_execution` | export | Dry run suppresses execution |
| 20 | `TestExporter::test_export_frame_args` | export | Correct args for frame export |
| 21 | `TestExporter::test_export_sheet_builds_args` | export | Correct args for sheet export |
| 22 | `TestLayers::test_list_parses_json` | layers | Layer list parses correctly |
| 23 | `TestLayers::test_list_names` | layers | Layer names extracted |
| 24 | `TestTagsClass::test_list_parses_json` | tags_slices | Tags parsed correctly |
| 25 | `TestSlicesClass::test_list_parses_json` | tags_slices | Slices parsed correctly |
| 26 | `TestPaletteClass::test_list_entries_empty` | palette | Empty palette handled |
| 27 | `TestScriptRunner::test_run_with_params` | script | Script runner passes params |
| 28 | `TestScriptRunner::test_run_parses_json_stdout` | script | JSON stdout auto-parsed |
| 29 | `TestScriptRunner::test_run_dry_run` | script | Dry run for scripts |
| 30 | `TestScriptRunner::test_run_inline_writes_temp_file` | script | Inline code writes temp file |
| 31 | `TestScriptRunner::test_run_stderr_captured` | script | Stderr captured on error |
| 32 | `TestHelpers::test_resolve_aseprite_bin_override` | helpers | Bin path override |
| 33 | `TestHelpers::test_resolve_aseprite_bin_not_found` | helpers | Missing bin raises |
| 34 | `TestHelpers::test_resolve_aseprite_bin_from_path` | helpers | Bin found in PATH |
| 35 | `TestHelpers::test_json_output_format` | helpers | JSON output helper works |

### E2E Tests (test_full_e2e.py)

| # | Test | Description |
|---|------|-------------|
| 36 | `TestCLISubprocess::test_cli_help` | CLI module loads |
| 37 | `TestCLISubprocess::test_session_state_serialization` | State round-trips through JSON |
| 38 | `TestE2EPipeline::test_full_pipeline_dry_run` | Full session pipeline |
| 39 | `TestE2EPipeline::test_exporter_dry_run` | Exporter dry run |
| 40 | `TestE2EPipeline::test_layers_dry_run` | Layers dry run |
| 41 | `TestE2EPipeline::test_tags_dry_run` | Tags dry run |
| 42 | `TestE2EPipeline::test_slices_dry_run` | Slices dry run |
| 43 | `TestE2EPipeline::test_palette_dry_run` | Palette dry run |
| 44 | `TestE2EPipeline::test_script_runner_dry_run` | Script runner dry run |
| 45 | `TestE2EPipeline::test_inline_script_dry_run` | Inline script dry run |
| 46 | `TestWorkflows::test_typical_animation_export_workflow` | Animation export flow |
| 47 | `TestWorkflows::test_sprite_inspection_workflow` | Inspection flow |
| 48 | `TestWorkflows::test_batch_export_workflow` | Batch export flow |
| 49 | `TestJSONOutput::test_session_to_json` | Session JSON format |
| 50 | `TestJSONOutput::test_sprite_info_serialization` | SpriteInfo serialization |
| 51 | `TestJSONOutput::test_json_helper_format` | JSON helper formatting |
| 52 | `TestErrorHandling::test_file_not_found` | File not found error |
| 53 | `TestErrorHandling::test_no_sprite_save` | Save without sprite |
| 54 | `TestErrorHandling::test_no_sprite_info` | Info without sprite |
| 55 | `TestErrorHandling::test_session_close_stale` | Close nonexistent |
| 56 | `TestErrorHandling::test_palette_load_dry_run` | Palette load dry run |
| 57 | `TestErrorHandling::test_script_stderr_dry_run` | Script error dry run |
| 58 | `TestDrawClass::test_init` | draw | Draw initializes |
| 59 | `TestDrawClass::test_new_builds_lua` | draw | new() builds correct Lua |
| 60 | `TestDrawClass::test_pixel_adds_putpixel` | draw | pixel() generates putPixel |
| 61 | `TestDrawClass::test_fill_generates_loop` | draw | fill() generates nested loops |
| 62 | `TestDrawClass::test_rect_fill_and_outline` | draw | rect() fill vs outline modes |
| 63 | `TestDrawClass::test_circle_generates_lua` | draw | circle() distance check |
| 64 | `TestDrawClass::test_line_bresenham` | draw | line() Bresenham algo |
| 65 | `TestDrawClass::test_chain_builds_script` | draw | Chained calls build full script |
| 66 | `TestDrawClass::test_dry_run_no_execution` | draw | Dry run returns Lua without exec |
| 67 | `TestDrawClass::test_save_no_path_raises` | draw | Save without path raises |
| 68 | `TestDrawClass::test_get_lua_returns_string` | draw | get_lua() returns valid Lua |
| 69 | `TestExporter::test_export_sheet_with_crop` | export | Crop option passes x,y,w,h |
| 70 | `TestExporter::test_export_sheet_all_options` | export | All new sheet flags pass through |
| 71 | `TestExporter::test_export_frame_with_kwargs` | export | Frame export accepts kwargs |
| 72 | `TestExporter::test_export_gif_with_options` | export | GIF export accepts full options |
| 73 | `TestExporter::test_export_tileset_with_kwargs` | export | Tileset export accepts kwargs |
| 74 | `TestExporter::test_build_args_static_method` | export | _build_args converts dict to CLI flags |
| 75 | `TestExpandedExport::test_export_sheet_crop_option` | export | Sheet crop dry-run |
| 76 | `TestExpandedExport::test_export_sheet_ignore_empty` | export | Sheet ignore-empty + merge-duplicates |
| 77 | `TestExpandedExport::test_export_sheet_split_grid` | export | Sheet split-grid + all-layers |
| 78 | `TestExpandedExport::test_export_sheet_color_and_format` | export | Sheet color-mode + pixel-format + dpi |
| 79 | `TestExpandedExport::test_export_sheet_oneframe` | export | Sheet oneframe flag |
| 80 | `TestExpandedExport::test_export_frame_with_new_options` | export | Frame with scale/trim/color/dpi/tag |
| 81 | `TestExpandedExport::test_export_gif_with_full_options` | export | GIF with scale/frame-range/color/dpi |
| 82 | `TestExpandedExport::test_export_tileset_with_new_options` | export | Tileset with all new flags |
| 83 | `TestExpandedExport::test_export_gif_dry_run_pipeline` | export | GIF dry run pipeline |

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\aseprite\agent-harness
collected 83 items

test_core.py::TestProject::test_init PASSED                                   [  1%]
test_core.py::TestProject::test_init_custom_bin PASSED                        [  2%]
test_core.py::TestProject::test_open_file_not_found PASSED                    [  3%]
test_core.py::TestProject::test_dry_run_no_execution PASSED                   [  4%]
test_core.py::TestProject::test_gather_info_parses_json PASSED                [  6%]
test_core.py::TestProject::test_extract_layers PASSED                         [  7%]
test_core.py::TestProject::test_extract_tags PASSED                           [  8%]
test_core.py::TestProject::test_extract_slices PASSED                         [  9%]
test_core.py::TestProject::test_close_clears_sprite PASSED                    [ 10%]
test_core.py::TestProject::test_save_no_sprite_raises PASSED                  [ 12%]
test_core.py::TestProject::test_info_no_sprite_no_path_raises PASSED          [ 13%]
test_core.py::TestSession::test_init PASSED                                   [ 14%]
test_core.py::TestSession::test_init_dry_run PASSED                           [ 15%]
test_core.py::TestSession::test_to_dict_empty PASSED                          [ 16%]
test_core.py::TestSession::test_to_json_empty PASSED                          [ 18%]
test_core.py::TestSession::test_list_sprites_empty PASSED                     [ 19%]
test_core.py::TestSession::test_session_state_dataclass PASSED                [ 20%]
test_core.py::TestExporter::test_init PASSED                                  [ 21%]
test_core.py::TestExporter::test_dry_run_no_execution PASSED                  [ 22%]
test_core.py::TestExporter::test_export_frame_args PASSED                     [ 24%]
test_core.py::TestExporter::test_export_sheet_builds_args PASSED              [ 25%]
test_core.py::TestExporter::test_export_sheet_with_crop PASSED                [ 26%]
test_core.py::TestExporter::test_export_sheet_all_options PASSED              [ 27%]
test_core.py::TestExporter::test_export_frame_with_kwargs PASSED              [ 28%]
test_core.py::TestExporter::test_export_gif_with_options PASSED               [ 30%]
test_core.py::TestExporter::test_export_tileset_with_kwargs PASSED            [ 31%]
test_core.py::TestExporter::test_build_args_static_method PASSED              [ 32%]
test_core.py::TestLayers::test_list_parses_json PASSED                        [ 33%]
test_core.py::TestLayers::test_list_names PASSED                              [ 34%]
test_core.py::TestTagsClass::test_list_parses_json PASSED                     [ 36%]
test_core.py::TestSlicesClass::test_list_parses_json PASSED                   [ 37%]
test_core.py::TestPaletteClass::test_list_entries_empty PASSED                [ 38%]
test_core.py::TestScriptRunner::test_run_with_params PASSED                   [ 39%]
test_core.py::TestScriptRunner::test_run_parses_json_stdout PASSED            [ 40%]
test_core.py::TestScriptRunner::test_run_dry_run PASSED                       [ 42%]
test_core.py::TestScriptRunner::test_run_inline_writes_temp_file PASSED       [ 43%]
test_core.py::TestScriptRunner::test_run_stderr_captured PASSED               [ 44%]
test_core.py::TestDrawClass::test_init PASSED                                 [ 45%]
test_core.py::TestDrawClass::test_new_builds_lua PASSED                       [ 46%]
test_core.py::TestDrawClass::test_pixel_adds_putpixel PASSED                  [ 48%]
test_core.py::TestDrawClass::test_fill_generates_loop PASSED                  [ 49%]
test_core.py::TestDrawClass::test_rect_fill_and_outline PASSED                [ 50%]
test_core.py::TestDrawClass::test_circle_generates_lua PASSED                 [ 51%]
test_core.py::TestDrawClass::test_line_bresenham PASSED                       [ 53%]
test_core.py::TestDrawClass::test_chain_builds_script PASSED                  [ 54%]
test_core.py::TestDrawClass::test_dry_run_no_execution PASSED                 [ 55%]
test_core.py::TestDrawClass::test_save_no_path_raises PASSED                  [ 56%]
test_core.py::TestDrawClass::test_get_lua_returns_string PASSED               [ 57%]
test_core.py::TestHelpers::test_resolve_aseprite_bin_override PASSED          [ 59%]
test_core.py::TestHelpers::test_resolve_aseprite_bin_not_found PASSED         [ 60%]
test_core.py::TestHelpers::test_resolve_aseprite_bin_from_path PASSED         [ 61%]
test_core.py::TestHelpers::test_json_output_format PASSED                     [ 62%]
test_full_e2e.py::TestCLISubprocess::test_cli_help PASSED                     [ 63%]
test_full_e2e.py::TestCLISubprocess::test_session_state_serialization PASSED  [ 65%]
test_full_e2e.py::TestE2EPipeline::test_full_pipeline_dry_run PASSED          [ 66%]
test_full_e2e.py::TestE2EPipeline::test_exporter_dry_run PASSED               [ 67%]
test_full_e2e.py::TestE2EPipeline::test_layers_dry_run PASSED                 [ 68%]
test_full_e2e.py::TestE2EPipeline::test_tags_dry_run PASSED                   [ 69%]
test_full_e2e.py::TestE2EPipeline::test_slices_dry_run PASSED                 [ 71%]
test_full_e2e.py::TestE2EPipeline::test_palette_dry_run PASSED                [ 72%]
test_full_e2e.py::TestE2EPipeline::test_script_runner_dry_run PASSED          [ 73%]
test_full_e2e.py::TestE2EPipeline::test_inline_script_dry_run PASSED          [ 74%]
test_full_e2e.py::TestWorkflows::test_typical_animation_export_workflow PASSED [ 75%]
test_full_e2e.py::TestWorkflows::test_sprite_inspection_workflow PASSED       [ 77%]
test_full_e2e.py::TestWorkflows::test_batch_export_workflow PASSED            [ 78%]
test_full_e2e.py::TestJSONOutput::test_session_to_json PASSED                 [ 79%]
test_full_e2e.py::TestJSONOutput::test_sprite_info_serialization PASSED       [ 80%]
test_full_e2e.py::TestJSONOutput::test_json_helper_format PASSED              [ 81%]
test_full_e2e.py::TestErrorHandling::test_file_not_found PASSED               [ 83%]
test_full_e2e.py::TestErrorHandling::test_no_sprite_save PASSED               [ 84%]
test_full_e2e.py::TestErrorHandling::test_no_sprite_info PASSED               [ 85%]
test_full_e2e.py::TestErrorHandling::test_session_close_stale PASSED          [ 86%]
test_full_e2e.py::TestErrorHandling::test_palette_load_dry_run PASSED         [ 87%]
test_full_e2e.py::TestErrorHandling::test_script_stderr_dry_run PASSED        [ 89%]
test_full_e2e.py::TestExpandedExport::test_export_sheet_crop_option PASSED    [ 90%]
test_full_e2e.py::TestExpandedExport::test_export_sheet_ignore_empty PASSED   [ 91%]
test_full_e2e.py::TestExpandedExport::test_export_sheet_split_grid PASSED     [ 92%]
test_full_e2e.py::TestExpandedExport::test_export_sheet_color_and_format PASSED [ 93%]
test_full_e2e.py::TestExpandedExport::test_export_sheet_oneframe PASSED       [ 95%]
test_full_e2e.py::TestExpandedExport::test_export_frame_with_new_options PASSED [ 96%]
test_full_e2e.py::TestExpandedExport::test_export_gif_with_full_options PASSED [ 97%]
test_full_e2e.py::TestExpandedExport::test_export_tileset_with_new_options PASSED [ 98%]
test_full_e2e.py::TestExpandedExport::test_export_gif_dry_run_pipeline PASSED [100%]

============================= 83 passed in 0.38s =============================
```

## Summary

| Metric | Value |
|--------|-------|
| Total tests | 83 |
| Passed | 83 |
| Failed | 0 |
| Duration | 0.38s |
| Python version | 3.13.2 |
| Platform | Windows 11 (win32) |
| Coverage | All 10 core modules + CLI + helpers + draw + expanded export |
