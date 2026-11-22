# ClassEval_64 (iteração 2): legibilidade 0.73 → 0.52 (Δ -0.21)

Testes: passou. Candidato à Figura 7.

## Canônico

```python
class NumberConverter:
    @staticmethod
    def decimal_to_binary(decimal_num):
        binary_num = bin(decimal_num)[2:]
        return binary_num

    @staticmethod
    def binary_to_decimal(binary_num):
        decimal_num = int(binary_num, 2)
        return decimal_num

    @staticmethod
    def decimal_to_octal(decimal_num):
        octal_num = oct(decimal_num)[2:]
        return octal_num

    @staticmethod
    def octal_to_decimal(octal_num):
        decimal_num = int(octal_num, 8)
        return decimal_num

    @staticmethod
    def decimal_to_hex(decimal_num):
        hex_num = hex(decimal_num)[2:]
        return hex_num

    @staticmethod
    def hex_to_decimal(hex_num):
        decimal_num = int(hex_num, 16)
        return decimal_num
```

## Refatorado pelo Qwen

```python
class NumberConverter:
    BIN_PREFIX = '0b'
    OCT_PREFIX = '0o'
    HEX_PREFIX = '0x'

    @staticmethod
    def decimal_to_binary(decimal_num):
        return NumberConverter._decimal_to_base_string(decimal_num, 2, NumberConverter.BIN_PREFIX)

    @staticmethod
    def binary_to_decimal(binary_num):
        return NumberConverter._base_string_to_decimal(binary_num, 2)

    @staticmethod
    def decimal_to_octal(decimal_num):
        return NumberConverter._decimal_to_base_string(decimal_num, 8, NumberConverter.OCT_PREFIX)

    @staticmethod
    def octal_to_decimal(octal_num):
        return NumberConverter._base_string_to_decimal(octal_num, 8)

    @staticmethod
    def decimal_to_hex(decimal_num):
        return NumberConverter._decimal_to_base_string(decimal_num, 16, NumberConverter.HEX_PREFIX)

    @staticmethod
    def hex_to_decimal(hex_num):
        return NumberConverter._base_string_to_decimal(hex_num, 16)

    @staticmethod
    def _decimal_to_base_string(decimal_num, base, prefix):
        return f"{decimal_num:o}" if base == 8 else f"{decimal_num:x}" if base == 16 else f"{decimal_num:b}"

    @staticmethod
    def _base_string_to_decimal(plain_string, base):
        return int(plain_string, base)
```
