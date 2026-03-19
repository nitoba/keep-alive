# Keep Alive | Discord Always Online

Mantém seu status no Discord como online simulando microatividade de mouse e teclado no sistema operacional. Pode rodar em foreground, background e com autostart no sistema.

## Instalação sem clone

Você não precisa clonar o repositório.

### Opção recomendada: `uv tool`

Instala o comando globalmente, isolado, direto de uma tag do GitHub:

```bash
uv tool install git+https://github.com/nitoba/keep-alive.git@v0.3.0
```

Depois disso:

```bash
keep-alive --help
keep-alive install --cron comercial
```

Para atualizar para outra tag:

```bash
uv tool install --force git+https://github.com/nitoba/keep-alive.git@v0.3.1
```

### Opção alternativa: `pipx`

```bash
pipx install git+https://github.com/nitoba/keep-alive.git@v0.3.0
```

### Se quiser rodar sem instalar globalmente

```bash
uvx --from git+https://github.com/nitoba/keep-alive.git@v0.3.0 keep-alive --help
```

## Fluxo de release por tag

Para distribuir uma nova versão:

```bash
git tag v0.3.1
git push origin v0.3.1
```

Distribua sempre por tag, não pela branch `main`.

## Desenvolvimento local

```bash
cd keep-alive

uv venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

uv pip install -e .
```

## Uso rápido

```bash
# Instalar como serviço do sistema
keep-alive install --cron comercial

# Ou iniciar manualmente em background
keep-alive start --cron comercial

# Ver status, logs e parar
keep-alive status
keep-alive logs -f
keep-alive stop

# Remover do autostart
keep-alive uninstall
```

As formas abaixo continuam válidas se você estiver no ambiente Python do projeto:

```bash
python -m keep_alive install --cron comercial

python -m keep_alive start --cron comercial

python -m keep_alive status
python -m keep_alive logs -f
python -m keep_alive stop

python -m keep_alive uninstall
```

## Subcomandos

| Comando | O que faz |
|---------|-----------|
| `start` | Inicia em background. |
| `run` | Roda em foreground. |
| `stop` | Para o daemon em execução. |
| `status` | Mostra o estado atual do daemon. |
| `logs` | Exibe logs. Com `-f`, acompanha em tempo real. |
| `install` | Configura autostart com o sistema. |
| `uninstall` | Remove o autostart. |

## Autostart

O comando `install` detecta o sistema operacional automaticamente:

| SO | Método | O que cria |
|----|--------|------------|
| Linux | systemd user-level | `~/.config/systemd/user/discord-online.service` |
| macOS | launchd | `~/Library/LaunchAgents/com.discord.always-online.plist` |
| Windows | Task Scheduler | Tarefa `discord-online` |

### Exemplos

```bash
python -m keep_alive install --cron comercial
python -m keep_alive install
python -m keep_alive install --cron "* 9-17 * * 1-5" --interval 120 --method combined
```

## Agendamento com Cron

```text
  ┌──────────── minuto        (0-59)
  │ ┌────────── hora          (0-23)
  │ │ ┌──────── dia do mês   (1-31)
  │ │ │ ┌────── mês          (1-12)
  │ │ │ │ ┌──── dia da semana (0=dom, 1=seg ... 6=sáb)
  │ │ │ │ │
  * * * * *
```

### Presets

| Preset | Expressão |
|--------|-----------|
| `always` | `* * * * *` |
| `comercial` / `business` | `* 8-18 * * 1-5` |
| `weekdays` | `* 8-20 * * 1-5` |
| `noturno` / `night` | `* 22-23,0-5 * * *` |
| `weekend` / `fds` | `* 10-22 * * 0,6` |
| `manha` / `morning` | `* 6-12 * * *` |
| `tarde` / `afternoon` | `* 12-18 * * *` |

## Opções

As flags abaixo valem para `start`, `run` e `install`:

| Flag | Curta | Padrão | Descrição |
|------|-------|--------|-----------|
| `--cron` | `-c` | `* * * * *` | Cron expression ou preset |
| `--interval` | `-i` | `200` | Segundos entre simulações |
| `--method` | `-m` | `mouse` | `mouse`, `keyboard` ou `combined` |
| `--focus` | `-f` | off | Foca a janela do Discord antes da simulação |

## Estrutura

```text
keep-alive/
├── keep_alive/
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── logging_utils.py
│   ├── paths.py
│   ├── process_manager.py
│   ├── runtime.py
│   ├── schedule.py
│   ├── simulator.py
│   └── installers/
├── pyproject.toml
├── README.md
└── var/                      # gerado em runtime
    ├── activity.log
    └── discord-online.pid
```
