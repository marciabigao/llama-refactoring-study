"""RQ3 (tarefas 4.1–4.2): legibilidade (Scalabrino et al., 2018) do código canônico, do Qwen e do GPT-4o-mini.

Usa o rsm.jar do pacote de replicação (rode antes scripts/07_get_gpt_package.py) e precisa de Java.
Verificação embutida: a média do canônico é comparada com a do artigo (Tabela 4: 0,6199).

Saída: results/rq3/readability_scores.csv, 1 linha por (model, iteration, task_id), com iteration = -1 no canônico.
Uso: python scripts/10_readability.py
"""
import csv
import shutil
import time

import numpy as np

from _common import config, load_tasks, read_jsonl, task_sort_key
from src.readability import run_rsm

OUT_DIR = config.RESULTS_ROOT / "rq3"
PKG = config.ROOT / "data" / "replication_package" / "data"
JAR = PKG / "rq3" / "readability_tool" / "rsm.jar"
PAPER_CANONICAL_MEAN = 0.6199  # Tabela 4 do artigo ("Before")
QWEN, GPT = config.MODEL_SLUG, "gpt-4o-mini"


def main():
    if not JAR.exists():
        raise SystemExit("[erro] rsm.jar não encontrado: rode scripts/07_get_gpt_package.py")
    if shutil.which("java") is None:
        raise SystemExit("[erro] Java não encontrado no PATH (instale um JRE/JDK)")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    tests = {(r["task_id"], r["iteration"]): r["passed"] for r in read_jsonl(config.TESTS_PATH)}

    jobs = [("canonical", -1, {tid: t["solution_code"] for tid, t in tasks.items()}, {})]
    by_iter = {}
    for r in read_jsonl(config.PARSED_PATH):
        if r.get("code"):
            by_iter.setdefault(r["iteration"], {})[r["task_id"]] = r["code"]
    for it in sorted(by_iter):
        jobs.append((QWEN, it, by_iter[it], tests))
    gpt_tests = {}
    for i in range(10):
        d = PKG / "rq1" / f"iter_{i}"
        if not (d / "files").is_dir():
            continue
        with (d / "test_results.csv").open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                gpt_tests[(row["task_id"], i)] = row["test_pass"].strip() == "True"
        jobs.append((GPT, i, {p.stem: p.read_text(encoding="utf-8") for p in (d / "files").glob("ClassEval_*.py")},
                     gpt_tests))

    rows = []
    for model, it, sources, tst in jobs:
        t0 = time.time()
        scores = run_rsm(JAR, sources)
        missing = sorted(set(sources) - set(scores), key=task_sort_key)
        for tid in sources:
            rows.append({"model": model, "iteration": it, "task_id": tid,
                         "readability": scores.get(tid, ""),
                         "tests_passed": "" if model == "canonical" else tst.get((tid, it), "")})
        print(f"  {model:14s} iter {it:>2}: {len(scores)}/{len(sources)} scores em {time.time() - t0:.0f}s"
              + (f"  (sem score: {', '.join(missing)})" if missing else ""))
        if model == "canonical":
            mean = float(np.mean(list(scores.values())))
            print(f"  verificação: média canônica = {mean:.4f} (artigo: {PAPER_CANONICAL_MEAN})")

    rows.sort(key=lambda r: (r["model"], r["iteration"], task_sort_key(r["task_id"])))
    with (OUT_DIR / "readability_scores.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} linhas -> results/rq3/readability_scores.csv")


if __name__ == "__main__":
    main()
