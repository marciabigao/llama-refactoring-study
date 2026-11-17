"""RQ1 (tarefas 2.3–2.4) — Calcula a Tabela 3: Mean TPR, Std TPR, pass@1/5/10 e Consistency.

Definições (seguem a Seção 4.1 do artigo):
  TPR da execução i  = proporção de TAREFAS (classes) cujo código refatorado passa em TODOS os testes na execução i.
  Mean/Std TPR       = média e desvio padrão do TPR entre as execuções (std amostral, ddof=1; ddof=0 também salvo).
  pass@k             = estimador não-viesado de Chen et al. (2021) com n execuções por tarefa, média sobre as tarefas.
  Consistency        = proporção de tarefas que passam em TODAS as execuções.
Extra: TPR em nível de caso de teste, e distribuição dos motivos de falha.

Opções:
  --exclude-canonical-failures   ignora classes cujo código canônico já falha no SEU ambiente
"""
import argparse
import json
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from _common import config, read_jsonl

ap = argparse.ArgumentParser()
ap.add_argument("--exclude-canonical-failures", action="store_true")
args = ap.parse_args()

config.ensure_dirs()
res = read_jsonl(config.TESTS_PATH)
if not res:
    raise SystemExit("[erro] rode antes: python scripts/04_run_tests.py")

excluded = set()
if args.exclude_canonical_failures:
    base = read_jsonl(config.CANONICAL_BASELINE)
    excluded = {r["task_id"] for r in base if not r["passed"]}
    print("Excluindo (falham no canônico):", sorted(excluded))
res = [r for r in res if r["task_id"] not in excluded]

by_task = defaultdict(dict)
for r in res:
    by_task[r["task_id"]][r["iteration"]] = r
iters = sorted({r["iteration"] for r in res})
tasks = sorted(by_task)
n_tasks = len(tasks)


def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)))


# TPR por execução (nível de tarefa)
tpr_runs = []
for it in iters:
    sel = [by_task[t][it]["passed"] for t in tasks if it in by_task[t]]
    tpr_runs.append(float(np.mean(sel)))

# pass@k
pk = {}
for k in (1, 5, 10):
    vals = []
    for t in tasks:
        n = len(by_task[t])
        c = sum(r["passed"] for r in by_task[t].values())
        if n >= k:
            vals.append(pass_at_k(n, c, k))
    pk[k] = float(np.mean(vals)) if vals else float("nan")
    if len(vals) < n_tasks:
        print(f"[aviso] pass@{k}: só {len(vals)}/{n_tasks} tarefas têm >= {k} execuções")

# Consistency
cons = float(np.mean([all(r["passed"] for r in by_task[t].values()) for t in tasks]))

# Extras: nível de caso de teste
tot_run = sum(r["tests_run"] for r in res)
tot_bad = sum(r["n_failures"] + r["n_errors"] for r in res if r["status"] == "tests_failed")
tc_tpr = (tot_run - tot_bad) / tot_run if tot_run else float("nan")

row = {"Model": config.MODEL, "Mean TPR": round(float(np.mean(tpr_runs)), 3),
       "Std TPR": round(float(np.std(tpr_runs, ddof=1)) if len(tpr_runs) > 1 else 0.0, 3),
       "pass@1": round(pk[1], 3), "pass@5": round(pk[5], 3), "pass@10": round(pk[10], 3),
       "Consistency": round(cons, 3)}
# Valores publicados no artigo (GPT-4o[-mini]) — Tabela 3
paper = {"Model": "GPT-4o (artigo)", "Mean TPR": 0.844, "Std TPR": 0.01, "pass@1": 0.86,
         "pass@5": 0.88, "pass@10": 0.89, "Consistency": 0.8}
t3 = pd.DataFrame([row])
cmp_ = pd.DataFrame([paper, row])
t3.to_csv(config.TABLES_DIR / "table3_rq1.csv", index=False)
cmp_.to_csv(config.TABLES_DIR / "table3_comparison_gpt_vs_llama.csv", index=False)
(config.TABLES_DIR / "table3_comparison_gpt_vs_llama.md").write_text(cmp_.to_markdown(index=False), encoding="utf-8")
pd.DataFrame({"iteration": iters, "TPR": tpr_runs}).to_csv(config.TABLES_DIR / "table3_tpr_per_run.csv", index=False)

status = Counter(r["status"] for r in res)
extra = {"n_tasks": n_tasks, "n_runs": len(iters), "excluded_tasks": sorted(excluded),
         "tpr_per_run": [round(x, 3) for x in tpr_runs], "std_tpr_ddof0": round(float(np.std(tpr_runs)), 4),
         "testcase_level_tpr": round(tc_tpr, 3), "status_counts": dict(status),
         "tasks_never_passing": sorted(t for t in tasks if not any(r["passed"] for r in by_task[t].values()))}
(config.TABLES_DIR / "table3_extra.json").write_text(json.dumps(extra, indent=2), encoding="utf-8")

print("\n=== Tabela 3 (RQ1) ===")
print(cmp_.to_string(index=False))
print("\n=== Extras ===")
print(json.dumps(extra, indent=2))
