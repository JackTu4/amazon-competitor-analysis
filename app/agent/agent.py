from pydantic import ValidationError
from app.models.competitor import CompetitorAnalysis
from app.tools.schema import tools
from app.tools.web_search import search_web
from app.llm.client import client
from app.agent.prompts import system_prompt
import json
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
def competitor_agent(target_product, competitor):
    user_prompt=f"""
    请分析以下产品：

    目标产品:{target_product}
    竞品:{competitor}
    """
    try:
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        response = client.chat.completions.create(
            model="qwen3.7-flash",
            messages=messages,
            tools = tools
        )
        #判断有无tool_calls    出现选择分支   有就执行  无就直接解析
        message=response.choices[0].message
        if message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [                      #因为第一次调用  大语言模型需要进行工具调用  所以有tool_calls
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }

                for tool_call in message.tool_calls # 几个工具调用就使用几次ToolCalll
                ]

            })
            #执行所有的tool
            for tool_call in message.tool_calls:
                try:
                    args=json.loads(tool_call.function.arguments)  #将 LLM 返回的 JSON 字符串解析成 Python 字典。
                    search_result = search_web(args["query"])
                    print("搜索结果:")
                    print(search_result)
                    print("开始提取搜索结果中的产品信息")
                    product_info = extract_product(
                        search_result.content,
                        search_result.url,
                        search_result.title
                    )
                    if product_info.price.amount is None:
                        print("第一次搜索没有获取到价格，开始补充搜索价格")

                        price_result = search_web(
                            f"{product_info.product.name} "
                            f"{product_info.product.asin} "
                            f"Amazon price"
                        )
                        print("价格搜索结果:")
                        print(price_result)
                        if product_info.product.asin in price_result.content:
                            print("价格搜索结果 ASIN 校验成功")
                            price_info = extract_product(
                                price_result.content,
                                price_result.url,
                                price_result.title
                            )
                            if price_info.price.amount is not None:
                                product_info.price.amount = price_info.price.amount
                                product_info.price.currency = price_info.price.currency

                                print(
                                    "价格获取成功:",
                                    product_info.price.amount,
                                    product_info.price.currency
                                )
                        else:
                            print("价格补充搜索仍然没有找到价格")
                        # 如果第一次搜索没有获取到五点，进行补充搜索
                        if not product_info.bullet_points:
                            print("第一次搜索没有获取到五点，开始补充搜索")

                            bullet_query = (
                                f"{product_info.product.name} "
                                f"{product_info.product.asin} "
                                f"Amazon About this item"
                            )

                            print("五点搜索关键词:", bullet_query)

                            bullet_result = search_web(bullet_query)

                            print("五点搜索结果:")
                            print(bullet_result)
                            # 先检查搜索结果是不是同一个商品
                            if product_info.product.asin in bullet_result.content:
                                print("ASIN校验成功，确认是同一个商品")
                                bullet_info = extract_product(
                                    bullet_result.content,
                                    bullet_result.url,
                                    bullet_result.title
                                )
                                if bullet_info.bullet_points:
                                    product_info.bullet_points = bullet_info.bullet_points
                                    print("五点获取成功:")
                                    print(product_info.bullet_points)
                                else:
                                    print("搜索结果中仍然没有五点")
                            else:
                                print("ASIN校验失败，不使用该搜索结果")
                    print("产品信息提取成功")
                    print(product_info)
                    print("搜索结果")
                    print(search_result)
            #把结果加入到messages中去
                    tool_data = {   #  数据清洗  只保留自己想要的几个数据
                        "product":{
                        "name": product_info.product.name,
                        "title": product_info.product.title,
                        "asin": product_info.product.asin,
                        "brand": product_info.product.brand
                        },
                        "price": {
                            "amount": product_info.price.amount,
                            "currency": product_info.price.currency
                        },
                        "rating": product_info.rating,
                        "reviews": product_info.reviews,
                        "bullet_points": product_info.bullet_points,
                        "features": [
        {
            "name": feature.name,
            "description": feature.description
        }
        for feature in product_info.features[:5]
    ],
    "source": {
        "title": product_info.source.title,
        "url": product_info.source.url
        }
}
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            tool_data,
                            ensure_ascii=False
                        )
                    })
                except Exception as e:
                    print(
                        "产品分析失败:",
                        e
                    )
                    error_data = {
                        "error": str(e),
                        "message": "该产品无法获取数据"
                    }
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            error_data,
                            ensure_ascii=False
                        )
                    })
            print("准备第二次调用LLM")
            print("messages=",messages)
            response=client.chat.completions.create(
                model="qwen3.7-flash",
                messages=messages,
                response_format={
                    "type": "json_object"
                }
            )
            final_content = response.choices[0].message.content
            print("LLM最终回答：")
            print(final_content)
            data = json.loads(final_content)
            print("解析后的data:")
            print(data)
            data=json.loads(final_content)
            if "error" in data:
                print("竞品分析失败:")
                print(
                    data.get(
                        "message",
                        "产品数据获取失败"
                    )
                )
                return {
                    "error": data["error"],
                    "message": data.get(
                        "message",
                        "产品数据获取失败"
                    )
                }
            result=CompetitorAnalysis(**data)
            print("数据校验成功")
            return result  #  最终结果结构化输出
        else:
            content = message.content
            data=json.loads(content)
            if "error" in data:
                print("竞品分析失败:")
                print(
                    data.get(
                        "message",
                        "产品数据获取失败"
                    )
                )
                return {
                    "error": data["error"],
                    "message": data.get(
                        "message",
                        "产品数据获取失败"
                    )
                }
            result=CompetitorAnalysis(**data)
            return result
    except json.JSONDecodeError:
        print("LLM返回不是JSON")
        return {
            "error": "JSON解析失败",
            "message": "LLM返回的数据不是合法JSON"
        }
    except ValidationError as e:
        print("数据校验错误")
        print(e)
        return {
            "error": "数据校验失败",
            "message": str(e)
        }
    except Exception as e:
        print(f"未知错误:{e}")
        return {
            "error": "Agent执行失败",
            "message": str(e)
        }