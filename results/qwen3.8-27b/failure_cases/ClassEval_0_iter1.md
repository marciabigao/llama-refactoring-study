# ClassEval_0 (iteração 1) — AccessGatewayFilter

**Refatorações declaradas pelo modelo:** Replace Magic Number with Symbolic Constant, Replace Loop with Pipeline, Replace Nested Conditional with Guard Clauses, Introduce Explaining Variable

**Testes que falharam:** 1 de 19

- `candidate.AccessGatewayFilterTestFilter.test_filter_7` (failure):
  ```
  Traceback (most recent call last):
    File "/tmp/ce_8uqi77xp/candidate.py", line 108, in test_filter_7
      self.assertIsNone(res)
  AssertionError: False is not None
  ```

## Diff (canônico -> Llama)

```diff
--- canonical
+++ llama_refactored
@@ -1,5 +1,11 @@
 import logging
 import datetime
+
+
+ALLOWED_PATH_PREFIXES = ["/api", "/login"]
+USER_LEVEL_THRESHOLD = 2
+JWT_VALIDITY_DAYS = 3
+JWT_DATE_FORMAT = "%Y-%m-%d"
 
 
 class AccessGatewayFilter:
@@ -14,32 +20,31 @@
         if self.is_start_with(request_uri):
             return True
 
-        try:
-            token = self.get_jwt_user(request)
-            user = token['user']
-            if user['level'] > 2:
-                self.set_current_user_info_and_log(user)
-                return True
-        except:
+        token = self.get_jwt_user(request)
+        if token is None:
             return False
 
+        user = token['user']
+        if user['level'] <= USER_LEVEL_THRESHOLD:
+            return False
+
+        self.set_current_user_info_and_log(user)
+        return True
+
     def is_start_with(self, request_uri):
-        start_with = ["/api", '/login']
-        for s in start_with:
-            if request_uri.startswith(s):
-                return True
-        return False
+        return any(request_uri.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)
 
     def get_jwt_user(self, request):
         token = request['headers']['Authorization']
         user = token['user']
         if token['jwt'].startswith(user['name']):
             jwt_str_date = token['jwt'].split(user['name'])[1]
-            jwt_date = datetime.datetime.strptime(jwt_str_date, "%Y-%m-%d")
-            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=3):
+            jwt_date = datetime.datetime.strptime(jwt_str_date, JWT_DATE_FORMAT)
+            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=JWT_VALIDITY_DAYS):
                 return None
         return token
 
     def set_current_user_info_and_log(self, user):
         host = user['address']
-        logging.log(msg=user['name'] + host + str(datetime.datetime.now()), level=1)
+        log_message = user['name'] + host + str(datetime.datetime.now())
+        logging.log(msg=log_message, level=logging.DEBUG)
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


ALLOWED_PATH_PREFIXES = ["/api", "/login"]
USER_LEVEL_THRESHOLD = 2
JWT_VALIDITY_DAYS = 3
JWT_DATE_FORMAT = "%Y-%m-%d"


class AccessGatewayFilter:

    def __init__(self):
        pass

    def filter(self, request):
        request_uri = request['path']
        method = request['method']

        if self.is_start_with(request_uri):
            return True

        token = self.get_jwt_user(request)
        if token is None:
            return False

        user = token['user']
        if user['level'] <= USER_LEVEL_THRESHOLD:
            return False

        self.set_current_user_info_and_log(user)
        return True

    def is_start_with(self, request_uri):
        return any(request_uri.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)

    def get_jwt_user(self, request):
        token = request['headers']['Authorization']
        user = token['user']
        if token['jwt'].startswith(user['name']):
            jwt_str_date = token['jwt'].split(user['name'])[1]
            jwt_date = datetime.datetime.strptime(jwt_str_date, JWT_DATE_FORMAT)
            if datetime.datetime.today() - jwt_date >= datetime.timedelta(days=JWT_VALIDITY_DAYS):
                return None
        return token

    def set_current_user_info_and_log(self, user):
        host = user['address']
        log_message = user['name'] + host + str(datetime.datetime.now())
        logging.log(msg=log_message, level=logging.DEBUG)
```

## Sua análise (preencher)

- O que o código original garantia?
- O que a refatoração mudou?
- Qual refatoração causou o desvio e por quê (ex.: colapsou um ramo, perdeu um return)?
