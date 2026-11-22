# ClassEval_57 (iteração 4): candidato à Figura 5

Flake8: 21 → 12 avisos · Pylint: 23 → 15 · δ Cognitive Complexity: -41 · δ NcLOC: -10

```diff
--- canonical
+++ qwen_refactored
@@ -2,99 +2,84 @@
 
 
 class MetricsCalculator2:
+    RANKING_OFFSET = 1
+    RANKING_DIVISOR_INCREMENT = 1
+
     def __init__(self):
         pass
 
     @staticmethod
-    def mrr(data):
+    def _calculate_ranking_array(sub_list):
+        length = len(sub_list)
+        return 1.0 / (np.array(list(range(length))) + MetricsCalculator2.RANKING_DIVISOR_INCREMENT)
+
+    @staticmethod
+    def _calculate_mr(sub_list, total_num):
+        if total_num == 0:
+            return 0.0
+        ranking_array = MetricsCalculator2._calculate_ranking_array(sub_list)
+        mr_np = sub_list * ranking_array
+        for team in mr_np:
+            if team > 0:
+                return team
+        return 0.0
+
+    @staticmethod
+    def _calculate_ap(sub_list, total_num):
+        if total_num == 0:
+            return 0.0
+        ranking_array = MetricsCalculator2._calculate_ranking_array(sub_list)
+        right_ranking_list = []
+        count = 1
+        for t in sub_list:
+            if t == 0:
+                right_ranking_list.append(0)
+            else:
+                right_ranking_list.append(count)
+                count += 1
+        return np.sum(np.array(right_ranking_list) * ranking_array) / total_num
+
+    @staticmethod
+    def _validate_data_type(data):
         if type(data) != list and type(data) != tuple:
             raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
+
+    @staticmethod
+    def mrr(data):
+        MetricsCalculator2._validate_data_type(data)
 
         if len(data) == 0:
             return 0.0, [0.0]
         if type(data) == tuple:
             (sub_list, total_num) = data
             sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-                mr_np = sub_list * ranking_array
-
-                mr = 0.0
-                for team in mr_np:
-                    if team > 0:
-                        mr = team
-                        break
-                return mr, [mr]
+            mr = MetricsCalculator2._calculate_mr(sub_list, total_num)
+            return mr, [mr]
 
         if type(data) == list:
             separate_result = []
             for (sub_list, total_num) in data:
                 sub_list = np.array(sub_list)
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
+                mr = MetricsCalculator2._calculate_mr(sub_list, total_num)
                 separate_result.append(mr)
             return np.mean(separate_result), separate_result
 
     @staticmethod
     def map(data):
-        if type(data) != list and type(data) != tuple:
-            raise Exception("the input must be a tuple([0,...,1,...],int) or a iteration of list of tuple")
+        MetricsCalculator2._validate_data_type(data)
 
         if len(data) == 0:
             return 0.0, [0.0]
         if type(data) == tuple:
             (sub_list, total_num) = data
             sub_list = np.array(sub_list)
-            if total_num == 0:
-                return 0.0, [0.0]
-            else:
-                ranking_array = 1.0 / (np.array(list(range(len(sub_list)))) + 1)
-
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
+            ap = MetricsCalculator2._calculate_ap(sub_list, total_num)
+            return ap, [ap]
 
         if type(data) == list:
             separate_result = []
             for (sub_list, total_num) in data:
                 sub_list = np.array(sub_list)
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
+                ap = MetricsCalculator2._calculate_ap(sub_list, total_num)
                 separate_result.append(ap)
             return np.mean(separate_result), separate_result
```
