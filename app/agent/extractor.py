import json
from app.llm.client import client
from app.models.extraction import ProductExtraction
def extract_product(text:str,url:str):
    print("文本长度:", len(text))
    prompt=f"""
你是一个专业的产品信息提取助手。
请从下面的网页正文中提取产品信息。
网页正文：
{text}
请严格按照下面的 JSON 结构返回：

{{
    "product": {{
        "name": null,
        "title": null,
        "asin": null,
        "brand": null
    }},
    "price": {{
        "amount": null,
        "currency": null
    }},
    "features": [
    {{
        "name": null,
        "description": null
    }}
],
    "source": {{
        "title": null,
        "url": "{url}"
    }}
}}
要求：
1. 只能提取网页中明确出现的信息。
2. 不要自己猜测。
3. 找不到的信息返回 null。
4. features 必须是数组。
5. features 中每个元素必须包含 name 和 description。
6. name 是功能名称，description 是功能的具体描述。
7. 只返回 JSON，不要返回其他文字。"""
    response=client.chat.completions.create(
        model="qwen3.8-27b",
        messages=[
            {
                "role":"system",
                "content":"你是一个专业的产品信息提取助手",
            },
            {
                "role":"user",
                "content":prompt,
            }
        ]
    )
    content=response.choices[0].message.content
    data=json.loads(content)
    result=ProductExtraction(**data)
    return result