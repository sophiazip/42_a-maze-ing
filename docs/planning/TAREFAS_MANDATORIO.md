# Detalhamento de Tarefas — Parte Mandatória (A-Maze-ing)

Este documento estabelece o plano de ação técnico dividido em tarefas atômicas (Fase 0 à Fase 13). Cada tarefa define o objetivo, o responsável primário, os arquivos manipulados, as ações detalhadas e o critério de aceitação.

---

## Fase 0 — Configuração do Repositório e Ferramentas

### T0.1 — Estrutura de Diretórios e Controle de Versão
- **Responsável:** Integrante B (com apoio de A)
- **Arquivos:** `.gitignore`, estrutura base de pastas
- **Ações:**
  - Configurar `.gitignore` bloqueando `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.pytest_cache/`, `dist/`, `build/`, `*.egg-info/`, `.venv/` e relatórios temporários.
  - Criar as pastas do projeto: `mazegen/`, `tests/`.
- **Critério de Conclusão:** Executar `git status` em diretório limpo exibindo apenas os arquivos rastreados esperados.

### T0.2 — Ambiente Virtual e Dependências
- **Responsável:** Integrante B
- **Arquivos:** `requirements-dev.txt`
- **Ações:**
  - Criar ambiente virtual Python 3.10+ (`python3 -m venv .venv`).
  - Instalar ferramentas de desenvolvimento: `flake8`, `mypy`, `pytest`, `build`.
- **Critério de Conclusão:** Comandos `flake8 --version` e `mypy --version` funcionam no terminal ativo.

### T0.3 — Automação com Makefile
- **Responsável:** Integrante B
- **Arquivos:** `Makefile`
- **Ações:**
  - Implementar os alvos mandatórios do subject:
    - `install`: instalação de dependências e pacote em modo editável.
    - `run`: execução de `python3 a_maze_ing.py config.txt`.
    - `debug`: execução com debugger interativo `python3 -m pdb a_maze_ing.py config.txt`.
    - `clean`: remoção de caches (`__pycache__`, `.mypy_cache`, etc.).
    - `lint`: execução de `flake8 .` e `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`.
    - `lint-strict`: execução de `flake8 .` e `mypy . --strict`.
- **Critério de Conclusão:** O comando `make lint` executa sem erros de sintaxe do Makefile.

---

## Fase 1 — Parser do Arquivo de Configuração

### T1.1 — Modelo de Dados `MazeConfig`
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/config.py`
- **Ações:**
  - Declarar a classe imutável `@dataclass(frozen=True) MazeConfig`.
  - Definir campos tipados: `width: int`, `height: int`, `entry: tuple[int, int]`, `exit: tuple[int, int]`, `output_file: str`, `perfect: bool`, `seed: Optional[int]`, `algorithm: str`.
  - Implementar a função `parse_config(path: str) -> MazeConfig` com leitura via gerenciador de contexto `with open`.
- **Critério de Conclusão:** Arquivo de teste parseia com sucesso as linhas do formato `CHAVE=VALOR`, ignorando comentários iniciados com `#`.

