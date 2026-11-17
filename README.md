# Refatoração com Llama (Groq) × GPT-4o — Itens 1 (Conjunto de Dados) e 2 (RQ1)

Replica a metodologia de *"From Human to Machine Refactoring: Assessing GPT-4's Impact on Python Class Quality and Readability"*
(Midolo, Tramontana, Di Penta — arXiv 2601.13139) usando um modelo Llama via API Groq.

## Estrutura

```
.env.example            -> copie para .env (chave Groq, modelo)
requirements.txt
src/                    config, lista de refatorações (Tabela 1), prompt (Seção 3.2), parser, executor de testes
scripts/
  00_check_environment.py     verifica deps, dados NLTK, chave e modelos disponíveis na Groq
  01_download_classeval.py    [1.1] baixa o ClassEval (100 classes + testes)
  02_generate_refactorings.py [1.2-1.4] 100 classes x 10 ciclos via Groq (retomável)
  03_parse_and_stats.py       [1.5-1.6] extrai código/lista, Tabela 2 e Figura 1
  04_run_tests.py             [2.1-2.2] roda os testes (--canonical = teste de sanidade do ambiente)
  05_rq1_metrics.py           [2.3-2.4] Tabela 3 (Mean/Std TPR, pass@k, Consistency) + comparação com o artigo
  06_failure_cases.py         [2.5] candidatos a "parecia certo, mas mudou o comportamento" (Figura 2)
results/<modelo>/...          saídas (tabelas .csv/.md, figuras .png, parsed.jsonl, raw/)
```

## Passo a passo

