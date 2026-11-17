# Refatoração com LLM aberto (Qwen3.8-27B via Groq) × GPT-4o — Itens 1 (Conjunto de Dados) e 2 (RQ1)

Replica a metodologia de *"From Human to Machine Refactoring: Assessing GPT-4's Impact on Python Class Quality and Readability"*
(Midolo, Tramontana, Di Penta — arXiv 2601.13139) usando um modelo Llama via API compatível com OpenAI (Groq).

## Estrutura

```
.env.example            -> copie para .env (chave Groq, modelo)
requirements.txt
src/                    config, lista de refatorações (Tabela 1), prompt (Seção 3.2), parser, executor de testes
scripts/
  00_check_environment.py     verifica deps, dados NLTK e faz uma chamada de teste ao modelo
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

### 3) Chave e modelo (Groq + Qwen3.8-27B, plano gratuito)
1. Crie a chave em https://console.groq.com/keys.
2. `cp .env.example .env` e edite (valores recomendados já vêm no exemplo):
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_...
   LLM_MODEL=qwen/qwen3.8-27b
   N_RUNS=3
   REQUEST_INTERVAL_S=2
   OTPM_LIMIT=1000
   ```
   O código usa o SDK `openai` apontando para a API compatível da Groq. Outros provedores: `LLM_PROVIDER=sambanova|fireworks` (veja o fim do `.env.example`).
3. `python scripts/00_check_environment.py` faz uma chamada de teste ao modelo (404 = ID errado, 401 = chave inválida, 429 = limite).
4. **Qwen3.8 é modelo de raciocínio híbrido.** O parser ignora blocos `<think>...</think>`. Depois das primeiras gerações, olhe `usage.reasoning_tokens` em `results/<modelo>/raw/*.json`: se for alto (consome sua cota), ponha `LLM_REASONING_EFFORT=none` no `.env`. Se a API recusar o parâmetro (HTTP 400), remova-o.
5. **Comparabilidade:** o artigo diz "GPT-4o" mas usou `gpt-4o-mini-2024-07-18`; a proposta cita Llama e aqui se usa Qwen (também de pesos abertos): avise o professor e ajuste o texto. Cada modelo grava em `results/<modelo>/`.

### Prazo de 3 dias — o que cabe
Limites do plano gratuito do `qwen/qwen3.8-27b` na Groq (fontes de terceiros que citam a doc da Groq; confirme em console.groq.com/settings/limits): 30 req/min, 1.000 req/dia, **8.000 tokens/min, 200.000 tokens/dia**. O gargalo é tokens/dia.
```bash
python scripts/02_generate_refactorings.py --plan --days 3     # calcula quantos ciclos cabem
```
Com ~1.400 tokens por geração (estimativa; o `--plan` passa a usar o valor MEDIDO depois de 5 gerações reais) cabem ~136 gerações/dia ⇒ ~400 em 3 dias. **Recomendado: `N_RUNS=3` (300 gerações, ~2,2 dias).** Com 10 ciclos (1.000 gerações) seriam ~7–8 dias.
**Limite por minuto observado na prática:** o erro 429 real da Groq mostrou `output tokens per minute (OTPM): Limit 1000` na conta. Com ~600 tokens de saída por geração isso dá ~1 geração a cada 36 s (300 gerações ≈ 3 h de relógio): não é o gargalo dos 3 dias, mas o script agora controla o ritmo (`OTPM_LIMIT`/`TPM_LIMIT` no `.env`) para não tomar 429. Se o pedido de uma classe grande nunca couber nesse limite (`Requested` > `Limit`), a geração é **PULADA** (aparece `[ATENÇÃO]` no final), conta como falha (`skipped_rate_limit`) e você pode reportar sem essas classes com `python scripts/05_rq1_metrics.py --exclude-skipped` (declarando isso). Subir para o Dev Tier da Groq remove essa restrição.

Consequências de usar 3 ciclos (declare nos slides): `pass@5` e `pass@10` ficam `n/a` (o script acrescenta `pass@3`); o desvio padrão do TPR usa só 3 pontos; é uma réplica reduzida do protocolo do artigo.
Para manter os 10 ciclos em < 3 dias a única via é plano pago (ex.: Groq Developer, que segundo fontes de terceiros cobra ~US$ 0,80/M de entrada e ~US$ 4,00/M de saída no Qwen3.8-27B ⇒ ordem de US$ 3 a 4 por 1.000 gerações; confirme preços) ou outro provedor.

