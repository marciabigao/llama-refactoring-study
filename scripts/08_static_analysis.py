"""RQ2 (tarefas 3.1–3.3): roda Flake8, Pylint, Lizard e complexidade cognitiva sobre
  (a) o código canônico do ClassEval,
  (b) os códigos refatorados pelo Qwen (results/<modelo>/parsed.jsonl),
  (c) os códigos refatorados pelo GPT-4o-mini (pacote de replicação do artigo, se presente).

As mesmas ferramentas e versões são aplicadas aos dois modelos, para uma comparação nas mesmas condições.
Detalhes das métricas e da configuração: src/static_tools.py.

Saídas (results/rq2/):
  static_metrics.csv   1 linha por (model, iteration, task_id); iteration = -1 é o canônico
  static_rules.csv     contagem por regra (flake8 / pylint) para cada (model, iteration, task_id)
  run_info.json        versões das ferramentas e grupos analisados

Uso:
  python scripts/07_get_gpt_package.py      # uma vez, para incluir o GPT
  python scripts/08_static_analysis.py
"""
import csv
import json
import time

from _common import config, load_tasks, read_jsonl, task_sort_key
from src import static_tools

OUT_DIR = config.RESULTS_ROOT / "rq2"
GPT_DIR = config.ROOT / "data" / "replication_package" / "data" / "rq1"
QWEN_LABEL = config.MODEL_SLUG
GPT_LABEL = "gpt-4o-mini"


def qwen_groups():
    parsed = read_jsonl(config.PARSED_PATH)
    if not parsed:
        raise SystemExit(f"[erro] {config.PARSED_PATH} não encontrado (rode 03_parse_and_stats.py)")
    tests = {(r["task_id"], r["iteration"]): r["passed"] for r in read_jsonl(config.TESTS_PATH)}
    groups = {}
    for r in parsed:
        if not r.get("code"):
            continue  # sem código extraível: fica fora da análise estática (registrado em run_info)
        groups.setdefault(r["iteration"], {})[r["task_id"]] = r["code"]
    return groups, tests, sum(1 for r in parsed if not r.get("code"))


def gpt_groups():
    if not GPT_DIR.is_dir():
        return {}, {}
    groups, tests = {}, {}
    for i in range(10):
        files_dir = GPT_DIR / f"iter_{i}" / "files"
        if not files_dir.is_dir():
            continue
        groups[i] = {p.stem: p.read_text(encoding="utf-8") for p in files_dir.glob("ClassEval_*.py")}
        test_csv = GPT_DIR / f"iter_{i}" / "test_results.csv"
        if test_csv.exists():
            with test_csv.open(encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    tests[(row["task_id"], i)] = row["test_pass"].strip() == "True"
    return groups, tests


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    canonical = {tid: t["solution_code"] for tid, t in tasks.items()}

    jobs = [("canonical", -1, canonical, {})]
    q_groups, q_tests, q_missing = qwen_groups()
    for it in sorted(q_groups):
        jobs.append((QWEN_LABEL, it, q_groups[it], q_tests))
    g_groups, g_tests = gpt_groups()
    if not g_groups:
        print("[aviso] pacote do GPT não encontrado: rode scripts/07_get_gpt_package.py para incluir o GPT-4o-mini")
    for it in sorted(g_groups):
        jobs.append((GPT_LABEL, it, g_groups[it], g_tests))

    metrics, rules, groups_info = [], [], []
    for model, it, sources, tests in jobs:
        t0 = time.time()
        rows, rule_rows = static_tools.analyze_group(sources)
        for r in rows:
            r["tests_passed"] = "" if model == "canonical" else tests.get((r["task_id"], it), "")
            metrics.append({"model": model, "iteration": it, **r})
        for r in rule_rows:
            rules.append({"model": model, "iteration": it, **r})
        groups_info.append({"model": model, "iteration": it, "n_files": len(sources)})
        print(f"  {model:14s} iter {it:>2}: {len(sources)} arquivos em {time.time() - t0:.0f}s")

    order = lambda r: (r["model"], r["iteration"], task_sort_key(r["task_id"]))  # noqa: E731
    metrics.sort(key=order)
    rules.sort(key=lambda r: (*order(r), r["tool"], r["rule"]))

    with (OUT_DIR / "static_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(metrics[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(metrics)
    with (OUT_DIR / "static_rules.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "iteration", "task_id", "tool", "rule", "count"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rules)
    info = {
        "tool_versions": static_tools.tool_versions(),
        "groups": groups_info,
        "qwen_generations_without_code": q_missing,
        "gpt_source": "Zenodo 10.5281/zenodo.17533631 (data/rq1/iter_*/files)" if g_groups else None,
        "notes": [
            "Todos os arquivos normalizados para terminar com uma única quebra de linha (remove o artefato W292).",
            "Flake8 com --isolated (configuração padrão) e plugins docstrings, bugbear, cognitive-complexity e commas.",
            "Pylint com configuração padrão (rcfile vazio), um processo por grupo de 100 arquivos, como no artigo.",
            "Ncloc/Statements/Complexity/Cognitive_Complexity calculados localmente (o artigo usou SonarCloud).",
        ],
    }
    (OUT_DIR / "run_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8", newline="\n")
    print(f"\n{len(metrics)} linhas -> results/rq2/static_metrics.csv")
    print(f"{len(rules)} linhas -> results/rq2/static_rules.csv")


if __name__ == "__main__":
    main()
