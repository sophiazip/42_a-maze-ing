# Inventário de Arquitetura e Contratos de Código — A-Maze-ing

Este documento cataloga a arquitetura de software planejada para o projeto, especificando a responsabilidade de cada módulo, as interfaces públicas das classes e o fluxo de dados entre os componentes do sistema.

---

## 1. Visão Geral da Arquitetura

O sistema é dividido em três camadas bem desacopladas: Núcleo de Domínio (`mazegen/generator.py`), Configuração e I/O (`mazegen/config.py` e rotinas de salvamento) e Camada de Apresentação (`renderer_ascii.py` e `renderer_mlx.py`).

```
                              config.txt
                                  │
                                  ▼
                          mazegen/config.py
                           (MazeConfig)
                                  │
                                  ▼
                        mazegen/generator.py
                          (MazeGenerator)
                           │           │
            ┌──────────────┴───────────┴──────────────┐
            ▼                                         ▼
   mazegen/renderer_ascii.py               mazegen/renderer_mlx.py
      (Interface Terminal)                   (Interface Gráfica)
            │                                         │
            └─────────────────┬───────────────────────┘
                              ▼
                         a_maze_ing.py
                        (Entry Point CLI)
                              │
                              ▼
                          maze.txt
                              │
                              ▼
                       maze_analyzer.py
                    (Validador Independente)
```

---

## 2. Especificação Módulo a Módulo

### 2.1 `mazegen/config.py`

Responsável pelo carregamento, análise sintática e validação estrita dos parâmetros do labirinto.

- **Classe `MazeConfig`:**
  - `@dataclass(frozen=True)`
  - Campos:
    - `width: int`: largura em número de células (colunas).
    - `height: int`: altura em número de células (linhas).
    - `entry: tuple[int, int]`: coordenada de entrada no formato cartesiano `(x, y)`.
    - `exit: tuple[int, int]`: coordenada de saída no formato cartesiano `(x, y)`.
    - `output_file: str`: caminho do arquivo de saída a ser gravado.
    - `perfect: bool`: define se o labirinto deve ser árvore geradora única (`True`) ou tabuleiro Pac-Man com circuitos (`False`).
    - `seed: Optional[int]`: semente numérica para garantir reprodutibilidade.
    - `algorithm: str`: identificador do gerador (`backtracker`, `kruskal`, `prim`).
    - `visual_mode: str`: modo de visualização inicial (`ascii` ou `mlx`).

- **Funções:**
  - `parse_config(filepath: str) -> MazeConfig`:
    - Abre o arquivo usando gerenciador de contexto `with open(...)`.
    - Ignora linhas em branco e comentários iniciados com `#`.
    - Separa chaves e valores dividindo estritamente pelo primeiro caractere `=`.
    - Valida que todas as 6 chaves mandatórias estão presentes.
    - Converte strings para inteiros, booleanos e tuplas cartesianas.
    - Executa validações de consistência: `width > 0`, `height > 0`, entrada e saída contidas nos limites da grade e não sobrepostas (`entry != exit`).
    - Em caso de inconsistência, levanta exceção customizada `ConfigError` contendo mensagem explicativa amigável.

---

### 2.2 `mazegen/generator.py`

Núcleo computacional do sistema. É o componente exigido pelo Capítulo VI do subject para publicação como pacote reutilizável no arquivo `mazegen-*.whl`.

- **Enum `Direction(IntFlag)`:**
  - `NORTH = 1`, `EAST = 2`, `SOUTH = 4`, `WEST = 8`.
  - Propriedades auxiliares:
    - `opposite -> Direction`: retorna a direção oposta (`NORTH <-> SOUTH`, `EAST <-> WEST`).
    - `step -> tuple[int, int]`: retorna a tupla `(d_row, d_col)` correspondente.