### T1.2 — Validação Semântica de Parâmetros
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/config.py`, `tests/test_config.py`
- **Ações:**
  - Validar se `width > 0` e `height > 0`.
  - Checar se as coordenadas `entry` e `exit` respeitam `0 <= x < width` e `0 <= y < height`.
  - Validar se `entry != exit`.
  - Levantar exceção customizada `ConfigError` caso falte qualquer chave obrigatória ou ocorra erro de formatação.
- **Critério de Conclusão:** Testes unitários cobrem entradas com chaves ausentes, coordenadas fora dos limites e tipos inválidos, levantando mensagens de erro claras sem rastreamento de pilha.

### T1.3 — Criação do Arquivo de Configuração Padrão
- **Responsável:** Integrante B
- **Arquivos:** `config.txt`
- **Ações:**
  - Escrever o arquivo padrão contendo as seis chaves mandatórias (`WIDTH`, `HEIGHT`, `ENTRY`, `EXIT`, `OUTPUT_FILE`, `PERFECT`) e exemplos comentados de chaves opcionais (`SEED`, `ALGORITHM`).
- **Critério de Conclusão:** `parse_config("config.txt")` retorna uma instância válida de `MazeConfig`.

---

## Fase 2 — Núcleo do Gerador (Estrutura de Dados)

### T2.1 — Mapeamento de Paredes com `Direction`
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Criar `Direction(IntFlag)` com os valores especificados no subject: `NORTH = 1`, `EAST = 2`, `SOUTH = 4`, `WEST = 8`.
  - Adicionar dicionários de mapeamento para direções opostas (`OPPOSITE`) e vetores de deslocamento de coordenadas (`STEP`).
- **Critério de Conclusão:** Asserções em teste confirmam que `Direction.NORTH.opposite == Direction.SOUTH` e `Direction.EAST.opposite == Direction.WEST`.

### T2.2 — Estrutura da Classe `MazeGenerator`
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Definir o construtor `MazeGenerator(config: MazeConfig)`.
  - Alocar a matriz `grid` com dimensões `[height][width]`, preenchendo todas as células com `ALL_WALLS = 15`.
  - Armazenar o gerador pseudoaleatório `random.Random(config.seed)`.
- **Critério de Conclusão:** Instanciação da classe inicializa a grade com todas as células em `0xF`.

### T2.3 — Operações Atômicas de Parede (Garantia de Coerência)
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Criar o método `_remove_wall(r1: int, c1: int, r2: int, c2: int, direction: Direction) -> None`.
  - Atualizar atomicamente `grid[r1][c1] &= ~direction` e `grid[r2][c2] &= ~OPPOSITE[direction]`.
- **Critério de Conclusão:** Teste unitário verifica que após a remoção de qualquer parede, nenhuma célula apresenta incoerência perante o vizinho.

---

## Fase 3 — Algoritmo de Geração Perfeito (`PERFECT=True`)

### T3.1 — Implementação do Recursive Backtracker
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Implementar método iterativo com pilha explícita em lista.
  - Selecionar célula inicial em `config.entry` (convertida para `row, col`).
  - Iterar selecionando aleatoriamente vizinho não visitado e abrindo a divisória.
- **Critério de Conclusão:** Labirinto gerado conecta todas as células livres com exatamente uma rota única entre qualquer par de nós.

### T3.2 — Verificação de Conectividade Global
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Criar rotina auxiliar de varredura BFS para verificar se o número de nós alcançáveis a partir da entrada coincide com o número de células não bloqueadas.
- **Critério de Conclusão:** O gerador garante $0$ células desconectadas em grades de quaisquer dimensões.

---

## Fase 4 — Obstáculo Obrigatório "42"

### T4.1 — Definição do Bitmap do Padrão "42"
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Definir a matriz de pontos do padrão "42" (largura 7 células, altura 5 células).
- **Critério de Conclusão:** Inspeção matricial confere a legibilidade visual dos dígitos 4 e 2.

### T4.2 — Posicionamento e Margem de Segurança
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Posicionar o bloco na grade assegurando que não cubra a entrada, a saída, os 4 cantos ou o centro.
  - Emitir aviso amigável no console se a grade for menor que $11 \times 11$, desativando a inserção do obstáculo sem quebrar a execução.
- **Critério de Conclusão:** Grades pequenas emitem mensagem clara; grades compatíveis preservam as células-chave desobstruídas.

### T4.3 — Integração com a Geração do Labirinto
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Antes de iniciar o algoritmo de geração, registrar as células do "42" como fechadas (`ALL_WALLS`) e marcadas como visitadas para que o gerador contorne os obstáculos sem criar ilhas externas.
- **Critério de Conclusão:** O `maze_analyzer.py` reconhece as células fechadas do "42" sem reportar corredores desconectados ao redor.

---

## Fase 5 — Modo Tabuleiro Jogável (`PERFECT=False`)

### T5.1 — Geração da Base Estrutural
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Gerar inicialmente uma base conexa completa contornando o obstáculo "42".
- **Critério de Conclusão:** Malha inicial conexa pronta para abertura de circuitos.

### T5.2 — Garantia de Cantos e Centro Abertos
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Validar que as coordenadas `(0, 0)`, `(0, W-1)`, `(H-1, 0)`, `(H-1, W-1)` e o centro possuem grau $\ge 2$.
  - Se algum canto for beco sem saída na árvore inicial, abrir parede adicional para seu vizinho jogável.
- **Critério de Conclusão:** Verificação `unreachable_key_cells == ()` no analisador.

### T5.3 — Introdução de Ciclos Independentes ($L \ge 2$)
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Selecionar paredes internas elegíveis entre células que não dividem o mesmo corredor imediato e abri-las.
  - Garantir que o número ciclomático $L = E - V + 1$ atinja no mínimo 2.
- **Critério de Conclusão:** O script `maze_analyzer.py` reporta `loops >= 2`.

### T5.4 — Controle de Becos sem Saída (Dead-Ends)
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Contabilizar células de grau 1 adjacentes a corredores navegáveis.
  - Abrir passagens adicionais até que a quantidade de becos reais seja menor ou igual a 2.
- **Critério de Conclusão:** `maze_analyzer.py` aprova o arquivo com veredito `Pac-Man-USABLE`.

### T5.5 — Prevenção de Áreas Abertas $3 \times 3$
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Implementar verificação preditiva que rejeita a remoção de qualquer parede caso ela resulte em um bloco contíguo de 9 células sem paredes internas.
- **Critério de Conclusão:** Nenhuma área vazia $3 \times 3$ é formada no tabuleiro.

---

## Fase 6 — Menor Caminho e Serialização

### T6.1 — Solucionador BFS (Menor Rota)
- **Responsável:** Integrante B (com revisão de A)
- **Arquivos:** `mazegen/generator.py` (ou `mazegen/solver.py`)
- **Ações:**
  - Implementar busca em largura com `collections.deque` a partir da entrada até a saída.
  - Rastrear nó predecessor e direção de movimentação (`N`, `E`, `S`, `W`).
  - Reconstruir o caminho contíguo em string.
- **Critério de Conclusão:** A string de direções conduz com exatidão da entrada até a saída respeitando as paredes abertas.

### T6.2 — Serializador do Arquivo de Saída
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Gerar as linhas com os dígitos hexadecimais de cada célula.
  - Inserir linha vazia e gravar as 3 linhas do rodapé: coordenadas da entrada, coordenadas da saída e rota da BFS terminada em `\n`.
- **Critério de Conclusão:** Arquivo gerado em disco possui formato idêntico ao exemplo do Capítulo IV do subject.

### T6.3 — Validação Automatizada com o Analisador
- **Responsável:** Integrante B e Integrante A
- **Arquivos:** `tests/test_analyzer.py`
- **Ações:**
  - Executar `python3 maze_analyzer.py maze.txt` tanto para `PERFECT=True` quanto para `PERFECT=False`.
- **Critério de Conclusão:** Retorno do analisador com código de saída 0 e status de validação aprovado.

---

## Fase 7 — Ponto de Entrada `a_maze_ing.py`

### T7.1 — Orquestração da Linha de Comando
- **Responsável:** Integrante B
- **Arquivos:** `a_maze_ing.py`
- **Ações:**
  - Validar a passagem do argumento do arquivo de configuração na linha de comando (`sys.argv[1]`).
  - Coordenar a leitura da configuração, instanciação do `MazeGenerator`, geração do labirinto e gravação do arquivo de saída.
- **Critério de Conclusão:** O comando `python3 a_maze_ing.py config.txt` executa a cadeia completa e grava o arquivo de saída.

### T7.2 — Tratamento Robusto de Exceções
- **Responsável:** Integrante B
- **Arquivos:** `a_maze_ing.py`
- **Ações:**
  - Tratar `FileNotFoundError`, `PermissionError`, `ConfigError` e parâmetros matematicamente impossíveis com mensagens claras no fluxo de erro padrão (`sys.stderr`).
  - Assegurar que nenhum erro de configuração resulte em encerramento com traceback do Python.
- **Critério de Conclusão:** Testes manuais com arquivos inexistentes ou corrompidos finalizam com código de saída 1 e mensagem de erro legível.

---

## Fase 8 — Representação Visual (ASCII)

### T8.1 — Renderizador ASCII do Labirinto
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/renderer_ascii.py`
- **Ações:**
  - Desenhar as paredes do labirinto usando caracteres visuais adequados.
  - Destacar a entrada com `E`, a saída com `X` e o padrão "42" com caracteres sólidos.
