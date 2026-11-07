# Guia Teórico e Técnico da Parte Mandatória — A-Maze-ing

Este documento compila os fundamentos teóricos de grafos, estruturas de dados em Python, aritmética binária e regras de arquitetura exigidas na parte mandatória do projeto A-Maze-ing.

---

## 1. Fundamentos de Grafos Aplicados a Labirintos

A geração e a resolução de labirintos baseiam-se em teoria dos grafos:

- **Vértice ($V$):** cada célula do tabuleiro, identificada pelas coordenadas `(row, col)`.
- **Aresta ($E$):** a passagem livre entre duas células adjacentes, criada pela remoção da parede divisória compartilhada.
- **Grau de um nó ($deg(v)$):** a quantidade de passagens abertas conectadas a essa célula.

### 1.1 Labirinto Perfeito como Árvore Geradora (Spanning Tree)

Quando o arquivo de configuração define `PERFECT=True`, a estrutura gerada precisa ser uma **árvore geradora**:

1. **Grafo conexo:** existe caminho entre qualquer par de células válidas da malha.
2. **Grafo acíclico:** não existem laços (*loops*). Se você partir de uma célula e seguir sem retroceder, nunca voltará à mesma célula.
3. **Caminho único:** entre a entrada `ENTRY` e a saída `EXIT`, existe exatamente um caminho possível.
4. **Relação de arestas:** para uma malha com $V$ células navegáveis, o total de passagens abertas é sempre:
   $$E = V - 1$$

Qualquer adição de aresta além de $V - 1$ fecha um ciclo. Qualquer subtração desconecta parte da malha, criando ilhas inacessíveis.

---

## 2. Codificação Hexadecimal de Paredes e Operações Bitwise

O subject especifica que cada célula da grade é representada em arquivo por um dígito hexadecimal correspondente a uma máscara de 4 bits.

### 2.1 Mapeamento de Bits

Cada bit ligado (`1`) indica que a respectiva parede está **fechada**:

| Bit | Valor Decimal | Direção Cardinal | Deslocamento `(row, col)` | Deslocamento `(x, y)` |
| :--- | :--- | :--- | :--- | :--- |
| Bit 0 (LSB) | 1 | Norte (N) | `(-1, 0)` | `(0, -1)` |
| Bit 1 | 2 | Leste (E) | `(0, +1)` | `(+1, 0)` |
| Bit 2 | 4 | Sul (S) | `(+1, 0)` | `(0, +1)` |
| Bit 3 (MSB) | 8 | Oeste (W) | `(0, -1)` | `(-1, 0)` |

Quando todas as 4 paredes estão fechadas:
$$1 + 2 + 4 + 8 = 15 = \text{0xF}$$

Quando as paredes Norte e Sul estão abertas, e Leste e Oeste estão fechadas:
$$\text{Leste}(2) + \text{Oeste}(8) = 10 = \text{0xA}$$

### 2.2 Estrutura `IntFlag` em Python

A melhor forma de modelar as direções no código é através de `enum.IntFlag`:

```python
from enum import IntFlag
from typing import Dict, Tuple

Cell = Tuple[int, int]  # (row, col)

class Direction(IntFlag):
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

OPPOSITE: Dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}

STEP: Dict[Direction, Tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}

ALL_WALLS = Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST
```

### 2.3 Coerência Bidirecional Estrita

Uma parede separa duas células vizinhas. Se a célula `A` tem sua parede Leste aberta, a célula vizinha `B` imediatamente à sua direita precisa obrigatoriamente ter sua parede Oeste aberta. Se houver discrepância, o script oficial `maze_analyzer.py` rejeita o arquivo como incoerente.

A remoção de parede deve atualizar as duas células atomicamente:

```python
def remove_wall(grid: list[list[int]], r1: int, c1: int, r2: int, c2: int, direction: Direction) -> None:
    # Remove a parede na célula de origem
    grid[r1][c1] &= ~direction
    # Remove a parede correspondente na célula vizinha
    grid[r2][c2] &= ~OPPOSITE[direction]
```

