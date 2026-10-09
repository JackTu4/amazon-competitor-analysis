import json
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = PROJECT_ROOT / "app" / "data" / "vector_store.json"
def save_vectors(embedded_chunks:list[dict])->None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            embedded_chunks, f, ensure_ascii=False
        )
    print(f"向量数据已保存到:{STORE_PATH}")
def load_vectors()->list[dict]:
    """从本地JSON文件读取文本,来源和向量"""
    if not STORE_PATH.exists():
        raise FileNotFoundError(
            f"向量文件不存在:{STORE_PATH},请先生成并保存向量"
        )
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
