# Detalhamento de Tarefas — Parte Bônus (A-Maze-ing)

Este documento detalha o planejamento das tarefas relacionadas aos bônus do Capítulo VIII do subject. O desenvolvimento destas tarefas é condicionado à conclusão de 100% da parte mandatória e à validação irrestrita no script `maze_analyzer.py`.

---

## Bônus 1 — Tabuleiro Trançado (*Braided Maze*) com Zero Dead-Ends

### B1.1 — Identificação Algorítmica de Becos sem Saída
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Implementar método para varrer a matriz e identificar células com exatamente uma passagem aberta ($deg(v) = 1$).
  - Distinguir becos reais (com parede voltada para corredor comum) de becos encerrados (adjacentes apenas ao "42" ou bordas da grade), espelhando o critério do `maze_analyzer.py`.
- **Critério de Conclusão:** O método contabiliza a mesma quantidade de becos reais apontada pelo analisador.

### B1.2 — Mecanismo de Remoção de Becos sem Saída (Braiding)
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Implementar método `braid()`: para cada beco real, selecionar uma parede fechada elegível voltada para vizinho navegável e abri-la atomicamente.
  - Repetir o processo em laço até que a contagem de becos sem saída reais seja zero.
- **Critério de Conclusão:** O labirinto atinge zero becos reais sem desconectar componentes nem violar coerência de paredes.

### B1.3 — Verificação Preventiva contra Áreas Abertas $3 \times 3$
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Criar função preditiva `_creates_open_area_3x3(r1, c1, r2, c2, direction) -> bool`.
  - Simular a abertura da parede e verificar se qualquer bloco $3 \times 3$ vizinho fica totalmente desprovido de divisórias internas. Se a abertura criar uma praça $3 \times 3$, a parede é descartada e testa-se outro vizinho elegível.
- **Critério de Conclusão:** Nenhuma área aberta contígua maior ou igual a $3 \times 3$ é gerada durante o trançamento.

### B1.4 — Teste de Conformidade com o Analisador Oficial
- **Responsável:** Integrante A e Integrante B
- **Arquivos:** `tests/test_braided.py`
- **Ações:**
  - Gerar labirintos trançados com diferentes dimensões e sementes.
  - Validar com `python3 maze_analyzer.py maze.txt --max-dead-ends 0`.
- **Critério de Conclusão:** O analisador emite o veredito `Pac-Man-USABLE` com a confirmação expressa de `no real dead-end -> bonus-grade (perfectly braided)`.

---

## Bônus 2 — Múltiplos Algoritmos de Geração

### B2.1 — Estrutura Disjoint Set Union (DSU)
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/dsu.py` (ou dentro de `generator.py`)
- **Ações:**
  - Implementar a classe `DisjointSetUnion` com dicionários de pais e postos.
  - Implementar `find` com compressão de caminho e `union` por posto.
- **Critério de Conclusão:** Testes unitários confirmam união de elementos e identificação de ciclos em tempo sub-microsegundo por operação.

### B2.2 — Gerador com Kruskal Randomizado
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Mapear todas as divisórias internas entre células livres navegáveis.
  - Embaralhar a lista de divisórias via `random.shuffle`.
  - Iterar sobre as divisórias unindo conjuntos disjuntos e abrindo as paredes correspondentes.
- **Critério de Conclusão:** O algoritmo gera uma árvore geradora conexa válida sem ciclos para qualquer dimensão de grade.

### B2.3 — Gerador com Prim Randomizado
- **Responsável:** Integrante A
- **Arquivos:** `mazegen/generator.py`
- **Ações:**
  - Iniciar árvore a partir da célula de entrada.
  - Manter conjunto com as paredes de fronteira das células visitadas.
  - Sortear parede da fronteira, conectar à nova célula e expandir a fronteira até esgotar nós não visitados.
- **Critério de Conclusão:** O gerador constrói árvore geradora com viés radial a partir da origem, validada pelo `maze_analyzer.py` com `PERFECT=True`.

### B2.4 — Configuração e Seleção Dinâmica de Algoritmo
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/config.py`, `mazegen/generator.py`
- **Ações:**
  - Aceitar a chave `ALGORITHM=backtracker|kruskal|prim` no `config.txt`.
  - Despachar a execução para a rotina correspondente durante a chamada a `generate()`.
- **Critério de Conclusão:** A alteração do algoritmo no arquivo de configuração reflete-se na topologia gerada.

---

## Bônus 3 — Animação em Tempo Real da Geração

### B3.1 — Animação no Terminal via Sequências ANSI
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/renderer_ascii.py`
- **Ações:**
  - Implementar modo de exibição animada utilizando sequência `\033[H` para reposicionar o cursor no topo da tela sem apagar o buffer completo.
  - Interpolar chamadas de desenho a cada remoção de parede com intervalo de atualização configurável (`time.sleep(0.01)`).
- **Critério de Conclusão:** O terminal exibe a progressão contínua da construção do labirinto sem oscilações de tela.

### B3.2 — Animação Gráfica via MiniLibX
- **Responsável:** Integrante B
- **Arquivos:** `mazegen/renderer_mlx.py`
- **Ações:**
  - Converter o método de geração em um gerador/iterador Python com `yield` a cada parede modificada.
  - Integrar com o gancho de repetição `mlx.loop_hook()` da biblioteca gráfica, redesenhando o buffer a cada passo até a conclusão da geração.
- **Critério de Conclusão:** A janela gráfica do MLX exibe visualmente a abertura progressiva das paredes em tempo real.
