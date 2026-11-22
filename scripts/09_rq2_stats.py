"""RQ2 (tarefas 3.3–3.5): estatísticas, Figura 3, Figura 4 e candidatos à Figura 5.

Entrada: results/rq2/static_metrics.csv (gerado por 08_static_analysis.py).
Convenção: δ = refatorado - canônico. δ < 0 = menos avisos / código menor ou menos complexo.

Saídas (results/rq2/):
  tables/rq2_summary[_passing].csv|md   por modelo e métrica: médias, δ, % melhorou/piorou/igual,
                                        Wilcoxon (canônico × média por tarefa nos ciclos), BH, r, Cliff's δ,
                                        e Wilcoxon pareado Qwen × GPT sobre o δ médio por tarefa
  tables/rq2_wilcoxon_per_iteration.csv Wilcoxon por ciclo (base da Figura 4), com BH por modelo
  figures/figure3_delta_boxplots.png    δ por ciclo para Cognitive Complexity, Complexity, Statements, Ncloc
  figures/figure4_heatmap_effect_r.png  efeito r do Wilcoxon por métrica × ciclo (GPT e Qwen lado a lado)
  examples/                             candidatos à Figura 5 (melhora estática com testes passando)

"_passing" = só pares cujo código refatorado passou em todos os testes.
Uso: python scripts/09_rq2_stats.py
"""
import difflib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from _common import config, load_tasks, read_jsonl  # noqa: E402
from src import stats_utils as su  # noqa: E402

RQ2 = config.RESULTS_ROOT / "rq2"
TABLES, FIGURES, EXAMPLES = RQ2 / "tables", RQ2 / "figures", RQ2 / "examples"
QWEN, GPT = config.MODEL_SLUG, "gpt-4o-mini"
MODEL_ORDER = [GPT, QWEN]
MODEL_LABEL = {GPT: "GPT-4o-mini", QWEN: "Qwen3.8-27B"}
COLOR = {GPT: "#2a78d6", QWEN: "#eb6834"}  # paleta categórica validada (slots 1 e 2)
INK, INK2, MUTED, SURFACE = "#0b0b0b", "#52514e", "#898781", "#fcfcfb"

SIZE_METRICS = ["Cognitive_Complexity", "Complexity", "Statements", "Ncloc"]
ISSUE_METRICS = [
    "flake_PycodestyleErrors", "flake_PycodestyleWarnings", "flake_PyFlakesErrors",
    "flake_DocstringIssues", "flake_BugRisks.BestPractices", "flake_McCabeComplexity", "flake_total",
    "pylint_convention", "pylint_refactor", "pylint_warning", "pylint_error", "pylint_total",
]
METRICS = SIZE_METRICS + ISSUE_METRICS


def write_table(df, name):
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{name}.csv", index=False, lineterminator="\n")
    (TABLES / f"{name}.md").write_text(df.to_markdown(index=False, floatfmt=".3f") + "\n",
                                       encoding="utf-8", newline="\n")


def paired(df, model):
    """Junta cada linha refatorada do modelo com o canônico da mesma tarefa."""
    can = df[df.model == "canonical"].set_index("task_id")[METRICS]
    ref = df[df.model == model].copy()
    for m in METRICS:
        ref[f"can_{m}"] = ref.task_id.map(can[m])
        ref[f"d_{m}"] = ref[m] - ref[f"can_{m}"]
    return ref


