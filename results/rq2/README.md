# RQ2: qualidade estática (Flake8, Pylint, tamanho e complexidade)

Gerado por `scripts/08_static_analysis.py` (métricas) e `scripts/09_rq2_stats.py` (estatística e figuras).
Todos os números abaixo saem de `tables/rq2_summary.csv`. Convenção: **δ = refatorado − canônico**, e δ < 0 = menos avisos / código menor ou menos complexo.

## Método

- **Mesmas ferramentas para os dois modelos.** Além dos 500 códigos do Qwen (5 ciclos), analisamos os 1.000 códigos do GPT-4o-mini (10 ciclos) publicados no pacote de replicação do artigo (Zenodo 10.5281/zenodo.17533631, CC-BY 4.0). A comparação é feita com as mesmas versões e configurações, e não contra os números impressos no artigo.
- **Flake8** com os plugins que o artigo usou (inferidos dos códigos nos relatórios deles): docstrings (D), bugbear (B), cognitive-complexity (CCR) e commas (C8). As categorias seguem o script `create_statistical_reports.py` do artigo.
- **Pylint** com configuração padrão, um processo por grupo de 100 arquivos, como no artigo.
- **Tamanho e complexidade:** o artigo usou o SonarCloud. Aqui o cálculo é local (Lizard, `cognitive_complexity` e `ast`). Concordância exata com os valores do SonarCloud que o artigo publicou para as 100 classes canônicas: NcLOC 100%, Cognitive 92%, Statements 88%, Complexity 85%.
- **Normalização:** todos os arquivos terminam com uma única quebra de linha. No pacote do artigo nenhum arquivo tinha newline final, o que somava +1 aviso W292 (Flake8) e +1 C0304 (Pylint) em todo arquivo.
- **Estatística:** Wilcoxon pareado entre o canônico e a média por tarefa nos ciclos (100 pares), correção de Benjamini–Hochberg por modelo, efeito r = z/√n e Cliff's δ (mesma fórmula do pacote do artigo). A Figura 4 usa o Wilcoxon por ciclo.

## Validação do pipeline (sobre os arquivos do GPT)

Rodando o nosso pipeline nos 1.000 arquivos do GPT e comparando com as tabelas do pacote do artigo:
- Flake8: 100% idêntico em todas as categorias. A exceção, PycodestyleWarnings, é exatamente 1 a menos por arquivo, que é o artefato W292 removido de propósito.
- NcLOC 100% idêntico; Cognitive Complexity 97%; Statements 86%; Complexity 87%.
- A taxa de aprovação nos testes do GPT recalculada a partir do pacote é 844/1000 = 0,844, igual ao Mean TPR do artigo.
- Os tamanhos de efeito r das categorias Flake8, calculados a partir das tabelas do próprio artigo, são idênticos aos nossos.

## Observação sobre os dados do artigo

Na tabela consolidada do pacote (`data/rq2/statistical_reports.csv`), **todas as contagens Pylint do código canônico são zero**. O relatório bruto (`canonical/reports/pylint_report.csv`) tem os dados, mas o script de consolidação não remove o prefixo `canonical_` dos nomes de módulo, então as linhas do canônico nunca casam (`create_statistical_reports.py`, linha 80). Com isso, as linhas Pylint da Figura 4 do artigo comparam o GPT contra zero. Na nossa reanálise as contagens do canônico estão corretas.

## Principais resultados (100 tarefas; médias por classe)

| Métrica | Canônico | GPT-4o-mini | Qwen3.8-27B | Qwen × GPT (p) |
|---|---|---|---|---|
| Cognitive Complexity | 11,73 | 7,61 (−4,12) | 8,73 (−3,01) | < 0,001 |
| Complexity (ciclomática) | 12,01 | 14,01 (+2,00) | 15,80 (+3,79) | < 0,001 |
| Statements | 31,42 | 34,31 (+2,89) | 42,42 (+10,98) | < 0,001 |
| NcLOC | 34,84 | 37,42 (+2,58) | 47,30 (+12,43) | < 0,001 |
| Flake8 total | 9,53 | 10,15 (+0,62) | 11,48 (+1,95) | < 0,001 |
| Pylint total | 10,27 | 10,31 (+0,04) | 10,81 (+0,54) | 0,003 |

Pontos para a discussão:
- **Os dois modelos reduzem a complexidade cognitiva**: o GPT diminui em 70,5% dos pares e o Qwen em 54,8%. Mas os dois **aumentam a complexidade ciclomática e o tamanho**. *Extract Method* cria funções novas, e cada função soma +1 na ciclomática.
- **O Qwen gera código bem mais longo**: NcLOC +12,4 contra +2,6 do GPT, e o NcLOC aumenta em 86,9% dos pares do Qwen. Comentários não entram no NcLOC, então o aumento é de código de fato.
- **Melhoras comuns aos dois:** riscos de bug (bugbear: r = −0,90 no GPT e −0,81 no Qwen), complexidade (CCR001/C8) e Pylint *refactor* (r ≈ −0,6/−0,7).
- **Pioras comuns aos dois:** docstrings (os modelos criam métodos novos sem docstring) e Pylint *convention*.
- **Pioras só do Qwen:** PyFlakes (r = 0,73: imports e variáveis não usados), avisos pycodestyle (r = 0,65) e erros Pylint (r = 0,61). No GPT esses itens ficam neutros ou melhoram.
- **2 dos 500 códigos do Qwen têm erro de sintaxe** (ClassEval_77 e ClassEval_80, ciclo 4). Ficam fora das métricas de tamanho.

## Exemplo de melhoria estática (Figura 5)

`examples/ClassEval_57_iter3.md`, a mesma classe da Figura 5 do artigo. O Qwen reduz o Flake8 de 21 para 10 avisos e o Pylint de 23 para 12, e o código passa nos testes. Mudanças nas regras: CCR001 2→0 (complexidade cognitiva), E721 6→1 (`type(x) == ...` trocado por `isinstance`) e E501 8→4 (linhas longas), as mesmas regras que o artigo destaca para o GPT. A complexidade cognitiva cai 44 pontos com a extração de `_compute_mr`, `_compute_ap` e `_validate_input`.

## Arquivos

- `static_metrics.csv`: 1 linha por (modelo, ciclo, tarefa); ciclo −1 = canônico.
- `static_rules.csv`: contagem por regra Flake8/Pylint.
- `run_info.json`: versões das ferramentas.
- `tables/rq2_summary.csv|md`: resumo com todas as tarefas.
- `tables/rq2_summary_passing.csv|md`: só os pares que passaram nos testes.
- `tables/rq2_wilcoxon_per_iteration.csv`: base da Figura 4.
- `figures/figure3_delta_boxplots.png`, `figures/figure4_heatmap_effect_r.png`.

## Limitações

- Os ciclos não são equivalentes: 10 no GPT e 5 no Qwen.
- O tamanho e a complexidade vêm de ferramentas locais, não do SonarCloud, mas a concordância foi verificada (acima).
- Os erros Pylint (E0401, import-error) dependem das bibliotecas instaladas no ambiente.
- Em `pylint_error` o número de pares com diferença é muito pequeno (r = ±1 com n de 1 a 3), então esses valores não devem ser interpretados.
