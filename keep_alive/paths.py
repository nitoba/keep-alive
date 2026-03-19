from pathlib import Path

from keep_alive.config import SERVICE_NAME

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
RUNTIME_DIR = PROJECT_DIR / "var"
PID_FILE = RUNTIME_DIR / f"{SERVICE_NAME}.pid"
LOG_FILE = RUNTIME_DIR / "activity.log"


def ensure_runtime_dir() -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR
