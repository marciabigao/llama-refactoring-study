# ClassEval_62 (iteração 4) — NLPDataProcessor

**Refatorações declaradas pelo modelo:** Replace Magic Number with Symbolic Constant, Replace Temp with Query, Replace Loop with Pipeline, Self-Encapsulate Field

**Testes que falharam:** 1 de 11

- `candidate.NLPDataProcessorTestRemove.test_remove_stop_words_5` (failure):
  ```
  Traceback (most recent call last):
    File "/tmp/ce_vz8u8tpt/candidate.py", line 67, in test_remove_stop_words_5
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
@@ -1,20 +1,16 @@
 class NLPDataProcessor:
 
+    DEFAULT_STOP_WORDS = ('a', 'an', 'the')
+
     def construct_stop_word_list(self):
-        stop_word_list = ['a', 'an', 'the']
-        return stop_word_list
+        return list(self.DEFAULT_STOP_WORDS)
 
     def remove_stop_words(self, string_list, stop_word_list):
+        stop_word_set = set(stop_word_list)
         answer = []
         for string in string_list:
-            string_split = string.split()
-            for word in string_split:
-                if word in stop_word_list:
-                    string_split.remove(word)
-            answer.append(string_split)
+            answer.append([word for word in string.split() if word not in stop_word_set])
         return answer
 
     def process(self, string_list):
-        stop_word_list = self.construct_stop_word_list()
-        words_list = self.remove_stop_words(string_list, stop_word_list)
-        return words_list
+        return self.remove_stop_words(string_list, self.construct_stop_word_list())
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

    DEFAULT_STOP_WORDS = ('a', 'an', 'the')

    def construct_stop_word_list(self):
        return list(self.DEFAULT_STOP_WORDS)

    def remove_stop_words(self, string_list, stop_word_list):
        stop_word_set = set(stop_word_list)
        answer = []
        for string in string_list:
            answer.append([word for word in string.split() if word not in stop_word_set])
        return answer

    def process(self, string_list):
        return self.remove_stop_words(string_list, self.construct_stop_word_list())
```

## Sua análise (preencher)

- O que o código original garantia?
- O que a refatoração mudou?
- Qual refatoração causou o desvio e por quê (ex.: colapsou um ramo, perdeu um return)?
