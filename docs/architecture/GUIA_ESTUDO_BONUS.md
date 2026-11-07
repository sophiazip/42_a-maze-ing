# Guia Teórico e Técnico da Parte Bônus — A-Maze-ing

Este documento detalha os algoritmos e a engenharia necessária para implementar os três bônus sugeridos no Capítulo VIII do subject: tabuleiro perfeitamente trançado (*braided* sem becos sem saída), geradores alternativos com Kruskal e Prim, e animação da geração em tempo real no terminal e via MiniLibX.

---

## 1. Bônus 1: Tabuleiro Trançado (*Braided Maze*) com Zero Dead-Ends

No jogo Pac-Man, corredores sem saída representam armadilhas fatais quando os fantasmas se aproximam. Um tabuleiro é classificado como *braided* (trançado) quando todos os becos sem saída são eliminados pela abertura de passagens adicionais, transformando todo caminho em parte de pelo menos um circuito.

### 1.1 Detecção de Becos sem Saída

Um beco sem saída é uma célula de grau 1 ($deg(v) = 1$), ou seja, possui apenas uma parede aberta e três paredes fechadas.

Para fins de avaliação pelo script oficial `maze_analyzer.py`, os becos dividem-se em dois tipos:
- **Beco encerrado (*enclosed*):** célula de grau 1 cujas paredes fechadas fazem divisa exclusivamente com o obstáculo "42" ou com as bordas externas da grade. Este tipo não pode ser aberto e é tolerado pelo analisador.
- **Beco real (*real dead-end*):** célula de grau 1 que possui pelo menos uma parede fechada voltada para outra célula jogável comum. O bônus exige que a contagem de becos reais seja exatamente zero.

### 1.2 Algoritmo de Trançamento (Braiding Loop)

O procedimento itera sobre a malha enquanto houver becos sem saída reais:

```python
def braid_maze(
    grid: list[list[int]],
    rows: int,
    cols: int,
    is_blocked: set[tuple[int, int]],
    rng: random.Random
) -> None:
    while True:
        dead_ends: list[tuple[int, int]] = []
        for r in range(rows):
            for c in range(cols):
                cell = (r, c)
                if cell in is_blocked:
                    continue
                # Conta quantas passagens estão abertas
                open_passages = sum(
                    1 for d in Direction if not (grid[r][c] & d)
                )
                if open_passages == 1 and has_openable_normal_wall(grid, r, c, rows, cols, is_blocked):
                    dead_ends.append(cell)

        if not dead_ends:
            break

        for r, c in dead_ends:
            # Reavalia o grau da célula (pode ter sido alterada por iteração anterior)
            open_count = sum(1 for d in Direction if not (grid[r][c] & d))
            if open_count > 1:
                continue

            candidates: list[tuple[Direction, int, int]] = []
            for d in Direction:
                if grid[r][c] & d:  # Parede fechada
                    dr, dc = STEP[d]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in is_blocked:
                        if not creates_3x3_open_area(grid, r, c, nr, nc, d, rows, cols):
                            candidates.append((d, nr, nc))

            if candidates:
                chosen_dir, nr, nc = rng.choice(candidates)
                remove_wall(grid, r, c, nr, nc, chosen_dir)
```

### 1.3 Prevenção de Áreas Abertas $3 \times 3$

O subject proíbe expressamente praças abertas maiores ou iguais a $3 \times 3$. A remoção descuidada de paredes pode conectar 9 células contíguas sem nenhuma divisória interna.

Para garantir que a abertura de uma parede candidata não viole essa restrição, simula-se a abertura e testa-se se qualquer bloco $3 \times 3$ adjacente ficou com todas as suas paredes internas abertas:

```python
def creates_3x3_open_area(
    grid: list[list[int]],
    r1: int,
    c1: int,
    r2: int,
    c2: int,
    direction: Direction,
    rows: int,
    cols: int
) -> bool:
    # Aplica temporariamente a remoção da parede
    grid[r1][c1] &= ~direction
    grid[r2][c2] &= ~OPPOSITE[direction]

    # Verifica se algum bloco 3x3 no entorno de (r1, c1) e (r2, c2) ficou vazio
    has_empty_square = False
    for top_r in range(max(0, min(r1, r2) - 2), min(rows - 2, max(r1, r2) + 1)):
        for left_c in range(max(0, min(c1, c2) - 2), min(cols - 2, max(c1, c2) + 1)):
            if is_block_fully_open(grid, top_r, left_c):
                has_empty_square = True
                break
        if has_empty_square:
            break

    # Restaura a parede
    grid[r1][c1] |= direction
    grid[r2][c2] |= OPPOSITE[direction]

    return has_empty_square
```

