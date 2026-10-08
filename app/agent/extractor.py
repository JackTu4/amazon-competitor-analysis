import json
from app.llm.client import client
from app.models.extraction import ProductExtraction
def extract_product(text:str,url:str,title: str):
    text = text[:5000]
    print("文本长度:", len(text))
    print(text)
    prompt = f"""
你是一个专业的亚马逊商品信息提取器。
你的唯一任务是：
从下面提供的 Amazon 网页文本中提取商品信息。

====================
【网页文本】
====================

{text}

====================
【数据来源规则】
====================

1. 只能使用上面的网页文本。
2. 不允许使用你的已有知识。
3. 不允许推测。
4. 不允许补充网页中不存在的信息。
5. 如果无法确认某个字段，返回 null。
6. 如果五点描述不存在，返回空列表 []。

====================
【字段提取规则】
====================
product.name：
- 从网页文本中提取商品名称。
- 优先使用 Model Name、商品标题等明确商品名称信息。
- 不要自己概括。
- 不要编造。

product.title：
- 只提取商品 listing 标题。
- 保留网页中的原始商品标题。
- 不要添加任何额外描述。

product.asin：
- 只提取网页中明确出现的 ASIN。
- 如果网页没有明确 ASIN，返回 null。
- 不允许根据 URL、标题或其他信息猜测 ASIN。

product.brand：
- 只提取网页中的 Brand。
- 如果没有明确 Brand，返回 null。
- 不允许根据商品名称推测品牌。

price.amount：
- 只提取当前商品明确显示的价格。
- 只提取数字。
- 如果没有明确价格，返回 null。

price.currency：
- 与当前商品价格对应的货币。
- 如果没有明确价格，返回 null。

features：
- 只提取 Amazon 的 About this item 中的商品卖点。
- 不要提取规格参数。
- 不要提取相关推荐商品。
- 不要提取广告商品。
- 不要提取导航信息。
- 每个 feature 必须包含 name 和 description。
- 如果没有明确的商品卖点，返回 []。

====================
【输出规则】
====================
1. 只能输出一个合法 JSON 对象。
2. 不允许输出 Markdown。
3. 不允许输出 ```json。
4. 不允许输出解释文字。
5. 不允许输出分析过程。
6. 不允许输出“以下是结果”等文字。
7. 不允许添加 schema 中不存在的字段。
8. 不允许删除 schema 中已有字段。
9. JSON 必须可以直接被 Python json.loads() 解析。
10.rating：
- 从 Customer Reviews 中提取评分。
- 例如：4.4 out of 5 stars → rating = 4.4。
- 如果网页没有明确评分，返回 null。
reviews：
- 从 Customer Reviews 中提取评论数量。
- 例如：(53) → reviews = 53。
- 如果网页没有明确评论数量，返回 null。
如果网页没有价格，price.amount 返回 null。
如果网页没有五点描述，bullet_points 返回 []。
不能根据常识补充。
====================
【输出格式】
====================
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
    "rating": null,
    "reviews": null,
    "bullet_points": [],
    "features": [],
    "source": {{
        "title": null,
        "url": "{url}"
    }}
}}
再次强调：
只输出 JSON。
不要输出任何其他文字。
"""
    print("发送给LLM文本长度:", len(text))
    response=client.chat.completions.create(
        model="qwen3.7-flash",
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
    data["source"]["url"] = url
    data["source"]["title"] = title
    result=ProductExtraction(**data)
    return result
