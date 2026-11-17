"""RQ1 (tarefas 2.1–2.2) — Executa as suítes de teste do ClassEval.

  python scripts/04_run_tests.py --canonical   # SANIDADE: roda o código canônico (deve passar ~100%)
  python scripts/04_run_tests.py               # roda as 1.000 gerações do Llama

Regra: gerações cujo código não pôde ser extraído (parse_ok=False) contam como FALHA (status 'no_code').
Saída: results/<modelo>/test_results.jsonl  (ou results/canonical_baseline.jsonl)
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

from _common import config, load_tasks, read_jsonl, task_sort_key, write_jsonl
from src.test_runner import run_candidate

ap = argparse.ArgumentParser()
ap.add_argument("--canonical", action="store_true")
ap.add_argument("--repeats", type=int, default=5,
                help="(com --canonical) nº de execuções por classe p/ detectar testes flaky (ex.: ClassEval_58 é aleatório)")
args = ap.parse_args()

tasks = load_tasks()
jobs = []
if args.canonical:
    for tid in sorted(tasks, key=task_sort_key):
        for rep in range(args.repeats):
            jobs.append({"task_id": tid, "iteration": -1, "rep": rep, "code": tasks[tid]["solution_code"]})
    out_path = config.CANONICAL_BASELINE
else:
    parsed = read_jsonl(config.PARSED_PATH)
    if not parsed:
        raise SystemExit("[erro] rode antes: python scripts/03_parse_and_stats.py")
    for r in parsed:
        jobs.append({"task_id": r["task_id"], "iteration": r["iteration"],
                     "code": r["code"] if r["parse_ok"] else None, "parse_error": r["error"],
                     "skipped": r.get("finish_reason") == "rate_limit_too_large"})
    out_path = config.TESTS_PATH


def work(j):
    base = {"task_id": j["task_id"], "iteration": j["iteration"]}
    if j["code"] is None:
        return {**base, "status": "skipped_rate_limit" if j.get("skipped") else "no_code", "passed": False, "tests_run": 0, "n_failures": 0,
                "n_errors": 0, "failures": [{"test": "<parse>", "kind": "error", "message": j.get("parse_error")}]}
    res = run_candidate(tasks[j["task_id"]], j["code"])
    return {**base, **res, "passed": res["status"] == "ok"}


with ThreadPoolExecutor(max_workers=config.N_WORKERS) as ex:
    results = list(tqdm(ex.map(work, jobs), total=len(jobs), unit="exec"))

results.sort(key=lambda r: (task_sort_key(r["task_id"]), r["iteration"]))
if args.canonical:  # colapsa as repetições: passa só se passou em TODAS; marca flaky se misturou
    merged = {}
    for r in results:
        m = merged.setdefault(r["task_id"], {**r, "passed": True, "n_pass": 0, "n_reps": 0})
        m["n_reps"] += 1
        m["n_pass"] += int(r["passed"])
        if not r["passed"]:
            m.update({k: r[k] for k in ("status", "tests_run", "n_failures", "n_errors", "failures")})
    for m in merged.values():
        m["passed"] = m["n_pass"] == m["n_reps"]
        m["flaky"] = 0 < m["n_pass"] < m["n_reps"]
        if m["passed"]:
            m["status"] = "ok"
    results = list(merged.values())
write_jsonl(out_path, results)
c = Counter(r["status"] for r in results)
print(f"\nStatus: {dict(c)}")
print(f"Aprovadas (todos os testes): {sum(r['passed'] for r in results)}/{len(results)}")
if args.canonical:
    bad = [r["task_id"] for r in results if not r["passed"]]
    print("Falharam no código CANÔNICO (problema de ambiente/teste, não do modelo):", bad or "nenhuma")
    print("  dos quais FLAKY (passam às vezes):", [r["task_id"] for r in results if r.get("flaky")] or "nenhuma")
    for r in results:
        if not r["passed"]:
            print(" -", r["task_id"], r["failures"][0]["message"].strip().splitlines()[-1][:150])
print(f"-> {out_path}")
