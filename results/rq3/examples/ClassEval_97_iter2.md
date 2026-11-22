# ClassEval_97 (iteração 2): legibilidade 0.38 → 0.62 (Δ +0.24)

Testes: passou. Candidato à Figura 7.

## Canônico

```python
class Words2Numbers:

    def __init__(self):
        self.numwords = {}
        self.units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
        ]
        self.tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        self.scales = ["hundred", "thousand", "million", "billion", "trillion"]

        self.numwords["and"] = (1, 0)
        for idx, word in enumerate(self.units):
            self.numwords[word] = (1, idx)
        for idx, word in enumerate(self.tens):
            self.numwords[word] = (1, idx * 10)
        for idx, word in enumerate(self.scales):
            self.numwords[word] = (10 ** (idx * 3 or 2), 0)

        self.ordinal_words = {'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8, 'ninth': 9, 'twelfth': 12}
        self.ordinal_endings = [('ieth', 'y'), ('th', '')]

    def text2int(self, textnum):
        textnum = textnum.replace('-', ' ')

        current = result = 0
        curstring = ""
        onnumber = False
        for word in textnum.split():
            if word in self.ordinal_words:
                scale, increment = (1, self.ordinal_words[word])
                current = current * scale + increment
                onnumber = True
            else:
                for ending, replacement in self.ordinal_endings:
                    if word.endswith(ending):
                        word = "%s%s" % (word[:-len(ending)], replacement)

                if word not in self.numwords:
                    if onnumber:
                        curstring += repr(result + current) + " "
                    curstring += word + " "
                    result = current = 0
                    onnumber = False
                else:
                    scale, increment = self.numwords[word]
                    current = current * scale + increment
                    if scale > 100:
                        result += current
                        current = 0
                    onnumber = True

        if onnumber:
            curstring += repr(result + current)

        return curstring

    def is_valid_input(self, textnum):

        textnum = textnum.replace('-', ' ')

        for word in textnum.split():
            if word in self.ordinal_words:
                continue
            else:
                for ending, replacement in self.ordinal_endings:
                    if word.endswith(ending):
                        word = "%s%s" % (word[:-len(ending)], replacement)

                if word not in self.numwords:
                    return False

        return True
```

## Refatorado pelo Qwen

```python
class Words2Numbers:

    # Symbolic constants to replace magic numbers
    HUNDRED = 100
    TENS_MULTIPLIER = 10
    SCALE_CUBES_EXPONENT = 3
    SCALE_DEFAULT_EXPONENT = 2
    SCALE_MINIMUM = 1

    def __init__(self):
        self.__numwords = {}
        self.__units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
        ]
        self.__tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        self.__scales = ["hundred", "thousand", "million", "billion", "trillion"]

        self.__numwords["and"] = (1, 0)
        for idx, word in enumerate(self.__units):
            self.__numwords[word] = (1, idx)
        for idx, word in enumerate(self.__tens):
            self.__numwords[word] = (1, idx * self.TENS_MULTIPLIER)
        for idx, word in enumerate(self.__scales):
            self.__numwords[word] = (10 ** (idx * self.SCALE_CUBES_EXPONENT or self.SCALE_DEFAULT_EXPONENT), 0)

        self.__ordinal_words = {'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8, 'ninth': 9, 'twelfth': 12}
        self.__ordinal_endings = [('ieth', 'y'), ('th', '')]

    @property
    def numwords(self):
        return self.__numwords

    @property
    def ordinal_words(self):
        return self.__ordinal_words

    @property
    def ordinal_endings(self):
        return self.__ordinal_endings

    def _strip_ordinal(self, word):
        """Strip ordinal suffixes from a word and return the base form."""
        for ending, replacement in self.__ordinal_endings:
            if word.endswith(ending):
                word = "%s%s" % (word[:-len(ending)], replacement)
        return word

    def _is_known_word(self, word):
        """Check if a word is a known number word."""
        return word in self.__numwords

    def text2int(self, textnum):
        textnum = textnum.replace('-', ' ')

        current = result = 0
        curstring = ""
        onnumber = False

        for word in textnum.split():
            if word in self.__ordinal_words:
                scale, increment = (1, self.__ordinal_words[word])
                current = current * scale + increment
                onnumber = True
            else:
                word = self._strip_ordinal(word)

                if not self._is_known_word(word):
                    if onnumber:
                        curstring += repr(result + current) + " "
                    curstring += word + " "
                    result = current = 0
                    onnumber = False
                else:
                    scale, increment = self.__numwords[word]
                    current = current * scale + increment
                    if scale > self.HUNDRED:
                        result += current
                        current = 0
                    onnumber = True

        if onnumber:
            curstring += repr(result + current)

        return curstring

    def is_valid_input(self, textnum):
        textnum = textnum.replace('-', ' ')

        for word in textnum.split():
            if word in self.__ordinal_words:
                continue

            word = self._strip_ordinal(word)

            if not self._is_known_word(word):
                return False

        return True
```
