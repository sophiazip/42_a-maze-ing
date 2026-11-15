# Guia de Áudio 8-bit e Animações (*Game-Feel*) — A-Maze-ing

Este guia documenta a arquitetura de animações em tempo real, efeitos visuais (*game-feel*) e síntese sonora chiptune em 8-bit implementada no projeto **A-Maze-ing**.

Documentos relacionados:
- [[docs/architecture/INVENTARIO_CODIGO.md]]
- [[docs/architecture/GUIA_ESTUDO_BONUS.md]]
- [[docs/testing/ROTEIRO_DEFESA_BONUS.md]]

---

## 1. Arquitetura de Animação (`mazegen/generator.py` + `mazegen/session.py`)

Em vez de acoplar loops de desenho dentro dos algoritmos de geração, o sistema separa **captura de eventos** e **reprodução visual**:

1. **Captura (`MazeGenerator.generate(record_steps=True)`)**:
   - Cada abertura de parede ou retrocesso emite um `GenerationStep(kind, cell_a, cell_b, direction, active)` na lista `generation_steps`:
     - `"carve"`: avanço normal (Backtracker, Kruskal, Prim ou ponte de conectividade).
     - `"backtrack"`: recuo na pilha do Recursive Backtracker ao encontrar beco sem saída.
     - `"braid"`: abertura adicional para eliminar becos no modo `PERFECT=False`.
   - O arquivo de saída (`maze.txt`) é gravado imediatamente com a grade final válida, sem depender da velocidade da animação.

2. **Rastreamento do Solver (`MazeGenerator.solve_with_trace()`)**:
   - Executa o mesmo BFS (`_bfs_solve()`) usado por `shortest_path()`, retornando `(explored_cells, shortest_path_cells)`:
     - `explored_cells`: ordem exata da frente de onda BFS a partir da entrada até atingir a saída.
     - `shortest_path_cells`: sequência ordenada `(row, col)` da entrada até a saída.

3. **Máquina de Estados (`MazeSession` em `mazegen/session.py`)**:
   - `MazeSession` controla o ciclo de vida visual em 5 estados (`anim_phase`):
     - **`carving`**: inicia `anim_grid` toda fechada (`ALL_WALLS`) e aplica `generation_steps` em lotes adaptativos (`max(1, len(steps) // 140)`), mantendo `carved_cells`, `active_cell` e um mapa de decaimento `carve_glow` (intensidade `8 -> 0`).
     - **`solving`**: expande a onda BFS (`solve_idx`) aplicando `solve_glow` (`7 -> 0`) na frente de onda e preenchendo `solve_visited`.
     - **`tracing`**: revela progressivamente a fita do menor caminho (`solve_path[:trace_idx]`) até tocar a saída.
     - **`celebrate`**: pulsa a fita do caminho e o marcador de saída durante 12 ticks.
     - **`idle`**: exibição estável final.
   - Atalho **`Space`** (`replay_or_skip()`) pula instantaneamente para `idle` se estiver animando, ou reinicia a reprodução se estiver parado.

---

## 2. Efeitos Visuais e Interatividade (`mazegen/renderer_mlx.py` & `mazegen/renderer_ascii.py`)

- **Interpolação de Cor (`_blend_argb`)**:
  - Células recém-escavadas e células na frente de onda BFS têm sua cor de piso interpolada linearmente entre o piso base e a cor ativa de parede/caminho, criando um rastro luminoso (*neon trail*) sem precisar de canal alpha de hardware.
- **Modo Rainbow Dinâmico (`KEYS_RAINBOW` — tecla `B` / `b`)**:
  - `MazeSession.advance_rainbow()` gira `rainbow_phase` em `[0.0, 1.0)` e `_hsv_to_argb()` calcula dinamicamente cores harmônicas para paredes, caminho, tint de piso e padrão `"42"`.
  - No loop MLX (`_on_loop`), a animação roda a ~60 FPS (`>= 0.016s`) e o rainbow a ~20 FPS (`>= 0.05s`) sem bloquear eventos de teclado (`mlx_key_hook`).
- **Randomização de Pontos (`pick_random_endpoints`)**:
  - Acionada por **`E`** na GUI MLX ou **`e`** no terminal ASCII, sorteia novas coordenadas `ENTRY` e `EXIT` evitando as células fechadas do padrão `"42"` e priorizando distância mínima de Manhattan `(width + height) // 3`.
- **Animação no Terminal (`_animate_ascii`)**:
  - Acionada pela opção **`v`** no menu ASCII, reproduz a escavação progressiva da grade usando `ANSI_CLEAR` (`\033[2J\033[H`) sem *flickering*.

---

## 3. Sistema de Áudio 8-bit Chiptune (`mazegen/sound.py`)

O áudio é gerado 100% em Python puro (biblioteca padrão `math`, `struct`, `subprocess`, `threading`), sem dependências externas como `pygame` ou `numpy`.

### 3.1 Síntese de Ondas Retrô
- Taxa de amostragem: **22050 Hz**, PCM mono **16-bit signed little-endian** (`s16le`).
- Formas de onda implementadas em `_sample_wave()`:
  - `square` (duty cycle 50%): timbre clássico de lead do NES, usado no traçado do caminho e na fanfarra final.
  - `square25` (duty cycle 25%): timbre mais estreito e percussivo, usado na escavação e cliques de UI.
  - `triangle`: timbre suave, usado em `backtrack` e na onda de scanner BFS (`solving`).
- `synthesize_tone()` aplica envelope linear de **attack (6%)** e **release (30%)**, além de interpolação opcional de frequência (`end_freq`) para efeitos de *pitch glide*.
- As notas são mapeadas sobre a escala pentatônica maior de Dó (`PENTATONIC_HZ`), garantindo que sequências aleatórias de células nunca soem desafinadas.

### 3.2 Streaming Contínuo de Baixa Latência
- Problema evitado: enviar pequenos blocos soltos para `paplay --raw` causa atraso (~2s de buffer padrão) e *buffer underruns* (cortes entre notas).
- Solução em `ChiptunePlayer`:
  - Abre `paplay --raw --rate=22050 --channels=1 --format=s16le --latency-msec=40 --process-time-msec=15` (com fallback para `pw-play`).
  - A thread daemon `_worker()` envia **continuamente** frames fixos de **20ms** (`FRAME_SAMPLES = 441`, `FRAME_BYTES = 882`), preenchendo períodos ociosos com `SILENCE_FRAME`.
  - Efeitos curtos substituem o buffer ativo (`_submit_pcm`) sem enfileirar atraso; a fanfarra de vitória (`synthesize_victory_fanfare`) usa `priority=True` para não ser interrompida.
  - Se não houver servidor de áudio ou player CLI disponível (ex.: ambiente headless/CI), `ChiptunePlayer.available` torna-se `False` e todas as chamadas viram *no-op* seguro.
  - Tecla **`M`** alterna mudo (`toggle_mute()`) e `clear()` zera o buffer imediatamente ao pular a animação (`Space`).