def summary(df, only_passing):
    rows, per_task_delta = [], {}
    for model in MODEL_ORDER:
        p = paired(df, model)
        if p.empty:
            continue
        if only_passing:
            p = p[p.tests_passed == True]  # noqa: E712
        per_task = p.groupby("task_id")[[*METRICS, *[f"can_{m}" for m in METRICS]]].mean()
        per_task_delta[model] = {m: per_task[m] - per_task[f"can_{m}"] for m in METRICS}
        for m in METRICS:
            d = p[f"d_{m}"].dropna()
            w = su.wilcoxon_paired(per_task[f"can_{m}"], per_task[m])
            rows.append({
                "model": MODEL_LABEL[model], "metric": m,
                "n_pairs": int(d.size), "n_tasks": int(per_task[m].notna().sum()),
                "mean_canonical": per_task[f"can_{m}"].mean(), "mean_refactored": per_task[m].mean(),
                "mean_delta": d.mean(), "median_delta": d.median(),
                "pct_improved": 100 * (d < 0).mean(), "pct_worsened": 100 * (d > 0).mean(),
                "pct_unchanged": 100 * (d == 0).mean(),
                "wilcoxon_W": w["W"], "p": w["p"], "r": w["r"],
                "cliffs_delta": su.cliffs_delta(per_task[f"can_{m}"], per_task[m]),
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_BH"] = np.nan
    for model in out.model.unique():
        idx = out.model == model
        out.loc[idx, "p_BH"] = su.bh_adjust(out.loc[idx, "p"])
    out["cliffs_magnitude"] = out.cliffs_delta.map(su.cliffs_magnitude)
    # Qwen × GPT: δ médio por tarefa, pareado por tarefa (só tarefas presentes nos dois)
    if GPT in per_task_delta and QWEN in per_task_delta:
        comp = {}
        for m in METRICS:
            a, b = per_task_delta[GPT][m], per_task_delta[QWEN][m]
            common = a.index.intersection(b.index)
            comp[m] = su.wilcoxon_paired(a[common], b[common])["p"]
        out["p_qwen_vs_gpt"] = out.metric.map(comp)
    return out


def per_iteration(df):
    rows = []
    for model in MODEL_ORDER:
        p = paired(df, model)
        for it, g in p.groupby("iteration"):
            for m in METRICS:
                w = su.wilcoxon_paired(g[f"can_{m}"], g[m])
                rows.append({"model": MODEL_LABEL[model], "iteration": int(it), "metric": m, **w})
    out = pd.DataFrame(rows)
    out["p_BH"] = np.nan
    for model in out.model.unique():
        idx = out.model == model
        out.loc[idx, "p_BH"] = su.bh_adjust(out.loc[idx, "p"])
    return out


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.yaxis.grid(True, color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)


def figure3(df):
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), facecolor=SURFACE)
    titles = {"Cognitive_Complexity": "Cognitive Complexity", "Complexity": "Complexity (cyclomatic)",
              "Statements": "Statements", "Ncloc": "NcLOC"}
    for ax, m in zip(axes.flat, SIZE_METRICS):
        ax.set_facecolor(SURFACE)
        pos, data, colors, labels = [], [], [], []
        x = 0
        for model in MODEL_ORDER:
            p = paired(df, model)
            for it in sorted(p.iteration.unique()):
                data.append(p[p.iteration == it][f"d_{m}"].dropna().values)
                pos.append(x)
                colors.append(COLOR[model])
                labels.append(str(int(it)))
                x += 1
            x += 1  # espaço entre os modelos
        bp = ax.boxplot(data, positions=pos, widths=0.6, patch_artist=True, showfliers=True,
                        medianprops={"color": INK, "linewidth": 1.5},
                        whiskerprops={"color": MUTED}, capprops={"color": MUTED},
                        flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": MUTED,
                                    "markeredgecolor": "none", "alpha": 0.6})
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.85)
            patch.set_edgecolor(SURFACE)
        ax.axhline(0, color=INK2, linewidth=1, linestyle="--")
        ax.set_xticks(pos)
        ax.set_xticklabels(labels)
        ax.set_title(titles[m], color=INK, fontsize=11, loc="left")
        ax.set_ylabel("δ (refatorado − canônico)", color=INK2, fontsize=9)
        style_axes(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[m]) for m in MODEL_ORDER]
    fig.legend(handles, [MODEL_LABEL[m] for m in MODEL_ORDER], loc="upper right", frameon=False,
               fontsize=9, labelcolor=INK2)
    fig.suptitle("Figura 3 — Diferença por ciclo (δ < 0 = código menor / menos complexo)",
                 x=0.01, ha="left", color=INK, fontsize=12)
    fig.supxlabel("ciclo", color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure3_delta_boxplots.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure4(it_df):
    metrics = [m for m in ISSUE_METRICS + SIZE_METRICS
               if not np.allclose(it_df[it_df.metric == m].r.fillna(0), 0)]
    cmap = LinearSegmentedColormap.from_list("div", ["#184f95", "#2a78d6", "#f0efec", "#e34948", "#9e2b2b"])
    panels = [m for m in MODEL_ORDER if MODEL_LABEL[m] in set(it_df.model)]
    widths = [it_df[it_df.model == MODEL_LABEL[m]].iteration.nunique() for m in panels]
    fig, axes = plt.subplots(1, len(panels), figsize=(3 + 0.55 * sum(widths), 0.42 * len(metrics) + 1.8),
                             gridspec_kw={"width_ratios": widths}, facecolor=SURFACE, squeeze=False)
    im = None
    for ax, model in zip(axes[0], panels):
        sub = it_df[it_df.model == MODEL_LABEL[model]]
        mat = sub.pivot(index="metric", columns="iteration", values="r").reindex(metrics)
        im = ax.imshow(mat.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
        for (i, j), v in np.ndenumerate(mat.values):
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="#ffffff" if abs(v) > 0.6 else INK)
        ax.set_xticks(range(mat.shape[1]))
        ax.set_xticklabels(mat.columns, fontsize=8, color=INK2)
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels(metrics if ax is axes[0][0] else [], fontsize=8, color=INK2)
        ax.set_title(MODEL_LABEL[model], color=INK, fontsize=10)
        ax.set_xlabel("ciclo", color=INK2, fontsize=8)
        for s in ax.spines.values():
            s.set_visible(False)
    cb = fig.colorbar(im, ax=axes[0].tolist(), fraction=0.03, pad=0.02)
    cb.set_label("efeito r do Wilcoxon (negativo = menos avisos / menor)", color=INK2, fontsize=8)
    cb.ax.tick_params(labelsize=7, colors=INK2)
    fig.suptitle("Figura 4 — Tamanho de efeito por ciclo", x=0.01, ha="left", color=INK, fontsize=12)
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure4_heatmap_effect_r.png", dpi=200, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def figure5_candidates(df):
    """Qwen: refatorações que passaram nos testes e mais reduziram avisos do Flake8."""
    p = paired(df, QWEN)
    p = p[(p.tests_passed == True) & (p.d_flake_total < 0)]  # noqa: E712
    p = p.sort_values(["d_flake_total", "d_pylint_total"]).head(5)
    cols = ["task_id", "iteration", "can_flake_total", "flake_total", "d_flake_total",
            "can_pylint_total", "pylint_total", "d_Cognitive_Complexity", "d_Ncloc"]
    write_table(p[cols], "rq2_figure5_candidates")
    tasks = load_tasks()
    code = {(r["task_id"], r["iteration"]): r["code"] for r in read_jsonl(config.PARSED_PATH)}
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    for _, r in p.iterrows():
        tid, it = r.task_id, int(r.iteration)
        diff = "\n".join(difflib.unified_diff(tasks[tid]["solution_code"].splitlines(),
                                              code[(tid, it)].splitlines(), "canonical", "qwen_refactored",
                                              lineterm=""))
        (EXAMPLES / f"{tid}_iter{it}.md").write_text(
            f"# {tid} (iteração {it}): candidato à Figura 5\n\n"
            f"Flake8: {int(r.can_flake_total)} → {int(r.flake_total)} avisos · "
            f"Pylint: {int(r.can_pylint_total)} → {int(r.pylint_total)} · "
            f"δ Cognitive Complexity: {r.d_Cognitive_Complexity:+.0f} · δ NcLOC: {r.d_Ncloc:+.0f}\n\n"
            f"```diff\n{diff}\n```\n", encoding="utf-8", newline="\n")


def main():
    df = pd.read_csv(RQ2 / "static_metrics.csv")
    df["tests_passed"] = df.tests_passed.map({True: True, False: False, "True": True, "False": False})
    models = set(df.model)
    if QWEN not in models:
        raise SystemExit("[erro] sem dados do Qwen em static_metrics.csv")
    if GPT not in models:
        print("[aviso] sem dados do GPT: a comparação fica só com o Qwen")
    write_table(summary(df, only_passing=False), "rq2_summary")
    write_table(summary(df, only_passing=True), "rq2_summary_passing")
    it_df = per_iteration(df)
    it_df.to_csv(TABLES / "rq2_wilcoxon_per_iteration.csv", index=False, lineterminator="\n")
    figure3(df)
    figure4(it_df)
    figure5_candidates(df)
    print("Tabelas em results/rq2/tables/, figuras em results/rq2/figures/, exemplos em results/rq2/examples/")


if __name__ == "__main__":
    main()
