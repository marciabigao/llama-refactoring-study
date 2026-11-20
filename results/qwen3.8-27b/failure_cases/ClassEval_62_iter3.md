# ClassEval_62 (iteração 3) — NLPDataProcessor

**Refatorações declaradas pelo modelo:** Extract Method, Remove Dead Code, Introduce Explaining Variable, Replace Loop with Pipeline

**Testes que falharam:** 1 de 11

- `candidate.NLPDataProcessorTestRemove.test_remove_stop_words_5` (failure):
  ```
  Traceback (most recent call last):
    File "/tmp/ce_gpnqrcec/candidate.py", line 73, in test_remove_stop_words_5
      self.assertEqual(words_list, expected_words_list)
  AssertionError: Lists differ: [['test'], ['apple'], ['dog']] != [['is', 'test'], ['is', 'apple'], ['is', 'dog']]
  
  First differing element 0:
  ['test']
  ['is', 'test']
  
  - [['test'], ['apple'], ['dog']]
  + [['is', 'test'], ['is', 'apple'], ['is', 'dog']]
  ?   ++++++          ++++++           ++++++
  ```

## Diff (canônico -> Llama)

```diff
--- canonical
+++ llama_refactored
@@ -1,17 +1,19 @@
 class NLPDataProcessor:
 
+    DEFAULT_STOP_WORDS = ['a', 'an', 'the']
+
     def construct_stop_word_list(self):
-        stop_word_list = ['a', 'an', 'the']
-        return stop_word_list
+        return self.DEFAULT_STOP_WORDS
 
     def remove_stop_words(self, string_list, stop_word_list):
         answer = []
         for string in string_list:
             string_split = string.split()
+            filtered_words = []
             for word in string_split:
-                if word in stop_word_list:
-                    string_split.remove(word)
-            answer.append(string_split)
+                if word not in stop_word_list:
+                    filtered_words.append(word)
+            answer.append(filtered_words)
         return answer
 
     def process(self, string_list):
```

## Código canônico

```python
class NLPDataProcessor:

    def construct_stop_word_list(self):
        stop_word_list = ['a', 'an', 'the']
        return stop_word_list

    def remove_stop_words(self, string_list, stop_word_list):
        answer = []
        for string in string_list:
            string_split = string.split()
            for word in string_split:
                if word in stop_word_list:
                    string_split.remove(word)
            answer.append(string_split)
        return answer

    def process(self, string_list):
        stop_word_list = self.construct_stop_word_list()
        words_list = self.remove_stop_words(string_list, stop_word_list)
        return words_list
```

## Código refatorado pelo Llama

```python
class NLPDataProcessor:

    DEFAULT_STOP_WORDS = ['a', 'an', 'the']

    def construct_stop_word_list(self):
        return self.DEFAULT_STOP_WORDS

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

    def process(self, string_list):
        stop_word_list = self.construct_stop_word_list()
        words_list = self.remove_stop_words(string_list, stop_word_list)
        return words_list
```

## Sua análise (preencher)

- O que o código original garantia?
- O que a refatoração mudou?
- Qual refatoração causou o desvio e por quê (ex.: colapsou um ramo, perdeu um return)?
