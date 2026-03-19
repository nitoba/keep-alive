import os
import platform
import shlex
import subprocess
import sys

from keep_alive.config import PACKAGE_MODULE


def is_frozen_binary() -> bool:
    return bool(getattr(sys, "frozen", False))


def command_hint() -> str:
    if is_frozen_binary():
        return os.path.basename(sys.executable)
    return "python -m keep_alive"


def get_python_path() -> str:
    return sys.executable


def get_pythonw_path() -> str:
    if is_frozen_binary():
        return sys.executable

    python_exe = sys.executable
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return python_exe


def get_display_env() -> str:
    return os.environ.get("DISPLAY", ":0")


def get_xdg_session() -> str:
    return os.environ.get("XDG_SESSION_TYPE", "x11")


def build_shared_cli_args(args) -> list[str]:
    cli_args = [
        "--cron",
        args.cron,
        "--interval",
        str(args.interval),
        "--method",
        args.method,
    ]
    if args.focus:
        cli_args.append("--focus")
    return cli_args


def build_module_command(
    subcommand: str,
    *,
    extra_args: list[str] | None = None,
    use_windowed_python: bool = False,
) -> list[str]:
    if is_frozen_binary():
        return [sys.executable, subcommand, *(extra_args or [])]

    python_path = get_pythonw_path() if use_windowed_python else get_python_path()
    return [python_path, "-m", PACKAGE_MODULE, subcommand, *(extra_args or [])]


def format_command(command: list[str]) -> str:
    if platform.system() == "Windows":
        return subprocess.list2cmdline(command)
    return shlex.join(command)
