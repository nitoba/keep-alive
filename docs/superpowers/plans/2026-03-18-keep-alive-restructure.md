# Keep Alive Restructure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Update:** A compatibilidade com `main.py` foi removida depois da aprovacao inicial do plano. Ao executar este trabalho, trate `python -m keep_alive` e `keep-alive` como entradas oficiais e desconsidere as etapas de compatibilidade com `main.py`.

**Goal:** Reorganizar o projeto em um pacote Python modular, mantendo o comportamento atual de simulacao, execucao em background/foreground e autostart por sistema operacional.

**Architecture:** A implementacao sera dividida em um pacote `keep_alive/` com modulos pequenos por responsabilidade. `main.py` vira apenas uma camada de compatibilidade, enquanto `keep_alive.cli` passa a ser o ponto central da interface de linha de comando e delega para modulos de schedule, simulacao, processo e instaladores por plataforma.

**Tech Stack:** Python 3.14, argparse, pyautogui, croniter, psutil, subprocess, uv

---

## Chunk 1: Core Package Refactor

### Task 1: Create package structure and shared runtime modules

**Files:**
- Create: `keep_alive/__init__.py`
- Create: `keep_alive/config.py`
- Create: `keep_alive/paths.py`
- Create: `keep_alive/logging_utils.py`
- Create: `keep_alive/runtime.py`

- [ ] **Step 1: Create the package skeleton**

Create the `keep_alive/` directory and add the package entry files.

- [ ] **Step 2: Move stable constants into shared modules**

Put service name, CLI defaults, supported methods and cron presets into `keep_alive/config.py`. Put project root, runtime directory, log path and pid path into `keep_alive/paths.py`.

- [ ] **Step 3: Add runtime helpers**

Move logging setup to `keep_alive/logging_utils.py`. Move environment helpers like python executable resolution, `DISPLAY` detection and session-type lookup to `keep_alive/runtime.py`.

- [ ] **Step 4: Keep entrypoint work deferred until the CLI exists**

Do not modify published entrypoints yet. Keep package scaffolding focused on shared modules so the project does not enter an intermediate broken state before `keep_alive/cli.py` exists.

- [ ] **Step 5: Verify package imports and legacy entrypoint stability**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `python main.py --help`
Expected: existing help text still renders successfully because scaffolding alone must not break the legacy entrypoint

- [ ] **Step 6: Commit**

```bash
git add keep_alive
git commit -m "refactor: scaffold keep_alive package"
```

### Task 2: Split scheduling and simulation logic out of the monolith

**Files:**
- Create: `keep_alive/schedule.py`
- Create: `keep_alive/simulator.py`

- [ ] **Step 1: Extract cron scheduling**

Move `CronSchedule` and cron formatting helpers into `keep_alive/schedule.py`, importing presets from `keep_alive.config`.

- [ ] **Step 2: Extract simulation strategies**

Move Discord detection, window focus helpers, simulation methods and `ActivitySimulator` into `keep_alive/simulator.py`.

- [ ] **Step 3: Keep behavior intact while changing module boundaries**

Do not redesign the simulation flow. Preserve current logic for interval jitter, active window waiting, Discord checks, focus behavior and loop logging. Copy code into the new modules first if needed, but do not cut over `main.py` yet in this task.

- [ ] **Step 4: Verify module compilation and legacy entrypoint stability**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `python main.py --help`
Expected: existing help text still renders successfully because the monolithic entrypoint remains the active implementation until Task 3

- [ ] **Step 5: Commit**

```bash
git add keep_alive/schedule.py keep_alive/simulator.py
git commit -m "refactor: extract schedule and simulator modules"
```

### Task 3: Extract process lifecycle and CLI dispatch

