"""RQ1 (tarefa 2.5) — Acha casos "parecia correto/modular, mas mudou o comportamento" (como a Figura 2).

Critério dos candidatos: o código canônico passa; a geração do Llama roda (sem erro de import/sintaxe),
falha SOMENTE por asserção (AssertionError => semântica alterada, não crash) e declarou refatorações.
Ranking: menos testes falhando primeiro (mudança sutil) e diff menor.
Saída: results/<modelo>/failure_cases/*.md  +  failure_cases_summary.csv. A ANÁLISE DESCRITIVA É SUA:
use o diff e as mensagens de asserção para explicar qual regra de negócio foi quebrada.
"""
import argparse
import difflib

import pandas as pd

from _common import config, load_tasks, read_jsonl

ap = argparse.ArgumentParser()
ap.add_argument("--top", type=int, default=5)
args = ap.parse_args()

config.ensure_dirs()
for old in config.FAILURE_DIR.glob("*.md"):
    old.unlink()
tasks = load_tasks()
tests = read_jsonl(config.TESTS_PATH)
parsed = {(r["task_id"], r["iteration"]): r for r in read_jsonl(config.PARSED_PATH)}
base_ok = {r["task_id"]: r["passed"] for r in read_jsonl(config.CANONICAL_BASELINE)}
if not base_ok:
    print("[aviso] sem canonical_baseline.jsonl; rode 04_run_tests.py --canonical. Assumindo canônico ok.")

cands = []
for r in tests:
    if r["status"] != "tests_failed" or r["n_errors"] > 0 or r["n_failures"] == 0:
        continue
    if not base_ok.get(r["task_id"], True):
        continue
    p = parsed.get((r["task_id"], r["iteration"]))
    if not p or not p["refactorings"]:
        continue
    orig = tasks[r["task_id"]]["solution_code"].splitlines()
    new = p["code"].splitlines()
    diff = list(difflib.unified_diff(orig, new, "canonical", "llama_refactored", lineterm=""))
    if not diff:  # código idêntico ao canônico => teste flaky/ambiente, não culpa do modelo
        continue
    cands.append((r["n_failures"], len(diff), r, p, diff))
cands.sort(key=lambda x: (x[0], x[1]))

print(f"Candidatos (falha semântica pura): {len(cands)}")
rows = []
for nf, dl, r, p, diff in cands:
    rows.append({"task_id": r["task_id"], "iteration": r["iteration"], "failing_tests": nf, "diff_lines": dl,
                 "claimed_refactorings": "; ".join(p["refactorings"])})
pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "failure_cases_summary.csv", index=False)

F = "`" * 3
for nf, dl, r, p, diff in cands[: args.top]:
    tid, it = r["task_id"], r["iteration"]
    t = tasks[tid]
    md = [f"# {tid} (iteração {it}) — {t['class_name']}", "",
          f"**Refatorações declaradas pelo modelo:** {', '.join(p['refactorings'])}", "",
          f"**Testes que falharam:** {nf} de {r['tests_run']}", ""]
    for f in r["failures"]:
        md += [f"- `{f['test']}` ({f['kind']}):", f"  {F}", "  " + f["message"].strip().replace("\n", "\n  "), f"  {F}"]
    md += ["", "## Diff (canônico -> Llama)", "", F + "diff", *diff, F, "",
           "## Código canônico", "", F + "python", t["solution_code"].rstrip(), F, "",
           "## Código refatorado pelo Llama", "", F + "python", p["code"].rstrip(), F, "",
           "## Sua análise (preencher)", "",
           "- O que o código original garantia?", "- O que a refatoração mudou?",
           "- Qual refatoração causou o desvio e por quê (ex.: colapsou um ramo, perdeu um return)?", ""]
    path = config.FAILURE_DIR / f"{tid}_iter{it}.md"
    path.write_text("\n".join(md), encoding="utf-8")
    print(f"  -> {path.name}: {nf} testes falhando, {dl} linhas de diff")
