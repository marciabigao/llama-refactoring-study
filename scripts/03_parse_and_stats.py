"""Tarefas 1.5–1.6 — Separa código/lista de refatorações e calcula Tabela 2 e Figura 1.

Saídas (results/<modelo>/):
  parsed.jsonl                         código extraído + refatorações por geração
  tables/table2_refactoring_counts.csv/.md
  tables/figure1_per_task_means.csv
  tables/generation_summary.json       estatísticas básicas p/ os slides
  figures/figure1_refactorings_per_task.png
"""
import json
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _common import config, load_tasks, task_sort_key, write_jsonl  # noqa: E402
from src.parsing import parse_response  # noqa: E402
from src.refactorings import REFACTORINGS  # noqa: E402

config.ensure_dirs()
tasks = load_tasks()

rows = []
for f in sorted(config.RAW_DIR.glob("*.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    p = parse_response(r["text"], r.get("finish_reason", "stop"))
    rows.append({"task_id": r["task_id"], "iteration": r["iteration"], "finish_reason": r.get("finish_reason"),
                 "usage": r.get("usage", {}), **p})
rows.sort(key=lambda x: (task_sort_key(x["task_id"]), x["iteration"]))
write_jsonl(config.PARSED_PATH, rows)
if not rows:
    raise SystemExit("[erro] nenhuma geração em results/<modelo>/raw/. Rode o script 02 antes.")

n = len(rows)
ok = [r for r in rows if r["parse_ok"]]
print(f"Gerações: {n} | parse OK: {len(ok)} | falhas de parse: {n - len(ok)}")
print("Falhas por motivo:", dict(Counter(r["error"] for r in rows if not r["parse_ok"])))

# ---------- Tabela 2: contagem de refatorações (cada tipo conta 1x por geração) ----------
cnt = Counter()
unrec = Counter()
for r in ok:
    cnt.update(r["refactorings"])
    unrec.update(r["unrecognized"])
t2 = pd.DataFrame({"Refactoring": REFACTORINGS, "Count": [cnt.get(k, 0) for k in REFACTORINGS]})
t2 = t2.sort_values("Count", ascending=False, kind="stable").reset_index(drop=True)
t2.to_csv(config.TABLES_DIR / "table2_refactoring_counts.csv", index=False)
(config.TABLES_DIR / "table2_refactoring_counts.md").write_text(t2.to_markdown(index=False), encoding="utf-8")
pd.DataFrame(unrec.most_common(), columns=["Unrecognized (not in Table 1)", "Count"]).to_csv(
    config.TABLES_DIR / "table2_unrecognized_names.csv", index=False)
print("\n=== Tabela 2 (top 10) ===")
print(t2.head(10).to_string(index=False))
print(f"\nNomes fora da Tabela 1 (possível alucinação): {sum(unrec.values())} ocorrências, {len(unrec)} nomes distintos")

# ---------- Figura 1: distribuição da média de refatorações por tarefa ----------
df = pd.DataFrame([{"task_id": r["task_id"], "n_ref": len(r["refactorings"])} for r in ok])
per_task = df.groupby("task_id")["n_ref"].mean().reindex(sorted(tasks, key=task_sort_key)).fillna(0.0)
per_task.rename("mean_refactorings").to_csv(config.TABLES_DIR / "figure1_per_task_means.csv")
rounded = per_task.round().astype(int)  # a Figura 1 do artigo usa barras em inteiros (1..5)
dist = rounded.value_counts(normalize=True).sort_index() * 100
xs = list(range(0, max(5, int(dist.index.max())) + 1))
ys = [dist.get(x, 0.0) for x in xs]
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(xs, ys, color="skyblue", edgecolor="black", width=0.9)
ax.set_xticks(xs)
ax.set_xlabel("Number of refactorings per task")
ax.set_ylabel("Tasks (%)")
ax.set_title(f"Percentage of Tasks by Number of Refactorings ({config.MODEL})")
fig.tight_layout()
fig.savefig(config.FIGURES_DIR / "figure1_refactorings_per_task.png", dpi=200)

# ---------- Estatísticas básicas p/ os slides ----------
summary = {
    "model": config.MODEL,
    "generations": n, "parse_ok": len(ok), "parse_failed": n - len(ok),
    "truncated_by_max_tokens": sum(r["truncated"] for r in rows),
    "mean_refactorings_per_generation": float(np.mean([len(r["refactorings"]) for r in ok])),
    "median_refactorings_per_generation": float(np.median([len(r["refactorings"]) for r in ok])),
    "generations_with_zero_refactorings": sum(1 for r in ok if not r["refactorings"]),
    "pct_tasks_by_rounded_mean": {int(k): round(float(v), 1) for k, v in dist.items()},
    "total_prompt_tokens": sum(r["usage"].get("prompt_tokens", 0) for r in rows),
    "total_completion_tokens": sum(r["usage"].get("completion_tokens", 0) for r in rows),
    "distinct_unrecognized_names": len(unrec),
}
(config.TABLES_DIR / "generation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("\n=== Resumo ===")
print(json.dumps(summary, indent=2))
print(f"\nFigura 1 -> {config.FIGURES_DIR / 'figure1_refactorings_per_task.png'}")
