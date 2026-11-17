"""Executa o código (canônico ou refatorado) contra a suíte de testes do ClassEval.

Cada execução roda em um subprocesso Python separado, dentro de um diretório temporário próprio
(alguns testes do ClassEval criam/lêem arquivos), com timeout. Montagem do arquivo candidato,
como no avaliador do próprio ClassEval:  imports  +  código da classe  +  testes unittest.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from . import config

MARK = "@@RESULT@@"

_DRIVER = r'''
import sys, json, unittest, importlib.util, traceback
MARK = "@@RESULT@@"
def emit(d):
    sys.stdout.write("\n" + MARK + json.dumps(d) + "\n"); sys.stdout.flush()
try:
    spec = importlib.util.spec_from_file_location("candidate", "candidate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["candidate"] = mod
    spec.loader.exec_module(mod)
except BaseException as e:
    emit({"status": "import_error", "tests_run": 0, "n_failures": 0, "n_errors": 0,
          "failures": [{"test": "<import>", "kind": "error",
                        "message": "".join(traceback.format_exception_only(type(e), e))[-600:]}]})
    sys.exit(0)
suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
res = unittest.TestResult(); res.buffer = True
suite.run(res)
fails = [{"test": t.id(), "kind": "failure", "message": tb[-600:]} for t, tb in res.failures]
errs = [{"test": t.id(), "kind": "error", "message": tb[-600:]} for t, tb in res.errors]
ok = res.testsRun > 0 and not fails and not errs
emit({"status": "ok" if ok else "tests_failed", "tests_run": res.testsRun,
      "n_failures": len(fails), "n_errors": len(errs), "failures": (fails + errs)[:8]})
'''


def build_candidate(task: dict, code: str) -> str:
    imports = "\n".join(task.get("import_statement", []))
    return f"{imports}\n\n{code}\n\n{task['test']}\n"


def run_candidate(task: dict, code: str, timeout: int = None) -> dict:
    timeout = timeout or config.TEST_TIMEOUT_S
    with tempfile.TemporaryDirectory(prefix="ce_") as tmp:
        tmp = Path(tmp)
        (tmp / "candidate.py").write_text(build_candidate(task, code), encoding="utf-8")
        (tmp / "_driver.py").write_text(_DRIVER, encoding="utf-8")
        (tmp / "tmpdir").mkdir()  # TMPDIR próprio: ClassEval_92 etc. usam gettempdir() e colidiriam em paralelo
        try:
            p = subprocess.run([sys.executable, "_driver.py"], cwd=tmp, capture_output=True,
                               text=True, timeout=timeout, env=_env(tmp / "tmpdir"))
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "tests_run": 0, "n_failures": 0, "n_errors": 0,
                    "failures": [{"test": "<all>", "kind": "error", "message": f"timeout>{timeout}s"}]}
        for line in reversed(p.stdout.splitlines()):
            if line.startswith(MARK):
                return json.loads(line[len(MARK):])
        return {"status": "crash", "tests_run": 0, "n_failures": 0, "n_errors": 0,
                "failures": [{"test": "<process>", "kind": "error",
                              "message": (p.stderr or p.stdout)[-600:]}]}


def _env(tmpdir):
    import os
    e = dict(os.environ)
    e["TMPDIR"] = str(tmpdir)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["MPLBACKEND"] = "Agg"
    return e
