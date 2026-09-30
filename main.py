from xml.dom import ValidationErr

from openai import OpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import json
class CompetitorAnalysis(BaseModel):
    competitor_name: Optional[str]
    competitor_title: Optional[str]
    asin: Optional[str]
    bullet_points: List[str]
    rating:Optional[float]
    reviews: Optional[str]
    price_difference: Optional[str]
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_URL"),
)
target_product=input("请输入目标产品:")
competitor=input("请输入竞品:")
system_prompt=f"""
你是一名专业的亚马逊竞品分析助手。

你的任务是根据用户提供的目标产品和竞品，
从以下维度进行竞品分析：

1. 竞品名称
2. 竞品标题
3. 竞品ASIN
4. 竞品五点
5. 竞品评级
6. 竞品评论
7. 价格差异
要求：
1. 输出清晰、结构化。
2. 不要编造不存在的信息。
3. 如果没有足够信息，明确说明“信息不足”。
4. 不要遗漏任何分析维度。

如果某项信息无法获取，请返回null，其中：
- bullet_points 如果无法获取，请返回空列表 []
- 其他无法获取的字段返回 null

不要编造信息。禁止填写中文占位文字。
请严格按照以下 JSON 格式输出：
{{
    "competitor_name": "...",
    "competitor_title": "...",
    "asin": "...",
    "bullet_points": [],
    "rating": null,
    "reviews": "...",
    "price_difference": "..."
}}
不要输出 JSON 之外的任何文字。
"""
user_prompt=f"""
请分析以下产品：

目标产品：{target_product}
竞品：{competitor}
"""
try:
    response = client.chat.completions.create(
        model="qwen3.8-27b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    content = response.choices[0].message.content
    data=json.loads(content)
    result=CompetitorAnalysis(**data)
    print(result)
except json.JSONDecodeError:
    print("LLM返回的内容不是合法JSON")
except ValidationErr as e:
    print("数据校验错误")
    print(e)
except Exception as e:
    print(f"发生未知错误:{e}")