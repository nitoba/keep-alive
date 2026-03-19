# Keep Alive Release Distribution Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar binarios `PyInstaller` para `macOS` e `Linux` via GitHub Releases e oferecer um `install.sh` para usuarios que nao querem Python nem clone do repositorio.

**Architecture:** A distribuicao sera feita por uma pipeline de GitHub Actions disparada por tags `v*`, que builda o CLI atual com `PyInstaller`, gera assets por plataforma e os anexa ao Release. Um `install.sh` versionado no repositorio detecta a plataforma do usuario, baixa o asset correto do Release e instala em `~/.local/bin/keep-alive`.

**Tech Stack:** GitHub Actions, PyInstaller, bash, Python, GitHub Releases

---

## Chunk 1: Build and Installer

### Task 1: Add PyInstaller packaging inputs

**Files:**
- Modify: `pyproject.toml`
- Create: `pyinstaller.spec`

- [ ] **Step 1: Add build dependency metadata**

Add the minimum project metadata needed for reliable builds, and if appropriate add `PyInstaller` to an optional dependency group or document it only in the build script. Do not change the runtime CLI entrypoint.

- [ ] **Step 2: Add a dedicated `PyInstaller` spec**

Create `pyinstaller.spec` so build configuration lives in the repo instead of being embedded inline in CI YAML. The generated executable name must be `keep-alive`.

- [ ] **Step 3: Ensure the spec targets the current CLI entrypoint**

Package the current `keep_alive` CLI without reworking the app architecture again.

- [ ] **Step 4: Verify Python package still loads**

Run: `python -m compileall keep_alive`
Expected: command completes without syntax errors

Run: `python -m keep_alive --help`
Expected: help text renders successfully

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml pyinstaller.spec
git commit -m "build: add pyinstaller packaging inputs"
```

### Task 2: Add build and install scripts

**Files:**
- Create: `scripts/build-pyinstaller.sh`
- Create: `scripts/install.sh`

- [ ] **Step 1: Add the build script**

Create `scripts/build-pyinstaller.sh` to install build-time dependencies, invoke `PyInstaller` through the spec file, and emit a normalized artifact into a canonical output path:
- `dist/release/keep-alive-linux`
- `dist/release/keep-alive-macos`

- [ ] **Step 2: Add the release installer script**

Create `scripts/install.sh` to:
- detect `macOS` or `Linux`
- select the expected asset name for the current platform
- download the binary from a GitHub Release
- install it to `~/.local/bin/keep-alive`
- mark it executable
- print PATH guidance and next-step commands

- [ ] **Step 3: Keep the installer auditably simple**

Do not edit shell startup files, configure autostart, or assume root privileges.

- [ ] **Step 4: Verify script syntax**

Run: `bash -n scripts/build-pyinstaller.sh`
Expected: no syntax errors

Run: `bash -n scripts/install.sh`
Expected: no syntax errors

- [ ] **Step 5: Verify installer asset mapping by inspection**

Run: `rg -n "keep-alive-(linux|macos)|~/.local/bin|curl|wget|github.com/.*/releases/download" scripts/install.sh`
Expected: installer logic clearly references supported assets, install path, and release download flow

- [ ] **Step 6: Commit**

```bash
git add scripts/build-pyinstaller.sh scripts/install.sh
git commit -m "build: add release build and install scripts"
```

## Chunk 2: Release Automation and Docs

### Task 3: Add GitHub Actions release workflow

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `scripts/build-pyinstaller.sh`
- Modify: `scripts/install.sh`

- [ ] **Step 1: Add the release workflow**

Create a workflow triggered by tags matching `v*`.

- [ ] **Step 2: Build binaries in a platform matrix**

Use a matrix with `ubuntu-latest` and `macos-latest`. Each job must:
- checkout the repo
- set up Python
- install dependencies
- run `scripts/build-pyinstaller.sh`
- upload or attach the generated binary

- [ ] **Step 3: Publish release assets consistently**

Ensure the workflow creates or updates the matching GitHub Release and publishes:
- `keep-alive-linux`
- `keep-alive-macos`
- `install.sh`

If a temporary artifact directory is used, keep final Release asset names stable and predictable.

- [ ] **Step 4: Keep installer and workflow naming aligned**

The asset names used in `scripts/install.sh` must exactly match the asset names uploaded by the workflow.

- [ ] **Step 5: Verify workflow and script consistency**

Run: `rg -n "keep-alive-linux|keep-alive-macos|install.sh|refs/tags/v|ubuntu-latest|macos-latest" .github/workflows/release.yml scripts/install.sh scripts/build-pyinstaller.sh`
Expected: workflow and installer use the same asset names and tag-trigger assumptions

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/release.yml scripts/build-pyinstaller.sh scripts/install.sh
git commit -m "ci: add release workflow for binary distribution"
```

