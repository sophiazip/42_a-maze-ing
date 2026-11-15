# Inventário de Arquitetura e Contratos de Código — A-Maze-ing

Este documento cataloga a arquitetura real do projeto **A-Maze-ing**, especificando a responsabilidade de cada módulo, as interfaces públicas das classes e o fluxo de dados entre os componentes do sistema.

Veja também:
- [[docs/architecture/GUIA_ESTUDO_MANDATORIO.md]]
- [[docs/architecture/GUIA_ESTUDO_BONUS.md]]
- [[docs/architecture/GUIA_AUDIO_E_ANIMACAO.md]]

---

## 1. Visão Geral da Arquitetura

O sistema é dividido em camadas bem desacopladas: Configuração (`mazegen/config.py`), Núcleo de Domínio (`mazegen/generator.py`), Estado e Animação (`mazegen/session.py`), Áudio 8-bit (`mazegen/sound.py`) e Camada de Apresentação (`renderer_ascii.py` e `renderer_mlx.py`).

```
                              config.txt
                                  │
                                  ▼
                          mazegen/config.py
                      (MazeConfig, ALGORITHMS)
                                  │
                                  ▼
                        mazegen/generator.py
             (MazeGenerator, GenerationStep, BFS, Braiding)
                          │               │
         ┌────────────────┘               └────────────────┐
         ▼                                                 ▼
mazegen/renderer_ascii.py                         mazegen/session.py
   (Interface Terminal)                      (MazeSession + Animação + Temas)
         │                                                 │
         │                                    ┌────────────┴────────────┐
         │                                    ▼                         ▼
         │                         mazegen/renderer_mlx.py       mazegen/sound.py
         │                            (MazeWindow / X11)        (ChiptunePlayer)
         │                                    │
         └──────────────────┬─────────────────┘
                            ▼
                      a_maze_ing.py
                     (Entry Point CLI)
                            │
                            ▼
                        maze.txt
```

---

## 2. Especificação Módulo a Módulo

### 2.1 `mazegen/config.py`

Responsável pelo carregamento, análise sintática e validação estrita dos parâmetros do labirinto.

- **Constantes centralizadas:**
  - `MANDATORY_KEYS`: `WIDTH`, `HEIGHT`, `ENTRY`, `EXIT`, `OUTPUT_FILE`, `PERFECT`.
  - `OPTIONAL_KEYS`: `SEED`, `ALGORITHM`, `DISPLAY`.
  - `ALGORITHMS: Tuple[str, ...] = ("backtracker", "kruskal", "prim")` e `VALID_ALGORITHMS = frozenset(ALGORITHMS)`.
  - `VALID_DISPLAYS = frozenset({"ascii", "mlx"})`.
- **Classe `MazeConfig` (`@dataclass(frozen=True)`):**
  - Campos: `width`, `height`, `entry`, `exit`, `output_file`, `perfect`, `seed: Optional[int] = None`, `algorithm: str = "backtracker"`, `display: str = "ascii"`.
- **Função `parse_config(path: str) -> MazeConfig`:**
  - Lê pares `KEY=VALUE` ignorando linhas vazias e comentários `#`.
  - Valida chaves obrigatórias, tipos, limites (`0 <= x < width`, `0 <= y < height`, `entry != exit`) e levanta `ConfigError` em qualquer inconsistência.

---

### 2.2 `mazegen/generator.py`

Núcleo computacional standalone exportado em `mazegen/__init__.py` para empacotamento em `mazegen-*.whl`.

- **Enum `Direction(IntFlag)`:** `NORTH = 1`, `EAST = 2`, `SOUTH = 4`, `WEST = 8`, com propriedades `opposite`, `step` e `letter`.
- **Dataclass `GenerationStep`:** registra `kind` (`"carve"`, `"backtrack"`, `"braid"`), `cell_a`, `cell_b`, `direction` e `active` para reprodução animada.
- **Classe `_DisjointSetUnion`:** Union-Find com compressão de caminho (`find`) e união por posto (`union`) para o algoritmo de Kruskal.
- **Classe `MazeGenerator`:**
  - Aceita `config: Optional[MazeConfig]` ou parâmetros nomeados (`width`, `height`, `entry`, `exit`, `perfect`, `seed`, `algorithm`).
  - `_compute_pattern_cells()`: centraliza o padrão `"42"` (`PATTERN_42`) ou o omite com aviso em `stderr` se o mapa for pequeno ou colidir com `entry`/`exit`.
  - `generate(record_steps: bool = False)`: executa `_run_backtracker`, `_run_kruskal` ou `_run_prim`, garante conectividade (`_ensure_full_connectivity`), aplica trançamento e loops (`_braid_and_add_loops`) quando `perfect=False`, e popula `generation_steps` se solicitado.
  - `shortest_path() -> str` e `shortest_path_coords() -> List[Coord]`: usam `_bfs_solve()` para encontrar a menor rota em `N/E/S/W`.
  - `solve_with_trace() -> Tuple[List[Cell], List[Cell]]`: retorna `(explored_cells, shortest_path_cells)` para animação da onda BFS.
  - `to_hex_rows()` e `write_output(filepath, path=None)`: serializam a grade em hexadecimal e gravam o arquivo de saída.
