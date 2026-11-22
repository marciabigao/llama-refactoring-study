# ClassEval_16 (iteração 0): legibilidade 0.72 → 0.53 (Δ -0.19)

Testes: passou. Candidato à Figura 7.

## Canônico

```python
class Calculator:
    def __init__(self):
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def calculate(self, expression):
        operand_stack = []
        operator_stack = []
        num_buffer = ''

        for char in expression:
            if char.isdigit() or char == '.':
                num_buffer += char
            else:
                if num_buffer:
                    operand_stack.append(float(num_buffer))
                    num_buffer = ''

                if char in '+-*/^':
                    while (
                            operator_stack and
                            operator_stack[-1] != '(' and
                            self.precedence(operator_stack[-1]) >= self.precedence(char)
                    ):
                        operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

                    operator_stack.append(char)
                elif char == '(':
                    operator_stack.append(char)
                elif char == ')':
                    while operator_stack and operator_stack[-1] != '(':
                        operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

                    operator_stack.pop()

        if num_buffer:
            operand_stack.append(float(num_buffer))

        while operator_stack:
            operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

        return operand_stack[-1] if operand_stack else None

    def precedence(self, operator):
        precedences = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '^': 3
        }
        return precedences.get(operator, 0)

    def apply_operator(self, operand_stack, operator_stack):
        operator = operator_stack.pop()
        if operator == '^':
            operand2 = operand_stack.pop()
            operand1 = operand_stack.pop()
            result = self.operators[operator](operand1, operand2)
            operand_stack.append(result)
        else:
            operand2 = operand_stack.pop()
            operand1 = operand_stack.pop()
            result = self.operators[operator](operand1, operand2)
            operand_stack.append(result)
        return operand_stack, operator_stack
```

## Refatorado pelo Qwen

```python
class Calculator:
    OPERATORS = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '/': lambda x, y: x / y,
        '^': lambda x, y: x ** y
    }

    PRECEDENCES = {
        '+': 1,
        '-': 1,
        '*': 2,
        '/': 2,
        '^': 3
    }

    def __init__(self):
        self._operators = dict(self.OPERATORS)
        self._precedences = dict(self.PRECEDENCES)

    def calculate(self, expression):
        operand_stack = []
        operator_stack = []
        num_buffer = ''

        for char in expression:
            if char.isdigit() or char == '.':
                num_buffer += char
            else:
                self._flush_num_buffer(num_buffer, operand_stack)
                num_buffer = ''

                if char in '+-*/^':
                    self._apply_precedence(operand_stack, operator_stack, char)
                    operator_stack.append(char)
                elif char == '(':
                    operator_stack.append(char)
                elif char == ')':
                    self._apply_closure(operand_stack, operator_stack)
                    operator_stack.pop()

        if num_buffer:
            operand_stack.append(float(num_buffer))

        self._finalize_operation(operand_stack, operator_stack)

        return operand_stack[-1] if operand_stack else None

    def precedence(self, operator):
        return self._precedences.get(operator, 0)

    def apply_operator(self, operand_stack, operator_stack):
        operator = operator_stack.pop()
        operand2 = operand_stack.pop()
        operand1 = operand_stack.pop()
        result = self._operators[operator](operand1, operand2)
        operand_stack.append(result)
        return operand_stack, operator_stack

    def _flush_num_buffer(self, num_buffer, operand_stack):
        if num_buffer:
            operand_stack.append(float(num_buffer))

    def _apply_precedence(self, operand_stack, operator_stack, current_operator):
        while (
                operator_stack and
                operator_stack[-1] != '(' and
                self.precedence(operator_stack[-1]) >= self.precedence(current_operator)
        ):
            operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

    def _apply_closure(self, operand_stack, operator_stack):
        while operator_stack and operator_stack[-1] != '(':
            operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

    def _finalize_operation(self, operand_stack, operator_stack):
        while operator_stack:
            operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)
```
