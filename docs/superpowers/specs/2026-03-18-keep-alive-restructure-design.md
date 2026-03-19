# Keep Alive Restructure Design

**Date:** 2026-03-18

**Goal**

Reorganizar o projeto em uma estrutura de pacote Python com responsabilidades separadas, preservando o objetivo atual do utilitario: manter o Discord online por simulacao de atividade, com execucao em foreground, background e autostart por sistema operacional.

**Current Problems**

- Toda a logica esta concentrada em `main.py`.
- Responsabilidades de CLI, agendamento, simulacao, daemon, runtime e instalacao por sistema operacional estao acopladas.
- Arquivos gerados em runtime ficam na raiz do projeto.
- A forma atual dificulta manutencao, leitura e evolucao local sem reabrir todo o arquivo principal.

## Scope

Incluido nesta refatoracao:

- Conversao do projeto para um pacote `keep_alive/`.
- Separacao de responsabilidades em modulos pequenos.
- Adicao de execucao oficial via `python -m keep_alive`.
- Ajuste do `pyproject.toml` para expor um script de console consistente.
- Manutencao de `python main.py ...` como camada de compatibilidade.
- Migracao de PID e log para `var/`.
- Atualizacao do `README.md` para refletir a nova organizacao e o novo entrypoint.

Fora de escopo:

- Novas features.
- Reescrita da logica de negocio.
- Introducao de testes automatizados.
- Mudancas arquiteturais excessivas para o tamanho atual do projeto.

## Target Structure

```text
keep-alive/
├── main.py
├── pyproject.toml
├── README.md
├── keep_alive/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── logging_utils.py
│   ├── paths.py
│   ├── schedule.py
│   ├── simulator.py
│   ├── runtime.py
│   ├── process_manager.py
│   └── installers/
│       ├── __init__.py
│       ├── linux.py
│       ├── macos.py
│       └── windows.py
└── var/
    ├── activity.log
    └── discord-online.pid
```

## Module Responsibilities

### `main.py`

Wrapper fino de compatibilidade. Nao contera logica de negocio. Apenas delegara para `keep_alive.cli.main()`.

### `keep_alive/__main__.py`

Ponto de entrada para `python -m keep_alive`.

### `keep_alive/cli.py`

Centraliza parser, definicao dos subcomandos, help e dispatch de alto nivel.

Responsavel por:

- montar o `argparse`
- definir aliases e experiencia da CLI
- encaminhar chamadas para simulacao, processo em background e instalacao

### `keep_alive/config.py`

Contera constantes e configuracoes estaveis do projeto:

- nome do servico
- presets de cron
- metodos suportados
- defaults de CLI

### `keep_alive/paths.py`

Centraliza paths do projeto e de runtime:

- raiz do projeto
- diretorio `var/`
- caminho do PID
- caminho do log

Deve garantir a criacao do diretorio de runtime quando necessario.

### `keep_alive/logging_utils.py`

Isola a configuracao de logging para foreground e daemon.

### `keep_alive/schedule.py`

Contera `CronSchedule` e toda a logica de janelas ativas/inativas.

### `keep_alive/simulator.py`

Contera:

- estrategias de simulacao (`mouse`, `keyboard`, `combined`)
- deteccao do Discord em execucao
- foco da janela
- `ActivitySimulator`

### `keep_alive/runtime.py`

Utilitarios de ambiente e runtime que nao pertencem diretamente a CLI nem aos instaladores, como leitura de variaveis do sistema e metadados do ambiente grafico.

### `keep_alive/process_manager.py`

Contera:

- leitura e escrita de PID
- daemonizacao
- stop
- status
- exibicao de logs
- execucao compartilhada de foreground e background

Esse modulo concentra todo o ciclo de vida do processo.

### `keep_alive/installers/*.py`

Cada sistema operacional tera um modulo proprio para autostart:

