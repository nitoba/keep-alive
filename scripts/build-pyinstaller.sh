#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

asset_suffix="$("$PYTHON_BIN" - <<'PY'
import platform

system = platform.system()
machine = platform.machine().lower()
arch_aliases = {
    "amd64": "x86_64",
    "x86-64": "x86_64",
    "x64": "x86_64",
    "aarch64": "arm64",
}
arch = arch_aliases.get(machine, machine)

if system == "Linux":
    print(f"linux-{arch}")
elif system == "Darwin":
    print(f"macos-{arch}")
else:
    raise SystemExit(f"unsupported platform: {system}")
PY
)"

release_dir="$ROOT_DIR/dist/release"
pyinstaller_dist_dir="$release_dir/pyinstaller"
pyinstaller_work_dir="$ROOT_DIR/build/pyinstaller"
artifact="$release_dir/keep-alive-${asset_suffix}"
source_binary="$pyinstaller_dist_dir/keep-alive"

mkdir -p "$release_dir" "$pyinstaller_dist_dir" "$pyinstaller_work_dir"

if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install --upgrade "${ROOT_DIR}[build]"
  pyinstaller_cmd=("$PYTHON_BIN" -m PyInstaller)
elif command -v uv >/dev/null 2>&1; then
  pyinstaller_cmd=(uv run --extra build python -m PyInstaller)
else
  echo "Neither pip nor uv is available to install build dependencies." >&2
  exit 1
fi

cd "$ROOT_DIR"

if [ -f "pyinstaller.spec" ]; then
  "${pyinstaller_cmd[@]}" \
    --distpath "$pyinstaller_dist_dir" \
    --workpath "$pyinstaller_work_dir" \
    --clean \
    pyinstaller.spec
else
  "${pyinstaller_cmd[@]}" \
    --name keep-alive \
    --onefile \
    --distpath "$pyinstaller_dist_dir" \
    --workpath "$pyinstaller_work_dir" \
    --specpath "$pyinstaller_work_dir" \
    --clean \
    keep_alive/__main__.py
fi

if [ ! -f "$source_binary" ]; then
  echo "Expected PyInstaller output not found: $source_binary" >&2
  exit 1
fi

cp "$source_binary" "$artifact"
chmod +x "$artifact"

echo "$artifact"