---

## 2. Bônus 2: Múltiplos Algoritmos de Geração

O suporte a múltiplos algoritmos enriquece o projeto demonstrando diferentes propriedades matemáticas de árvores geradoras.

### 2.1 Kruskal Randomizado com Disjoint Set Union (DSU)

O algoritmo de Kruskal trata o labirinto como uma floresta inicial onde cada célula pertence ao seu próprio conjunto conexo. O algoritmo sorteia arestas e conecta células pertencentes a componentes distintas.

#### Estrutura DSU com Otimizações

A estrutura utiliza compressão de caminho e união por posto para alcançar complexidade quase linear $O(\alpha(V))$:

```python
class DisjointSetUnion:
    def __init__(self, elements: list[tuple[int, int]]) -> None:
        self.parent: dict[tuple[int, int], tuple[int, int]] = {p: p for p in elements}
        self.rank: dict[tuple[int, int], int] = {p: 0 for p in elements}

    def find(self, item: tuple[int, int]) -> tuple[int, int]:
        root = item
        while root != self.parent[root]:
            root = self.parent[root]
        # Compressão de caminho
        curr = item
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
        return root

    def union(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return False  # Já pertencem ao mesmo conjunto

        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
        else:
            self.parent[root_b] = root_a
            self.rank[root_a] += 1
        return True
```

#### Aplicação ao Labirinto
1. Lista-se todas as divisórias internas entre células livres vizinhas `((r, c), (nr, nc), direction)`.
2. Embaralha-se a lista com `rng.shuffle(edges)`.
3. Para cada divisória, executa-se `dsu.union(cell_a, cell_b)`. Se retornar `True`, remove-se a parede. Se retornar `False`, a parede permanece para evitar ciclos.

### 2.2 Prim Randomizado

O algoritmo de Prim mantém uma única árvore em expansão:
1. Inicia-se marcando uma célula inicial como parte da árvore e adicionando todas as suas paredes vizinhas a uma lista de fronteira.
2. A cada iteração, sorteia-se aleatoriamente uma parede da lista de fronteira.
3. Se a célula do outro lado da parede ainda não pertence à árvore:
   - Abre-se a parede conectando as duas células.
   - Marca-se a nova célula como visitada.
   - Adiciona-se as paredes vizinhas da nova célula à lista de fronteira.
4. Repete-se o processo até a lista de fronteira esvaziar.

### 2.3 Comparação de Características Topológicas

| Algoritmo | Estrutura Principal | Viés Topológico (*Bias*) | Comprimento dos Corredores | Densidade de Ramificações |
| :--- | :--- | :--- | :--- | :--- |
| **Recursive Backtracker** | Pilha LIFO | Viés direcional longo | Corredores muito longos e sinuosos | Baixa (poucas bifurcações) |
| **Kruskal Randomizado** | DSU com pesos uniformes | Sem viés preferencial | Corredores médios e bem distribuídos | Média-alta (árvore bem balanceada) |
| **Prim Randomizado** | Conjunto de fronteira | Viés radial a partir da origem | Corredores curtos | Altíssima (muitos becos curtos) |

---

## 3. Bônus 3: Animação da Geração em Tempo Real

A visualização do processo construtivo do labirinto oferece excelente didática durante a defesa técnica.

### 3.1 Animação no Terminal via Sequências de Escape ANSI

Para atualizar a tela sem piscamentos indesejados (*screen flickering*):
- O código de escape `\033[H` posiciona o cursor na linha 1, coluna 1 do terminal sem apagar o buffer completo.
- O código `\033[?25l` oculta o cursor durante o processo, e `\033[?25h` restaura a visibilidade ao final.
- Um atraso programado (`time.sleep(0.02)`) desacelera o laço a cada $k$ paredes abertas.

### 3.2 Animação no MiniLibX (MLX)

No ambiente gráfico MLX, loops bloqueantes com `time.sleep` travam a janela e impedem o processamento de eventos do X11.

A arquitetura correta desacopla o gerador em um gerador de passos (*generator/iterator* Python via `yield`):

```python
def step_by_step_generation(self) -> Iterator[None]:
    # A cada remoção de parede:
    yield
```

No loop de eventos do MLX:
1. Registra-se uma função de gancho de repetição (*loop hook*) via `mlx.loop_hook(mlx_ptr, update_frame, param)`.
2. A cada chamada da função de gancho, consome-se um passo do gerador (`next(generator_step)`).
3. Redesenha-se o buffer da janela e empurra-se para a tela com `mlx.put_image_to_window`.
4. Quando o gerador esgota os passos (`StopIteration`), desativa-se o gancho e a interface entra em modo de interação estável.
