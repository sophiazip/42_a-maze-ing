# Flashcards para Treinamento de Defesa — A-Maze-ing

Estes flashcards foram projetados para treinamento em dupla antes da avaliação por pares (peer-evaluation). Um integrante atua como avaliador formulando a pergunta, enquanto o outro responde tecnicamente sem consultar anotações.

---

## Bloco 1: Teoria dos Grafos e Estrutura de Dados

### Card 1.1
- **Pergunta:** O que é uma árvore geradora (*spanning tree*) e como ela se relaciona com um labirinto perfeito (`PERFECT=True`)?
- **Resposta:** Uma árvore geradora é um subgrafo conexo e acíclico que contém todos os vértices do grafo original. Em um labirinto perfeito, as células são os vértices e as passagens abertas são as arestas. Ter uma árvore geradora significa que existe exatamente um único caminho entre quaisquer duas células, sem nenhum ciclo ou bifurcação que retorne ao mesmo ponto.

### Card 1.2
- **Pergunta:** Qual a relação matemática exata entre o número de células livres e o número de passagens em um labirinto perfeito?
- **Resposta:** Se o labirinto possui $V$ células navegáveis, ele terá obrigatoriamente $E = V - 1$ passagens abertas. Se houver menos arestas, o grafo fica desconexo; se houver mais, surgem ciclos.

### Card 1.3
- **Pergunta:** O que é o número ciclomático de um grafo e como ele é calculado no modo jogável (`PERFECT=False`)?
- **Resposta:** O número ciclomático $L$ mede a quantidade de ciclos independentes em um grafo conexo e é dado por $L = E - V + 1$. No modo `PERFECT=True`, $L = 0$. No modo `PERFECT=False`, o subject exige $L \ge 2$, garantindo rotas alternativas para perseguições.

### Card 1.4
- **Pergunta:** Por que usamos BFS (Busca em Largura) e não DFS (Busca em Profundidade) para encontrar o caminho no arquivo de saída?
- **Resposta:** A BFS explora os nós camada por camada a partir da origem, garantindo que o primeiro momento em que o alvo é alcançado corresponde ao menor caminho em número de passos (arestas não ponderadas). A DFS segue um ramo até o fim antes de retroceder, podendo encontrar um caminho longo e sinuoso que não é o mínimo.

### Card 1.5
- **Pergunta:** Qual a complexidade de tempo e memória da BFS implementada com fila?
- **Resposta:** A complexidade de tempo é $O(V + E)$ e a complexidade de memória é $O(V)$, onde $V$ é o total de células navegáveis da grade e $E$ é o total de passagens abertas. Em uma grade retangular, cada célula tem no máximo 4 vizinhos, de modo que $E \le 2V$, tornando a execução linear em relação à área da grade.

---

## Bloco 2: Aritmética Binária e Formato de Arquivo

### Card 2.1
- **Pergunta:** Como funciona a codificação hexadecimal das paredes exigida pelo subject?
- **Resposta:** Cada célula usa 4 bits, onde cada bit ligado (`1`) indica que a respectiva parede está fechada: Bit 0 (1) = Norte, Bit 1 (2) = Leste, Bit 2 (4) = Sul e Bit 3 (8) = Oeste. Uma célula cercada por quatro paredes possui valor $1+2+4+8 = 15$, que corresponde ao caractere hexadecimal `F`. Uma célula aberta ao Norte e ao Sul tem valor $2+8=10$, correspondente a `A`.

### Card 2.2
- **Pergunta:** O que é coerência de paredes e como o gerador a garante?
- **Resposta:** Coerência significa que duas células vizinhas devem concordar sobre o estado da parede compartilhada. Se a célula `A` tem sua parede Leste aberta, a célula vizinha `B` imediatamente à direita deve ter sua parede Oeste aberta. No código, a função de remoção atualiza as duas células atomicamente com operações bitwise: `grid[r][c] &= ~direction` e `grid[nr][nc] &= ~opposite[direction]`.

### Card 2.3
- **Pergunta:** Qual a convenção de coordenadas usada no arquivo de saída?
- **Resposta:** O arquivo de saída utiliza a convenção cartesiana `x,y`, onde `x` representa a coluna (eixo horizontal) e `y` representa a linha (eixo vertical). Internamente, matrizes em Python costumam ser indexadas por `grid[row][col]`, portanto é necessário converter para `col,row` ao serializar.

---

## Bloco 3: Regras de Negócio do Subject

### Card 3.1
- **Pergunta:** Quais são os 5 requisitos obrigatórios do modo tabuleiro Pac-Man (`PERFECT=False`)?
- **Resposta:**
  1. Conectividade total de todas as células livres (sem ilhas isoladas).
  2. Pelo menos duas rotas independentes ($L \ge 2$).
  3. Os 4 cantos e o centro devem ser corredores abertos navegáveis.
  4. Becos sem saída reais devem ser raros (máximo de 2 permitidos no mandatório).
  5. Nenhuma área aberta contígua maior ou igual a $3 \times 3$.

