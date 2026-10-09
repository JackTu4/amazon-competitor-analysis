from openai import OpenAI
import os
from dotenv import load_dotenv
from app.rag.retriever import retrieve
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_URL"),
    timeout=520.0,
    max_retries=2
)
def answer_question(question: str) -> str:
    """检索相关产品资料，并让 LLM 基于资料回答问题。"""
    results = retrieve(question, top_k=3)
    context="\n\n".join(
        f"来源:{item['source']}\n内容:{item['text']}"
        for item in results
    )
    response = client.chat.completions.create(
        model="qwen3.7-flash",
        messages=[
            {
                "role":"system",
                "content":(
                    "你是一个专业的亚马逊产品分析助手。"
                    "请严格依据提供的参考资料回答问题。"
                    "如果资料中没有相关信息，请明确说明资料不足，"
                    "不要编造产品参数。"
                    "回答时尽量指出信息来源。"
            )
        },
                {"role":"user",
                "content":(
                    f"用户问题：{question}\n\n"
                    f"参考资料：\n{context}"
    )
             }
        ]
    )
    return response.choices[0].message.content or ""