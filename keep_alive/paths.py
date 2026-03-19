import os
import platform
import sys
from pathlib import Path

from keep_alive.config import SERVICE_NAME


def _is_frozen_binary() -> bool:
    return bool(getattr(sys, "frozen", False))


def _get_runtime_dir() -> Path:
    if not _is_frozen_binary():
        return PROJECT_DIR / "var"

    system = platform.system()
    if system == "Darwin":
        state_root = Path.home() / "Library" / "Application Support"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        state_root = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        state_root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_root / "keep-alive" / "var"


if _is_frozen_binary():
    PACKAGE_DIR = Path(sys.executable).resolve().parent
    PROJECT_DIR = PACKAGE_DIR
else:
    PACKAGE_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = PACKAGE_DIR.parent

RUNTIME_DIR = _get_runtime_dir()
PID_FILE = RUNTIME_DIR / f"{SERVICE_NAME}.pid"
LOG_FILE = RUNTIME_DIR / "activity.log"


def ensure_runtime_dir() -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR
