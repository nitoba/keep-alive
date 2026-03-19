import atexit
import logging
import os
import platform
import signal
import subprocess
import sys

from keep_alive.config import APP_LOGGER_NAME, MIN_INTERVAL, WARN_INTERVAL
from keep_alive.logging_utils import setup_logging
from keep_alive.paths import LOG_FILE, PID_FILE, PROJECT_DIR, ensure_runtime_dir
from keep_alive.runtime import build_module_command, build_shared_cli_args, command_hint


def _write_pid():
    ensure_runtime_dir()
    PID_FILE.write_text(str(os.getpid()))
    atexit.register(_remove_pid)


def _remove_pid():
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def read_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def daemonize(child_args: list[str]):
    if platform.system() == "Windows":
        _daemonize_windows(child_args)
        return

    try:
        pid = os.fork()
        if pid > 0:
            print(f"🚀 Daemon iniciado (PID: {pid})")
            print(f"   Logs: {LOG_FILE}")
            print(f"   PID file: {PID_FILE}")
            print(f"   Parar: {command_hint()} stop")
            raise SystemExit(0)
    except OSError as exc:
        sys.stderr.write(f"Erro no primeiro fork: {exc}\n")
        raise SystemExit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            raise SystemExit(0)
    except OSError as exc:
        sys.stderr.write(f"Erro no segundo fork: {exc}\n")
        raise SystemExit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, sys.stdin.fileno())
    os.dup2(devnull, sys.stdout.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    os.close(devnull)

    os.chdir(PROJECT_DIR)
    _write_pid()


def _daemonize_windows(child_args: list[str]):
    command = build_module_command(
        "_daemon_child",
        extra_args=child_args,
        use_windowed_python=True,
    )
    create_no_window = 0x08000000
    proc = subprocess.Popen(
        command,
        creationflags=create_no_window,
        cwd=str(PROJECT_DIR),
        close_fds=True,
    )

    print(f"🚀 Processo em background iniciado (PID: {proc.pid})")
    print(f"   Logs: {LOG_FILE}")
    print(f"   PID file: {PID_FILE}")
    print(f"   Parar: {command_hint()} stop")
    raise SystemExit(0)


def cmd_stop():
    pid = read_pid()
    if pid is None:
        print("⚠️  Nenhum daemon em execução (PID file não encontrado).")
        return

    print(f"🛑 Enviando sinal de parada ao PID {pid}...")
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
        else:
            os.kill(pid, signal.SIGTERM)
        print("✅ Sinal enviado. O daemon vai encerrar em breve.")
        print(f"   Acompanhe: tail -f {LOG_FILE}")
    except ProcessLookupError:
        print(f"⚠️  Processo {pid} não encontrado. Limpando PID file...")
        _remove_pid()
    except PermissionError:
        print(f"❌ Sem permissão para encerrar PID {pid}. Tente com sudo.")


def cmd_status():
    pid = read_pid()
    if pid is None:
        print("⚪ Daemon não está rodando.")
        print(f"   PID file: {PID_FILE}")
        print(f"   Log file: {LOG_FILE}")
        return

    print(f"🟢 Daemon rodando (PID: {pid})")
    print(f"   PID file: {PID_FILE}")
    print(f"   Log file: {LOG_FILE}")

    try:
        lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
        last_lines = lines[-5:]
        print(f"\n   Últimas {len(last_lines)} linhas do log:")
        for line in last_lines:
            print(f"   {line}")
    except FileNotFoundError:
        pass


def cmd_logs(*, follow: bool = False, lines: int = 20):
    if not LOG_FILE.exists():
        print(f"⚠️  Arquivo de log não encontrado: {LOG_FILE}")
        return

    if follow:
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["powershell", "-Command", f"Get-Content '{LOG_FILE}' -Tail {lines} -Wait"],
                )
            else:
                subprocess.run(["tail", "-f", "-n", str(lines), str(LOG_FILE)])
        except KeyboardInterrupt:
            pass
        return

    all_lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
    for line in all_lines[-lines:]:
        print(line)


def run_simulator(args, *, daemon_mode: bool = False):
    log = setup_logging(daemon_mode=daemon_mode)

    if args.interval < MIN_INTERVAL:
        log.error("Intervalo mínimo é 10 segundos.")
        raise SystemExit(1)
    if args.interval > WARN_INTERVAL:
        log.warning(
            f"⚠️  Intervalo de {args.interval}s é próximo do limite de 5min do Discord. "
            "Recomendado: ≤ 240s."
        )

    from keep_alive.schedule import CronSchedule
    from keep_alive.simulator import ActivitySimulator

    try:
        schedule = CronSchedule(args.cron)
    except ValueError as exc:
        log.error(str(exc))
        raise SystemExit(1)

    if not PID_FILE.exists():
        _write_pid()

    sim = ActivitySimulator(
        interval=args.interval,
        method=args.method,
        focus=args.focus,
        schedule=schedule,
    )
    signal.signal(signal.SIGINT, sim.stop)
    signal.signal(signal.SIGTERM, sim.stop)

    if daemon_mode:
        logging.getLogger(APP_LOGGER_NAME).info(f"🔒 Rodando como daemon (PID: {os.getpid()})")

    sim.run()


def start_background(args):
    existing_pid = read_pid()
    if existing_pid:
        print(f"⚠️  Daemon já está rodando (PID: {existing_pid}).")
        print(f"   Use '{command_hint()} stop' primeiro.")
        raise SystemExit(1)

    child_args = build_shared_cli_args(args)
    daemonize(child_args)
    run_simulator(args, daemon_mode=True)


def run_daemon_child(args):
    _write_pid()
    run_simulator(args, daemon_mode=True)