### Card 3.2
- **Pergunta:** O que é o padrão "42" e como ele afeta a conectividade da grade?
- **Resposta:** É um desenho formado por células completamente fechadas (`0xF`) simulando os dígitos 4 e 2. Essas células devem ser marcadas como obstáculos antes do algoritmo de geração para que as passagens sejam construídas ao redor delas. Se a grade for pequena demais para conter o padrão, o gerador deve emitir um aviso no console e prosseguir sem ele, sem abortar com erro.

### Card 3.3
- **Pergunta:** Qual a diferença entre um beco sem saída real e um beco encerrado (*enclosed*) no analisador?
- **Resposta:** Um beco sem saída possui grau 1 (apenas uma passagem aberta). Ele é considerado real quando uma de suas paredes fechadas poderia ser aberta em direção a outro corredor jogável comum. Ele é encerrado quando todas as suas paredes fechadas fazem divisa apenas com a borda externa da grade ou com as células de obstáculo do número "42". O analisador penaliza apenas becos reais.

---

## Bloco 4: Algoritmos Alternativos e Bônus

### Card 4.1
- **Pergunta:** Como funciona o algoritmo de Kruskal para geração de labirintos e como ele detecta ciclos?
- **Resposta:** Ele cria uma lista com todas as paredes internas da grade e as embaralha aleatoriamente. Utiliza a estrutura Disjoint Set Union (DSU / Union-Find) para controlar quais células já estão conectadas. Para cada parede, se as duas células vizinhas pertencem a conjuntos diferentes, o algoritmo unifica os conjuntos e remove a parede. Se já pertencem ao mesmo conjunto, a parede permanece fechada, evitando a formação de ciclos.

### Card 4.2
- **Pergunta:** Quais as duas otimizações essenciais da estrutura DSU e qual a sua complexidade?
- **Resposta:** As otimizações são a compressão de caminho (*path compression*), que faz os nós apontarem diretamente para a raiz durante a busca, e a união por posto (*union by rank*), que anexa a árvore menor sob a raiz da árvore maior. Juntas, reduzem o tempo de cada operação para $O(\alpha(V))$, onde $\alpha$ é o inverso da função de Ackermann (tempo praticamente constante).

### Card 4.3
- **Pergunta:** Qual a diferença visual entre um labirinto gerado por DFS (Recursive Backtracker) e um gerado por Prim?
- **Resposta:** O DFS possui forte viés direcional, criando caminhos longos, contínuos e pouco ramificados, com poucas bifurcações. O Prim cresce radialmente a partir da raiz, gerando uma árvore com muitas ramificações curtas e becos sem saída superficiais espalhados por todo o tabuleiro.

---

## Bloco 5: Qualidade de Software, Tipagem e Empacotamento

### Card 5.1
- **Pergunta:** O que é verificado pelo comando `flake8` no projeto?
- **Resposta:** O `flake8` analisa o estilo de código segundo a norma PEP 8, checando espaçamento correto, comprimento de linha (máximo padrão de 79 ou configurado em 88), convenções de nomenclatura e identificação de importações não utilizadas ou variáveis indefinidas.

### Card 5.2
- **Pergunta:** Por que a flag `--disallow-untyped-defs` do mypy é importante?
- **Resposta:** Esta flag proíbe que qualquer função ou método seja declarado sem anotações de tipo completas em seus parâmetros e em seu tipo de retorno, impedindo que partes do código usem tipagem dinâmica implícita (`Any`).

### Card 5.3
- **Pergunta:** Como o módulo reutilizável `mazegen` deve ser construído e instalado para avaliação?
- **Resposta:** Na raiz do repositório, com ferramentas de build instaladas no virtualenv, executa-se `python3 -m build`. Isso gera o pacote wheel `mazegen-1.0.0-py3-none-any.whl` (ou arquivo `.tar.gz`) que pode ser instalado em outro ambiente com `pip install mazegen-*.whl` para reutilizar a classe `MazeGenerator`.

---

## Bloco 6: Simulação de Modificação ao Vivo (Live Modification)

### Card 6.1
- **Pergunta do Avaliador:** "Mude o caractere de saída de 'X' para 'S' e altere a cor do menor caminho para ciano."
- **Resposta Prática:** No arquivo `mazegen/renderer_ascii.py`, altero a constante `EXIT_CHAR = 'S'` e, na função de formatação ANSI, modifico o código de cor da rota de verde (`\033[92m`) para ciano (`\033[96m`). Em seguida, executo `make run` para demonstrar o resultado imediato.

### Card 6.2
- **Pergunta do Avaliador:** "Como garantir que passar um arquivo de configuração inexistente não encerre com traceback do Python?"
- **Resposta Prática:** No arquivo `a_maze_ing.py`, a chamada para `parse_config` é envolvida por um bloco `try-except (FileNotFoundError, ConfigError) as exc:`. O tratamento imprime uma mensagem limpa no fluxo de erro padrão (`sys.stderr.write(f"Erro: {exc}\n")`) e encerra o processo chamando `sys.exit(1)`.
