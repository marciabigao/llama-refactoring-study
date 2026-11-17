"""Extrai (a) o código refatorado e (b) a lista de refatorações do padrão de saída do modelo."""
import re

from .refactorings import canonicalize

_PY_RE = re.compile(r"```[ \t]*(?:python|py|python3)[ \t]*\r?\n(.*?)```", re.S | re.I)
_TEXT_RE = re.compile(r"```[ \t]*(?:text|txt|plaintext|plain)[ \t]*\r?\n(.*?)```", re.S | re.I)
_ANY_RE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[ \t]*\r?\n(.*?)```", re.S)
_LINE_RE = re.compile(r"refactorings?(?:\s+applied)?\s*:\s*(.+)", re.I)
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_NONE_WORDS = {"none", "n/a", "na", "no refactorings", "no refactoring", "no refactorings applied", ""}


def _split_list(blob: str):
    items = []
    for part in re.split(r"[,\n;]", blob):
        part = _BULLET_RE.sub("", part).strip().strip("\"'`*. ")
        if part.lower() in _NONE_WORDS:
            continue
        items.append(part)
    return items


def parse_response(text: str, finish_reason: str = "stop") -> dict:
    out = {"parse_ok": False, "error": None, "code": None,
           "refactorings_raw": [], "refactorings": [], "unrecognized": [],
           "truncated": finish_reason == "length"}
    if not text:
        out["error"] = "empty_response"
        return out

    # Modelos de raciocínio (Qwen3.x) podem emitir <think>...</think>; código dentro do raciocínio NÃO conta.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    if re.search(r"<think>", text, re.I):          # raciocínio não fechado (resposta truncada)
        text = text[: re.search(r"<think>", text, re.I).start()]
    if not text.strip():
        out["error"] = "truncated_no_code_block" if out["truncated"] else "only_reasoning"
        return out

    # --- código ---
    blocks = _PY_RE.findall(text)
    if not blocks:  # fallback: bloco sem linguagem, mas que parece Python
        blocks = [b for lang, b in _ANY_RE.findall(text)
                  if lang.lower() in ("", "python") and re.search(r"^\s*(class|def)\s", b, re.M)]
    if not blocks:
        out["error"] = "truncated_no_code_block" if out["truncated"] else "no_python_block"
        return out
    with_class = [b for b in blocks if re.search(r"^\s*class\s+\w+", b, re.M)]
    out["code"] = (with_class or blocks)[0].strip("\n") + "\n"
    out["parse_ok"] = True

    # --- lista de refatorações ---
    raw = []
    m = _TEXT_RE.search(text)
    if m:
        raw = _split_list(m.group(1))
    else:
        for mm in _LINE_RE.finditer(text):
            raw = _split_list(mm.group(1))
            if raw:
                break
    out["refactorings_raw"] = raw

    seen, unrec = [], []
    for r in raw:
        c = canonicalize(r)
        if c is None:
            if r not in unrec:
                unrec.append(r)
        elif c not in seen:  # conta cada tipo de refatoração uma vez por geração
            seen.append(c)
    out["refactorings"] = seen
    out["unrecognized"] = unrec
    return out
