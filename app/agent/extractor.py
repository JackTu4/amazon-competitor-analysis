import json
from app.llm.client import client
from app.models.extraction import ProductExtraction
def extract_product(text:str,url:str):
    text = text[:5000]
    print("文本长度:", len(text))
    print(text)
    prompt=f"""
你是亚马逊商品信息抽取专家。
规则：
1. 只提取第一个完整商品
2. 忽略:
   - 推荐商品
   - Similar item
   - More results
   - Brand store
   - 广告
3. 如果网页是搜索列表:
   返回最匹配query的第一个商品
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
1. 商品名称:
- 不包含Amazon.com
- 不包含Electronics
2. 商品标题:
- 只保留商品listing标题
3. ASIN:
- 从网页中找到ASIN
4. 品牌:
- Brand字段
5. 价格:
- 查找美元价格，例如 $37.99
- 找不到返回null
6. 五点描述:
- 只提取 About this item 下的5条
- 不要提取规格参数
不要猜测。
不存在返回null。"""
    print("发送给LLM文本长度:", len(text))
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