- **Função `pick_random_endpoints(width, height, blocked_cells, rng=None)`:** sorteia novas coordenadas `(entry, exit)` fora das células do `"42"`, priorizando distância mínima de Manhattan `(width + height) // 3`.

---

### 2.3 `mazegen/session.py`

Máquina de estados de apresentação e animação desacoplada do servidor gráfico X11 (permitindo testes unitários *headless*).

- **Paletas e Cores:** `WALL_PALETTE`, `PATTERN_PALETTE` e `_hsv_to_argb(hue, sat, val)` para o modo Rainbow.
- **Classe `MazeSession`:**
  - Gerencia `show_path`, `wall_color_index`, `pattern_color_index`, `rainbow` e `rainbow_phase`.
  - Ações de usuário: `toggle_path()`, `toggle_rainbow()`, `cycle_wall_color()`, `cycle_pattern_color()`, `cycle_algorithm()`, `regenerate()`, `randomize_endpoints()`.
  - Máquina de estados de animação (`anim_phase`: `"carving"` → `"solving"` → `"tracing"` → `"celebrate"` → `"idle"`): `start_carve_animation()`, `start_solve_animation()`, `step_animation()`, `replay_or_skip()`, `skip_animation()`.

---

### 2.4 `mazegen/sound.py`

Motor de áudio 8-bit chiptune em Python puro (detalhado em [[docs/architecture/GUIA_AUDIO_E_ANIMACAO.md]]).

- **Síntese:** `synthesize_tone()`, `synthesize_sequence()`, `synthesize_victory_fanfare()` sobre `PENTATONIC_HZ` a `22050 Hz` (`s16le`).
- **Classe `ChiptunePlayer`:**
  - Thread daemon enviando frames contínuos de `20ms` (`FRAME_BYTES = 882`) para `paplay --raw --latency-msec=40 --process-time-msec=15` (ou `pw-play`).
  - Métodos reativos: `play_carve()`, `play_solve()`, `play_trace()`, `play_victory()`, `play_ui_click()`, `toggle_mute()`, `clear()`, `close()`.

---

### 2.5 `mazegen/renderer_ascii.py`

Renderizador Unicode box-drawing com cores ANSI para terminal.

- `render_ascii(gen, show_path=True, wall_color_idx=0, pattern_color_idx=0) -> str`: desenha junções precisas (`JUNCTION_GLYPHS`), ponte de caminho, entrada (`◆`), saída (`★`) e padrão `"42"`.
- `run_ascii_loop(...)` e `_animate_ascii(...)`: menu interativo com regeneração (`1/r`), caminho (`2/p`), tema (`3/c`), cor do 42 (`t`), rainbow (`b`), algoritmo (`a`), randomizar pontos (`e`), animação (`v`) e saída (`4/q`).

---

### 2.6 `mazegen/renderer_mlx.py`

Interface gráfica nativa via MiniLibX (`mlx-2.2`).

- **Classe `MazeWindow`:**
  - Consome `MazeSession` e `ChiptunePlayer`.
  - Rasteriza piso xadrez, trilhas de brilho (`_blend_argb`), fita contínua do caminho (`_draw_path_ribbon`), beacons concêntricos (`_draw_beacon`), paredes e barras HUD superior/inferior.
  - Loop não-bloqueante `_on_loop`: avança animações a ~60 FPS (`0.016s`), rainbow a ~20 FPS (`0.05s`) e dispara notas sincronizadas via `_emit_animation_sound()`.
  - Atalhos (`_on_key_press`): `1/R` (Regen), `2/P` (Path), `3/C` (Tema), `T` (42), `B` (Rainbow), `A` (Algo), `E` (Pontos aleatórios), `M` (Mute), `Space` (Skip/Play), `4/Q/Esc` (Sair).

---

### 2.7 `a_maze_ing.py` e `tests/`

- **`a_maze_ing.py`**: CLI principal com suporte a `--display ascii|mlx`, execução de `MazeGenerator.generate(record_steps=True)`, gravação do arquivo de saída e tratamento limpo de erros.
- **`tests/`**: suíte `unittest` cobrindo configuração (`test_config.py`), algoritmos/trançamento/trace/endpoints (`test_generator.py`), renderização e ciclo de vida de `MazeSession` (`test_renderer.py`) e síntese/player 8-bit (`test_sound.py`).
