import subprocess
import textwrap
from pathlib import Path

from keep_alive.paths import LOG_FILE, PROJECT_DIR
from keep_alive.runtime import build_module_command, build_shared_cli_args

LABEL = "com.discord.always-online"


def build_plist_content(args) -> str:
    command = build_module_command("run", extra_args=build_shared_cli_args(args))
    command_xml = "\n".join(f"                <string>{part}</string>" for part in command)

    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{LABEL}</string>

            <key>ProgramArguments</key>
            <array>
{command_xml}
            </array>

            <key>WorkingDirectory</key>
            <string>{PROJECT_DIR}</string>

            <key>RunAtLoad</key>
            <true/>

            <key>KeepAlive</key>
            <dict>
                <key>SuccessfulExit</key>
                <false/>
            </dict>

            <key>StandardOutPath</key>
            <string>{LOG_FILE}</string>

            <key>StandardErrorPath</key>
            <string>{LOG_FILE}</string>

            <key>ProcessType</key>
            <string>Background</string>
        </dict>
        </plist>
        """
    )


def install(args) -> bool:
    plist_file = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    plist_file.parent.mkdir(parents=True, exist_ok=True)
    plist_file.write_text(build_plist_content(args))

    print(f"📄 LaunchAgent criado: {plist_file}")
    print("   Carregando agente...")

    result = subprocess.run(
        ["launchctl", "load", str(plist_file)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"   ❌ Erro: {result.stderr.strip()}")
        return False

    print()
    print("✅ LaunchAgent instalado e iniciado!")
    print("   O script vai iniciar automaticamente no login.")
    print()
    print("   Comandos úteis:")
    print("   launchctl list | grep discord              # ver status")
    print(f"   launchctl unload {plist_file}              # parar")
    print("   python -m keep_alive logs -f               # ver logs")
    return True


def uninstall() -> bool:
    plist_file = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    if not plist_file.exists():
        print(f"⚠️  LaunchAgent não encontrado: {plist_file}")
        return False

    print("   Descarregando agente...")
    subprocess.run(["launchctl", "unload", str(plist_file)], capture_output=True, text=True)
    plist_file.unlink()
    print(f"✅ LaunchAgent removido: {plist_file}")
    return True
