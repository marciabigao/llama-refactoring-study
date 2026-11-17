"""Tarefa 1.1 — Baixa o benchmark ClassEval (100 classes Python + testes unitários)."""
import json
import urllib.request

from _common import config

URL = "https://raw.githubusercontent.com/FudanSELab/ClassEval/master/data/ClassEval_data.json"

config.DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
print(f"Baixando {URL} ...")
with urllib.request.urlopen(URL, timeout=60) as r:
    raw = r.read()
tasks = json.loads(raw)
assert len(tasks) == 100, f"esperado 100 tarefas, veio {len(tasks)}"
n_methods = sum(len(t["methods_info"]) for t in tasks)
config.DATA_PATH.write_bytes(raw)
print(f"OK: {len(tasks)} classes, {n_methods} métodos -> {config.DATA_PATH}")
