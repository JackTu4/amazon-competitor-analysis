from openai import OpenAI
import httpx2
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_URL"),
    http_client=httpx2.Client(trust_env=False),
    timeout=520.0,
    max_retries=2,
)