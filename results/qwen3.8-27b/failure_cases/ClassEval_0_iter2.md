# ClassEval_0 (iteração 2) — AccessGatewayFilter

**Refatorações declaradas pelo modelo:** Replace Magic Number with Symbolic Constant, Introduce Explaining Variable, Remove Dead Code, Consolidate Duplicate Conditional Fragments, Replace Loop with Pipeline, Add Parameter, Replace Nested Conditional with Guard Clauses, Remove Control Flag, Encapsulate Collection, Inline Temp, Separate Query from Modifier, Rename Variable, Extract Method, Replace Method with Method Object, Encapsulate Field, Self-Encapsulate Field, Introduce Null Object, Parameterize Method, Preserve Whole Object, Replace Parameter with Method Call, Replace Parameter with Explicit Methods, Replace Data Value with Object, Inline Method, Remove Parameter, Decompose Conditional, Consolidate Conditional Expression, Remove Assignments to Parameters, Split Temporary Variable, Replace Temp with Query

**Testes que falharam:** 1 de 19

- `candidate.AccessGatewayFilterTestFilter.test_filter_7` (failure):
  ```
  Traceback (most recent call last):
    File "/tmp/ce_wbe6ztzg/candidate.py", line 109, in test_filter_7
      self.assertIsNone(res)
  AssertionError: False is not None
  ```

## Diff (canônico -> Llama)

```diff
--- canonical
+++ llama_refactored
@@ -3,6 +3,10 @@
 
 
 class AccessGatewayFilter:
+
+    PUBLIC_PATH_PREFIXES = ("/api", "/login")
+    MAX_USER_LEVEL = 2
+    JWT_EXPIRATION_DAYS = 3
 
     def __init__(self):
         pass
@@ -16,27 +20,29 @@
 
         try:
             token = self.get_jwt_user(request)
+            if token is None:
+                return False
             user = token['user']
-            if user['level'] > 2:
+            if user['level'] > self.MAX_USER_LEVEL:
                 self.set_current_user_info_and_log(user)
                 return True
-        except:
+            return False
+        except Exception:
             return False
 
     def is_start_with(self, request_uri):
-        start_with = ["/api", '/login']
-        for s in start_with:
-            if request_uri.startswith(s):
-                return True
-        return False
+        return any(request_uri.startswith(prefix) for prefix in self.PUBLIC_PATH_PREFIXES)
 
     def get_jwt_user(self, request):
         token = request['headers']['Authorization']
         user = token['user']
-        if token['jwt'].startswith(user['name']):
-            jwt_str_date = token['jwt'].split(user['name'])[1]
+        if not isinstance(token, dict) or 'jwt' not in token:
+            return token
+        jwt_val = token['jwt']
+        if isinstance(jwt_val, str) and jwt_val.startswith(user['name']):
+            jwt_str_date = jwt_val.split(user['name'])[1]
             jwt_date = datetime.datetime.strptime(jwt_str_date, "%Y-%m-%d")
-            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=3):
+            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=self.JWT_EXPIRATION_DAYS):
                 return None
         return token
 
```

## Código canônico

```python
import logging
import datetime


class AccessGatewayFilter:

    def __init__(self):
        pass

    def filter(self, request):
        request_uri = request['path']
        method = request['method']

        if self.is_start_with(request_uri):
            return True

        try:
            token = self.get_jwt_user(request)
            user = token['user']
            if user['level'] > 2:
                self.set_current_user_info_and_log(user)
                return True
        except:
            return False

    def is_start_with(self, request_uri):
        start_with = ["/api", '/login']
        for s in start_with:
            if request_uri.startswith(s):
                return True
        return False

    def get_jwt_user(self, request):
        token = request['headers']['Authorization']
        user = token['user']
        if token['jwt'].startswith(user['name']):
            jwt_str_date = token['jwt'].split(user['name'])[1]
            jwt_date = datetime.datetime.strptime(jwt_str_date, "%Y-%m-%d")
            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=3):
                return None
        return token

    def set_current_user_info_and_log(self, user):
        host = user['address']
        logging.log(msg=user['name'] + host + str(datetime.datetime.now()), level=1)
```

## Código refatorado pelo Llama

```python
import logging
import datetime


class AccessGatewayFilter:

    PUBLIC_PATH_PREFIXES = ("/api", "/login")
    MAX_USER_LEVEL = 2
    JWT_EXPIRATION_DAYS = 3

    def __init__(self):
        pass

    def filter(self, request):
        request_uri = request['path']
        method = request['method']

        if self.is_start_with(request_uri):
            return True

        try:
            token = self.get_jwt_user(request)
            if token is None:
                return False
            user = token['user']
            if user['level'] > self.MAX_USER_LEVEL:
                self.set_current_user_info_and_log(user)
                return True
            return False
        except Exception:
            return False

    def is_start_with(self, request_uri):
        return any(request_uri.startswith(prefix) for prefix in self.PUBLIC_PATH_PREFIXES)

    def get_jwt_user(self, request):
        token = request['headers']['Authorization']
        user = token['user']
        if not isinstance(token, dict) or 'jwt' not in token:
            return token
        jwt_val = token['jwt']
        if isinstance(jwt_val, str) and jwt_val.startswith(user['name']):
            jwt_str_date = jwt_val.split(user['name'])[1]
            jwt_date = datetime.datetime.strptime(jwt_str_date, "%Y-%m-%d")
            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=self.JWT_EXPIRATION_DAYS):
                return None
        return token

    def set_current_user_info_and_log(self, user):
        host = user['address']
        logging.log(msg=user['name'] + host + str(datetime.datetime.now()), level=1)
```

## Sua análise (preencher)

- O que o código original garantia?
- O que a refatoração mudou?
- Qual refatoração causou o desvio e por quê (ex.: colapsou um ramo, perdeu um return)?
