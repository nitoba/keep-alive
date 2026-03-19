# Keep Alive Release Distribution Design

**Date:** 2026-03-18

**Goal**

Distribuir o `keep-alive` para usuarios que nao querem instalar Python nem clonar o repositorio, usando GitHub Releases com binarios gerados por `PyInstaller` para `macOS` e `Linux`, junto com um instalador `bash`.

## Scope

Incluido:

- Workflow de release no GitHub Actions disparado por tags `v*`
- Build de binarios `PyInstaller` para `macOS` e `Linux`
- Publicacao dos binarios como assets do GitHub Release
- Publicacao de `install.sh` como asset do GitHub Release
- Script `install.sh` para instalar o binario em `~/.local/bin/keep-alive`
- Atualizacao do `README.md` com os fluxos de distribuicao por tag Git e por Release

Fora de escopo:

- Suporte a Windows nesta etapa
- Publicacao no PyPI
- Instalacao automatica de autostart dentro do `install.sh`
- Suporte adicional a multiplas arquiteturas fora das entregues pelos runners iniciais da CI

## Distribution Model

O projeto passa a ter dois caminhos oficiais de distribuicao:

1. **Git tag install** para usuarios com Python:
   - `uv tool install git+https://github.com/nitoba/keep-alive.git@vX.Y.Z`
   - `pipx install git+https://github.com/nitoba/keep-alive.git@vX.Y.Z`

2. **GitHub Release binaries** para usuarios sem Python:
   - baixar binario pronto do Release
   - ou executar `install.sh` para detectar a plataforma e instalar automaticamente

## Target Files

```text
keep-alive/
├── .github/
│   └── workflows/
│       └── release.yml
├── scripts/
│   ├── build-pyinstaller.sh
│   └── install.sh
├── pyinstaller.spec
├── README.md
└── pyproject.toml
```

## Artifact Strategy

Os Releases devem publicar, no minimo:

- `keep-alive-linux`
- `keep-alive-macos`
- `install.sh`

Se o workflow ou plataforma exigir nome com arquitetura, isso pode ser refletido no nome do asset, desde que o instalador saiba resolver a variante correta.

## Release Workflow

O workflow deve:

- disparar em push de tags `v*`
- criar ou atualizar o GitHub Release correspondente
- rodar em matrix para `ubuntu-latest` e `macos-latest`
- instalar dependencias do projeto e `PyInstaller`
- buildar o executavel com script dedicado do repositorio
- anexar os binarios ao Release
- anexar `scripts/install.sh` ao Release

O workflow nao deve depender de comandos locais manuais depois que a tag for enviada.

## PyInstaller Packaging

O empacotamento deve:

- usar um ponto de entrada claro para o CLI atual
- gerar um executavel chamado `keep-alive`
- evitar depender de flags longas inline no YAML; a configuracao deve ficar em `pyinstaller.spec` e/ou em um script de build

Se for necessario incluir imports ocultos ou ajustes especificos de `PyInstaller`, eles devem ficar versionados no repositorio, nao escondidos no workflow.

## Install Script

`scripts/install.sh` deve:

- detectar `macOS` ou `Linux`
- selecionar o asset correto do Release
- baixar o binario usando `curl` ou `wget`
- instalar em `~/.local/bin/keep-alive`
- marcar como executavel
- informar o usuario se `~/.local/bin` nao estiver no `PATH`
- mostrar os proximos comandos sugeridos (`keep-alive --help`, `keep-alive install ...`)

O script deve ser simples, auditavel e sem efeitos colaterais extras.

Nao deve:

- editar shell profile automaticamente
- configurar autostart
- exigir clone do repositorio

## User Experience

### Usuario com Python

Instala por tag Git e roda `keep-alive`.

### Usuario sem Python

Instala por script:

```bash
curl -fsSL <release-install-url> | bash
```

Ou baixa manualmente o binario do Release.

## Documentation

O `README.md` deve explicar:

- distribuicao por tag Git
- distribuicao por Release/binario
- diferenca entre usuarios com e sem Python
- como publicar nova versao por tag
- como instalar pelo `install.sh`

## Risks

### PyInstaller runtime issues

Algumas dependencias de automacao podem exigir ajustes de bundle ou imports ocultos.

Mitigacao:

- usar `pyinstaller.spec`
- validar o executavel gerado ao menos com `--help`

### Platform-specific behavior

O binario nao elimina dependencias do ambiente grafico, permissoes de acessibilidade ou requisitos de sessao do SO.

Mitigacao:

- documentar esse limite no README
- manter o comportamento funcional do app igual ao atual

### Release asset naming drift

Se os nomes dos assets mudarem, o instalador pode quebrar.

Mitigacao:

- centralizar nomes ou convencoes no workflow e no `install.sh`
- manter o mapeamento simples

## Verification Strategy

Sem testes automatizados, a validacao minima deve incluir:

- `python -m compileall keep_alive`
- `python -m keep_alive --help`
- validacao do script `install.sh` com shell lint basico ou `bash -n`
- validacao do workflow YAML por inspeção e consistencia com os nomes dos assets
- validacao dos scripts de build localmente sem publicar Release, quando possivel

## Success Criteria

- Tag `vX.Y.Z` dispara workflow de release
- Workflow gera binarios para `macOS` e `Linux`
- Release contem binarios e `install.sh`
- Usuario consegue instalar sem Python e sem clone
- O comando instalado expõe `keep-alive --help`
- README documenta os dois fluxos oficiais de distribuicao
