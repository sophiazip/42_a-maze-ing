# Plano de Distribuição de Tarefas para Dupla — A-Maze-ing

Este documento organiza a divisão do trabalho entre dois desenvolvedores (Integrante A e Integrante B). O modelo prioriza o paralelismo com minimização de dependências diretas e define a posse clara de módulos para evitar conflitos de merge no Git.

---

## 1. Níveis de MVP e Gatilhos de Contingência

Projetos com prazos fixos exigem priorização pragmática para assegurar a aprovação antes de qualquer investimento em recursos secundários.

### 1.1 Níveis de Entrega

| Nível | Escopo Técnico | Critério de Aceitação |
| :--- | :--- | :--- |
| **Nível 0 (Mínimo Viável)** | `PERFECT=True` operacional; geração de arquivo em hexadecimal válido; `maze_analyzer.py` passa sem erros; `a_maze_ing.py` trata erros de arquivo; `Makefile` e `LICENSE.md` presentes. | Evita nota zero; atende aos requisitos estruturais básicos. |
| **Nível 1 (Mandatório Completo)** | Nível 0 + `PERFECT=False` com tabuleiro Pac-Man válido ($L \ge 2$, cantos/centro abertos, $\le 2$ dead-ends, sem áreas $3 \times 3$); padrão "42" posicionado; visualizador ASCII com as 3 interações; empacotamento `.whl` funcional; `flake8` e `mypy` sem alertas. | Aprovação integral na parte obrigatória do projeto. |
| **Nível 2 (Diferencial com Bônus)** | Nível 1 + tabuleiro perfeitamente trançado (*braided* com 0 dead-ends); algoritmos alternativos (Kruskal com DSU e Prim); animação no terminal e integração gráfica MLX. | Pontuação de bônus na avaliação. |

### 1.2 Gatilhos de Contingência

- **Ponto de Corte 1 (70% do prazo decorrido):** Se o modo `PERFECT=False` apresentar falhas no `maze_analyzer.py` (loops insuficientes ou dead-ends acima do limite), congela-se imediatamente a implementação gráfica MLX e quaisquer bônus. Os dois integrantes concentram-se na correção topológica do gerador.
- **Ponto de Corte 2 (85% do prazo decorrido):** Se os relatórios do `mypy` ou `flake8` acusarem erros, nenhuma funcionalidade nova é iniciada. Todo o esforço converge para tipagem estrita, docstrings e limpeza de código.
- **Véspera da Defesa:** Nenhum código novo é adicionado. O dia é dedicado exclusivamente a ensaios da avaliação com flashcards, simulação de modificação ao vivo e verificação do ambiente com repositório recém-clonado em pasta temporária.

---

## 2. Matriz de Riscos Técnicos e Mitigações

| Risco Identificado | Probabilidade | Impacto | Ação de Mitigação |
| :--- | :--- | :--- | :--- |
| **Incoerência entre paredes vizinhas** | Média | Fatal | Abertura atômica de paredes via função única `remove_wall`, atualizando os dois lados simultaneamente com operadores bitwise. |
| **Modo Pac-Man sem loops suficientes ($L < 2$)** | Alta | Alto | Garantir que, após a geração da base em árvore, a rotina abra arestas adicionais em células que não compartilham a mesma vizinhança imediata. |
| **Criação acidental de áreas abertas $3 \times 3$** | Média | Alto | Função de pré-validação simula a abertura de cada parede candidata e rejeita a alteração se formar quadrado aberto $3 \times 3$. |
| **Padrão "42" bloqueia cantos ou o centro** | Média | Alto | Definir região de ancoragem protegida com cálculo de offset dinâmico; validar que as coordenadas dos 4 cantos e do centro não pertencem ao padrão. |
| **Estouro de pilha no Recursive Backtracker** | Média | Alto | Implementação com pilha explícita em lista (`heap`) em vez de funções recursivas que dependem do limite de chamadas do interpretador. |
| **Falha na compilação do pacote wheel `.whl`** | Média | Alto | Configuração e validação antecipada do `pyproject.toml` no início do projeto, testando instalação em virtualenv limpo. |
| **Dificuldade na explicação do código do colega na defesa** | Média | Fatal | Sessões obrigatórias de revisão de código em cada Pull Request e rodadas de perguntas usando o arquivo de flashcards. |

---

## 3. Matriz de Responsabilidades Primárias

| Domínio de Atuação | Integrante Responsável | Arquivos Sob Posse Primária |
| :--- | :--- | :--- |
| **Núcleo & Algoritmos** | **Integrante A** | `mazegen/generator.py`, lógica de grafos, BFS, DSU, algoritmos de geração e braiding. |
| **I/O, Visual, Build & Qualidade** | **Integrante B** | `a_maze_ing.py`, `mazegen/config.py`, `mazegen/renderer_ascii.py`, `mazegen/renderer_mlx.py`, `pyproject.toml`, `Makefile`, `LICENSE.md`. |

*Nota:* Ambos os integrantes desenvolvem testes unitários para seus respectivos módulos e revisam o código do parceiro via Pull Request antes do merge na branch `main`.

---

## 4. Estimativa de Esforço por Bloco de Trabalho

