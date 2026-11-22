# ClassEval_76 (iteração 3): legibilidade 0.83 → 0.66 (Δ -0.18)

Testes: passou. Candidato à Figura 7.

## Canônico

```python
class SignInSystem:
    def __init__(self):
        self.users = {}

    def add_user(self, username):
        if username in self.users:
            return False
        else:
            self.users[username] = False
            return True

    def sign_in(self, username):
        if username not in self.users:
            return False
        else:
            self.users[username] = True
            return True

    def check_sign_in(self, username):
        if username not in self.users:
            return False
        else:
            if self.users[username]:
                return True
            else:
                return False

    def all_signed_in(self):
        if all(self.users.values()):
            return True
        else:
            return False

    def all_not_signed_in(self):
        not_signed_in_users = []
        for username, signed_in in self.users.items():
            if not signed_in:
                not_signed_in_users.append(username)
        return not_signed_in_users
```

## Refatorado pelo Qwen

```python
class SignInSystem:
    NOT_SIGNED_IN = False
    SIGNED_IN = True

    def __init__(self):
        self._users = {}

    def add_user(self, username):
        if self._is_user_present(username):
            return False
        self._users[username] = self.SIGN_IN_STATE_NOT_SIGNED_IN
        return True

    def sign_in(self, username):
        if not self._is_user_present(username):
            return False
        self._users[username] = self.SIGN_IN_STATE_SIGNED_IN
        return True

    def check_sign_in(self, username):
        return self._is_user_present(username) and self._is_signed_in(username)

    def all_signed_in(self):
        return all(self._users.values())

    def all_not_signed_in(self):
        return [username for username, signed_in in self._users.items() if not signed_in]

    @property
    def users(self):
        return self._users.copy()

    def _is_user_present(self, username):
        return username in self._users

    def _is_signed_in(self, username):
        return self._users[username] == self.SIGN_IN_STATE_SIGNED_IN

    SIGN_IN_STATE_SIGNED_IN = True
    SIGN_IN_STATE_NOT_SIGNED_IN = False
```
