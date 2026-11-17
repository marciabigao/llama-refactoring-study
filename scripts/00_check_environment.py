"""Verifica Python, dependências usadas pelos testes do ClassEval, dados NLTK e a chave Groq."""
import importlib
import os
import sys

from _common import config

print(f"Python {sys.version.split()[0]} ({sys.executable})")
if sys.version_info < (3, 10):
    print("[AVISO] use Python >= 3.10")

mods = ["groq", "dotenv", "numpy", "pandas", "matplotlib", "nltk", "gensim", "bs4", "PyPDF2",
        "reportlab", "PIL", "openpyxl", "scipy", "jsonlines", "Levenshtein", "func_timeout", "docx"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
        print(f"  ok  {m}")
    except Exception as e:  # noqa: BLE001
        print(f"  FALTA {m}: {e}")
        missing.append(m)

# Dados NLTK usados por algumas classes do ClassEval (tokenização, stopwords, lemmatização, POS)
try:
    import nltk
    for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "averaged_perceptron_tagger",
                "averaged_perceptron_tagger_eng", "omw-1.4"]:
        nltk.download(pkg, quiet=True)
    print("  ok  dados NLTK")
except Exception as e:  # noqa: BLE001
    print(f"  [AVISO] NLTK: {e}")

print(f"\nModelo configurado: {config.MODEL}")
key = os.getenv("GROQ_API_KEY", "")
if config.MODEL == "mock":
    print("Modo MOCK (sem API).")
elif not key.startswith("gsk_"):
    print("[ERRO] GROQ_API_KEY ausente/ inválida no .env")
else:
    try:
        from groq import Groq
        ids = sorted(m.id for m in Groq(api_key=key).models.list().data)
        print("Modelos disponíveis na sua conta Groq:")
        for i in ids:
            print("   -", i)
        if config.MODEL not in ids:
            print(f"[ERRO] '{config.MODEL}' não está na lista. Ajuste GROQ_MODEL no .env.")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] não consegui listar modelos: {e}")

if missing:
    print("\nInstale o que falta: pip install -r requirements.txt")