### Task 4: Update documentation for both distribution paths

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document binary distribution**

Add a section for users without Python covering:
- GitHub Release binaries
- `curl | bash` installer usage
- manual asset download

- [ ] **Step 2: Preserve the Git tag install path**

Keep the documented `uv tool`, `pipx`, and `uvx` flows for users who do want a Python-based install.

- [ ] **Step 3: Document release publishing**

Explain the publishing flow clearly:
- commit to `main`
- create tag `vX.Y.Z`
- push tag
- wait for the release workflow to finish

- [ ] **Step 4: Document platform limitations**

State that:
- support currently targets `macOS` and `Linux`
- the binary does not bypass OS accessibility or graphical-session requirements

- [ ] **Step 5: Verify docs reference current commands**

Run: `rg -n "uv tool install|pipx install|uvx --from|curl -fsSL|GitHub Release|PyInstaller|git tag v[0-9]+\\.[0-9]+\\.[0-9]+|git push origin v[0-9]+\\.[0-9]+\\.[0-9]+" README.md`
Expected: docs cover both install paths and release versioning examples coherently without depending on a single hard-coded version

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: add binary release installation guidance"
```

## Chunk 3: Verification and Release Publication

### Task 5: Run local pre-release verification

**Files:**
- Review: `pyinstaller.spec`
- Review: `scripts/build-pyinstaller.sh`
- Review: `scripts/install.sh`
- Review: `.github/workflows/release.yml`
- Review: `README.md`

- [ ] **Step 1: Verify the Python CLI still works**

Run: `python -m compileall keep_alive`
Expected: command completes without syntax errors

Run: `python -m keep_alive --help`
Expected: help text renders successfully

- [ ] **Step 2: Verify shell scripts**

Run: `bash -n scripts/build-pyinstaller.sh`
Expected: no syntax errors

Run: `bash -n scripts/install.sh`
Expected: no syntax errors

- [ ] **Step 3: Smoke-check local binary build if environment permits**

Run: `bash scripts/build-pyinstaller.sh`
Expected: script completes and produces a platform-named executable in the expected output directory

Run: `find dist/release -maxdepth 1 -type f -name "keep-alive-*" -print`
Expected: exactly one platform-named executable is present for the current local build

Run: `artifact=$(find dist/release -maxdepth 1 -type f -name "keep-alive-*" -print -quit) && "$artifact" --help`
Expected: the generated executable runs successfully and renders CLI help

If local build is not possible due to environment or missing system capabilities, record that limitation explicitly before publishing.

- [ ] **Step 4: Verify release asset naming one last time**

Run: `rg -n "keep-alive-linux|keep-alive-macos|install.sh" .github/workflows/release.yml scripts/install.sh scripts/build-pyinstaller.sh`
Expected: asset naming is identical across workflow and installer

### Task 6: Create and push the release tag

**Files:**
- Modify: git refs only

- [ ] **Step 1: Confirm the working tree is clean**

Decide the final version tag up front as `vX.Y.Z`, and if the docs still contain a placeholder or older example that must change for this release, update and commit that before continuing.

Run: `git branch --show-current`
Expected: branch is `main`

Run: `git status --short`
Expected: no output

- [ ] **Step 2: Create the version tag**

Run: `git tag vX.Y.Z`
Expected: tag is created locally

- [ ] **Step 3: Push branch and tag**

Run: `git push origin main`
Expected: branch push succeeds

Run: `git push origin vX.Y.Z`
Expected: tag push succeeds and triggers the release workflow

- [ ] **Step 4: Verify remote state**

Run: `git ls-remote --tags origin "vX.Y.Z"`
Expected: remote shows the new tag

- [ ] **Step 5: Record the release trigger outcome**

If GitHub CLI is available and authenticated, inspect the workflow and Release outcome. At minimum verify:
- the Release for the tag exists
- the Release contains `keep-alive-linux`
- the Release contains `keep-alive-macos`
- the Release contains `install.sh`

If GitHub CLI is not available, record that remote Release asset verification could not be completed from this environment.
