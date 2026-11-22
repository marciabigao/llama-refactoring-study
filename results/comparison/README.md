# Comparação GPT-4o-mini × Qwen3.8-27B (RQ1–RQ3) e limitações

Gerado por `scripts/12_comparison.py`. A tabela completa, com o arquivo de origem de cada número, está em `comparison_table.md`.
- **RQ1** é recalculada pelo script para os dois modelos nas mesmas condições (`rq1_recomputed.csv`).
- **RQ2 e RQ3** são lidas de `results/rq2/tables/rq2_summary.csv` e `results/rq3/tables/table4_readability.csv`.

**Sobre o modelo do artigo:** o texto do artigo diz "GPT-4o", mas o modelo usado foi o `gpt-4o-mini-2024-07-18`. Por isso o chamamos de GPT-4o-mini.

## Como a comparação foi feita

- **Mesmos dados de entrada para o GPT:** os 1.000 códigos e os resultados de teste vêm do pacote de replicação do artigo (Zenodo 10.5281/zenodo.17533631). Os números do GPT não foram copiados do PDF. Foram recalculados com as mesmas ferramentas e scripts usados no Qwen.
- **RQ1 com o mesmo número de ciclos:** pass@k e Consistency dependem do número de ciclos. Por isso a comparação principal usa só os ciclos 0–4 do GPT, contra os 5 ciclos do Qwen.
- **RQ1 com as mesmas tarefas:** são 98 tarefas nos dois modelos, sem ClassEval_17 e ClassEval_48, que falham no código canônico. No pacote, essas duas também falham em todos os ciclos do GPT.
- **Verificação:** com as 100 tarefas e os 10 ciclos, o script reproduz a Tabela 3 do artigo: Mean TPR 0,844, pass@5 0,876 (0,88 no artigo), pass@10 0,890 e Consistency 0,800.
  - A exceção é o pass@1: o artigo reporta 0,86, mas recalculado dá 0,844.
  - Com o estimador de Chen et al., o pass@1 é igual ao Mean TPR, então o 0,86 do artigo não é coerente com o próprio Mean TPR de 0,844.

## Tabela comparativa (resumo)

| RQ | Métrica | GPT-4o-mini | Qwen3.8-27B | Qwen × GPT (p) |
|---|---|---|---|---|
| RQ1 | Mean TPR = pass@1 (ciclos 0–4, 98 tarefas) | 0,863 | 0,635 | < 0,0001 |
| RQ1 | pass@5 | 0,898 | 0,939 | |
| RQ1 | Consistency (passa nos 5 ciclos) | 0,837 | 0,245 | |
| RQ1 | TPR por caso de teste | 0,984 | 0,832 | |
| RQ1 | Tarefas que nunca passam (de 98) | 10 | 6 | |
| RQ2 | Cognitive Complexity, δ (canônico 11,73) | −4,119 | −3,012 | < 0,0001 |
| RQ2 | Complexity ciclomática, δ (canônico 12,01) | +2,004 | +3,787 | < 0,0001 |
| RQ2 | NcLOC, δ (canônico 34,84) | +2,580 | +12,428 | < 0,0001 |
| RQ2 | Flake8 total, δ (canônico 9,53) | +0,615 | +1,946 | < 0,0001 |
| RQ2 | Pylint total, δ (canônico 10,27) | +0,044 | +0,542 | 0,0025 |
| RQ3 | Legibilidade, Δ médio (canônico 0,6199) | −0,0240 | −0,0031 | < 0,0001 |
| RQ3 | % piorou | 70,7% | 57,6% | |
| RQ3 | Cliff's δ (refatorado × canônico) | −0,183 (small) | −0,087 (negligible) | |

Os testes Qwen × GPT são Wilcoxon pareados por tarefa, sobre:
- RQ1: a proporção de ciclos que passam;
- RQ2: o δ médio por tarefa;
- RQ3: o Δ médio por tarefa.

Na RQ1 o teste usa os ciclos 0–4 dos dois modelos: n = 73 tarefas com diferença, r = −0,60.

## Conclusões

1. **Correção (RQ1): o GPT-4o-mini é bem mais confiável.**
   - Em um ciclo qualquer, 86,3% das classes do GPT passam em todos os testes, contra 63,5% do Qwen.
   - A Consistency mostra a maior diferença: 83,7% das classes do GPT passam nos 5 ciclos, contra 24,5% no Qwen.
   - Mas o Qwen tem pass@5 maior (0,939 contra 0,898) e menos tarefas que nunca passam (6 contra 10). Ele quase sempre consegue uma refatoração correta em algum ciclo, só que de forma instável.
   - Na prática, com o Qwen é preciso gerar várias vezes e filtrar pelos testes.
