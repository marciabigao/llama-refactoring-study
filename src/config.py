"""Configuração central. Valores padrão seguem o artigo (Midolo et al., 2026):
temperature=1.0, top_p=1.0, max_tokens=4000, 10 execuções por tarefa."""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- Provedor / modelo ----
# Provedores com API compatível com OpenAI. "mock" = teste offline sem API.
PROVIDERS = {
    "sambanova": {"base_url": "https://api.sambanova.ai/v1", "key_env": "SAMBANOVA_API_KEY",
                  "default_model": "Meta-Llama-3.3-70B-Instruct", "interval": 3.5,  # free tier: 20 RPM, 20 RPD, 200K TPD
                  "daily_tokens": 200_000, "daily_requests": 20},
    "fireworks": {"base_url": "https://api.fireworks.ai/inference/v1", "key_env": "FIREWORKS_API_KEY",
                  "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct", "interval": 0.5,
                  "daily_tokens": 0, "daily_requests": 0},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",
             "default_model": "qwen/qwen3.8-27b", "interval": 12.0,  # plano gratuito Qwen3.8-27B: 30 RPM, 8K TPM, 1K RPD, 200K TPD
             "daily_tokens": 200_000, "daily_requests": 1000},
}
PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
MODEL = (os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL")
         or PROVIDERS.get(PROVIDER, PROVIDERS["groq"])["default_model"])  # LLM_MODEL=mock p/ teste offline
if MODEL == "mock":
    PROVIDER = "mock"
if PROVIDER not in PROVIDERS and PROVIDER != "mock":
    raise SystemExit(f"[erro] LLM_PROVIDER inválido: {PROVIDER} (use sambanova, fireworks, groq ou LLM_MODEL=mock)")
BASE_URL = os.getenv("LLM_BASE_URL") or PROVIDERS.get(PROVIDER, {}).get("base_url")
API_KEY = os.getenv(PROVIDERS.get(PROVIDER, {}).get("key_env", ""), "")
MODEL_SLUG = re.sub(r"[^A-Za-z0-9._-]+", "_", MODEL.split("/")[-1])  # pasta de resultados: results/<slug>/
N_RUNS = int(os.getenv("N_RUNS", "10"))
TEMPERATURE = 1.0
TOP_P = 1.0
MAX_TOKENS = 4000
# Cotas diárias (usadas só pelo planejador --plan; 0 = sem limite). Ajuste no .env se mudar de plano.
DAILY_TOKEN_QUOTA = int(os.getenv("DAILY_TOKEN_QUOTA") or PROVIDERS.get(PROVIDER, {}).get("daily_tokens", 0))
DAILY_REQUEST_QUOTA = int(os.getenv("DAILY_REQUEST_QUOTA") or PROVIDERS.get(PROVIDER, {}).get("daily_requests", 0))
# Modelos de raciocínio (ex.: Qwen3.8): ex. "none" ou "low" p/ não gastar tokens pensando. Vazio = não enviar.
REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT", "").strip()
REQUEST_INTERVAL_S = float(os.getenv("REQUEST_INTERVAL_S") or PROVIDERS.get(PROVIDER, {}).get("interval", 0.5))

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
