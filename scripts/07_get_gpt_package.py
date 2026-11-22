"""RQ2/RQ3 (preparação): baixa o pacote de replicação do artigo (Midolo et al.) do Zenodo.

O pacote (CC-BY 4.0, https://doi.org/10.5281/zenodo.17533631) traz os códigos refatorados pelo
GPT-4o-mini nos 10 ciclos, as métricas originais (Flake8, Pylint, SonarCloud) e a ferramenta de
legibilidade de Scalabrino (rsm.jar). Com ele, as mesmas ferramentas rodam sobre GPT e Qwen
nas mesmas condições.

Destino: data/replication_package/ (ignorado pelo git; ~87 MB baixados).
Uso: python scripts/07_get_gpt_package.py
"""
import shutil
import sys
import urllib.request
import zipfile

from _common import config

ZIP_URL = "https://zenodo.org/api/records/17533854/files/replication_package.zip/content"
DEST = config.ROOT / "data" / "replication_package"
ZIP_PATH = config.ROOT / "data" / "replication_package.zip"


def main():
    if (DEST / "data" / "rq1").is_dir():
        print("Pacote já presente em data/replication_package/ (nada a fazer).")
        return
    if not ZIP_PATH.exists():
        print("Baixando o pacote de replicação (~87 MB) do Zenodo...")
        tmp = ZIP_PATH.with_suffix(".part")
        with urllib.request.urlopen(ZIP_URL) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out)
        tmp.rename(ZIP_PATH)
    print("Extraindo...")
    DEST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        for member in zf.infolist():
            name = member.filename
            if name.startswith("__MACOSX") or name.endswith(".DS_Store"):
                continue
            # o zip tem uma pasta raiz "replication_package/"; extrai o conteúdo direto em DEST
            rel = name.split("/", 1)[1] if "/" in name else ""
            if not rel or ".." in rel.split("/"):
                continue
            target = DEST / rel
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    ZIP_PATH.unlink()
    if not (DEST / "data" / "rq1").is_dir():
        sys.exit("[erro] extração incompleta: data/replication_package/data/rq1 não encontrado")
    print("Pronto: data/replication_package/")


if __name__ == "__main__":
    main()
