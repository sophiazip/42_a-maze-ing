# Roteiro de Teste e Guia de Defesa — Parte Mandatória (A-Maze-ing)

Este documento orienta o ensaio geral pré-defesa e fornece um roteiro sistemático para conduzir a avaliação presencial por pares (*peer-evaluation*).

---

## 1. Preparação Pré-Defesa do Ambiente

Antes de chamar os avaliadores, garanta que a estação de trabalho esteja pronta e higienizada:

- [ ] Repositório em branch limpa e sem modificações não commitadas (`git status` limpo).
- [ ] Versão do Python confirmada no terminal: `python3 --version` ($\ge 3.10$).
- [ ] Ambiente virtual criado e ativado (`source .venv/bin/activate`).
- [ ] Dependências instaladas via `make install`.
- [ ] Arquivo de configuração padrão `config.txt` presente na raiz.
- [ ] Arquivo de licença `LICENSE.md` presente na raiz.
- [ ] Pacote compilado `mazegen-*.whl` posicionado na raiz do repositório.
- [ ] Script de validação oficial `maze_analyzer.py` acessível no diretório.

---

## 2. Bateria de Verificação Automatizada

Execute esta sequência de comandos diante do avaliador para comprovar a conformidade estrutural do projeto:

### 2.1 Limpeza e Higiene
```bash
make clean
```
*Resultado esperado:* Todos os diretórios de cache (`__pycache__`, `.mypy_cache`, `.pytest_cache`, `build`, `dist`) são eliminados sem erros.

### 2.2 Auditoria de Estilo e Tipagem Estrita
```bash
make lint
make lint-strict
```
*Resultado esperado:* O `flake8` não emite nenhuma advertência de formatação. O `mypy` executa com sucesso em modo `--strict` sem acusar tipos indefinidos ou ausentes.

### 2.3 Bateria de Testes Unitários
```bash
pytest -v
```
*Resultado esperado:* Todos os testes unitários passam com status verde, cobrindo o parser de configuração, o gerador de matrizes e as funções de suporte.

---

## 3. Validação Topológica com o `maze_analyzer.py`

Gere labirintos em ambos os modos obrigatórios e passe-os pelo analisador oficial:

### 3.1 Modo Perfeito (`PERFECT=True`)
1. Configure `PERFECT=True` no `config.txt` (ou passe via parâmetro).
2. Execute o gerador:
   ```bash
   make run
   ```
3. Valide o arquivo de saída gerado com o analisador:
   ```bash
   python3 maze_analyzer.py maze.txt
   ```
*Resultado esperado no terminal:*
- Wall coherence: OK (zero células incoerentes).
- Reachable region: 100% das células livres conectadas.
- Cycles / loops: exatamente 0 (árvore geradora única).
- Status final: **PERFECT MAZE**.

### 3.2 Modo Tabuleiro Jogável (`PERFECT=False`)
1. Configure `PERFECT=False` no `config.txt`.
2. Execute o gerador:
   ```bash
   make run
   ```
3. Valide o arquivo com o analisador:
   ```bash
   python3 maze_analyzer.py maze.txt
   ```
*Resultado esperado no terminal:*
- Loops independentes: $\ge 2$.
- Cantos e centro: presentes na região jogável e desobstruídos.
- Dead-ends reais: $\le 2$.
- Status final: **Pac-Man-USABLE**.

---

## 4. Testes de Casos de Borda e Tratamento de Exceções

O avaliador testará entradas inválidas para verificar a resiliência do programa:

| Cenário de Teste | Comando Executado | Comportamento Esperado |
| :--- | :--- | :--- |
| **Execução sem argumentos** | `python3 a_maze_ing.py` | Exibe sintaxe de uso no stderr e encerra com código 1, sem traceback. |
| **Arquivo inexistente** | `python3 a_maze_ing.py non_existent.txt` | Mensagem limpa: `Erro: arquivo não encontrado`, sem traceback. |
| **Chave obrigatória ausente** | `config.txt` sem a chave `EXIT` | Mensagem clara informando qual chave obrigatória está faltando. |
| **Coordenadas fora dos limites** | `ENTRY=99,99` em grade $20 \times 15$ | Mensagem indicando que a coordenada excede as dimensões configuradas. |
| **Entrada e saída sobrepostas** | `ENTRY=5,5` e `EXIT=5,5` | Mensagem informando que entrada e saída devem ser distintas. |
| **Grade muito pequena** | `WIDTH=7` e `HEIGHT=7` | Mensagem informativa no console indicando que a grade não comporta o padrão "42", gerando o labirinto normalmente sem travar. |
| **Reprodutibilidade com semente** | Duas execuções com o mesmo `SEED=42` | `diff maze1.txt maze2.txt` retorna vazio, comprovando determinismo. |

