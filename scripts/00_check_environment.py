"""Verifica Python, dependências usadas pelos testes do ClassEval, dados NLTK e a chave/modelo do provedor."""
import importlib
import sys

from _common import config

print(f"Python {sys.version.split()[0]} ({sys.executable})")
if sys.version_info < (3, 10):
    print("[AVISO] use Python >= 3.10")

mods = ["openai", "dotenv", "numpy", "pandas", "matplotlib", "tabulate", "nltk", "gensim", "bs4", "PyPDF2",
        "reportlab", "PIL", "openpyxl", "scipy", "jsonlines", "Levenshtein", "func_timeout", "docx"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
        print(f"  ok  {m}")
    except Exception as e:  # noqa: BLE001
        print(f"  FALTA {m}: {e}")
        missing.append(m)

try:
    import nltk
    for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "averaged_perceptron_tagger",
                "averaged_perceptron_tagger_eng", "omw-1.4"]:
        nltk.download(pkg, quiet=True)
    print("  ok  dados NLTK")
except Exception as e:  # noqa: BLE001
    print(f"  [AVISO] NLTK: {e}")

print(f"\nProvedor: {config.PROVIDER} | Modelo: {config.MODEL}")
if config.PROVIDER == "mock":
    print("Modo MOCK (sem API).")
elif not config.API_KEY:
    print(f"[ERRO] {config.PROVIDERS[config.PROVIDER]['key_env']} ausente no .env")
else:
    try:
        from openai import OpenAI
        r = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL, max_retries=0, timeout=60
                   ).chat.completions.create(model=config.MODEL, max_tokens=8,
                                             messages=[{"role": "user", "content": "Say OK"}])
        print(f"  ok  chamada de teste ao modelo -> {r.choices[0].message.content!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] chamada de teste falhou: {type(e).__name__}: {e}")
        print("  404 = ID do modelo errado | 401 = chave inválida | 402/412 = sem saldo | 429 = limite")

if missing:
    print("\nInstale o que falta: pip install -r requirements.txt")
