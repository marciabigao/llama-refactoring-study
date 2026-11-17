"""Lista de refatorações de Fowler usadas no estudo (Tabela 1 do artigo) e normalização de nomes."""
import re
from difflib import get_close_matches

# Ordem e nomes exatamente como na Tabela 1 do artigo.
REFACTORINGS = [
    "Extract Method",
    "Inline Method",
    "Replace Temp with Query",
    "Split Temporary Variable",
    "Remove Assignments to Parameters",
    "Replace Method with Method Object",
    "Encapsulate Field",
    "Encapsulate Collection",
    "Replace Magic Number with Symbolic Constant",
    "Replace Data Value with Object",
    "Self-Encapsulate Field",
    "Decompose Conditional",
    "Consolidate Conditional Expression",
    "Consolidate Duplicate Conditional Fragments",
    "Remove Control Flag",
    "Replace Nested Conditional with Guard Clauses",
    "Introduce Null Object",
    "Add Parameter",
    "Remove Parameter",
    "Separate Query from Modifier",
    "Parameterize Method",
    "Preserve Whole Object",
    "Replace Parameter with Method Call",
    "Replace Parameter with Explicit Methods",
    "Rename Variable",
    "Introduce Explaining Variable",
    "Inline Temp",
    "Remove Dead Code",
    "Replace Loop with Pipeline",
]


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


_KEY_TO_CANON = {_key(n): n for n in REFACTORINGS}


def canonicalize(name: str):
    """Devolve o nome canônico (Tabela 1) ou None se for desconhecido/alucinado."""
    k = _key(name)
    if not k:
        return None
    if k in _KEY_TO_CANON:
        return _KEY_TO_CANON[k]
    close = get_close_matches(k, list(_KEY_TO_CANON), n=1, cutoff=0.88)
    return _KEY_TO_CANON[close[0]] if close else None