---

## 3. Algoritmo de Geração Perfeita: Recursive Backtracker

Para gerar uma árvore geradora sem viés excessivo e com corredores naturais, o **Recursive Backtracker** é o algoritmo de referência. 

### 3.1 Implementação Iterativa com Pilha Explícita

O interpretador Python padrão limita a recursão em 1000 chamadas (`sys.getrecursionlimit()`). Uma grade $40 \times 40$ possui 1600 células e causaria `RecursionError` se implementada via recursão direta. Por isso, a implementação deve usar uma pilha (`list`) na memória heap:

```python
import random

def generate_perfect_maze(
    rows: int,
    cols: int,
    start_cell: tuple[int, int],
    blocked_cells: set[tuple[int, int]],
    rng: random.Random
) -> list[list[int]]:
    grid = [[int(ALL_WALLS) for _ in range(cols)] for _ in range(rows)]
    visited = set(blocked_cells)
    
    stack: list[tuple[int, int]] = [start_cell]
    visited.add(start_cell)
    
    while stack:
        current = stack[-1]
        r, c = current
        
        # Encontra vizinhos válidos ainda não visitados
        unvisited_neighbors: list[tuple[Direction, tuple[int, int]]] = []
        for direction in Direction:
            dr, dc = STEP[direction]
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                unvisited_neighbors.append((direction, (nr, nc)))
        
        if unvisited_neighbors:
            direction, (nr, nc) = rng.choice(unvisited_neighbors)
            remove_wall(grid, r, c, nr, nc, direction)
            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()
            
    return grid
```

---

## 4. O Obstáculo Obrigatório "42"

O subject exige a presença do padrão "42" desenhado no tabuleiro através de células totalmente fechadas (`0xF`).

### 4.1 Definição Matricial

O número pode ser modelado como um bitmap booleano compacto:

```python
# Padrão 42 em grade 5x7
PATTERN_42 = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]
```

### 4.2 Restrições de Posicionamento
- O "42" deve ser posicionado de forma que suas células não coincidam com a entrada, com a saída, com os 4 cantos ou com o centro do labirinto.
- Se a largura ou altura configurada for insuficiente para conter o padrão com margens mínimas de navegação ao redor, o programa deve emitir uma mensagem de aviso no terminal e omitir o padrão, sem encerrar o programa de forma abrupta.
- Antes da geração das passagens, todas as coordenadas ocupadas pelo "42" são marcadas como visitadas e bloqueadas. O algoritmo de geração flui contornando o obstáculo, garantindo que nenhuma célula externa fique isolada.

---

## 5. Modo Tabuleiro Jogável (`PERFECT=False`)

Quando `PERFECT=False` (comportamento padrão), o labirinto deve ser utilizável como um tabuleiro no estilo Pac-Man.

### 5.1 Critérios Verificados pelo `maze_analyzer.py`

1. **Ciclos Independentes ($L \ge 2$):**
   $$L = E - V + 1$$
   O tabuleiro precisa oferecer no mínimo duas rotas independentes para que o jogador nunca fique indefeso perante perseguições.
2. **Conectividade Total:** todas as células livres devem pertencer à mesma região conexa (`disconnected_corridors == 0`).
3. **Células-Chave Desimpedidas:**
   - Os 4 cantos: `(0, 0)`, `(0, W-1)`, `(H-1, 0)`, `(H-1, W-1)`.
   - O centro do tabuleiro: ponto de surgimento do jogador.
4. **Controle de Beco Sem Saída (Dead-Ends):**
   - Um beco sem saída real é uma célula que possui apenas 1 parede aberta ($deg(v) = 1$) e cuja parede fechada faz divisa com um corredor livre navegável.
   - O subject tolera no máximo 2 becos sem saída reais no modo mandatório. Becos adjacentes ao obstáculo "42" ou à borda externa não contam como penalidade pelo analisador.
