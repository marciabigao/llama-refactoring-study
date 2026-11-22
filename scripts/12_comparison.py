"""Etapa 4: comparação GPT-4o-mini × Qwen3.8-27B nas três RQs, em uma tabela só.

RQ1 é recalculada aqui nas MESMAS condições para os dois modelos:
  - Qwen: results/<modelo>/test_results.jsonl (testes rodados pelo grupo, 5 ciclos);
  - GPT:  data/replication_package/data/rq1/iter_*/test_results.csv (testes do artigo, 10 ciclos).
  Mesmas 98 tarefas (sem ClassEval_17 e ClassEval_48, que falham no canônico) e mesmas definições do
  scripts/05_rq1_metrics.py. Para o GPT há duas linhas: os 10 ciclos e só os ciclos 0–4, que é a
  comparação justa com os 5 ciclos do Qwen (pass@5 e Consistency dependem do número de ciclos).
RQ2 e RQ3 só são lidas das tabelas já geradas (scripts 09 e 11), sem recalcular nada.

Saídas (results/comparison/):
  rq1_recomputed.csv|md     RQ1 dos dois modelos nas mesmas condições (+ linha do artigo)
  comparison_table.csv|md   tabela única RQ1–RQ3, com a coluna `source` apontando o arquivo de origem
Uso: python scripts/12_comparison.py
"""
import csv
import sys

import numpy as np
import pandas as pd

from _common import config, read_jsonl
from src import stats_utils as su

OUT = config.RESULTS_ROOT / "comparison"
PKG_RQ1 = config.ROOT / "data" / "replication_package" / "data" / "rq1"
EXCLUDED = {"ClassEval_17", "ClassEval_48"}
QWEN_LABEL, GPT_LABEL = "Qwen3.8-27B", "GPT-4o-mini"
PAPER_RQ1 = {"model": "GPT-4o-mini (artigo, 100 tarefas)", "n_tasks": 100, "n_cycles": 10, "mean_tpr": 0.844,
             "std_tpr": 0.01, "pass@1": 0.86, "pass@5": 0.88, "pass@10": 0.89, "consistency": 0.80}


def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)))


def load_qwen():
    """{task_id: {iteration: (passou, casos_rodados, casos_com_falha)}}"""
    out = {}
    for r in read_jsonl(config.TESTS_PATH):
        bad = r["n_failures"] + r["n_errors"] if r["status"] == "tests_failed" else 0
        out.setdefault(r["task_id"], {})[r["iteration"]] = (bool(r["passed"]), r["tests_run"], bad)
    return out


def load_gpt():
    out = {}
    for i in range(10):
        f = PKG_RQ1 / f"iter_{i}" / "test_results.csv"
        if not f.exists():
            sys.exit("[erro] pacote do artigo ausente: rode scripts/07_get_gpt_package.py")
        with f.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                ok, bad = int(row["tests_passed"] or 0), int(row["tests_failed"] or 0)
                out.setdefault(row["task_id"], {})[i] = (row["test_pass"].strip() == "True", ok + bad, bad)
    return out


def rq1_metrics(label, data, cycles, excluded=EXCLUDED):
    tasks = sorted(t for t in data if t not in excluded)
    tpr = [np.mean([data[t][i][0] for t in tasks]) for i in cycles]
    n = len(cycles)
    row = {"model": label, "n_tasks": len(tasks), "n_cycles": n,
           "mean_tpr": float(np.mean(tpr)), "std_tpr": float(np.std(tpr, ddof=1))}
    for k in (1, 5, 10):
        row[f"pass@{k}"] = (float(np.mean([pass_at_k(n, sum(data[t][i][0] for i in cycles), k) for t in tasks]))
                            if n >= k else np.nan)
    row["consistency"] = float(np.mean([all(data[t][i][0] for i in cycles) for t in tasks]))
    run = sum(data[t][i][1] for t in tasks for i in cycles)
    bad = sum(data[t][i][2] for t in tasks for i in cycles)
    row["testcase_tpr"] = (run - bad) / run if run else np.nan
    row["never_passing"] = sum(not any(data[t][i][0] for i in cycles) for t in tasks)
    return row, pd.Series({t: np.mean([data[t][i][0] for i in cycles]) for t in tasks})


def fmt(x, nd=3):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n/a"
    return "< 0.0001" if p < 1e-4 else f"{p:.4f}"