- `linux.py`: systemd user-level
- `macos.py`: launchd
- `windows.py`: Task Scheduler

Um `__init__.py` de dispatch selecionara o instalador correto por plataforma.

## CLI and Compatibility

As interfaces desejadas apos a refatoracao sao:

- `python -m keep_alive <subcomando>`
- `keep-alive <subcomando>` via script definido no `pyproject.toml`
- `python main.py <subcomando>` como compatibilidade

Os subcomandos existentes devem continuar semanticamente equivalentes:

- `start`
- `run`
- `stop`
- `status`
- `logs`
- `install`
- `uninstall`

Pequenos ajustes de UX sao permitidos se simplificarem a implementacao, mas sem alterar o fluxo principal de uso.

## Runtime Files

Arquivos gerados pelo app devem sair da raiz e passar a morar em `var/`.

Consequencias esperadas:

- raiz mais limpa
- local unico para artefatos temporarios do projeto
- paths previsiveis para comandos de status, logs e stop

Todos os comandos internos e instaladores devem usar esses paths centralizados, nunca caminhos duplicados hardcoded.

## Migration Strategy

### Phase 1: Introduce package layout

- criar o pacote `keep_alive/`
- mover constantes e responsabilidades para modulos pequenos
- manter comportamento atual o mais intacto possivel

### Phase 2: Rewire entrypoints

- transformar `main.py` em wrapper
- adicionar `keep_alive/__main__.py`
- atualizar `pyproject.toml` para apontar para o novo entrypoint

### Phase 3: Centralize runtime paths

- criar utilitarios para `var/`
- atualizar logging, PID e comandos operacionais
- garantir que instaladores e processo background usem os novos caminhos

### Phase 4: Update system installers

- ajustar Linux, macOS e Windows para chamar o entrypoint correto
- preservar argumentos de cron, interval, metodo e foco

### Phase 5: Update docs

- atualizar `README.md`
- documentar nova estrutura
- corrigir exemplos de uso

## Design Constraints

- Priorizar separacao de responsabilidades sobre micro-abstracoes.
- Evitar interfaces artificiais demais para um projeto pequeno.
- Reaproveitar a logica existente sempre que possivel.
- Nao alterar o objetivo final do utilitario.
- Preservar o comportamento de foreground, background e autostart.

## Risks

### Entrypoint regression

Mudancas na forma como `install` escreve os comandos de execucao podem quebrar inicializacao em Linux, macOS ou Windows se o entrypoint final estiver inconsistente.

Mitigacao:

- centralizar a resolucao do entrypoint e dos paths
- revisar cada instalador contra a nova estrutura

### PID/log path regression

Mover arquivos para `var/` pode quebrar `status`, `logs` e `stop` se houver duplicacao de caminhos.

Mitigacao:

- definir paths em um unico modulo
- usar apenas esses helpers nos fluxos operacionais

### Daemon behavior regression

A logica de daemonizacao e sensivel a ordem de setup, PID e logging.

Mitigacao:

- preservar a sequencia atual de funcionamento
- limitar a refatoracao a separacao modular, nao a reescrita da logica

## Verification Strategy

Sem testes automatizados, a validacao sera operacional:

- verificar que o pacote importa corretamente
- verificar que `python -m keep_alive --help` responde
- verificar que `python main.py --help` continua funcionando
- verificar que os subcomandos principais seguem resolvendo no parser
- revisar os comandos gerados pelos instaladores por plataforma

Se o ambiente permitir, executar verificacoes basicas de ajuda e parsing sem acionar efeitos destrutivos do sistema.

## Success Criteria

- O projeto deixa de depender de um unico arquivo monolitico.
- A estrutura final fica organizada por responsabilidade.
- A execucao via pacote funciona.
- A compatibilidade com `python main.py ...` continua disponivel.
- PID e log ficam em `var/`.
- O `README.md` e o `pyproject.toml` refletem a nova organizacao.
