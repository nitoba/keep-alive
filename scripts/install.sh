#!/usr/bin/env bash
set -euo pipefail

repo="${KEEP_ALIVE_REPO:-nitoba/keep-alive}"
bin_dir="${HOME}/.local/bin"
target="${bin_dir}/keep-alive"
asset_tag="${KEEP_ALIVE_VERSION:-}"

detect_platform() {
  case "$(uname -s)" in
    Linux)
      echo "linux"
      ;;
    Darwin)
      echo "macos"
      ;;
    *)
      echo "unsupported"
      ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64)
      echo "x86_64"
      ;;
    arm64|aarch64)
      echo "arm64"
      ;;
    *)
      echo "unsupported"
      ;;
  esac
}

fetch_text() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$1"
  else
    echo "curl or wget is required" >&2
    exit 1
  fi
}

download_file() {
  local url="$1"
  local output="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$output" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$output" "$url"
  else
    echo "curl or wget is required" >&2
    exit 1
  fi
}

platform="$(detect_platform)"
if [ "$platform" = "unsupported" ]; then
  echo "Unsupported platform: $(uname -s)" >&2
  exit 1
fi

arch="$(detect_arch)"
if [ "$arch" = "unsupported" ]; then
  echo "Unsupported architecture: $(uname -m)" >&2
  exit 1
fi

case "${platform}-${arch}" in
  linux-x86_64)
    asset_name="keep-alive-linux-x86_64"
    ;;
  macos-arm64)
    asset_name="keep-alive-macos-arm64"
    ;;
  macos-x86_64)
    asset_name="keep-alive-macos-x86_64"
    ;;
  *)
    echo "No prebuilt binary is available for ${platform}-${arch}" >&2
    exit 1
    ;;
esac

if [ -z "$asset_tag" ]; then
  release_json="$(fetch_text "https://api.github.com/repos/${repo}/releases/latest")"
  asset_tag="$(printf '%s\n' "$release_json" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
fi

if [ -z "$asset_tag" ]; then
  echo "Unable to resolve latest release tag for ${repo}" >&2
  exit 1
fi

download_url="https://github.com/${repo}/releases/download/${asset_tag}/${asset_name}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$bin_dir"
download_file "$download_url" "$tmp_dir/keep-alive"
cp "$tmp_dir/keep-alive" "$target"
chmod +x "$target"

echo "Installed keep-alive to ~/.local/bin/keep-alive"
echo "Actual path: ${target}"
case ":${PATH}:" in
  *":${bin_dir}:"*)
    ;;
  *)
    echo "~/.local/bin is not on your PATH yet."
    echo "Add it to your shell profile or export it for this session:"
    echo "  export PATH=\"${bin_dir}:\$PATH\""
    ;;
esac
echo "Next:"
echo "  keep-alive --help"
echo "  keep-alive install --help"
