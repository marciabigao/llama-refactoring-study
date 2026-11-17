import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402


def load_tasks():
    if not config.DATA_PATH.exists():
        sys.exit(f"[erro] {config.DATA_PATH} não existe. Rode: python scripts/01_download_classeval.py")
    tasks = json.loads(config.DATA_PATH.read_text(encoding="utf-8"))
    return {t["task_id"]: t for t in tasks}


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def task_sort_key(tid: str):
    return int(tid.split("_")[-1])
