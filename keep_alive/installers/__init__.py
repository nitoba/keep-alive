import platform


def resolve_installer_module():
    system = platform.system()
    if system == "Linux":
        from keep_alive.installers import linux as module
    elif system == "Darwin":
        from keep_alive.installers import macos as module
    elif system == "Windows":
        from keep_alive.installers import windows as module
    else:
        raise RuntimeError(f"Sistema operacional '{system}' não suportado.")
    return module


def install(args):
    return resolve_installer_module().install(args)


def uninstall():
    return resolve_installer_module().uninstall()
