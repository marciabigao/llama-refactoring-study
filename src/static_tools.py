"""RQ2: execução das ferramentas de análise estática sobre um conjunto de classes.

Cada grupo (modelo × ciclo, ou canônico) é gravado num diretório temporário com um arquivo
<task_id>.py por classe, como no pacote de replicação do artigo. Flake8 e Pylint rodam UMA vez
por grupo, com cwd no diretório temporário e caminhos relativos, de modo que nenhum caminho
da máquina local entra nos resultados (só task_id e códigos de regra).

Ferramentas e configuração (iguais às inferidas do pacote de replicação):
  flake8 + plugins flake8-docstrings (D), flake8-bugbear (B), flake8-cognitive-complexity (CCR),
  flake8-commas (C8); configuração padrão (--isolated, linha máx. 79).
  pylint com configuração padrão; contagem por tipo (convention/refactor/warning/error/fatal/info).

Métricas de tamanho e complexidade (no artigo vieram do SonarCloud; aqui são calculadas localmente;
concordância exata com os valores do SonarCloud publicados para as 100 classes canônicas:
NcLOC 100%, Cognitive 92%, Statements 88%, Complexity 85%):
  Ncloc                 = NLOC do Lizard (linhas com código, sem comentários/linhas em branco)
  Statements            = nº de nós ast.stmt (todas as instruções, inclusive def/class/import)
  Complexity            = ciclomática no estilo Sonar: +1 por função, if/elif, for, while,
                          expressão condicional, cada operador and/or e cada `if` de compreensão
  Cognitive_Complexity  = soma, por função, da complexidade cognitiva (pacote cognitive_complexity)
  Lizard_CCN            = soma da complexidade ciclomática por função segundo o Lizard (referência)
"""
import ast
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import lizard
from cognitive_complexity.api import get_cognitive_complexity

FLAKE8_CATEGORIES = {  # mesma classificação de create_statistical_reports.py (pacote do artigo)
    "B": "BugRisks.BestPractices",
    "D": "DocstringIssues",
    "C": "McCabeComplexity",  # no artigo agrega CCR001 (cognitiva) e C8xx (vírgulas)
    "F": "PyFlakesErrors",
    "E": "PycodestyleErrors",
    "W": "PycodestyleWarnings",
}
PYLINT_TYPES = ["convention", "refactor", "warning", "error", "fatal", "info"]


def normalize_source(code: str) -> str:
    """Todos os arquivos terminam com exatamente uma quebra de linha.

    No pacote do artigo os arquivos não tinham newline final, o que gerava 1 aviso W292 por
    arquivo (artefato da gravação, não do código). Normalizando, o artefato some para todos.
    """
    return code.rstrip() + "\n"


def flake8_category(code: str) -> str:
    return FLAKE8_CATEGORIES.get(code[:1], "Unmapped")


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def run_flake8(workdir: Path):
    res = _run([sys.executable, "-m", "flake8", "--isolated", "--exit-zero",
                "--format=%(path)s|%(code)s", "."], workdir)
    if res.returncode not in (0, 1):
        raise RuntimeError(f"flake8 falhou: {res.stderr.strip()[:500]}")
    counts = Counter()  # (task_id, code) -> n
    for line in res.stdout.splitlines():
        if "|" not in line:
            continue
        path, code = line.rsplit("|", 1)
        counts[(Path(path).stem, code.strip())] += 1
    return counts


def run_pylint(workdir: Path, files):
    rc = workdir / "_empty_pylintrc"
    rc.write_text("", encoding="utf-8")
    res = _run([sys.executable, "-m", "pylint", "-j", "0", f"--rcfile={rc.name}",
                "--output-format=json", "--exit-zero", *files], workdir)
    try:
        msgs = json.loads(res.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"saída do pylint inválida: {res.stderr.strip()[:500]}") from exc
    counts = Counter()  # (task_id, type, message-id) -> n
    for m in msgs:
        counts[(Path(m["path"]).stem, m["type"], m["message-id"])] += 1
    return counts


def _statements(tree):
    return sum(1 for n in ast.walk(tree) if isinstance(n, ast.stmt))


def _sonar_like_complexity(tree):
    c = 0
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            c += 1
        elif isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp)):
            c += 1
        elif isinstance(n, ast.BoolOp):
            c += len(n.values) - 1
        elif isinstance(n, ast.comprehension):
            c += len(n.ifs)
    return c


def size_metrics(name: str, src: str) -> dict:
    out = {"Ncloc": None, "Statements": None, "Complexity": None,
           "Cognitive_Complexity": None, "Lizard_CCN": None, "syntax_ok": False}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    info = lizard.analyze_file.analyze_source_code(name, src)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    out.update({
        "Ncloc": info.nloc,
        "Statements": _statements(tree),
        "Complexity": _sonar_like_complexity(tree),
        "Cognitive_Complexity": sum(get_cognitive_complexity(f) for f in funcs),
        "Lizard_CCN": sum(f.cyclomatic_complexity for f in info.function_list),
        "syntax_ok": True,
    })
    return out


def analyze_group(sources: dict):
    """sources: {task_id: código}. Retorna (linhas por tarefa, linhas longas por regra)."""
    with tempfile.TemporaryDirectory(prefix="rq2_") as tmp:
        workdir = Path(tmp)
        files = []
        for tid, code in sources.items():
            (workdir / f"{tid}.py").write_text(normalize_source(code), encoding="utf-8", newline="\n")
            files.append(f"{tid}.py")
        flake = run_flake8(workdir)
        pyl = run_pylint(workdir, files)

    rows, rules = [], []
    for tid, code in sources.items():
        row = {"task_id": tid}
        row.update(size_metrics(f"{tid}.py", normalize_source(code)))
        cat = Counter()
        for (t, code_id), n in flake.items():
            if t == tid:
                cat[flake8_category(code_id)] += n
                rules.append({"task_id": tid, "tool": "flake8", "rule": code_id, "count": n})
        for c in FLAKE8_CATEGORIES.values():
            row[f"flake_{c}"] = cat.get(c, 0)
        row["flake_total"] = sum(cat.values())
        typ = Counter()
        for (t, mtype, mid), n in pyl.items():
            if t == tid:
                typ[mtype] += n
                rules.append({"task_id": tid, "tool": "pylint", "rule": mid, "count": n})
        for t in PYLINT_TYPES:
            row[f"pylint_{t}"] = typ.get(t, 0)
        row["pylint_total"] = sum(typ.values())
        rows.append(row)
    return rows, rules


def tool_versions() -> dict:
    """Versões dos pacotes (via metadados; não grava caminhos locais)."""
    from importlib.metadata import PackageNotFoundError, version
    out = {"python": sys.version.split()[0]}
    for pkg in ("flake8", "pyflakes", "pycodestyle", "flake8-docstrings", "flake8-bugbear",
                "flake8-cognitive-complexity", "flake8-commas", "pylint", "astroid", "lizard",
                "cognitive_complexity"):
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None
    return out
