"""RQ3: legibilidade com o modelo de Scalabrino et al. (2018), via rsm.jar do pacote de replicação.

Igual ao script readability.py do artigo: `java -jar rsm.jar <arquivo.py>` com cwd na pasta da
ferramenta, e o score é o primeiro número decimal da saída (intervalo 0–1). A ferramenta foi feita
para Java e lê o .py com um parser Java (as mensagens "no viable alternative..." no stderr são
esperadas). Isso é uma ameaça à validade herdada do artigo, mas mantém a comparabilidade.

Os arquivos vão para um diretório temporário com o nome <task_id>.py e são processados em lotes
(a ferramenta aceita vários arquivos por chamada). Só task_id e score são devolvidos; nenhum caminho
local entra nos resultados.
"""
import re
import subprocess
import tempfile
from pathlib import Path

LINE_RE = re.compile(r"^(?P<path>.+?)\t(?P<score>\d+\.\d+)\s*$")


def run_rsm(jar: Path, sources: dict, batch: int = 50) -> dict:
    """sources: {task_id: código}. Retorna {task_id: score}; tarefas sem score ficam de fora."""
    jar = Path(jar).resolve()
    scores = {}
    with tempfile.TemporaryDirectory(prefix="rq3_") as tmp:
        paths = []
        for tid, code in sources.items():
            p = Path(tmp) / f"{tid}.py"
            # Sem newline final, como os arquivos do pacote do artigo: o score é sensível a isso
            # (com newline a média canônica cai de 0,6199 para 0,6158). Mesmo tratamento para todos.
            p.write_text(code.rstrip(), encoding="utf-8", newline="\n")
            paths.append(p)
        for i in range(0, len(paths), batch):
            scores.update(_call(jar, paths[i:i + batch]))
        # Se a ferramenta quebra num arquivo, o resto do lote se perde: reprocessa um a um
        # (como o script do artigo, que chama o jar uma vez por arquivo).
        for p in paths:
            if p.stem not in scores:
                scores.update(_call(jar, [p]))
    return scores


def _call(jar: Path, paths) -> dict:
    res = subprocess.run(["java", "-jar", str(jar), *map(str, paths)], cwd=jar.parent,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = {}
    for line in res.stdout.splitlines():
        m = LINE_RE.match(line)
        if m:
            out[Path(m["path"]).stem] = float(m["score"])
    return out
