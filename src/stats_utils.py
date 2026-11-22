"""Estatística compartilhada por RQ2 e RQ3 (mesmos testes do artigo / pacote de replicação).

Convenção de sinal em todo o projeto: d = depois - antes (refatorado - canônico).
  RQ2: d < 0 = menos avisos / código menor ou menos complexo (melhora).
  RQ3: d > 0 = mais legível (melhora).
"""
import numpy as np
from scipy.stats import rankdata, wilcoxon
from statsmodels.stats.multitest import multipletests


def wilcoxon_paired(before, after, alternative="two-sided"):
    """Wilcoxon signed-rank pareado em (after - before), zero_method='wilcox' (como no artigo).

    Retorna dict com n (pares sem empate em zero), W (estatística do scipy), p,
    z (aproximação normal com correção de empates, sinal de after - before) e r = z / sqrt(n),
    o tamanho de efeito usado no heatmap da Figura 4 do artigo.
    """
    before = np.asarray(before, dtype=float)
    after = np.asarray(after, dtype=float)
    mask = np.isfinite(before) & np.isfinite(after)
    d = after[mask] - before[mask]
    d = d[d != 0]
    n = int(d.size)
    if n == 0:
        return {"n": 0, "W": np.nan, "p": 1.0, "z": 0.0, "r": 0.0}
    res = wilcoxon(d, zero_method="wilcox", alternative=alternative)
    ranks = rankdata(np.abs(d))
    w_plus = ranks[d > 0].sum()
    mean = n * (n + 1) / 4.0
    _, counts = np.unique(np.abs(d), return_counts=True)
    var = n * (n + 1) * (2 * n + 1) / 24.0 - (counts ** 3 - counts).sum() / 48.0
    z = (w_plus - mean) / np.sqrt(var) if var > 0 else 0.0
    return {"n": n, "W": float(res.statistic), "p": float(res.pvalue), "z": float(z), "r": float(z / np.sqrt(n))}


def cliffs_delta(before, after):
    """Cliff's delta como no pacote do artigo: P(after > before) - P(after < before) sobre todos os pares cruzados."""
    before = np.asarray(before, dtype=float)
    after = np.asarray(after, dtype=float)
    mask = np.isfinite(before) & np.isfinite(after)
    before, after = before[mask], after[mask]
    if before.size == 0:
        return np.nan
    diffs = np.subtract.outer(after, before)
    return float((np.sum(diffs > 0) - np.sum(diffs < 0)) / (before.size * after.size))


def cliffs_magnitude(delta):
    """Limiares de Romano et al. (2006), os mesmos do pacote do artigo."""
    if delta is None or not np.isfinite(delta):
        return "n/a"
    a = abs(delta)
    if a < 0.147:
        return "negligible"
    if a < 0.33:
        return "small"
    if a < 0.474:
        return "medium"
    return "large"


def bh_adjust(pvalues):
    """Correção de Benjamini–Hochberg (FDR), como em perform_wilcoxon.py do artigo."""
    p = np.asarray(pvalues, dtype=float)
    if p.size == 0:
        return p
    out = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    if ok.any():
        out[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return out


def mean_ci95(x):
    """Média e IC 95% (t de Student) — usado na Tabela 4 (Δ 95% CI)."""
    from scipy.stats import t
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return float(np.mean(x)) if n else np.nan, np.nan, np.nan
    m = x.mean()
    h = t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return float(m), float(m - h), float(m + h)