| Bloco de Trabalho | Horas por Integrante | Horas em Paralelo | Descrição do Foco |
| :--- | :--- | :--- | :--- |
| **Alinhamento Teórico e Ensino Cruzado** | 6 a 8 h | 6 a 8 h | Estudo individual seguido de sessões de nivelamento mútuo (A ensina Grafos e BFS; B ensina Bitwise e Packaging). |
| **Desenvolvimento Mandatório** | 22 a 30 h | 16 a 22 h | Implementação dos módulos do gerador, parser, visualizador ASCII e integração do fluxo CLI. |
| **Qualidade, Tipagem e Cobertura de Testes** | 6 a 8 h | 4 a 6 h | Adequação integral a `flake8`, validação estrita com `mypy` e testes de regressão com `maze_analyzer.py`. |
| **Desenvolvimento de Bônus (Opcional)** | 8 a 12 h | 6 a 9 h | Algoritmo de braiding com zero dead-ends, geradores adicionais (Kruskal/Prim) e renderizador MLX. |
| **Ensaios de Defesa e Ajustes Finais** | 4 a 6 h | 4 a 6 h | Treinamento com simulação de perguntas técnicas e modificações de código em tempo real. |
| **Total Estimado (Mandatório)** | **38 a 52 h** | **30 a 42 h** | Aproximadamente 6 a 8 dias úteis em regime part-time (4 a 5h diárias). |

---

## 5. Cronograma Paralelo Fase a Fase

```mermaid
flowchart TD
    subgraph A["Integrante A (Algoritmos e Grafos)"]
        direction TB
        A1["Fase 2: IntFlag e Coerência de Paredes"] --> A2["Fase 3: Recursive Backtracker (DFS)"]
        A2 --> A3["Fase 4: Posicionamento do Padrão 42"]
        A3 --> A4["Fase 5: Modo Pac-Man (Loops e Dead-ends)"]
        A4 --> A5["Fase 6: BFS e Menor Caminho"]
    end

    subgraph B["Integrante B (I/O, Visual e Empacotamento)"]
        direction TB
        B0["Fase 0: Repositório, Makefile e venv"] --> B1["Fase 1: Config Parser e Validações"]
        B1 --> B2["Fase 6: Serialização em Hexadecimal"]
        B2 --> B3["Fase 7: Entry Point a_maze_ing.py"]
        B3 --> B4["Fase 8: Renderizador ASCII Interativo"]
        B4 --> B5["Fase 9: Packaging e pyproject.toml"]
    end

    subgraph C["Etapas Conjuntas (Qualidade e Defesa)"]
        direction TB
        C1["Fase 11: Qualidade de Código (flake8 e mypy)"] --> C2["Fase 12: Testes com maze_analyzer"]
        C2 --> C3["Fase 13: Ensaio Geral da Defesa"]
    end

    A5 --> C1
    B5 --> C1
```

| Dia Estimado | Integrante A (Algoritmos) | Integrante B (I/O & Visual) | Foco de Integração |
| :--- | :--- | :--- | :--- |
| **Dia 1** | Fase 2: `Direction(IntFlag)` e `remove_wall` | Fase 0: Setup, Makefile e venv; Fase 1: Parser | `make lint` inicial rodando |
| **Dia 2** | Fase 3: Recursive Backtracker (DFS iterativo) | Fase 1: Validações e `config.txt` padrão | Teste unitário de parsing |
| **Dia 3** | Fase 4: Bitmap e posicionamento do "42" | Fase 6: Serialização do arquivo em hex | Validação da matriz com "42" |
| **Dia 4** | Fase 5: Modo Pac-Man (loops e dead-ends) | Fase 7: CLI em `a_maze_ing.py` | Execução ponta a ponta sem visual |
| **Dia 5** | Fase 6: BFS e menor caminho | Fase 8: Renderizador ASCII interativo | Teste das 3 interações no terminal |
| **Dia 6** | Apoio e revisão de regressão | Fase 9: `pyproject.toml` e build do wheel | `pip install mazegen-*.whl` |
| **Dia 7** | Fase 11: Tipagem estrita com `mypy` | Fase 11: Conformidade com `flake8` | `make lint-strict` 100% limpo |
| **Dia 8** | Fase 12: Regressão no `maze_analyzer.py` | Fase 12: Cobertura com `pytest` | 50 labirintos validados sem erro |
| **Dia 9** | Fase 13: Flashcards e ensaio técnico | Fase 13: Limpeza e simulação ao vivo | Ensaio cronometrado da defesa |

---

## 6. Sessões de Nivelamento Técnico (Ensino Cruzado)

Antes de iniciar as fases mais complexas, a equipe realiza sessões curtas de 30 minutos em que cada um explica ao outro a lógica da sua área:

1. **Sessão 1 (Dia 2):** Integrante B demonstra o funcionamento das máscaras de bits (`Direction.NORTH = 1`, etc.) e a leitura do `config.txt`. Integrante A demonstra como o grafo é percorrido com a pilha do DFS.
2. **Sessão 2 (Dia 4):** Integrante A demonstra o cálculo ciclomático $L = E - V + 1$ e como as paredes extras são abertas para criar loops no tabuleiro. Integrante B demonstra o fluxo de escape ANSI e o controle de teclado no terminal.
3. **Sessão 3 (Dia 6):** Integrante B demonstra o build do pacote wheel e a instalação limpa em virtualenv. Integrante A demonstra a fila da BFS e a reconstrução da rota mais curta.
