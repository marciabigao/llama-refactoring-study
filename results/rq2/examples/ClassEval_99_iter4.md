# ClassEval_99 (iteração 4): candidato à Figura 5

Flake8: 15 → 7 avisos · Pylint: 15 → 10 · δ Cognitive Complexity: +2 · δ NcLOC: +8

```diff
--- canonical
+++ qwen_refactored
@@ -6,33 +6,44 @@
         self.file_name = file_name
 
     def read_zip_file(self):
+        return self._open_zip_file(self.file_name)
+
+    def extract_all(self, output_path):
+        return self._extract_files(output_path, None)
+
+    def extract_file(self, file_name, output_path):
+        return self._extract_files(output_path, file_name)
+
+    def create_zip_file(self, files, output_file_name):
+        return self._create_zip_file(files, output_file_name)
+
+    def _open_zip_file(self, file_name):
         try:
-            zip_file = zipfile.ZipFile(self.file_name, 'r')
-            return zip_file
-        except:
+            return zipfile.ZipFile(file_name, 'r')
+        except Exception:
             return None
 
-    def extract_all(self, output_path):
+    def _extract_files(self, output_path, file_name=None):
         try:
-            with zipfile.ZipFile(self.file_name, 'r') as zip_file:
-                zip_file.extractall(output_path)
-            return True
-        except:
+            zip_file = self._open_zip_file(self.file_name)
+            if zip_file is None:
+                return False
+            try:
+                if file_name is None:
+                    zip_file.extractall(output_path)
+                else:
+                    zip_file.extract(file_name, output_path)
+                return True
+            finally:
+                zip_file.close()
+        except Exception:
             return False
 
-    def extract_file(self, file_name, output_path):
-        try:
-            with zipfile.ZipFile(self.file_name, 'r') as zip_file:
-                zip_file.extract(file_name, output_path)
-            return True
-        except:
-            return False
-
-    def create_zip_file(self, files, output_file_name):
+    def _create_zip_file(self, files, output_file_name):
         try:
             with zipfile.ZipFile(output_file_name, 'w') as zip_file:
                 for file in files:
                     zip_file.write(file)
             return True
-        except:
+        except Exception:
             return False
```