5. **Largura Máxima de Corredores (Regra Anti-3x3):**
   - É proibido criar praças abertas de dimensão $3 \times 3$ ou maior.
   - Áreas abertas de $2 \times 2$, $2 \times 3$ ou $3 \times 2$ são permitidas, desde que não haja um bloco $3 \times 3$ desprovido de paredes internas.

---

## 6. Algoritmo de Menor Caminho: Busca em Largura (BFS)

Para encontrar o caminho mais curto entre a entrada `ENTRY` e a saída `EXIT`, utiliza-se a Busca em Largura (BFS), cuja complexidade de tempo é $O(V + E)$ em grafos não-ponderados:

```python
from collections import deque
from typing import Optional, List, Tuple, Dict

DIRECTION_CHAR = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}

def solve_bfs(
    grid: list[list[int]],
    start: tuple[int, int],
    target: tuple[int, int],
    rows: int,
    cols: int
) -> tuple[list[tuple[int, int]], str]:
    queue = deque([start])
    parent: dict[tuple[int, int], tuple[tuple[int, int], Direction]] = {}
    visited = {start}
    
    found = False
    while queue:
        curr = queue.popleft()
        if curr == target:
            found = True
            break
            
        r, c = curr
        for direction in Direction:
            # Verifica se a parede está aberta nessa direção
            if not (grid[r][c] & direction):
                dr, dc = STEP[direction]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    parent[(nr, nc)] = (curr, direction)
                    queue.append((nr, nc))
                    
    if not found:
        return [], ""
        
    # Reconstrução do caminho de trás para frente
    path_cells: list[tuple[int, int]] = []
    directions: list[str] = []
    curr = target
    while curr != start:
        path_cells.append(curr)
        prev, direction = parent[curr]
        directions.append(DIRECTION_CHAR[direction])
        curr = prev
    path_cells.append(start)
    path_cells.reverse()
    directions.reverse()
    
    return path_cells, "".join(directions)
```

---

## 7. Formato do Arquivo de Saída

O arquivo gerado em disco deve seguir estritamente o layout:

```text
3A79... [linhas de caracteres hexadecimais, uma linha por linha da grade]
...
[linha em branco]
0,0     [coordenada x,y da entrada]
19,14   [coordenada x,y da saída]
EESSWWN [sequência contígua de passos do menor caminho]
```

Aviso crucial sobre coordenadas: na convenção cartesiana do subject, `x` representa a coluna e `y` representa a linha. Ao ler do config ou escrever no rodapé, utilize sempre `f"{col},{row}"`.

---

## 8. Requisitos de Reuso e Empacotamento

A lógica de geração deve ser desacoplada da interface de linha de comando:

1. **Módulo `mazegen`:** contém a classe `MazeGenerator` com métodos de acesso ao estado interno do labirinto (`to_hex_grid()`, `get_shortest_path()`, `solve()`).
2. **Empacotamento via `pyproject.toml`:** especificação padrão PEP 621. A execução de `python3 -m build` gera um arquivo `.whl` na raiz (`mazegen-1.0.0-py3-none-any.whl`).
3. **Licença `LICENSE.md`:** deve constar na raiz do repositório, garantindo permissão expressa para reutilização em projetos subsequentes da escola (por exemplo, licença MIT ou Apache 2.0).

---

## 9. Visualização e Interações

O programa oferece duas formas de apresentação:
1. **ASCII no terminal:** desenha paredes usando caracteres como `#` ou blocos ANSI, marcando entrada com `E`, saída com `X`, e o menor caminho com caracteres coloridos.
2. **Gráfica com MLX (MiniLibX):** desenha uma janela interativa com tiles renderizados diretamente em buffer de imagem.

### Interações Mínimas Obrigatórias
- Tecla para gerar um novo labirinto com nova semente aleatória.
- Tecla para exibir ou ocultar a rota do menor caminho.
- Tecla para alternar a paleta de cores das paredes.
- Tecla ou comando para encerrar o programa de forma limpa.