### 4) Baixar o ClassEval e validar o ambiente de testes
```bash
python scripts/01_download_classeval.py
python scripts/04_run_tests.py --canonical --repeats 5
```
O 2º comando roda o **código canônico** contra os testes. Deveria passar ~100%. Nos meus testes (Linux, root, Python 3.12, numpy 1.26) 5 classes falham por razões do benchmark/ambiente, **não do modelo**:
`ClassEval_17` (teste depende da data atual), `_31` e `_51` (precisão de ponto flutuante), `_48` (hostname fixo no teste),
`_50` (espera erro de permissão; como root o arquivo é gravável). Além disso `ClassEval_58` (Minesweeper) é **aleatório/flaky** (~20% de falha mesmo no canônico).
Registre isso no relatório. No passo 7 você reporta os resultados com e sem essas classes.

### 5) Gerar as refatorações
Teste rápido (3 classes × 2 ciclos):
```bash
python scripts/02_generate_refactorings.py --tasks 3 --runs 2
python scripts/02_generate_refactorings.py --plan --days 3      # agora com tokens MEDIDOS
```
Experimento completo, **sem supervisão** (retoma sozinho quando a cota diária zera):
```bash
nohup python scripts/02_generate_refactorings.py --auto-resume > generate.log 2>&1 &
tail -f generate.log          # acompanhar (Ctrl+C só sai do tail)
```
(Em Windows use WSL, ou `tmux`/`screen` no Linux. O computador precisa ficar ligado e sem suspender.)
- Parâmetros como no artigo: `temperature=1.0`, `top_p=1.0`, `max_tokens=4000`; prompt de sistema = Seção 3.2 com a Tabela 1; prompt de usuário = código da classe.
- Ordem **ciclo a ciclo**: a qualquer momento você tem ciclos completos; dá para rodar os passos 03–05 com resultados parciais.
- 429 por minuto: espera automática (lê o "try again in ..." do servidor). Cota **diária**: com `--auto-resume` dorme até o reset e continua; sem a flag, para com mensagem e você roda de novo depois. Chave/modelo inválidos ou saldo esgotado param com mensagem clara. Tudo é retomável.
- Teste do pipeline sem API: `LLM_MODEL=mock` (grava em `results/mock/`).

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
- **pass@k:** estimador não-viesado de Chen et al. (2021) com n = nº de ciclos (10 no artigo). Com menos ciclos, pass@k para k > n sai como `n/a` e é acrescentado pass@n. Observação: com n=10, pass@1 = Mean TPR por definição; o artigo reporta 0.86 vs 0.844 (diferença provavelmente de arredondamento/definição) — mencione isso na comparação.
- **Consistency:** fração de classes que passam nos 10 ciclos.
- Gerações sem código extraível contam como **falha** (`no_code`); veja `table3_extra.json` → `status_counts`.
- `results/<modelo>/tables/table3_comparison_gpt_vs_llama.md` já traz a tabela comparativa (valores do GPT-4o vêm da Tabela 3 do artigo).
- `06_failure_cases.py` gera `.md` com diff canônico→Llama, refatorações declaradas e mensagens de asserção. Escolha um caso e preencha a seção "Sua análise" (esse texto é seu — o script só acha candidatos de **falha semântica pura**, sem crash).

## O que levar para os slides
Item 1: `experiment_config.json` (prompt/parâmetros), Tabela 2, Figura 1, `generation_summary.json`.
Item 2: `table3_comparison_gpt_vs_llama.md`, `table3_extra.json` (TPR por ciclo, falhas por tipo) e o caso de falha semântica.

## Limitações a declarar
Testes do ClassEval com falhas de ambiente/aleatoriedade (acima); possível divergência do modelo Llama usado vs. o `gpt-4o-mini` do artigo; amostragem com temperature=1.0 (resultados variam entre execuções); lista de refatorações é autodeclarada pelo modelo.
