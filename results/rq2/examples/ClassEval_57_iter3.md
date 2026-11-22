# ClassEval_57 (iteração 3): candidato à Figura 5

Flake8: 21 → 10 avisos · Pylint: 23 → 12 · δ Cognitive Complexity: -44 · δ NcLOC: -7

```diff
--- canonical
+++ qwen_refactored
@@ -2,99 +2,88 @@
 
 
 class MetricsCalculator2:
+    RANKING_ARRAY_OFFSET = 1
+
     def __init__(self):
         pass
 
     @staticmethod
-    def mrr(data):
+    def _compute_ranking_array(sub_list):
+        length = len(sub_list)
+        return 1.0 / (np.array(list(range(length))) + MetricsCalculator2.RANKING_ARRAY_OFFSET)
+
+    @staticmethod
+    def _compute_mr(sub_list, total_num):
+        if total_num == 0:
+            return 0.0
+        ranking_array = MetricsCalculator2._compute_ranking_array(sub_list)
+        mr_np = sub_list * ranking_array
+        for team in mr_np:
+            if team > 0:
+                return float(team)
+        return 0.0
+
+    @staticmethod
+    def _compute_ap(sub_list, total_num):
+        if total_num == 0:
+            return 0.0
+        ranking_array = MetricsCalculator2._compute_ranking_array(sub_list)
+        right_ranking_list = MetricsCalculator2._compute_right_ranking_list(sub_list)
+        return float(np.sum(np.array(right_ranking_list) * ranking_array) / total_num)
+
+    @staticmethod
+    def _compute_right_ranking_list(sub_list):
+        right_ranking_list = []
+        count = 1
+        for t in sub_list:
+            if t == 0:
+                right_ranking_list.append(0)
+            else:
+                right_ranking_list.append(count)
+                count += 1
+        return right_ranking_list
+
+    @staticmethod
+    def _validate_input(data):
         if type(data) != list and type(data) != tuple:
             raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
-
         if len(data) == 0:
             return 0.0, [0.0]
-        if type(data) == tuple:
-            (sub_list, total_num) = data
+
+    @staticmethod
+    def mrr(data):
+        validation_result = MetricsCalculator2._validate_input(data)
+        if validation_result is not None:
+            return validation_result
+
+        if isinstance(data, tuple):
+            sub_list, total_num = data
             sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-                mr_np = sub_list * ranking_array
+            mr = MetricsCalculator2._compute_mr(sub_list, total_num)
+            return mr, [mr]
 
-                mr = 0.0
-                for team in mr_np:
-                    if team > 0:
-                        mr = team
-                        break
-                return mr, [mr]
-
-        if type(data) == list:
-            separate_result = []
-            for (sub_list, total_num) in data:
-                sub_list = np.array(sub_list)
-
-                if total_num == 0:
-                    mr = 0.0
-                else:
-                    ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-                    mr_np = sub_list * ranking_array
-
-                    mr = 0.0
-                    for team in mr_np:
-                        if team > 0:
-                            mr = team
-                            break
-
-                separate_result.append(mr)
-            return np.mean(separate_result), separate_result
+        if isinstance(data, list):
+            separate_result = [
+                MetricsCalculator2._compute_mr(np.array(sub_list), total_num)
+                for (sub_list, total_num) in data
+            ]
+            return float(np.mean(separate_result)), separate_result
 
     @staticmethod
     def map(data):
-        if type(data) != list and type(data) != tuple:
-            raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
+        validation_result = MetricsCalculator2._validate_input(data)
+        if validation_result is not None:
+            return validation_result
 
-        if len(data) == 0:
-            return 0.0, [0.0]
-        if type(data) == tuple:
-            (sub_list, total_num) = data
+        if isinstance(data, tuple):
+            sub_list, total_num = data
             sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
+            ap = MetricsCalculator2._compute_ap(sub_list, total_num)
+            return ap, [ap]
 
-                right_ranking_list = []
-                count = 1
-                for t in sub_list:
-                    if t == 0:
-                        right_ranking_list.append(0)
-                    else:
-                        right_ranking_list.append(count)
-                        count += 1
-
-                ap = np.sum(np.array(right_ranking_list) * ranking_array) / total_num
-                return ap, [ap]
-
-        if type(data) == list:
-            separate_result = []
-            for (sub_list, total_num) in data:
-                sub_list = np.array(sub_list)
-
-                if total_num == 0:
-                    ap = 0.0
-                else:
-                    ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-
-                    right_ranking_list = []
-                    count = 1
-                    for t in sub_list:
-                        if t == 0:
-                            right_ranking_list.append(0)
-                        else:
-                            right_ranking_list.append(count)
-                            count += 1
-
-                    ap = np.sum(np.array(right_ranking_list) * ranking_array) / total_num
-
-                separate_result.append(ap)
-            return np.mean(separate_result), separate_result
+        if isinstance(data, list):
+            separate_result = [
+                MetricsCalculator2._compute_ap(np.array(sub_list), total_num)
+                for (sub_list, total_num) in data
+            ]
+            return float(np.mean(separate_result)), separate_result
```
