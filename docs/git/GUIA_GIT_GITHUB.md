# Guia de Coordenação Git e GitHub para o Projeto A-Maze-ing

Este documento estabelece o fluxo de trabalho em equipe para o desenvolvimento do A-Maze-ing em dupla. O objetivo é manter o histórico limpo, evitar regressões na branch principal e permitir que os dois integrantes desenvolvam funcionalidades em paralelo sem bloqueios ou conflitos destrutivos.

---

## 1. Organização de Branches

O repositório adota um fluxo baseado em branches curtas por funcionalidade (*trunk-based development* simplificado):

```
main (protegida, código estável e testado)
 │
 ├── study-guides (documentos de planejamento e guias de estudo)
 │
 ├── feature/config-parser (exemplo de branch de funcionalidade)
 └── feature/recursive-backtracker
```

### Regras das branches
- Nomes de branches são sempre em inglês, em minúsculas, usando hífens para separar palavras.
- A branch `main` nunca recebe commits diretos. Toda alteração entra exclusivamente via Pull Request aprovado pelo colega de equipe.
- A branch `study-guides` armazena o planejamento, os guias de estudo e os roteiros de teste. Ela permanece isolada do código-fonte do gerador para manter a raiz limpa durante a avaliação do código.
- Prefixos padrão para branches de trabalho:
  - `feature/<nome>`: novas implementações (ex.: `feature/bfs-pathfinder`, `feature/mlx-renderer`).
  - `fix/<nome>`: correção de defeitos em código já mesclado (ex.: `fix/wall-coherence-bounds`).
  - `refactor/<nome>`: reestruturação de código existente sem alterar comportamento externo.
  - `test/<nome>`: criação ou expansão de baterias de teste.
  - `docs/<nome>`: atualizações na documentação do projeto.

---

## 2. Padrão de Commits Semânticos

Todos os commits devem ter mensagens em inglês seguindo a convenção *Conventional Commits*. O foco deve estar em **micro-commits**: alterações pequenas, atômicas e com propósito único.

### Formato da Mensagem

```
<tipo>(<escopo>): <descrição no imperativo e minúsculo>

[corpo opcional explicando o motivo da mudança, quando não óbvio]
```

### Tipos Permitidos
- `feat`: adição de nova funcionalidade visível ao usuário ou nova capacidade no módulo.
- `fix`: correção de bug no gerador, no parser ou na interface gráfica.
- `docs`: adição ou modificação de documentação e comentários estruturais.
- `refactor`: modificação interna de código que não adiciona recurso nem corrige bug.
- `test`: inclusão ou ajuste de testes unitários ou de integração.
- `chore`: manutenção de arquivos de ambiente, lint, scripts internos ou gitignore.
- `build`: alterações no sistema de empacotamento (`pyproject.toml`, dependências do `Makefile`).

### Exemplos Práticos de Micro-Commits
- `feat(config): add MazeConfig dataclass with basic field parsing`
- `test(config): add unit tests for missing keys in config file`
- `fix(config): enforce entry coordinate boundaries check`
- `feat(generator): implement Direction bitmask enum with opposite helper`
- `feat(generator): initialize grid cells with ALL_WALLS bitmask`
- `feat(generator): implement two-way wall removal helper`
- `feat(solver): implement BFS queue to find shortest exit route`
- `chore(repo): configure flake8 and mypy flags in Makefile`

Evite mensagens vagas como `fix bugs`, `wip`, `update`, ou commits gigantes contendo alterações em dez arquivos não relacionados.

---

## 3. Rotina Diária de Trabalho em Dupla

Para evitar divergências no código compartilhado, a dupla deve seguir este ciclo ao iniciar qualquer tarefa:

### Passo 1: Atualizar a base local
Antes de criar qualquer branch, sincronize sua cópia com o repositório remoto:

```bash
git checkout main
git pull origin main
```

### Passo 2: Criar a branch da tarefa
Crie a branch a partir da `main` atualizada:

```bash
git checkout -b feature/config-parser
```

### Passo 3: Desenvolver com micro-commits e checagem local
Durante o trabalho, faça commits atômicos. Antes de cada commit, execute as ferramentas de lint:

```bash
make lint
git add mazegen/config.py tests/test_config.py
git commit -m "feat(config): parse key-value lines ignoring comments"
```

### Passo 4: Publicar e abrir Pull Request
Envie a branch para o repositório remoto:

```bash
git push -u origin feature/config-parser
```

Abra um Pull Request no GitHub apontando da sua branch para a `main`. No título do PR, utilize o identificador da tarefa (ex.: `T1.1 - Parser de Configuração`).

### Passo 5: Revisão por Pares (Peer Review)
O colega responsável pela revisão deve:
1. Ler o diff no GitHub, verificando aderência aos tipos (`mypy`), estilo (`flake8`) e ausência de complexidade desnecessária.
2. Baixar a branch localmente se necessário para rodar testes manuais ou automatizados:
   ```bash
   git fetch origin
   git checkout feature/config-parser
   make lint && pytest
   ```
3. Aprovar o PR ou solicitar ajustes pontuais via comentários no código.
4. Após aprovação, realizar o merge (preferencialmente *Squash and merge* ou *Rebase and merge*, conforme combinado pela equipe) e deletar a branch remota.

---

## 4. Gestão de Conflitos de Merge

Conflitos ocorrem quando duas pessoas editam as mesmas linhas de um arquivo em branches concorrentes. O procedimento padrão para resolução é o rebase sobre a `main` atualizada:

```bash
# Na sua branch de trabalho:
git fetch origin
git rebase origin/main
```

Se o Git pausar informando conflito:
1. Abra os arquivos conflitantes listados por `git status`.
2. Localize os marcadores `<<<<<<<`, `=======` e `>>>>>>>`.
3. Edite o código mantendo a lógica correta acordada com o colega.
4. Salve o arquivo e marque como resolvido:
   ```bash
   git add <arquivo-resolvido>
   git rebase --continue
   ```
5. Após concluir o rebase, execute `make lint` para validar a integridade.
6. Atualize o remoto com `git push --force-with-lease origin <sua-branch>`.

---

## 5. Integração Contínua (GitHub Actions)

O repositório deve conter um fluxo de trabalho em `.github/workflows/ci.yml` que valida automaticamente todo commit e PR contra a branch `main`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 mypy pytest build
      - name: Run Flake8
        run: flake8 .
      - name: Run Mypy
        run: mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
      - name: Run Pytest
        run: pytest
```

---

## 6. Checklist de Higiene do Repositório

Antes de considerar qualquer entrega concluída, certifique-se de que:
- O arquivo `.gitignore` bloqueia `__pycache__`, `.pytest_cache`, `.mypy_cache`, diretórios `.venv`, arquivos `.whl` temporários e relatórios de cobertura.
- Nenhum arquivo com credenciais, arquivos temporários de editor (`.vscode`, `.idea`, `*.swp`) ou caches de byte-code foram rastreados pelo Git.
- Todos os arquivos de texto terminam com quebra de linha `\n`.