### 1) Criar o repositório no GitHub
1. Instale o Git (https://git-scm.com) e configure uma vez:
   `git config --global user.name "Seu Nome"` e `git config --global user.email "voce@email.com"`.
2. No GitHub: **New repository** → nome `llama-refactoring-study` → **Private** (ou Public) → **não** marque README/.gitignore (já existem aqui) → Create.
3. No terminal, dentro da pasta do projeto:
   ```bash
   git init -b main
   git add .
   git commit -m "Setup inicial: pipeline de geração e RQ1"
   git remote add origin https://github.com/SEU_USUARIO/llama-refactoring-study.git
   git push -u origin main
   ```
   (Se pedir senha, use um *Personal Access Token*: GitHub → Settings → Developer settings → Tokens, ou `gh auth login` com o GitHub CLI.)
4. Confira que `.env` **não** foi enviado (o `.gitignore` já o exclui). Para os colegas: cada um cria o próprio `.env`.

### 2) Ambiente Python
Requer **Python 3.10+** (testado em 3.12).
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
> `numpy<2` é proposital: os testes do ClassEval usam `np.mat` (removido no NumPy 2).
> Recomendação de segurança: os scripts executam código gerado por LLM. Rode em venv/WSL/Docker, não em máquina com dados sensíveis.

### 3) Chave e modelo Groq
1. Crie a chave em https://console.groq.com/keys (gratuita).
2. `cp .env.example .env` e edite: `GROQ_API_KEY=gsk_...` e `GROQ_MODEL=...`.
3. `python scripts/00_check_environment.py` — lista os modelos Llama disponíveis na SUA conta. Use um deles em `GROQ_MODEL`
   (padrão: `llama-3.3-70b-versatile`; alternativa mais barata/rápida: `llama-3.1-8b-instant`). Catálogo muda: confira https://console.groq.com/docs/models.
   - **Nota de comparabilidade:** na Seção 3.2 o artigo diz "GPT-4o", mas o modelo realmente usado foi `gpt-4o-mini-2024-07-18`. Cite isso nos slides; para uma comparação mais justa de porte, considere também rodar um Llama menor (cada modelo grava em `results/<modelo>/`, sem misturar).

### 4) Baixar o ClassEval e validar o ambiente de testes
```bash
python scripts/01_download_classeval.py
python scripts/04_run_tests.py --canonical --repeats 5
```
O 2º comando roda o **código canônico** contra os testes. Deveria passar ~100%. Nos meus testes (Linux, root, Python 3.12, numpy 1.26) 5 classes falham por razões do benchmark/ambiente, **não do modelo**:
`ClassEval_17` (teste depende da data atual), `_31` e `_51` (precisão de ponto flutuante), `_48` (hostname fixo no teste),
`_50` (espera erro de permissão; como root o arquivo é gravável). Além disso `ClassEval_58` (Minesweeper) é **aleatório/flaky** (~20% de falha mesmo no canônico).
Registre isso no relatório. No passo 7 você reporta os resultados com e sem essas classes.

### 5) Gerar as 1.000 refatorações
Primeiro um teste rápido (3 classes × 2 ciclos):
```bash
python scripts/02_generate_refactorings.py --tasks 3 --runs 2
```
Depois o experimento completo (retomável; pode interromper com Ctrl+C e rodar de novo):
```bash
python scripts/02_generate_refactorings.py
```
- Parâmetros fixos como no artigo: `temperature=1.0`, `top_p=1.0`, `max_tokens=4000` (enviado como `max_completion_tokens`), 10 ciclos; prompt de sistema = Seção 3.2 com a lista da Tabela 1; prompt de usuário = código da classe.
- Ordem **ciclo a ciclo**: se a cota acabar, você já tem ciclos completos (ex.: 6 ciclos × 100 classes).
- **Limites da Groq (tier gratuito):** há limites por minuto (tratados com espera automática) e por **dia** em tokens. 1.000 gerações ≈ 1–2 M de tokens; no 70B gratuito isso pode levar vários dias (o script avisa "COTA DIÁRIA" e para; rode de novo depois). `llama-3.1-8b-instant` tem cota bem maior; o plano pago (on-demand) resolve em ~1 h. Os limites mudam — veja https://console.groq.com/settings/limits.
- Teste do pipeline sem API: `GROQ_MODEL=mock` (gera respostas falsas com ~14% de bugs sintéticos; grava em `results/mock/`).

### 6) Extrair código/lista, Tabela 2 e Figura 1
```bash
python scripts/03_parse_and_stats.py
```
Saídas em `results/<modelo>/`: `tables/table2_refactoring_counts.csv|md`, `figures/figure1_refactorings_per_task.png`, `tables/generation_summary.json` (estatísticas para os slides: nº de refatorações por geração, truncamentos por `max_tokens`, nomes fora da Tabela 1 = possíveis alucinações, tokens usados).
Convenções (como no artigo): cada tipo de refatoração conta 1× por geração; a Figura 1 usa a média por tarefa ao longo dos ciclos, arredondada ao inteiro. A lista de refatorações é a **declarada** pelo modelo (não verificada no código).

### 7) RQ1: testes, Tabela 3 e caso de falha
```bash
python scripts/04_run_tests.py                          # 1.000 execuções de testes
python scripts/05_rq1_metrics.py                        # todas as 100 classes
python scripts/05_rq1_metrics.py --exclude-canonical-failures   # sem as que falham no canônico
python scripts/06_failure_cases.py --top 5
```
- **Mean/Std TPR:** TPR de cada ciclo = fração das 100 classes que passam em *todos* os testes; média e desvio (amostral, ddof=1) entre ciclos.
- **pass@1/5/10:** estimador não-viesado de Chen et al. (2021), n=10. Observação: com n=10, pass@1 = Mean TPR por definição; o artigo reporta 0.86 vs 0.844 (diferença provavelmente de arredondamento/definição) — mencione isso na comparação.
- **Consistency:** fração de classes que passam nos 10 ciclos.
- Gerações sem código extraível contam como **falha** (`no_code`); veja `table3_extra.json` → `status_counts`.
- `results/<modelo>/tables/table3_comparison_gpt_vs_llama.md` já traz a tabela comparativa (valores do GPT-4o vêm da Tabela 3 do artigo).
- `06_failure_cases.py` gera `.md` com diff canônico→Llama, refatorações declaradas e mensagens de asserção. Escolha um caso e preencha a seção "Sua análise" (esse texto é seu — o script só acha candidatos de **falha semântica pura**, sem crash).

## O que levar para os slides
Item 1: `experiment_config.json` (prompt/parâmetros), Tabela 2, Figura 1, `generation_summary.json`.
Item 2: `table3_comparison_gpt_vs_llama.md`, `table3_extra.json` (TPR por ciclo, falhas por tipo) e o caso de falha semântica.

## Limitações a declarar
Testes do ClassEval com falhas de ambiente/aleatoriedade (acima); possível divergência do modelo Llama usado vs. o `gpt-4o-mini` do artigo; amostragem com temperature=1.0 (resultados variam entre execuções); lista de refatorações é autodeclarada pelo modelo.
