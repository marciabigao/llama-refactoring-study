# RQ1: caso de falha semântica (equivalente à Figura 2 do artigo)

**Caso escolhido:** `ClassEval_62` (`NLPDataProcessor`), iteração 3. É a versão com o diff mais limpo; a iteração 1 falha pelo mesmo motivo.
**Arquivos de origem:** `failure_cases/ClassEval_62_iter3.md`, `failure_cases/ClassEval_62_iter1.md` e `test_results.jsonl`.

## O que aconteceu

A refatoração parece correta e até "melhor", mas muda o comportamento do método `remove_stop_words`, e 1 dos 11 testes falha (`test_remove_stop_words_5`).

### Código canônico

```python
def remove_stop_words(self, string_list, stop_word_list):
    answer = []
    for string in string_list:
        string_split = string.split()
        for word in string_split:
            if word in stop_word_list:
                string_split.remove(word)   # remove da lista enquanto itera sobre ela
        answer.append(string_split)
    return answer
```

### Código refatorado pelo Qwen (iteração 3)

```python
def remove_stop_words(self, string_list, stop_word_list):
    answer = []
    for string in string_list:
        string_split = string.split()
        filtered_words = []
        for word in string_split:
            if word not in stop_word_list:
                filtered_words.append(word)
        answer.append(filtered_words)
    return answer
```

Refatorações declaradas pelo modelo: *Extract Method, Remove Dead Code, Introduce Explaining Variable, Replace Loop with Pipeline*. Na prática, a mudança neste método é a troca de "remover da lista original" por "construir uma lista filtrada".

## Análise

**O que o código original garantia?**
O canônico remove itens de `string_split` **enquanto itera sobre essa mesma lista**. Em Python, cada `remove` desloca os elementos seguintes uma posição para a esquerda, e o iterador avança e **pula a palavra que vinha logo depois** da removida. Assim, quando duas stop words aparecem seguidas, a segunda sobrevive.

Rastreamento com a entrada do teste (`'This is a test'`, stop words `['a', 'an', 'the', 'This', 'is']`):

| Passo | Palavra visitada | Ação | Lista após o passo |
|---|---|---|---|
| 1 | `This` | remove | `['is', 'a', 'test']` |
| 2 | `a` (`is` foi pulada) | remove | `['is', 'test']` |
| fim | — | — | resultado: `['is', 'test']` |

O teste `test_remove_stop_words_5` espera exatamente esse resultado, `[['is', 'test'], ['is', 'apple'], ['is', 'dog']]`. Ou seja, a suíte de testes **codifica o efeito colateral do bug** como comportamento esperado.

**O que a refatoração mudou?**
A versão refatorada filtra corretamente todas as stop words e devolve `[['test'], ['apple'], ['dog']]`. Quando as stop words não aparecem em sequência, os dois códigos devolvem o mesmo resultado (os testes 1 a 4 passam). A diferença só aparece no caso de stop words consecutivas, e foi exatamente esse caso que o teste 5 cobriu.

**Qual refatoração causou o desvio e por quê?**
A troca do laço com `remove` por uma lista filtrada, rotulada como *Replace Loop with Pipeline* (na iteração 1 ela aparece como list comprehension). Uma refatoração, por definição, deve preservar o comportamento externo, **inclusive os comportamentos acidentais**. O modelo tratou o código como se a intenção fosse "remover todas as stop words" e "corrigiu" o laço. Na iteração 1 ele chega a escrever isso num comentário dentro do código: *"Bug fix/refactor: Modifying a list while iterating causes issues."* O resultado é uma mudança semântica apresentada como refatoração.

**Por que esse caso é interessante para a discussão:**
- O novo código é mais legível e, do ponto de vista da intenção, mais correto. Uma revisão de código provavelmente o aprovaria, mas ele quebra o contrato verificado pelos testes. É o mesmo tipo de risco apontado na Figura 2 do artigo: uma refatoração aparentemente modular que muda o significado.
- O padrão se repete: `ClassEval_62` não passa em nenhuma das 5 iterações (está em `tasks_never_passing`). `test_remove_stop_words_5` falha nas iterações 0, 1, 3 e 4. A iteração 2 tem outro problema, com 6 testes com erro.
- Também mostra uma limitação do critério "passou nos testes": aqui a falha indica preservação de comportamento violada, não código pior.

## Verificação

O comportamento dos dois trechos foi reproduzido localmente com a entrada do teste:
- stop words `['a', 'an', 'the']`: os dois devolvem `[['This', 'is', 'test'], ['This', 'is', 'apple'], ['This', 'is', 'dog']]`;
- stop words `['a', 'an', 'the', 'This', 'is']`: o canônico devolve `[['is', 'test'], ...]` e o refatorado devolve `[['test'], ...]`.
