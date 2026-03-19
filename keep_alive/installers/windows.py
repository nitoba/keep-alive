import subprocess

from keep_alive.config import SERVICE_NAME
from keep_alive.runtime import build_module_command, build_shared_cli_args


def build_task_command(args) -> str:
    command = build_module_command(
        "run",
        extra_args=build_shared_cli_args(args),
        use_windowed_python=True,
    )
    return subprocess.list2cmdline(command)


def install(args) -> bool:
    task_command = build_task_command(args)
    command = [
        "schtasks",
        "/Create",
        "/TN",
        SERVICE_NAME,
        "/TR",
        task_command,
        "/SC",
        "ONLOGON",
        "/RL",
        "HIGHEST",
        "/F",
    ]

    print(f"📄 Criando tarefa agendada: {SERVICE_NAME}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Erro: {result.stderr.strip()}")
        print()
        print("   Talvez seja necessário rodar como Administrador.")
        print("   Abra o terminal como Admin e tente novamente.")
        return False

    print("   Iniciando tarefa...")
    subprocess.run(["schtasks", "/Run", "/TN", SERVICE_NAME], capture_output=True, text=True)

    print()
    print("✅ Tarefa agendada criada e iniciada!")
    print("   O script vai iniciar automaticamente no logon.")
    print()
    print("   Comandos úteis:")
    print(f"   schtasks /Query /TN {SERVICE_NAME}          # ver status")
    print(f"   schtasks /End /TN {SERVICE_NAME}            # parar")
    print(f"   schtasks /Run /TN {SERVICE_NAME}            # iniciar")
    print("   python -m keep_alive logs -f                # ver logs")
    return True


def uninstall() -> bool:
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", SERVICE_NAME, "/F"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"   ❌ Erro: {result.stderr.strip()}")
        return False

    print("✅ Tarefa agendada removida.")
    return True
