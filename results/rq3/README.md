# RQ3: legibilidade (modelo de Scalabrino et al., 2018)

Gerado por `scripts/10_readability.py` (scores) e `scripts/11_rq3_stats.py` (Tabela 4, Figura 6 e exemplos).
Os números abaixo saem de `tables/table4_readability.csv` e `tables/rq3_per_iteration.csv`. Convenção: **Δ = refatorado − canônico**, e Δ > 0 = mais legível. O score vai de 0 a 1.

## Método

- Mesma ferramenta do artigo: o `rsm.jar` do pacote de replicação (Zenodo 10.5281/zenodo.17533631), executado como no script `readability.py` dos autores.
- Aplicada aos 100 canônicos, aos 500 códigos do Qwen e aos 1.000 do GPT-4o-mini do pacote.
- Agregação igual à do artigo: o "depois" de cada tarefa é a **média dos ciclos**, pareada com o score do canônico.
- Testes: Wilcoxon pareado unilateral "refatorado > canônico", que é o teste do artigo, mais o unilateral contrário e o bilateral. Também r = z/√n e Cliff's δ.

## Validação

- Scores **idênticos aos do artigo**: 99/99 classes canônicas e 990/990 códigos do GPT.
- Com os dados do GPT, o nosso script **reproduz exatamente a Tabela 4** do artigo: médias, desvios, Δ, IC 95%, 29,3%/70,7%, W = 1350, p = 1,000 e Cliff's δ = −0,183.
- Detalhe técnico: o score é sensível à quebra de linha no fim do arquivo. Com newline final, a média do canônico cai para 0,6158. Por isso os arquivos são gravados como no pacote do artigo, sem newline final, para todos os modelos.

## Leitura correta do p = 1,000 do artigo

O artigo testa só a hipótese "o refatorado é **mais** legível". p = 1,000 significa apenas que não há evidência de melhora. O teste na direção oposta mostra uma **piora significativa** no GPT (p unilateral "menor" < 0,0001, IC 95% de Δ = [−0,0378; −0,0102]). Isso explica a aparente contradição do artigo, que reporta p = 1,000 junto com um IC que exclui o zero.

## Tabela 4 (99 tarefas)

| | Canônico | Refatorado | Δ médio (IC 95%) | Melhorou | Piorou | p bilateral | Cliff's δ |
|---|---|---|---|---|---|---|---|
| GPT-4o-mini (artigo) | 0,6199 | 0,5959 | −0,0240 [−0,0378; −0,0102] | 29,3% | 70,7% | — (p "maior" = 1,000) | −0,183 |
| GPT-4o-mini (nosso) | 0,6199 | 0,5959 | −0,0240 [−0,0378; −0,0102] | 29,3% | 70,7% | 0,0001 | −0,183 (small) |
| Qwen3.8-27B | 0,6199 | 0,6168 | −0,0031 [−0,0158; 0,0095] | 42,4% | 57,6% | 0,344 | −0,087 (negligible) |

- **Qwen × GPT** (Δ por tarefa, Wilcoxon pareado): p = 0,0001. O Qwen perde significativamente menos legibilidade que o GPT.
- **Só os pares que passaram nos testes** (`table4_readability_passing.md`): GPT Δ = −0,0278 (n = 88 tarefas) e Qwen Δ = −0,0003 (n = 90). A conclusão não muda.
- **Estabilidade por ciclo** (`rq3_per_iteration.csv`): o GPT piora em todos os 10 ciclos (Δ entre −0,022 e −0,026). O Qwen varia entre +0,003 (ciclo 0) e −0,009 (ciclo 1).

## Pontos para a discussão

- **O GPT reproduz o achado do artigo:** a legibilidade cai pouco, mas de forma consistente.
- **O Qwen praticamente preserva a legibilidade**, mesmo gerando código bem mais longo (RQ2: NcLOC +12,4). Ou seja, mais código não significou código menos legível segundo esse modelo.
- **Hipótese testada e descartada:** "o Qwen preserva a legibilidade porque acrescenta comentários". No Qwen, as refatorações que acrescentaram comentários (13,1% dos pares) perderam *mais* legibilidade (Δ −0,018 contra −0,002), com Spearman ρ = −0,19 entre a variação de comentários e a de legibilidade. A causa da diferença entre os modelos fica em aberto.
- **Na Figura 6**, os dois modelos parecem puxar os scores para o meio: classes canônicas pouco legíveis tendem a subir e as muito legíveis tendem a cair. É uma observação visual, não testada.

## Exemplo (Figura 7)

`examples/ClassEval_64_iter2.md` (testes passando): a legibilidade cai de **0,73 para 0,52**. O Qwen trocou seis conversões triviais (`bin(n)[2:]`, `int(s, 8)`, ...) por chamadas a um método genérico com expressões condicionais encadeadas, constantes de prefixo e um parâmetro `prefix` que nunca é usado. É uma abstração desnecessária: o código continua correto, mas fica mais difícil de ler. No sentido contrário, `examples/ClassEval_97_iter2.md` é o maior ganho (0,38 → 0,62).

## Cobertura

- `ClassEval_83` não recebe score em nenhuma versão (a ferramenta falha nela; o artigo também tem só 99 classes). Fica fora da tabela.
- Do Qwen, mais 12 gerações ficaram sem score porque a ferramenta falhou nelas: ciclo 0: 51, 53, 80; ciclo 1: 51, 60; ciclo 2: 99; ciclo 3: 45, 97; ciclo 4: 6, 22, 32, 38. A média por tarefa usa os ciclos que têm score.

## Limitações

- O `rsm.jar` foi construído e treinado para **Java** e lê Python com um parser Java. Isso é uma ameaça à validade herdada do artigo, mantida para garantir a comparabilidade.
- Os ciclos não são equivalentes: 5 no Qwen e 10 no GPT.
- O score é sensível a detalhes de formatação, como a quebra de linha final (ver Validação).