- **Critério de Conclusão:** O labirinto é renderizado no terminal mantendo proporções visuais coerentes.

### T8.2 — Laço de Interação no Terminal
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/renderer_ascii.py`
- **Ações:**
  - Implementar menu interativo respondendo a comandos de tecla:
    - Regenerar labirinto com nova semente.
    - Exibir ou ocultar a rota do menor caminho com cores ANSI.
    - Alternar paletas de cores das paredes.
    - Sair do programa.
- **Critério de Conclusão:** O usuário alterna entre os estados sem necessidade de reiniciar a aplicação.

### T8.3 — Suporte Opcional à Biblioteca Gráfica MiniLibX
- **Responsável:** Integrante B (com apoio de A)
- **Arquivos:** `mazegen/renderer_mlx.py`
- **Ações:**
  - Carregar dinamicamente o módulo `mlx` caso esteja instalado no sistema.
  - Implementar janela interativa mapeando eventos de teclado para regeneração, exibição de rota e troca de cores.
- **Critério de Conclusão:** A interface gráfica MLX opera com as mesmas capacidades do renderizador ASCII quando disponível.

---

## Fase 9 — Reusabilidade e Empacotamento

### T9.1 — Estruturação do Módulo Standalone
- **Responsável:** Integrante A e Integrante B
- **Arquivos:** `mazegen/__init__.py`, `mazegen/generator.py`
- **Ações:**
  - Exportar a classe principal na raiz do pacote: `from mazegen.generator import MazeGenerator`.
  - Isolar qualquer dependência de CLI ou visualização fora do pacote central de geração.
- **Critério de Conclusão:** `python3 -c "import mazegen; gen = mazegen.MazeGenerator(...)"` funciona de forma autônoma.

### T9.2 — Configuração do `pyproject.toml`
- **Responsável:** Integrante B
- **Arquivos:** `pyproject.toml`
- **Ações:**
  - Declarar metadados do pacote (nome `mazegen`, versão `1.0.0`, descrição, autores, Python `>=3.10`).
  - Configurar sistema de build padronizado (setuptools).
- **Critério de Conclusão:** O comando `python3 -m build` compila o pacote sem avisos de configuração obsoleta.

### T9.3 — Geração do Pacote `.whl`
- **Responsável:** Integrante B
- **Arquivos:** `mazegen-1.0.0-py3-none-any.whl`
- **Ações:**
  - Construir o pacote e posicionar o arquivo `.whl` na raiz do repositório conforme exigido pelo Capítulo VI do subject.
  - Testar a instalação em um ambiente virtual isolado: `pip install mazegen-*.whl`.
- **Critério de Conclusão:** O módulo instalado via wheel funciona em script externo independente.

### T9.4 — Licença de Código Aberto
- **Responsável:** Integrante B
- **Arquivos:** `LICENSE.md`
- **Ações:**
  - Adicionar arquivo `LICENSE.md` com licença permissiva (MIT) autorizando expressamente a reutilização e distribuição do código em projetos futuros da 42.
- **Critério de Conclusão:** Arquivo presente na raiz contendo os termos de reutilização.

---

## Fase 10 — Documentação Técnica e README

### T10.1 — Elaboração do `README.md`
- **Responsável:** Integrante B e Integrante A
- **Arquivos:** `README.md`
- **Ações:**
  - Inserir a linha de abertura obrigatória em itálico: `*This project has been created as part of the 42 curriculum by <login1>, <login2>.*`
  - Redigir as seções exigidas pelo subject: Descrição, Instruções de Instalação/Uso, Recursos e Uso de IA, Estrutura do Config, Justificativa dos Algoritmos, Guia de Reuso do Módulo, Gestão da Equipe e Retrospectiva.
- **Critério de Conclusão:** Todas as seções requeridas pelo Capítulo VII do subject estão presentes e documentadas.

### T10.2 — Guia Rápido de Uso do Módulo Reutilizável
- **Responsável:** Integrante A
- **Arquivos:** `README.md` e docstrings de `MazeGenerator`
- **Ações:**
  - Incluir exemplos de código demonstrando como instanciar `MazeGenerator`, passar parâmetros customizados e extrair o labirinto gerado e sua rota de solução.
- **Critério de Conclusão:** Exemplo fornecido no README pode ser copiado, colado e executado diretamente com sucesso.

---

## Fase 11 — Qualidade de Código, Estilo e Tipagem

### T11.1 — Anotação de Tipos e Docstrings PEP 257
- **Responsável:** Integrante A e Integrante B
- **Arquivos:** Todos os arquivos Python do projeto
- **Ações:**
  - Anotar 100% dos parâmetros e tipos de retorno de funções e métodos utilizando o módulo `typing`.
  - Redigir docstrings para todas as classes, métodos e funções públicas.
- **Critério de Conclusão:** Nenhuma função ou método sem tipagem estrita no projeto.

### T11.2 — Validação com Flake8
- **Responsável:** Integrante B
- **Arquivos:** `.flake8`, código-fonte
- **Ações:**
  - Executar `flake8 .` e sanar quaisquer desvios de PEP 8 (comprimento de linha, quebras incorretas, importações não utilizadas).
- **Critério de Conclusão:** `flake8 .` retorna saída vazia com código de término 0.

### T11.3 — Checagem Estática com Mypy
- **Responsável:** Integrante A
- **Arquivos:** Código-fonte
- **Ações:**
  - Executar as flags obrigatórias do subject:
    `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`.
  - Executar validação estrita com `mypy . --strict`.
- **Critério de Conclusão:** Mypy relata zero inconsistências em modo estrito.

---

## Fase 12 — Testes Automatizados

### T12.1 — Bateria de Testes Unitários com Pytest
- **Responsável:** Integrante A e Integrante B
- **Arquivos:** `tests/test_config.py`, `tests/test_generator.py`, `tests/test_renderer.py`
- **Ações:**
  - Implementar testes para coerência de paredes, algoritmo de geração, limites de coordenadas e comportamento com seeds repetidas.
- **Critério de Conclusão:** O comando `pytest` executa todos os testes unitários com 100% de aprovação.

### T12.2 — Testes de Regressão com o Analisador Oficial
- **Responsável:** Integrante A e Integrante B
- **Arquivos:** Scripts de teste em `tests/`
- **Ações:**
  - Criar script automatizado gerando 50 labirintos aleatórios em modo perfeito e 50 em modo Pac-Man, submetendo cada um ao `maze_analyzer.py`.
- **Critério de Conclusão:** Todos os 100 labirintos gerados são aprovados sem advertências de incoerência, ilhas desconectadas ou violações topológicas.

---

## Fase 13 — Revisão Final e Preparação para a Defesa

### T13.1 — Auditoria de Requisitos do Subject
- **Responsável:** Ambos os integrantes em conjunto
- **Arquivos:** Todos os arquivos do repositório
- **Ações:**
  - Conferir item por item dos Capítulos III a VII do subject (nomenclatura exata de arquivos, comportamento dos argumentos, ausência de falhas com entradas inválidas).
- **Critério de Conclusão:** 100% dos requisitos mandatórios formalmente validados.

### T13.2 — Higienização do Repositório
- **Responsável:** Integrante B
- **Arquivos:** Raiz do repositório
- **Ações:**
  - Executar `make clean`.
  - Verificar com `git status` e `git clean -nd` que nenhum resíduo de build ou arquivos não rastreados estão presentes.
- **Critério de Conclusão:** Árvore do Git perfeitamente limpa.

### T13.3 — Simulação e Ensaio de Defesa Presencial
- **Responsável:** Ambos os integrantes em conjunto
- **Arquivos:** `docs/flashcards/FLASHCARDS_DEFESA.md`
- **Ações:**
  - Realizar simulação completa de defesa, com perguntas técnicas cruzadas e ensaio de alteração de código ao vivo em tempo cronometrado.
- **Critério de Conclusão:** Ambos os integrantes conseguem explicar qualquer linha do código e aplicar modificações solicitadas com segurança.