---

## 5. Demonstração Visual e Interatividade

Inicie a aplicação e demonstre ao avaliador o atendimento integral aos requisitos de interação:

1. **Regeneração:** Pressione a tecla `1` ou `R` e aponte a geração de uma nova topologia de labirinto na tela.
2. **Menor Caminho:** Pressione a tecla `2` ou `P` e mostre a exibição e o ocultamento da rota mais curta calculada entre a entrada e a saída.
3. **Cores:** Pressione a tecla `3` ou `C` e demonstre a troca dinâmica da paleta de cores das paredes.
4. **Encerramento:** Pressione `4` ou `Q` e mostre que o terminal é restaurado ao seu estado inicial sem artefatos gráficos.

---

## 6. Prova de Reusabilidade do Módulo e Empacotamento

O Capítulo VI do subject especifica que o avaliador solicitará a compilação e a reutilização do módulo em ambiente limpo:

### 6.1 Recompilação do Pacote na Defesa
```bash
# Remove o pacote pré-existente
rm -f *.whl dist/*
# Compila novamente a partir do código-fonte
python3 -m build
# Copia o novo .whl para a raiz se necessário
cp dist/*.whl .
```

### 6.2 Teste de Importação Autônoma
No terminal, execute um script Python inline para provar a independência do módulo:

```bash
python3 -c "
from mazegen.generator import MazeGenerator
from mazegen.config import MazeConfig

cfg = MazeConfig(width=10, height=10, entry=(0, 0), exit=(9, 9), output_file='test.txt', perfect=True)
gen = MazeGenerator(cfg)
gen.generate()
path, directions = gen.solve()
print('Módulo reutilizado com sucesso!')
print(f'Comprimento do menor caminho: {len(path)} passos')
print(f'Sequência de passos: {directions[:10]}...')
"
```

---

## 7. Simulação de Modificação ao Vivo pelo Avaliador

O Capítulo IX do subject prevê que o avaliador pode solicitar uma modificação rápida no código durante a avaliação. A equipe deve estar apta a aplicar e demonstrar a alteração em poucos minutos.

### Exemplo 1: Adicionar Exibição do Comprimento da Rota no Terminal
- **Solicitação típica:** "Quero que, ao exibir o labirinto no terminal, o programa imprima também a quantidade exata de passos do menor caminho."
- **Solução técnica:**
  1. No arquivo `a_maze_ing.py` ou `mazegen/renderer_ascii.py`, localize o ponto após o cálculo de `gen.solve()`.
  2. Adicione a linha:
     ```python
     print(f"Comprimento da rota ótima: {len(directions)} passos")
     ```
  3. Execute `make run` e mostre o resultado na saída.

### Exemplo 2: Modificar o Caractere Visual de Entrada ou Saída
- **Solicitação típica:** "Troque o marcador de entrada de 'E' para '@' e de saída de 'X' para '$'."
- **Solução técnica:**
  1. No arquivo `mazegen/renderer_ascii.py`, localize as constantes:
     ```python
     ENTRY_CHAR = "@"
     EXIT_CHAR = "$"
     ```
  2. Execute `make run` e mostre o novo caractere renderizado na grade.

### Exemplo 3: Alterar a Tolerância de Becos no Validador
- **Solicitação típica:** "Como vocês provam que o gerador de vocês respeita os parâmetros de dead-ends se eu mudar a tolerância?"
- **Solução técnica:**
  Execute `python3 maze_analyzer.py maze.txt --max-dead-ends 1` demonstrando a flexibilidade e a robustez do algoritmo implementado.
