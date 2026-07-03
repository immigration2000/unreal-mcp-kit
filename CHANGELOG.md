# Changelog

All notable changes to unreal-mcp-kit.

## [1.7.0] - 2026-07-03
### Added
- **Modal-dialog handling** documented (5.8 CLAUDE.md + `ue5-8-mcp`): modal dialogs block the
  game thread, which also stalls the MCP server, so an already-open modal can't be dismissed by
  the agent. Prevent by launching the editor with `-unattended` (dialogs auto-return defaults;
  beware destructive prompts); detect by reading the Output Log for Error/Warning after each
  mutate instead of relying on the modal.
- **Blueprint variable default-value pattern** documented in the 5.8 CLAUDE.md template and the
  `ue5-8-mcp` skill: create var → `compile_blueprint` → set on the CDO via `set_editor_property`
  → save → read-back (load class with `_C`). Fixes the common bottleneck where the MCP creates
  an empty variable but can't fill its default value.
- **UE 5.7 support** via new `setup-ue57` skill. Since UE 5.7 has no official MCP plugin,
  it documents the community-server path: VibeUE (Blueprint/asset/editor tools, HTTP MCP on
  :8088) plus optional UnrealClaude (viewport capture + actor manipulation, MCP on :3000),
  Claude Code connection (`claude mcp add` via mcp-remote), and a 5.7 CLAUDE.md template
  (imports VibeUE's AGENTS.md.sample). The `ue5-8-mcp` gotcha skill is server-agnostic and
  applies to 5.7 as well.
### Changed
- Skill descriptions now gate by engine version so the correct one triggers without a router:
  `setup-ue58-mcp` = UE 5.8+, `setup-ue57` = UE 5.7; `ue5-8-mcp` marked server-agnostic (5.7 + 5.8).
- Removed dead `re` import from `setup_project.py` (unused since the deep-probe rewrite).

## [1.6.0] - 2026-07-03
### Changed
- **Retired the raw-HTTP toolset probe in `--deep`.** Wire-level investigation on a live
  UE 5.8 editor confirmed the server returns `tools/call` results as `text/event-stream` while
  closing the POST body empty (0 bytes); a simple `urllib` POST client can never receive it
  (MCP-Protocol-Version header, delays, separate GET stream → 405, and protocol downgrade all
  had no effect). Only a full MCP Streamable-HTTP client (e.g. Claude Code) consumes it.
  `--deep` now just prints an informational note. The canonical toolset-load check is the
  connected agent calling `list_toolsets` (confirmed: 19 toolsets on a working setup).
- Removed now-dead helpers (`_post`, `_extract_json`, `_collect_text`, `KNOWN_WORK_TOOLSETS`).

## [1.5.0] - 2026-07-03
### Fixed
- `--deep` toolset parsing now matches the real `list_toolsets` response format
  (`- Module.ToolsetName: description` text list), correctly distinguishing work toolsets
  from AgentSkillToolset-only. Validated against a live UE 5.8 editor's response (19 toolsets).
### Note
- The **canonical runtime check** is asking the connected agent to run `list_toolsets`
  (reliable — it uses the agent's own MCP client). `--deep` is a best-effort HTTP convenience
  and may still report "inconclusive" on some Streamable-HTTP session configs; that is not a
  failure. Confirmed working via list_toolsets = success.

## [1.4.0] - 2026-07-03
### Added
- Auto Start Server is now configured automatically: setup writes
  `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings] bAutoStartServer=True`
  into the project's `Config/DefaultEditorPerProjectUserSettings.ini` (preserves existing
  sections/keys, idempotent). Removes the manual "Editor Preferences → Auto Start Server" step;
  a restart is still needed once to load the newly enabled plugins. `--no-autostart` to skip.
- `--verify` now reports whether Auto Start Server is configured.

## [1.3.0] - 2026-07-03
### Added
- Offline functional test (`tests/test_setup.py` + `tests/sample.uproject`) that runs the setup
  script against a fixture and asserts: existing plugins preserved, MCP + EditorToolset (+Niagara)
  added/enabled, `.uproject.bak` created, `.mcp.json`/`CLAUDE.md` written, idempotent re-run,
  `--verify` fails when server down, `--deep` degrades without crashing. Wired into CI.

## [1.2.0] - 2026-07-03
### Added
- `--deep` (experimental): verify performs a real MCP handshake (`initialize` → `list_toolsets`)
  to confirm work toolsets actually loaded, catching the "server up but only AgentSkillToolset"
  failure at runtime. Degrades safely — never hard-fails on uncertainty.
- Friendly error on malformed `.uproject` (points to `.uproject.bak` for recovery).
- `--verify` server probe now notes its same-PC requirement (avoids false "server down" when
  the agent runs in a sandbox/remote).
- CI workflow validating JSON manifests and Python syntax on push.

## [1.1.0] - 2026-07-03
### Added
- `--verify` doctor mode: checks plugin activation, `.mcp.json`, and server reachability,
  with exact fix hints for each failure.
- `.uproject.bak` automatic backup before editing (`--no-backup` to skip).

## [1.0.0] - 2026-06-29
### Added
- `setup-ue58-mcp` skill + `setup_project.py`: enable `ModelContextProtocol` + `EditorToolset`
  in `.uproject`, write `.mcp.json`, copy `CLAUDE.md` (idempotent, preserves existing plugins).
- `ue5-8-mcp` knowledge skill: engine-level gotchas, reflection rules, crash patterns,
  tool-search workflow.
- Marketplace + plugin manifests, install scripts, MIT license.