**Files:**
- Create: `keep_alive/process_manager.py`
- Create: `keep_alive/cli.py`
- Create: `keep_alive/__main__.py`
- Modify: `main.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Move process lifecycle code**

Move PID handling, daemonization, `stop`, `status`, `logs` and shared simulator startup flow into `keep_alive/process_manager.py`.

- [ ] **Step 2: Build the new CLI entrypoint**

Implement the `argparse` parser in `keep_alive/cli.py`, keeping the current subcommands and flags unless a small adjustment is clearly justified. Dispatch commands to `process_manager` and simulator startup immediately. For `install` and `uninstall`, keep a temporary compatibility path local to `cli.py` until the dedicated installer package exists in Task 5, so the published entrypoint never points at missing modules.

- [ ] **Step 3: Convert `main.py` into compatibility wrapper**

Replace the monolithic contents of `main.py` with a thin wrapper that imports and calls `keep_alive.cli.main`.

- [ ] **Step 4: Update published entrypoints only after the CLI exists**

Update `pyproject.toml` so the console script points to `keep_alive.cli:main`. Ensure `keep_alive/__main__.py` also routes to the same entrypoint.

- [ ] **Step 5: Verify both entry styles**

Run: `python -m keep_alive --help`
Expected: help text renders successfully

Run: `python main.py --help`
Expected: help text renders successfully and matches the package CLI behavior

- [ ] **Step 6: Verify all existing subcommands still resolve in the parser**

Run: `python -m keep_alive start --help`
Expected: help text renders successfully

Run: `python -m keep_alive run --help`
Expected: help text renders successfully

Run: `python -m keep_alive logs --help`
Expected: help text renders successfully

Run: `python -m keep_alive install --help`
Expected: help text renders successfully

Run: `python -m keep_alive stop --help`
Expected: help text renders successfully

Run: `python -m keep_alive status --help`
Expected: help text renders successfully

Run: `python -m keep_alive uninstall --help`
Expected: help text renders successfully

- [ ] **Step 7: Verify key subcommands execute without destructive actions**

Run: `python -m keep_alive status`
Expected: command executes without import/path errors, even if it reports that no daemon is running

Run: `python -m keep_alive logs -n 1`
Expected: command executes without import/path errors, even if it reports that the log file does not exist yet

Run: `python main.py status`
Expected: command executes with the same behavior as the package entrypoint

- [ ] **Step 8: Commit**

```bash
git add keep_alive/process_manager.py keep_alive/cli.py keep_alive/__main__.py main.py pyproject.toml
git commit -m "refactor: move process lifecycle and cli into package"
```

## Chunk 2: Platform Integration and Documentation

### Task 4: Move runtime artifacts to `var/` and update process consumers

**Files:**
- Modify: `keep_alive/paths.py`
- Modify: `keep_alive/process_manager.py`
- Modify: `keep_alive/cli.py`
- Modify: `.gitignore`

- [ ] **Step 1: Finalize runtime directory behavior**

Ensure `var/` is created lazily when commands need log or PID access. Make all runtime file references go through `keep_alive.paths`.

- [ ] **Step 2: Update process consumers**

Verify that status, logs, stop and daemon startup all point to the `var/` paths and do not use duplicated root-level file paths.

- [ ] **Step 3: Update the temporary install compatibility path**

If `install` and `uninstall` are still temporarily routed through `cli.py`, update that temporary path now so it also depends on the shared runtime and entrypoint helpers. Do not leave a committed state where runtime consumers use `var/` but the temporary installer path still reflects old root-level assumptions.

- [ ] **Step 4: Run runtime-path verification**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `python -m keep_alive status`
Expected: command executes and references the new runtime paths when applicable

Run: `python -m keep_alive logs -n 1`
Expected: command executes without import/path errors, even if it reports that the log file does not exist yet under `var/`

Run: `python main.py status`
Expected: command executes with the same runtime-path behavior

Run: `rg -n "PID_FILE|LOG_FILE|RUNTIME_DIR|ensure_runtime_dir" keep_alive/process_manager.py keep_alive/paths.py`
Expected: runtime file handling is centralized through shared helpers, not duplicated root-level literals

- [ ] **Step 5: Commit**

```bash
git add keep_alive/paths.py keep_alive/process_manager.py keep_alive/cli.py .gitignore
git commit -m "refactor: centralize runtime files under var"
```

### Task 5: Isolate autostart installers by platform

**Files:**
- Create: `keep_alive/installers/__init__.py`
- Create: `keep_alive/installers/linux.py`
- Create: `keep_alive/installers/macos.py`
- Create: `keep_alive/installers/windows.py`
- Modify: `keep_alive/cli.py`
- Modify: `keep_alive/runtime.py`
- Modify: `keep_alive/paths.py`

- [ ] **Step 1: Move Linux autostart logic**

Put systemd service generation and uninstall flow into `keep_alive/installers/linux.py`.

- [ ] **Step 2: Move macOS autostart logic**

Put launchd plist generation and uninstall flow into `keep_alive/installers/macos.py`.

- [ ] **Step 3: Move Windows autostart logic**

Put Task Scheduler creation and uninstall flow into `keep_alive/installers/windows.py`.

- [ ] **Step 4: Add platform dispatch**

Implement a package-level installer dispatcher in `keep_alive/installers/__init__.py` so the CLI can call one install/uninstall API independent of platform. Expose a non-destructive resolver such as `resolve_installer_module()` in addition to the side-effectful install/uninstall wrappers.

- [ ] **Step 5: Expose pure command builders before wiring side effects**

In each installer module, create pure helpers that build the generated service/plist/task content or command strings before the actual install/uninstall functions apply side effects. Make the CLI switch from the temporary compatibility path in `cli.py` to the real installer dispatcher only after these builders and wrappers exist.

- [ ] **Step 6: Repoint generated commands to the new package entrypoint**

Review every generated command string and make it use the new package execution path consistently. Preserve the installer arguments `--cron`, `--interval`, `--method` and conditional `--focus` across Linux, macOS and Windows. Runtime file paths must come from shared helpers, not duplicated literals.

- [ ] **Step 7: Verify generated installer content explicitly**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `rg -n -- \"python -m keep_alive|--cron|--interval|--method|--focus\" keep_alive/installers`
Expected: output shows Linux, macOS and Windows installer code preserving `--cron`, `--interval`, `--method` and conditional `--focus` while routing through the shared package entrypoint or shared command builder

