# Guias de Estudo e Planejamento — A-Maze-ing

Esta branch (`study-guides`) consolida todo o planejamento técnico, teórico, arquitetural e colaborativo para o desenvolvimento do projeto **A-Maze-ing** em dupla na 42.

---

## 1. Estrutura da Documentação

A documentação está organizada em quatro áreas de domínio técnico:

```
docs/
├── git/
│   └── GUIA_GIT_GITHUB.md             # Fluxo de branches, micro-commits, PRs e CI
├── architecture/
│   ├── GUIA_ESTUDO_MANDATORIO.md      # Grafos, DFS, bitwise, BFS, Pac-Man e empacotamento
│   ├── GUIA_ESTUDO_BONUS.md           # Braiding (zero dead-ends), Kruskal (DSU), Prim e animação
│   └── INVENTARIO_CODIGO.md           # Mapeamento de módulos, classes e contratos de interface
├── flashcards/
│   └── FLASHCARDS_DEFESA.md           # Cartões de perguntas e respostas para ensaio de avaliação
├── planning/
│   ├── DISTRIBUICAO_DUPLA.md          # Divisão de papéis, matriz de risco e plano de contingência
│   ├── TAREFAS_MANDATORIO.md          # Decomposição passo a passo das tarefas T0.1 a T13.4
│   └── TAREFAS_BONUS.md               # Decomposição das tarefas de bônus B1.1 a B3.2
└── testing/
    ├── ROTEIRO_DEFESA_MANDATORIO.md   # Checklist pré-defesa e simulação de modificação ao vivo
    └── ROTEIRO_DEFESA_BONUS.md        # Protocolo de demonstração de bônus no analisador e MLX
```

---

## 2. Mapa Rápido de Navegação

### Para a Gestão e Rotina da Dupla
- [Guia Git & GitHub](docs/git/GUIA_GIT_GITHUB.md): consulte antes de criar branches ou abrir Pull Requests. Define o padrão de micro-commits semânticos em inglês e a regra de branch protection.
- [Distribuição de Tarefas para Dupla](docs/planning/DISTRIBUICAO_DUPLA.md): define as responsabilidades do Integrante A (Algoritmos e Grafos) e do Integrante B (I/O, Visual e Empacotamento), além dos pontos de corte de MVP (Níveis 0, 1 e 2).
- [Tarefas da Parte Mandatória](docs/planning/TAREFAS_MANDATORIO.md): guia sequencial das Fases 0 a 13, cobrindo o setup, o parser, a geração, a BFS e o empacotamento em pacote `.whl`.
- [Tarefas da Parte Bônus](docs/planning/TAREFAS_BONUS.md): roteiro dos bônus opcionais de tabuleiro trançado sem becos sem saída, geradores adicionais e animações.

### Para o Estudo Teórico e de Código
- [Guia de Estudo Mandatório](docs/architecture/GUIA_ESTUDO_MANDATORIO.md): aprofundamento em teoria dos grafos (árvores geradoras), operações bitwise com `IntFlag`, prevenção de estouro de pilha no DFS e regras do tabuleiro Pac-Man.
- [Guia de Estudo de Bônus](docs/architecture/GUIA_ESTUDO_BONUS.md): implementação do algoritmo de braiding, estrutura Disjoint Set Union (DSU) com compressão de caminho e união por posto para Kruskal, e controle de animação no MLX.
- [Inventário de Código](docs/architecture/INVENTARIO_CODIGO.md): especificação dos módulos `mazegen/config.py`, `mazegen/generator.py`, `mazegen/renderer_ascii.py` e `mazegen/renderer_mlx.py`.

### Para a Preparação da Defesa (Peer-Evaluation)
- [Flashcards de Defesa](docs/flashcards/FLASHCARDS_DEFESA.md): perguntas técnicas pontuais para simulações de arguição oral entre a dupla.
- [Roteiro de Teste e Defesa Mandatória](docs/testing/ROTEIRO_DEFESA_MANDATORIO.md): sequência exata de comandos a demonstrar perante o avaliador, com foco em lint, analisador oficial e exemplos de modificação de código ao vivo.
- [Roteiro de Defesa de Bônus](docs/testing/ROTEIRO_DEFESA_BONUS.md): testes específicos com `python3 maze_analyzer.py --max-dead-ends 0` e demonstração gráfica.
