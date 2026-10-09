from pathlib import Path
def load_document(directory:str)->list[dict]:
    documents = []
    for path in Path(directory).glob("*"):
        if path .suffix.lower() not in {".md",".txt"}:
            continue
        text=path.read_text(encoding="utf-8")
        if not text.strip():
            continue
        documents.append({
            "text":text,
            "source":str(path)
        })
    return documents