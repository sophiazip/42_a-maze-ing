# Roteiro de Teste e Guia de Defesa — Parte Bônus (A-Maze-ing)

Este documento estabelece o protocolo de demonstração e validação técnica para os três bônus desenvolvidos no projeto.

---

## 1. Condição Prévia de Avaliação

Os bônus são avaliados estritamente após a conclusão e aprovação de 100% dos requisitos mandatórios. Se algum item mandatório apresentar falha, a avaliação é encerrada antes dos bônus.

---

## 2. Bônus 1: Tabuleiro Trançado (*Braided Maze*) com Zero Dead-Ends

A validação do tabuleiro trançado é objetiva e verificada diretamente pelo script do subject.

### 2.1 Passo a Passo da Demonstração
1. Gere um labirinto em modo trançado (via parâmetro de linha de comando ou configuração `BRAIDED=True` no `config.txt`):
   ```bash
   python3 a_maze_ing.py config.txt
   ```
2. Submeta o arquivo de saída ao validador oficial com tolerância zero de becos sem saída reais:
   ```bash
   python3 maze_analyzer.py maze.txt --max-dead-ends 0
   ```

### 2.2 Veredito Esperado no Terminal
O analisador deve emitir o seguinte diagnóstico:
```text
Dead-ends: 0 real, X enclosed by "42" pattern
Loops: N independent routes (L >= 2)
Verdict: Pac-Man-USABLE (no real dead-end -> bonus-grade (perfectly braided))
```

### 2.3 Checagem de Áreas $3 \times 3$
Mostre ao avaliador que a remoção agressiva de becos sem saída não gerou praças abertas desprovidas de divisórias internas:
- O relatório do analisador confirma ausência de violação de corredor contíguo.
- A visualização em tela atesta a preservação da malha de corredores.

---

## 3. Bônus 2: Múltiplos Algoritmos de Geração

Demonstre a capacidade do motor de gerar labirintos sob três algoritmos matematicamente distintos.

### 3.1 Demonstração Prática
Gere três labirintos utilizando a mesma semente (`SEED=42`), variando apenas a chave `ALGORITHM`:

```bash
# 1. Recursive Backtracker (padrão)
python3 a_maze_ing.py config_backtracker.txt

# 2. Kruskal Randomizado (com DSU)
python3 a_maze_ing.py config_kruskal.txt

# 3. Prim Randomizado
python3 a_maze_ing.py config_prim.txt
```

### 3.2 Diferenciação Visual e Topológica Diante do Avaliador
Apresente as características de cada resultado:
- **Recursive Backtracker:** Corredores muito longos, sinuosos e com poucas bifurcações. O menor caminho tende a ser longo.
- **Kruskal:** Padrão uniforme sem viés direcional, com distribuição balanceada de bifurcações e corredores médios.
- **Prim:** Alta densidade de ramificações curtas e becos rasos espalhados radialmente a partir da célula inicial.

### 3.3 Defesa do Código da DSU
Abra o arquivo `mazegen/dsu.py` (ou `generator.py`) e mostre:
- O método `find` com compressão de caminho (os nós apontam para a raiz após a busca).
- O método `union` com critério por posto (a árvore mais rasa é anexada sob a árvore mais profunda).
- A verificação de pertencimento que impede a criação de ciclos no algoritmo de Kruskal.

---

## 4. Bônus 3: Animação da Geração em Tempo Real

Apresente o processo de construção procedural do labirinto operando em tempo real.

### 4.1 Demonstração no Terminal (ASCII)
Execute o gerador em modo animado:
```bash
python3 a_maze_ing.py config.txt --animate
```
- Aponte a ausência de piscamento de tela (*flickering*), garantida pelo reposicionamento de cursor com a sequência ANSI `\033[H`.
- Mostre a pilha de visitação do algoritmo avançando e retrocedendo durante a busca em profundidade.

### 4.2 Demonstração no MiniLibX (Gráfica)
Se o ambiente contar com a biblioteca gráfica MLX compilada:
```bash
python3 a_maze_ing.py config.txt --display=mlx --animate
```
- Aponte a abertura das paredes sendo desenhada tile a tile na janela gráfica.
- Explique a arquitetura não-bloqueante: a geração avança a cada pulso do `mlx.loop_hook`, permitindo que os eventos do X11 continuem sendo processados sem travar a interface gráfica.
