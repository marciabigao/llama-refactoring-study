# ClassEval_57 (iteração 1): candidato à Figura 5

Flake8: 21 → 13 avisos · Pylint: 23 → 9 · δ Cognitive Complexity: -41 · δ NcLOC: -6

```diff
--- canonical
+++ qwen_refactored
@@ -2,99 +2,100 @@
 
 
 class MetricsCalculator2:
+    RELEVANT = 1
+    NOT_RELEVANT = 0
+    ZERO = 0
+    ONE = 1
+
     def __init__(self):
         pass
 
     @staticmethod
+    def _build_ranking_array(length):
+        """Build a ranking array where position i has value 1/(i+1)."""
+        return 1.0 / (np.array(list(range(length))) + MetricsCalculator2.ONE)
+
+    @staticmethod
+    def _find_first_positive_mrr(mr_np):
+        """Find the first positive MRR value in the array."""
+        for value in mr_np:
+            if value > MetricsCalculator2.ZERO:
+                return value
+        return MetricsCalculator2.ZERO
+
+    @staticmethod
+    def _calculate_mrr_single(sub_list, total_num):
+        """Calculate MRR for a single relevance list and total number of relevant items."""
+        if total_num == MetricsCalculator2.ZERO:
+            return MetricsCalculator2.ZERO * 1.0
+
+        sub_list = np.array(sub_list)
+        ranking_array = MetricsCalculator2._build_ranking_array(len(sub_list))
+        mr_np = sub_list * ranking_array
+        return MetricsCalculator2._find_first_positive_mrr(mr_np)
+
+    @staticmethod
+    def _build_right_ranking_list(sub_list):
+        """Build a list of right rankings where relevant items get incremental counts."""
+        right_ranking_list = []
+        count = MetricsCalculator2.ONE
+        for t in sub_list:
+            if t == MetricsCalculator2.NOT_RELEVANT:
+                right_ranking_list.append(MetricsCalculator2.ZERO)
+            else:
+                right_ranking_list.append(count)
+                count += 1
+        return right_ranking_list
+
+    @staticmethod
+    def _calculate_map_single(sub_list, total_num):
+        """Calculate MAP for a single relevance list and total number of relevant items."""
+        if total_num == MetricsCalculator2.ZERO:
+            return MetricsCalculator2.ZERO * 1.0
+
+        sub_list = np.array(sub_list)
+        ranking_array = MetricsCalculator2._build_ranking_array(len(sub_list))
+        right_ranking_list = MetricsCalculator2._build_right_ranking_list(sub_list)
+        return np.sum(np.array(right_ranking_list) * ranking_array) / total_num
+
+    @staticmethod
     def mrr(data):
-        if type(data) != list and type(data) != tuple:
+        """Calculate Mean Reciprocal Rank."""
+        if not isinstance(data, (list, tuple)):
             raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
 
         if len(data) == 0:
-            return 0.0, [0.0]
-        if type(data) == tuple:
+            return MetricsCalculator2.ZERO * 1.0, [MetricsCalculator2.ZERO * 1.0]
+
+        if isinstance(data, tuple):
             (sub_list, total_num) = data
-            sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-                mr_np = sub_list * ranking_array
+            mr = MetricsCalculator2._calculate_mrr_single(sub_list, total_num)
+            return mr, [mr]
 
-                mr = 0.0
-                for team in mr_np:
-                    if team > 0:
-                        mr = team
-                        break
-                return mr, [mr]
-
-        if type(data) == list:
+        if isinstance(data, list):
             separate_result = []
             for (sub_list, total_num) in data:
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
+                mr = MetricsCalculator2._calculate_mrr_single(sub_list, total_num)
                 separate_result.append(mr)
             return np.mean(separate_result), separate_result
 
     @staticmethod
     def map(data):
-        if type(data) != list and type(data) != tuple:
+        """Calculate Mean Average Precision."""
+        if not isinstance(data, (list, tuple)):
             raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
 
         if len(data) == 0:
-            return 0.0, [0.0]
-        if type(data) == tuple:
+            return MetricsCalculator2.ZERO * 1.0, [MetricsCalculator2.ZERO * 1.0]
+
+        if isinstance(data, tuple):
             (sub_list, total_num) = data
-            sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
+            ap = MetricsCalculator2._calculate_map_single(sub_list, total_num)
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
+        if isinstance(data, list):
             separate_result = []
             for (sub_list, total_num) in data:
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
+                ap = MetricsCalculator2._calculate_map_single(sub_list, total_num)
                 separate_result.append(ap)
             return np.mean(separate_result), separate_result
```
