import getpass
import subprocess
import textwrap
from pathlib import Path

from keep_alive.config import SERVICE_NAME
from keep_alive.paths import PROJECT_DIR
from keep_alive.runtime import (
    build_module_command,
    build_shared_cli_args,
    command_hint,
    format_command,
    get_display_env,
    get_xdg_session,
)


def build_service_content(args) -> str:
    user = getpass.getuser()
    exec_start = format_command(
        build_module_command("run", extra_args=build_shared_cli_args(args))
    )
    exec_stop = format_command(build_module_command("stop"))

    return textwrap.dedent(
        f"""\
        [Unit]
        Description=Discord Always Online — Input Simulator
        After=graphical-session.target
        PartOf=graphical-session.target

        [Service]
        Type=simple
        Environment=DISPLAY={get_display_env()}
        Environment=XDG_SESSION_TYPE={get_xdg_session()}
        Environment=XAUTHORITY=/home/{user}/.Xauthority
        WorkingDirectory={PROJECT_DIR}
        ExecStart={exec_start}
        ExecStop={exec_stop}
        Restart=on-failure
        RestartSec=30

        [Install]
        WantedBy=default.target
        """
    )


def install(args) -> bool:
    service_content = build_service_content(args)
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    service_file = systemd_dir / f"{SERVICE_NAME}.service"
    service_file.write_text(service_content)

    print(f"📄 Serviço criado: {service_file}")

    commands = [
        (["systemctl", "--user", "daemon-reload"], "Recarregando systemd..."),
        (["systemctl", "--user", "enable", SERVICE_NAME], "Habilitando autostart..."),
        (["systemctl", "--user", "start", SERVICE_NAME], "Iniciando serviço..."),
    ]
    for command, message in commands:
        print(f"   {message}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ Erro: {result.stderr.strip()}")
            return False

    subprocess.run(
        ["loginctl", "enable-linger", getpass.getuser()],
        capture_output=True,
        text=True,
    )

    print()
    print("✅ Serviço instalado e iniciado!")
    print("   O script vai iniciar automaticamente com o sistema.")
    print()
    print("   Comandos úteis:")
    print(f"   systemctl --user status {SERVICE_NAME}    # ver status")
    print(f"   systemctl --user stop {SERVICE_NAME}      # parar")
    print(f"   systemctl --user restart {SERVICE_NAME}   # reiniciar")
    print(f"   journalctl --user -u {SERVICE_NAME} -f    # ver logs do systemd")
    print(f"   {command_hint()} logs -f                  # ver logs do app")
    return True


def uninstall() -> bool:
    service_file = Path.home() / ".config" / "systemd" / "user" / f"{SERVICE_NAME}.service"
    if not service_file.exists():
        print(f"⚠️  Serviço não encontrado: {service_file}")
        return False

    commands = [
        (["systemctl", "--user", "stop", SERVICE_NAME], "Parando serviço..."),
        (["systemctl", "--user", "disable", SERVICE_NAME], "Desabilitando autostart..."),
    ]
    for command, message in commands:
        print(f"   {message}")
        subprocess.run(command, capture_output=True, text=True)

    service_file.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
    print(f"✅ Serviço removido: {service_file}")
    return True
