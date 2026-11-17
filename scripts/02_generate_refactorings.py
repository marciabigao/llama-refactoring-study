"""Tarefas 1.2–1.4 — Gera as refatorações com Llama via Groq.

100 classes x 10 ciclos = 1.000 gerações, com temperature=1.0, top_p=1.0, max_tokens=4000.
- Ordem: ciclo por ciclo (ciclo 0 em todas as classes, depois ciclo 1...). Se a cota acabar, você já tem ciclos completos.
- Retomável: gerações já salvas em results/<modelo>/raw/ são puladas. Pode rodar de novo a qualquer momento.
- GROQ_MODEL=mock gera respostas falsas (código canônico) para testar todo o pipeline sem API.

Uso:
    python scripts/02_generate_refactorings.py                 # tudo
    python scripts/02_generate_refactorings.py --tasks 3 --runs 2   # teste rápido (3 classes x 2 ciclos)
"""
import argparse
import json
import os
import re
import time
import zlib
from datetime import datetime, timezone

from tqdm import tqdm

from _common import config, load_tasks, task_sort_key
from src.prompts import build_system_prompt, build_user_prompt


class DailyLimit(Exception):
    pass


def parse_wait(msg: str) -> float:
    m = re.search(r"try again in\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:([\d.]+)s)?", msg)
    if not m or not any(m.groups()):
        return 20.0
    h, mi, s = (float(x) if x else 0.0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def mock_response(task: dict, it: int) -> dict:
    """Resposta falsa p/ testar o pipeline. ~1/7 das gerações recebem um bug sintético."""
    code = task["solution_code"]
    if zlib.crc32(f"{task['task_id']}-{it}".encode()) % 7 == 0:
        code = code.replace(" + ", " - ", 1) if " + " in code else code.replace(" == ", " != ", 1)
    fence = "`" * 3
    text = f"{fence}python\n{code}\n{fence}\n\n{fence}text\nExtract Method, Inline Method, Rename Variable\n{fence}"
    return {"text": text, "finish_reason": "stop", "usage": {}}


def call_groq(client, system, user):
    import groq
    attempt = 0
    while True:
        try:
            r = client.chat.completions.create(
                model=config.MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=config.TEMPERATURE, top_p=config.TOP_P,
                max_completion_tokens=config.MAX_TOKENS, n=1)
            ch = r.choices[0]
            u = r.usage
            return {"text": ch.message.content or "", "finish_reason": ch.finish_reason,
                    "usage": {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens}
                    if u else {}}
        except groq.RateLimitError as e:
            msg = str(e)
            if re.search(r"per day|\bTPD\b|\bRPD\b", msg):
                raise DailyLimit(msg)
            wait = min(parse_wait(msg) + 1.0, 120.0)
            tqdm.write(f"  [429] limite por minuto; aguardando {wait:.0f}s")
            time.sleep(wait)
        except (groq.APIConnectionError, groq.APITimeoutError, groq.InternalServerError) as e:
            attempt += 1
            if attempt > 6:
                raise
            wait = min(2 ** attempt, 60)
            tqdm.write(f"  [rede/servidor] {type(e).__name__}; tentativa {attempt}, aguardando {wait}s")
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=int, default=None, help="usar só as N primeiras classes (teste)")
    ap.add_argument("--runs", type=int, default=None, help="número de ciclos (padrão: N_RUNS do .env)")
    args = ap.parse_args()

    config.ensure_dirs()
    tasks = load_tasks()
    ids = sorted(tasks, key=task_sort_key)[: args.tasks]
    n_runs = args.runs or config.N_RUNS
    system = build_system_prompt()

    # Guarda os parâmetros do experimento junto com os resultados (reprodutibilidade)
    (config.RESULTS_DIR / "experiment_config.json").write_text(json.dumps({
        "model": config.MODEL, "temperature": config.TEMPERATURE, "top_p": config.TOP_P,
        "max_tokens": config.MAX_TOKENS, "n_runs": n_runs, "n_tasks": len(ids),
        "system_prompt": system,
        "user_prompt": "<solution_code da classe do ClassEval>",
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    client = None
    if config.MODEL != "mock":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise SystemExit("[erro] defina GROQ_API_KEY no .env")
        from groq import Groq
        client = Groq(api_key=key, max_retries=0)  # retries são tratados por nós

    jobs = [(it, tid) for it in range(n_runs) for tid in ids
            if not (config.RAW_DIR / f"{tid}__iter{it}.json").exists()]
    print(f"Modelo: {config.MODEL} | pendentes: {len(jobs)} de {len(ids) * n_runs}")
    last = 0.0
    try:
        for it, tid in tqdm(jobs, unit="ger"):
            if client is None:
                resp = mock_response(tasks[tid], it)
            else:
                dt = time.time() - last
                if dt < config.REQUEST_INTERVAL_S:
                    time.sleep(config.REQUEST_INTERVAL_S - dt)
                last = time.time()
                resp = call_groq(client, system, build_user_prompt(tasks[tid]))
            rec = {"task_id": tid, "iteration": it, "model": config.MODEL,
                   "timestamp": datetime.now(timezone.utc).isoformat(), **resp}
            tmp = config.RAW_DIR / f".{tid}__iter{it}.tmp"
            tmp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            tmp.replace(config.RAW_DIR / f"{tid}__iter{it}.json")  # escrita atômica
    except DailyLimit as e:
        print(f"\n[COTA DIÁRIA ATINGIDA] {e}\nO progresso está salvo. Rode o script de novo quando a cota renovar "
              f"(ou use um modelo com cota maior).")
    except KeyboardInterrupt:
        print("\nInterrompido. Progresso salvo; rode novamente para continuar.")
    done = len(list(config.RAW_DIR.glob("*.json")))
    print(f"Gerações salvas: {done}/{len(ids) * n_runs}")


if __name__ == "__main__":
    main()
