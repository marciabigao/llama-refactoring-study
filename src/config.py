"""Configuração central. Valores padrão seguem o artigo (Midolo et al., 2026):
temperature=1.0, top_p=1.0, max_tokens=4000, 10 execuções por tarefa."""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- Modelo / geração ----
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # use GROQ_MODEL=mock p/ teste offline
MODEL_SLUG = re.sub(r"[^A-Za-z0-9._-]+", "_", MODEL)
N_RUNS = int(os.getenv("N_RUNS", "10"))
TEMPERATURE = 1.0
TOP_P = 1.0
MAX_TOKENS = 4000
REQUEST_INTERVAL_S = float(os.getenv("REQUEST_INTERVAL_S", "2.5"))

# ---- Testes ----
TEST_TIMEOUT_S = int(os.getenv("TEST_TIMEOUT_S", "60"))
N_WORKERS = int(os.getenv("N_WORKERS", "4"))

# ---- Caminhos ----
DATA_PATH = ROOT / "data" / "ClassEval_data.json"
RESULTS_ROOT = ROOT / "results"
RESULTS_DIR = RESULTS_ROOT / MODEL_SLUG          # tudo que depende do modelo
RAW_DIR = RESULTS_DIR / "raw"                    # 1 JSON por (tarefa, iteração)
PARSED_PATH = RESULTS_DIR / "parsed.jsonl"
TESTS_PATH = RESULTS_DIR / "test_results.jsonl"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
FAILURE_DIR = RESULTS_DIR / "failure_cases"
CANONICAL_BASELINE = RESULTS_ROOT / "canonical_baseline.jsonl"  # independe do modelo


def ensure_dirs():
    for d in (RAW_DIR, TABLES_DIR, FIGURES_DIR, FAILURE_DIR):
        d.mkdir(parents=True, exist_ok=True)