Run: `python -c "from types import SimpleNamespace as NS; from keep_alive.installers.linux import build_service_content; from keep_alive.installers.macos import build_plist_content; from keep_alive.installers.windows import build_task_command; args = NS(cron='comercial', interval=120, method='combined', focus=True); print('--cron' in build_service_content(args)); print('--interval' in build_service_content(args)); print('--method' in build_service_content(args)); print('--focus' in build_service_content(args)); print('--cron' in build_plist_content(args)); print('--interval' in build_plist_content(args)); print('--method' in build_plist_content(args)); print('--focus' in build_plist_content(args)); print('--cron' in build_task_command(args)); print('--interval' in build_task_command(args)); print('--method' in build_task_command(args)); print('--focus' in build_task_command(args))"`
Expected: prints only `True` lines, confirming the generated installer payloads preserve all required arguments without executing installation side effects

Run: `python -c "from keep_alive.installers import resolve_installer_module; print(resolve_installer_module().__name__)"`
Expected: prints the current platform installer module path, confirming that non-destructive installer dispatch resolution works through the real package API

- [ ] **Step 8: Commit**

```bash
git add keep_alive/installers keep_alive/cli.py keep_alive/runtime.py keep_alive/paths.py
git commit -m "refactor: split platform installers"
```

### Task 6: Update documentation and usage examples

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Update the README**

Document the new package structure, new execution forms (`python -m keep_alive` and console script), compatibility path via `python main.py`, and the new runtime file location.

- [ ] **Step 2: Update visible package metadata where needed**

Ensure the documented command examples and published console entrypoint in `pyproject.toml` match the final CLI.

- [ ] **Step 3: Run end-to-end verification commands**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `python -m keep_alive --help`
Expected: help text renders successfully

Run: `python main.py --help`
Expected: help text renders successfully

Run: `python -m keep_alive status`
Expected: command executes and references the new runtime paths when applicable

- [ ] **Step 4: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs: update package usage and structure"
```

### Task 7: Final review and cleanup

**Files:**
- Review: `keep_alive/`
- Review: `main.py`
- Review: `README.md`
- Review: `pyproject.toml`

- [ ] **Step 1: Remove dead imports and stale code paths**

Review the final tree and delete any leftovers from the monolithic implementation that are no longer referenced.

- [ ] **Step 2: Run final verification**

Run: `python -m compileall keep_alive main.py`
Expected: command completes without syntax errors

Run: `python -m keep_alive --help`
Expected: help text renders successfully

Run: `python main.py --help`
Expected: help text renders successfully

Run: `python -m keep_alive status`
Expected: command executes without import errors and reflects the shared runtime-path behavior

Run: `python main.py status`
Expected: command executes without import errors or stale path references

- [ ] **Step 3: Commit**

```bash
git add keep_alive main.py README.md pyproject.toml .gitignore
git commit -m "chore: clean up package refactor"
```
