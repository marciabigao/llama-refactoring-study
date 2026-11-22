"""RQ3 (tarefas 4.3–4.4): Tabela 4, Figura 6 e candidatos à Figura 7.

Entrada: results/rq3/readability_scores.csv (gerado por 10_readability.py).
Agregação igual à do artigo (verificada: reproduz exatamente a Tabela 4 com os dados do GPT do pacote):
o score "depois" de cada tarefa é a MÉDIA dos ciclos, e o "antes" é o score do canônico. Ficam só as tarefas
com score canônico. Δ = depois − antes (Δ > 0 = mais legível).

Testes: Wilcoxon pareado unilateral "depois > antes" (o do artigo; p alto = sem evidência de melhora),
mais o unilateral "depois < antes" (piora) e o bilateral; Cliff's δ como no pacote do artigo.

Saídas (results/rq3/):
  tables/table4_readability[_passing].csv|md   Tabela 4 por modelo (+ artigo) e Qwen × GPT
  tables/rq3_per_iteration.csv                 média e % melhorou/piorou por ciclo
  figures/figure6_paired_readability.png       canônico × refatorado por tarefa (acima da diagonal = melhorou)
  examples/                                    candidatos à Figura 7 (maiores quedas com testes passando)
Uso: python scripts/11_rq3_stats.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _common import config, load_tasks, read_jsonl  # noqa: E402
from src import stats_utils as su  # noqa: E402

RQ3 = config.RESULTS_ROOT / "rq3"
TABLES, FIGURES, EXAMPLES = RQ3 / "tables", RQ3 / "figures", RQ3 / "examples"
QWEN, GPT = config.MODEL_SLUG, "gpt-4o-mini"
MODEL_ORDER = [GPT, QWEN]
MODEL_LABEL = {GPT: "GPT-4o-mini", QWEN: "Qwen3.8-27B"}
COLOR = {GPT: "#2a78d6", QWEN: "#eb6834"}
INK, INK2, MUTED, SURFACE = "#0b0b0b", "#52514e", "#898781", "#fcfcfb"
PAPER = {  # Tabela 4 do artigo (GPT-4o-mini, 10 ciclos), para referência
    "model": "GPT-4o-mini (artigo)", "n_tasks": 99, "before_mean": 0.6199, "before_sd": 0.1002,
    "after_mean": 0.5959, "after_sd": 0.0847, "delta_mean": -0.0240, "delta_sd": 0.0690,
    "delta_ci_low": -0.0378, "delta_ci_high": -0.0102, "pct_improved": 29.3, "pct_worsened": 70.7,
    "W_greater": 1350.0, "p_greater": 1.000, "cliffs_delta": -0.183,
}


def write_table(df, name):
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{name}.csv", index=False, lineterminator="\n")
    (TABLES / f"{name}.md").write_text(df.to_markdown(index=False, floatfmt=".4f") + "\n",
                                       encoding="utf-8", newline="\n")


def per_task(df, model, only_passing=False):
    can = df[df.model == "canonical"].set_index("task_id").readability.dropna()
    ref = df[(df.model == model)].dropna(subset=["readability"])
    if only_passing:
        ref = ref[ref.tests_passed == True]  # noqa: E712
    after = ref.groupby("task_id").readability.mean()
    common = can.index.intersection(after.index)
    return pd.DataFrame({"before": can[common], "after": after[common]})


def table4(df, only_passing):
    rows, deltas = [], {}
    for model in MODEL_ORDER:
        t = per_task(df, model, only_passing)
        if t.empty:
            continue
        d = t.after - t.before
        deltas[model] = d
        m, lo, hi = su.mean_ci95(d)
        g = su.wilcoxon_paired(t.before, t.after, alternative="greater")
        less = su.wilcoxon_paired(t.before, t.after, alternative="less")
        two = su.wilcoxon_paired(t.before, t.after)
        cd = su.cliffs_delta(t.before, t.after)
        rows.append({
            "model": MODEL_LABEL[model], "n_tasks": len(t),
            "before_mean": t.before.mean(), "before_sd": t.before.std(ddof=1),
            "after_mean": t.after.mean(), "after_sd": t.after.std(ddof=1),
            "delta_mean": m, "delta_sd": d.std(ddof=1), "delta_ci_low": lo, "delta_ci_high": hi,
            "pct_improved": 100 * (d > 0).mean(), "pct_worsened": 100 * (d < 0).mean(),
            "W_greater": g["W"], "p_greater": g["p"], "p_less": less["p"], "p_two_sided": two["p"],
            "r": two["r"], "cliffs_delta": cd, "cliffs_magnitude": su.cliffs_magnitude(cd),
        })
    out = pd.DataFrame(rows)
    if not only_passing:
        out = pd.concat([pd.DataFrame([PAPER]), out], ignore_index=True)
    if GPT in deltas and QWEN in deltas:
        common = deltas[GPT].index.intersection(deltas[QWEN].index)
        p = su.wilcoxon_paired(deltas[GPT][common], deltas[QWEN][common])["p"]
        out["p_qwen_vs_gpt_delta"] = np.where(out.model.isin([MODEL_LABEL[GPT], MODEL_LABEL[QWEN]]), p, np.nan)
    return out


def per_iteration(df):
    can = df[df.model == "canonical"].set_index("task_id").readability.dropna()
    rows = []
    for model in MODEL_ORDER:
        for it, g in df[df.model == model].dropna(subset=["readability"]).groupby("iteration"):
            g = g[g.task_id.isin(can.index)]
            d = g.readability.values - can[g.task_id].values
            rows.append({"model": MODEL_LABEL[model], "iteration": int(it), "n": len(g),
                         "after_mean": g.readability.mean(), "delta_mean": d.mean(),
                         "pct_improved": 100 * (d > 0).mean(), "pct_worsened": 100 * (d < 0).mean()})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "rq3_per_iteration.csv", index=False, lineterminator="\n")
    return out


def figure6(df):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), facecolor=SURFACE, sharex=True, sharey=True)
    lim = (0.2, 0.95)
    for ax, model in zip(axes, MODEL_ORDER):
        t = per_task(df, model)
        d = t.after - t.before
        ax.set_facecolor(SURFACE)
        ax.plot(lim, lim, color=INK2, linewidth=1, linestyle="--", zorder=1)
        ax.scatter(t.before, t.after, s=34, color=COLOR[model], edgecolor=SURFACE, linewidth=1.2, zorder=2)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_aspect("equal")
        ax.set_title(f"{MODEL_LABEL[model]}  ·  melhorou {100 * (d > 0).mean():.1f}% · piorou "
                     f"{100 * (d < 0).mean():.1f}%", color=INK, fontsize=10, loc="left")
        ax.set_xlabel("legibilidade do canônico", color=INK2, fontsize=9)
        ax.text(0.23, 0.91, "acima da diagonal = mais legível", color=MUTED, fontsize=8, va="top")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(MUTED)
        ax.tick_params(colors=INK2, labelsize=8)
        ax.grid(True, color="#e6e5e1", linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("legibilidade do refatorado (média dos ciclos)", color=INK2, fontsize=9)
    fig.suptitle("Figura 6 — Legibilidade por tarefa: canônico × refatorado (Scalabrino et al., 0–1)",
                 x=0.01, ha="left", color=INK, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure6_paired_readability.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure7_candidates(df):
    """Qwen: refatorações que passaram nos testes e mais perderam legibilidade (e a que mais ganhou)."""
    can = df[df.model == "canonical"].set_index("task_id").readability
    q = df[(df.model == QWEN) & (df.tests_passed == True)].dropna(subset=["readability"]).copy()  # noqa: E712
    q["canonical"] = q.task_id.map(can)
    q = q.dropna(subset=["canonical"])
    q["delta"] = q.readability - q.canonical
    picks = pd.concat([q.nsmallest(3, "delta"), q.nlargest(1, "delta")])
    write_table(picks[["task_id", "iteration", "canonical", "readability", "delta"]], "rq3_figure7_candidates")
    tasks = load_tasks()
    code = {(r["task_id"], r["iteration"]): r["code"] for r in read_jsonl(config.PARSED_PATH)}
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    for _, r in picks.iterrows():
        tid, it = r.task_id, int(r.iteration)
        (EXAMPLES / f"{tid}_iter{it}.md").write_text(
            f"# {tid} (iteração {it}): legibilidade {r.canonical:.2f} → {r.readability:.2f} (Δ {r.delta:+.2f})\n\n"
            "Testes: passou. Candidato à Figura 7.\n\n"
            f"## Canônico\n\n```python\n{tasks[tid]['solution_code'].rstrip()}\n```\n\n"
            f"## Refatorado pelo Qwen\n\n```python\n{code[(tid, it)].rstrip()}\n```\n", encoding="utf-8", newline="\n")


def main():
    df = pd.read_csv(RQ3 / "readability_scores.csv")
    df["tests_passed"] = df.tests_passed.map({True: True, False: False, "True": True, "False": False})
    write_table(table4(df, only_passing=False), "table4_readability")
    write_table(table4(df, only_passing=True), "table4_readability_passing")
    per_iteration(df)
    figure6(df)
    figure7_candidates(df)
    print("Tabelas em results/rq3/tables/, figura em results/rq3/figures/, exemplos em results/rq3/examples/")


if __name__ == "__main__":
    main()
