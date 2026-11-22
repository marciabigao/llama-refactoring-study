# ClassEval_58 (iteração 4): candidato à Figura 5

Flake8: 19 → 10 avisos · Pylint: 35 → 8 · δ Cognitive Complexity: -61 · δ NcLOC: -17

```diff
--- canonical
+++ qwen_refactored
@@ -10,56 +10,39 @@
 
     def generate_mine_sweeper_map(self):
         arr = [[0 for row in range(self.n)] for column in range(self.n)]
-        for num in range(self.k):
-            x = random.randint(0, self.n-1)
-            y = random.randint(0, self.n-1)
+        for _ in range(self.k):
+            x, y = self._random_position()
             arr[y][x] = 'X'
-            if (x >=0 and x <= self.n-2) and (y >= 0 and y <= self.n-1):
-                if arr[y][x+1] != 'X':
-                    arr[y][x+1] += 1
-            if (x >=1 and x <= self.n-1) and (y >= 0 and y <= self.n-1):
-                if arr[y][x-1] != 'X':
-                    arr[y][x-1] += 1
-            if (x >= 1 and x <= self.n-1) and (y >= 1 and y <= self.n-1):
-                if arr[y-1][x-1] != 'X':
-                    arr[y-1][x-1] += 1
-    
-            if (x >= 0 and x <= self.n-2) and (y >= 1 and y <= self.n-1):
-                if arr[y-1][x+1] != 'X':
-                    arr[y-1][x+1] += 1 
-            if (x >= 0 and x <= self.n-1) and (y >= 1 and y <= self.n-1):
-                if arr[y-1][x] != 'X':
-                    arr[y-1][x] += 1
-    
-            if (x >=0 and x <= self.n-2) and (y >= 0 and y <= self.n-2):
-                if arr[y+1][x+1] != 'X':
-                    arr[y+1][x+1] += 1
-            if (x >= 1 and x <= self.n-1) and (y >= 0 and y <= self.n-2):
-                if arr[y+1][x-1] != 'X':
-                    arr[y+1][x-1] += 1
-            if (x >= 0 and x <= self.n-1) and (y >= 0 and y <= self.n-2):
-                if arr[y+1][x] != 'X':
-                    arr[y+1][x] += 1
-        return arr
-    
-    def generate_playerMap(self):
-        arr = [['-' for row in range(self.n)] for column in range(self.n)]
+            self._increment_neighbors(arr, x, y)
         return arr
 
-    def check_won(self, map):
+    def _random_position(self):
+        return random.randint(0, self.n - 1), random.randint(0, self.n - 1)
+
+    def _is_valid_position(self, x, y):
+        return 0 <= x < self.n and 0 <= y < self.n
+
+    def _increment_neighbors(self, arr, x, y):
+        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
+            nx, ny = x + dx, y + dy
+            if self._is_valid_position(nx, ny) and arr[ny][nx] != 'X':
+                arr[ny][nx] += 1
+
+    def generate_playerMap(self):
+        return [['-' for _ in range(self.n)] for _ in range(self.n)]
+
+    def check_won(self, player_map):
         for i in range(self.n):
             for j in range(self.n):
-                if map[i][j] == '-' and self.minesweeper_map[i][j] != 'X':
+                if player_map[i][j] == '-' and self.minesweeper_map[i][j] != 'X':
                     return False
         return True
-    
+
     def sweep(self, x, y):
-
-        if (self.minesweeper_map[x][y] == 'X'):
+        if self.minesweeper_map[x][y] == 'X':
             return False
-        else:
-            self.player_map[x][y] = self.minesweeper_map[x][y]
-            self.score += 1
-            if self.check_won(self.player_map) == True:
-                return True
-            return self.player_map
+        self.player_map[x][y] = self.minesweeper_map[x][y]
+        self.score += 1
+        if self.check_won(self.player_map):
+            return True
+        return self.player_map
```
