import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client=OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_URL"),
    timeout=520.0,
    max_retries=2
)
print("API URL:", client.base_url)
print("API Key 是否已读取:", bool(client.api_key))
print("API Key 前缀:", client.api_key[:6] if client.api_key else "未读取")
def get_embedding(text:str)->list[float]:
    response=client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL"),
        input=text,
    )
    return response.data[0].embedding