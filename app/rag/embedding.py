import os
from openai import OpenAI
from functools import lru_cache
from dotenv import load_dotenv
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
from app.llm.client import client

load_dotenv()
@lru_cache(maxsize=512)
def _get_embedding_cached(text: str) -> tuple[float, ...]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return tuple(response.data[0].embedding)


def get_embedding(text: str) -> list[float]:
    return list(_get_embedding_cached(text))