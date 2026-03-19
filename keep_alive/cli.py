import argparse
import platform
import sys

from keep_alive.config import (
    CRON_PRESETS,
    DEFAULT_CRON,
    DEFAULT_INTERVAL,
    DEFAULT_METHOD,
    LOG_TAIL_LINES,
    METHOD_CHOICES,
)
from keep_alive.paths import ensure_runtime_dir
from keep_alive.runtime import command_hint, get_python_path


def format_presets_help() -> str:
    lines = []
    seen: dict[str, str] = {}
    for name, expr in CRON_PRESETS.items():
        if expr not in seen:
            seen[expr] = name
            lines.append(f"    {name:<14s} → {expr}")
        else:
            lines.append(f"    {name:<14s} → (alias de '{seen[expr]}')")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mantém o Discord online simulando atividade do usuário no SO.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Subcomandos:
  {command_hint()} start                # inicia em background (daemon)
  {command_hint()} stop                 # para o daemon
  {command_hint()} status               # verifica se está rodando
  {command_hint()} logs                 # mostra últimas linhas do log
  {command_hint()} logs -f              # acompanha o log em tempo real
  {command_hint()} run                  # roda em foreground (terminal)
  {command_hint()} install              # configura autostart com o sistema
  {command_hint()} uninstall            # remove autostart

Formato cron (5 campos):
  ┌──────────── minuto        (0-59)
  │ ┌────────── hora          (0-23)
  │ │ ┌──────── dia do mês   (1-31)
  │ │ │ ┌────── mês          (1-12)
  │ │ │ │ ┌──── dia da semana (0=dom, 1=seg ... 6=sáb)
  │ │ │ │ │
  * * * * *

Exemplos:
  {command_hint()} start --cron "* 8-18 * * 1-5"
  {command_hint()} start --cron comercial -i 120
  {command_hint()} install --cron comercial
  {command_hint()} run --cron noturno --method combined

Presets disponíveis:
{format_presets_help()}
        """,
    )

    sub = parser.add_subparsers(dest="command", help="Ação a executar")

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "-i",
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Intervalo base em segundos entre simulações (padrão: {DEFAULT_INTERVAL})",
    )
    shared.add_argument(
        "-m",
        "--method",
        choices=METHOD_CHOICES,
        default=DEFAULT_METHOD,
        help=f"Método de simulação (padrão: {DEFAULT_METHOD})",
    )
    shared.add_argument(
        "-f",
        "--focus",
        action="store_true",
        default=False,
        help="Focar janela do Discord antes de cada simulação (Windows)",
    )
    shared.add_argument(
        "-c",
        "--cron",
        type=str,
        default=DEFAULT_CRON,
        help=f"Cron expression ou preset (padrão: '{DEFAULT_CRON}' = 24/7)",
    )

    sub.add_parser("start", parents=[shared], help="Inicia o simulador em background (daemon)")
    sub.add_parser("run", parents=[shared], help="Roda o simulador em foreground (terminal aberto)")
    sub.add_parser("stop", help="Para o daemon em execução")
    sub.add_parser("status", help="Mostra se o daemon está rodando")

    logs_parser = sub.add_parser("logs", help="Mostra os logs do daemon")
    logs_parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        default=False,
        help="Acompanhar logs em tempo real (tipo tail -f)",
    )
    logs_parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=LOG_TAIL_LINES,
        help=f"Número de linhas para mostrar (padrão: {LOG_TAIL_LINES})",
    )

    sub.add_parser(
        "install",
        parents=[shared],
        help="Configura autostart com o sistema (systemd/launchd/Task Scheduler)",
    )
    sub.add_parser("uninstall", help="Remove o autostart do sistema")

    return parser


def build_internal_daemon_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=METHOD_CHOICES,
        default=DEFAULT_METHOD,
    )
    parser.add_argument(
        "-f",
        "--focus",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--cron",
        type=str,
        default=DEFAULT_CRON,
    )
    return parser


def cmd_install(args):
    from keep_alive import installers

    system = platform.system()
    ensure_runtime_dir()
    print("=" * 55)
    print("📦 Instalando autostart — Discord Always Online")
    print(f"   SO         : {system}")
    print(f"   Python     : {get_python_path()}")
    print(f"   Cron       : {args.cron}")
    print(f"   Intervalo  : {args.interval}s")
    print(f"   Método     : {args.method}")
    print("=" * 55)
    print()

    try:
        success = installers.install(args)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        print(f"   Use '{command_hint()} start' manualmente.")
        return 1

    if not success:
        print()
        print("❌ Instalação falhou. Verifique os erros acima.")
        print(f"   Você ainda pode usar '{command_hint()} start' manualmente.")
        return 1
    return 0


def cmd_uninstall():
    from keep_alive import installers

    system = platform.system()
    print(f"🗑️  Removendo autostart ({system})...")
    print()
    try:
        installers.uninstall()
    except RuntimeError as exc:
        print(f"❌ {exc}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "_daemon_child":
        args = build_internal_daemon_parser().parse_args(argv[1:])
        from keep_alive import process_manager

        process_manager.run_daemon_child(args)
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        print("\n💡 Uso rápido:")
        print(f"   {command_hint()} start --cron comercial   # background")
        print(f"   {command_hint()} run --cron comercial     # foreground")
        print(f"   {command_hint()} install --cron comercial # autostart com o SO")
        return 0

    from keep_alive import process_manager

    if args.command == "start":
        process_manager.start_background(args)
        return 0
    if args.command == "run":
        process_manager.run_simulator(args, daemon_mode=False)
        return 0
    if args.command == "stop":
        process_manager.cmd_stop()
        return 0
    if args.command == "status":
        process_manager.cmd_status()
        return 0
    if args.command == "logs":
        process_manager.cmd_logs(follow=args.follow, lines=args.lines)
        return 0
    if args.command == "install":
        return cmd_install(args)
    if args.command == "uninstall":
        return cmd_uninstall()

    parser.error(f"Subcomando desconhecido: {args.command}")
    return 2