def write(df, name):
    df.to_csv(OUT / f"{name}.csv", index=False, lineterminator="\n")
    (OUT / f"{name}.md").write_text(df.to_markdown(index=False) + "\n", encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    qwen, gpt = load_qwen(), load_gpt()
    q_row, q_task = rq1_metrics(QWEN_LABEL, qwen, range(5))
    # Verificação: com as 100 tarefas e 10 ciclos deve reproduzir a Tabela 3 do artigo
    g100_row, _ = rq1_metrics(f"{GPT_LABEL} (verificação: 100 tarefas, 10 ciclos)", gpt, range(10), excluded=set())
    g10_row, _ = rq1_metrics(f"{GPT_LABEL} (10 ciclos)", gpt, range(10))
    g5_row, g_task = rq1_metrics(f"{GPT_LABEL} (ciclos 0–4)", gpt, range(5))
    rq1 = pd.DataFrame([PAPER_RQ1, g100_row, g10_row, g5_row, q_row])
    # Qwen × GPT por tarefa (proporção de ciclos que passam, ciclos 0–4 nos dois), Wilcoxon bilateral
    common = q_task.index.intersection(g_task.index)
    w = su.wilcoxon_paired(g_task[common], q_task[common])
    rq1["p_qwen_vs_gpt_5cyc"] = [np.nan, np.nan, np.nan, w["p"], w["p"]]
    write(rq1.round(4), "rq1_recomputed")
    print(f"Wilcoxon por tarefa (ciclos 0–4): n = {w['n']}, p = {w['p']:.3g}, r = {w['r']:+.3f}")

    s2 = pd.read_csv(config.RESULTS_ROOT / "rq2" / "tables" / "rq2_summary.csv").set_index(["model", "metric"])
    t4 = pd.read_csv(config.RESULTS_ROOT / "rq3" / "tables" / "table4_readability.csv").set_index("model")
    src1, src2, src3 = ("results/comparison/rq1_recomputed.csv", "results/rq2/tables/rq2_summary.csv",
                        "results/rq3/tables/table4_readability.csv")
    rows = []

    def add(rq, metric, gpt_v, qwen_v, p, src, note=""):
        rows.append({"rq": rq, "metric": metric, "gpt_4o_mini": gpt_v, "qwen3_8_27b": qwen_v,
                     "p_qwen_vs_gpt": p, "source": src, "note": note})

    p1 = fmt_p(w["p"])
    add("RQ1", "Mean TPR (ciclos 0–4, 98 tarefas)", fmt(g5_row["mean_tpr"]), fmt(q_row["mean_tpr"]), p1, src1)
    add("RQ1", "Std TPR (ciclos 0–4)", fmt(g5_row["std_tpr"]), fmt(q_row["std_tpr"]), "", src1)
    add("RQ1", "pass@1", fmt(g5_row["pass@1"]), fmt(q_row["pass@1"]), "", src1)
    add("RQ1", "pass@5 (5 ciclos)", fmt(g5_row["pass@5"]), fmt(q_row["pass@5"]), "", src1)
    add("RQ1", "pass@10", fmt(g10_row["pass@10"]), "n/a", "", src1, "Qwen tem só 5 ciclos")
    add("RQ1", "Consistency (passa nos 5 ciclos)", fmt(g5_row["consistency"]), fmt(q_row["consistency"]), "", src1)
    add("RQ1", "TPR por caso de teste", fmt(g5_row["testcase_tpr"]), fmt(q_row["testcase_tpr"]), "", src1)
    add("RQ1", "Tarefas que nunca passam (de 98)", str(g5_row["never_passing"]), str(q_row["never_passing"]), "", src1)

    rq2_metrics = [("Cognitive_Complexity", "Cognitive Complexity"), ("Complexity", "Complexity (ciclomática)"),
                   ("Statements", "Statements"), ("Ncloc", "NcLOC"), ("flake_total", "Flake8 total"),
                   ("pylint_total", "Pylint total"), ("flake_PyFlakesErrors", "PyFlakes"),
                   ("flake_DocstringIssues", "Docstrings (D)"), ("flake_BugRisks.BestPractices", "Bugbear (B)")]
    for key, name in rq2_metrics:
        g, q = s2.loc[(GPT_LABEL, key)], s2.loc[(QWEN_LABEL, key)]
        can = g["mean_canonical"]
        add("RQ2", f"{name}: δ médio (canônico {can:.2f})", f"{g['mean_delta']:+.3f} (r {g['r']:+.2f})",
            f"{q['mean_delta']:+.3f} (r {q['r']:+.2f})", fmt_p(q["p_qwen_vs_gpt"]), src2)

    g, q = t4.loc[GPT_LABEL], t4.loc[QWEN_LABEL]
    add("RQ3", f"Legibilidade: média (canônico {g['before_mean']:.4f})", f"{g['after_mean']:.4f}",
        f"{q['after_mean']:.4f}", "", src3)
    add("RQ3", "Δ médio [IC 95%]", f"{g['delta_mean']:+.4f} [{g['delta_ci_low']:+.4f}; {g['delta_ci_high']:+.4f}]",
        f"{q['delta_mean']:+.4f} [{q['delta_ci_low']:+.4f}; {q['delta_ci_high']:+.4f}]",
        fmt_p(q["p_qwen_vs_gpt_delta"]), src3)
    add("RQ3", "% melhorou / % piorou", f"{g['pct_improved']:.1f} / {g['pct_worsened']:.1f}",
        f"{q['pct_improved']:.1f} / {q['pct_worsened']:.1f}", "", src3)
    add("RQ3", "Wilcoxon bilateral (refatorado × canônico)", fmt_p(g["p_two_sided"]), fmt_p(q["p_two_sided"]), "", src3)
    add("RQ3", "Cliff's δ", f"{g['cliffs_delta']:+.3f} ({g['cliffs_magnitude']})",
        f"{q['cliffs_delta']:+.3f} ({q['cliffs_magnitude']})", "", src3)
    write(pd.DataFrame(rows), "comparison_table")

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(rq1.round(4).to_string(index=False))
    print(f"\n{len(rows)} linhas -> results/comparison/comparison_table.csv|md")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