- **Classe `MazeGenerator`:**
  - `__init__(config: MazeConfig) -> None`:
    - Armazena a configuração.
    - Instancia o gerador de números pseudoaleatórios `random.Random(config.seed)`.
    - Inicializa a matriz interna `grid: list[list[int]]` com dimensões `[height][width]`, preenchendo cada posição com `int(ALL_WALLS)`.
    - Calcula as posições ocupadas pelo padrão "42" e as marca como células fechadas não-navegáveis.
  - `generate() -> None`:
    - Se `config.perfect == True`: executa a geração de árvore única através do algoritmo escolhido (`_run_backtracker`, `_run_kruskal` ou `_run_prim`).
    - Se `config.perfect == False`: gera a base perfeita inicial, assegura a abertura dos 4 cantos e do centro, e abre paredes controladas para introduzir ciclos ($L \ge 2$) mantendo os becos sem saída abaixo do limite exigido.
  - `braid() -> None`:
    - Localiza todos os nós de grau 1 adjacentes a corredores navegáveis.
    - Remove paredes divisórias até que a contagem de becos sem saída reais chegue a zero, rejeitando candidatos que gerem áreas $3 \times 3$ abertas.
  - `solve() -> tuple[list[tuple[int, int]], str]`:
    - Executa busca em largura (BFS) da entrada `(entry_row, entry_col)` até a saída `(exit_row, exit_col)`.
    - Retorna a lista contendo as coordenadas das células percorridas e a string contígua com as direções (`N`, `E`, `S`, `W`).
  - `to_hex_rows() -> list[str]`:
    - Converte cada linha da matriz de inteiros em uma string formada por dígitos hexadecimais em caixa alta (`0-9`, `A-F`).
  - `write_output_file(destination_path: Optional[str] = None) -> None`:
    - Grava o arquivo físico de saída seguindo rigorosamente a estrutura estipulada pelo subject: linhas da grade, linha vazia, coordenadas da entrada, coordenadas da saída e menor caminho.

---

### 2.3 `mazegen/renderer_ascii.py`

Responsável pela apresentação em modo texto no terminal padrão.

- **Funções Principais:**
  - `draw_maze_to_string(generator: MazeGenerator, show_path: bool, color_theme: str) -> str`:
    - Monta uma representação gráfica em caracteres Unicode/ASCII para exibir paredes verticais, horizontais e interseções.
    - Aplica sequências ANSI de cor para realçar paredes, entrada (`E`), saída (`X`), células do número "42" e a rota calculada.
  - `run_ascii_interactive_loop(generator: MazeGenerator) -> None`:
    - Exibe o labirinto renderizado e um menu de comandos de tecla simples:
      - `1` ou `R`: regenera o labirinto com nova semente aleatória.
      - `2` ou `P`: alterna a visibilidade do menor caminho (*toggle path*).
      - `3` ou `C`: cicla a cor das paredes entre os temas disponíveis.
      - `4` ou `Q`: encerra a execução do programa.

---

### 2.4 `mazegen/renderer_mlx.py`

Interface gráfica nativa operando com a biblioteca gráfica MiniLibX (MLX via X11).

- **Classe `MazeWindow`:**
  - `__init__(generator: MazeGenerator, tile_size: int = 24) -> None`:
    - Inicializa o contexto MLX via `mlx.init()`.
    - Cria a janela do sistema com dimensões proporcionais à grade: `width * tile_size` por `height * tile_size`.
    - Aloca um buffer de imagem com `mlx.new_image()`.
  - `render_frame() -> None`:
    - Desenha cada célula e suas paredes correspondentes preenchendo os pixels no buffer.
    - Se a rota estiver ativada, sobrepõe os marcadores coloridos do menor caminho.
    - Envia o buffer pronto para a janela com `mlx.put_image_to_window()`.
  - `on_key_press(keycode: int) -> int`:
    - Captura eventos de teclado:
      - Tecla `R` ou `1`: aciona `generator.regenerate()` e redesenha o buffer.
      - Tecla `P` ou `2`: inverte o booleano `show_path` e atualiza a janela.
      - Tecla `C` ou `3`: cicla a paleta de cores.
      - Tecla `Escape` ou `Q`: fecha a janela e encerra o loop de eventos de forma limpa.

---

### 2.5 `a_maze_ing.py`

Ponto de entrada obrigatório na raiz do repositório.

- **Comportamento do `main`:**
  - Verifica se o caminho do arquivo de configuração foi fornecido via `sys.argv[1]`. Em caso negativo, exibe a sintaxe de uso e encerra com código de saída 1.
  - Chama `parse_config(sys.argv[1])` encapsulado em bloco `try-except` para interceptar erros sem que o interpretador exiba *traceback* descontrolado.
  - Instancia `MazeGenerator(config)`.
  - Executa a geração do labirinto e salva o resultado no caminho indicado por `config.output_file`.
  - Inicia a visualização interativa configurada (ASCII ou MLX).