2. **Qualidade estática (RQ2): a mesma direção nos dois modelos, com efeitos maiores no Qwen.**
   - Os dois reduzem a complexidade cognitiva e aumentam a complexidade ciclomática e o tamanho.
   - O Qwen gera código bem mais longo: NcLOC +12,4 contra +2,6.
   - O Qwen também acrescenta mais avisos de estilo. As pioras exclusivas dele são PyFlakes, avisos pycodestyle e erros Pylint.
   - Os dois melhoram os riscos de bug (bugbear) e pioram as docstrings, em proporções parecidas (docstrings: p = 0,38).
3. **Legibilidade (RQ3): o Qwen preserva, o GPT piora um pouco.**
   - A queda do GPT é pequena, mas consistente. A do Qwen não é significativa.
   - A diferença entre os modelos é significativa, mesmo com o Qwen gerando mais código. A causa não foi identificada: a hipótese dos comentários foi testada e descartada (ver `results/rq3/README.md`).
4. **Resumo:** nenhum modelo domina o outro.
   - O GPT-4o-mini é preferível quando a correção em uma única tentativa importa.
   - O Qwen, de pesos abertos, chega a uma correção semelhante com várias tentativas, preserva melhor a legibilidade, mas gera código maior e com mais avisos.

## Limitações e ameaças à validade

**Do desenho da réplica**
- **Ciclos:** 5 no Qwen e 10 no GPT.
  - pass@10 do Qwen = n/a.
  - Na RQ1 a comparação foi feita com os ciclos 0–4 do GPT.
  - Na RQ2 e na RQ3 a média por tarefa do Qwen usa 5 ciclos e a do GPT usa 10, então a do Qwen é mais ruidosa.
- **Modelo:** comparamos um modelo aberto de 27B parâmetros com o `gpt-4o-mini-2024-07-18`, não com o GPT-4o.
  - O Qwen foi acessado pela API da Groq, que não fixa uma versão do modelo. Uma nova execução pode dar resultados diferentes.
- **Parâmetros de geração:**
  - O Qwen usou temperature 1,0, top_p 1,0, max_tokens 4000 e o raciocínio padrão do provedor (`experiment_config.json`).
  - O pacote do artigo não inclui o script de geração, então não sabemos se os parâmetros do GPT foram os mesmos.
  - O prompt é o da Seção 3.2 do artigo.
- **Gerações do Qwen:**
  - 1 geração foi cortada por max_tokens e 11 não listaram nenhuma refatoração (`generation_summary.json`);
  - 2 têm erro de sintaxe (ClassEval_77 e ClassEval_80, ciclo 4);
  - 5 terminaram com erro de importação nos testes.

**Das medições**
- **Ambientes de teste:**
  - Os testes do Qwen foram executados pelo grupo. No nosso ambiente, todas as classes canônicas passam, exceto 17 e 48 (`canonical_baseline.jsonl`).
  - Os testes do GPT foram executados pelos autores, e não os rodamos de novo.
  - Uma diferença de ambiente pode afetar algumas tarefas. A ClassEval_58 é conhecida por ser instável.
- **Tamanho e complexidade:** o artigo usou o SonarCloud, e aqui usamos ferramentas locais.
  - A concordância com os valores do SonarCloud publicados pelo artigo para o código canônico é: NcLOC 100%, Cognitive 92%, Statements 88% e Complexity 85% (`results/rq2/README.md`).
  - Os dois modelos foram medidos com as mesmas ferramentas, então a comparação entre eles não é afetada.
- **Pylint:**
  - Os erros Pylint dependem das bibliotecas instaladas.
  - Os dados do artigo têm um bug: as contagens Pylint do código canônico estão zeradas. Por isso comparamos com a nossa reanálise, não com a Figura 4 do artigo.
- **Legibilidade:**
  - O modelo de Scalabrino é treinado para Java e lê Python com um parser Java (ameaça herdada do artigo).
  - A ClassEval_83 não recebe score, e 12 gerações do Qwen ficaram sem score.
  - O score muda com detalhes de formatação, como o newline final.

**De generalização**
- Um único benchmark (ClassEval, 100 classes pequenas e autocontidas). Os resultados podem não valer para código real de projetos maiores.
- Possível contaminação: o ClassEval é público, e os dois modelos podem tê-lo visto no treinamento.
- Um único modelo aberto e um único prompt. Outros modelos ou formas de pedir a refatoração podem dar resultados diferentes.

## Arquivos

- `rq1_recomputed.csv|md`: RQ1 do artigo, verificação com 100 tarefas, GPT com 10 ciclos e com os ciclos 0–4, e Qwen.
- `comparison_table.csv|md`: tabela única RQ1–RQ3, com a coluna `source`.
