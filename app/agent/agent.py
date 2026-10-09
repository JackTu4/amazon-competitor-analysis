import json
from pydantic import ValidationError
from app.models.competitor import CompetitorAnalysis
from app.tools.schema import tools
from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
from app.llm.client import client
from app.agent.prompts import system_prompt
def competitor_agent(target_product, competitor):
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": (
                f"请分析以下产品：\n"
                f"目标产品：{target_product}\n"
                f"竞品：{competitor}"
            )
        }
    ]
    try:
        response = client.chat.completions.create(
            model="qwen3.7-flash",
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message
        print("本次工具调用数量：", len(message.tool_calls or []))
        for call in message.tool_calls or []:
            print("工具名称：", call.function.name)
            print("工具参数：", call.function.arguments)
        if not message.tool_calls:
            return {
                "error": "没有调用搜索工具",
                "message": "LLM 没有发起商品搜索，无法完成分析"
            }
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                for call in message.tool_calls
            ]
        })
        for i, call in enumerate(message.tool_calls, start=1):
            print(f"\n========== 开始处理第 {i} 个商品 ==========")
            print("工具参数原文：", call.function.arguments)
            tool_data = {}
            try:
                args = json.loads(call.function.arguments)
                if call.function.name != "search_web":
                    raise ValueError(
                        f"不支持的工具：{call.function.name}"
                    )
                search_result = search_web(args["query"])
                if not search_result or not search_result.url:
                    raise ValueError("没有找到有效的商品网页")
                print("搜索标题：", search_result.title)
                print("搜索 URL：", search_result.url)
                page = read_webpage(search_result.url)
                print("网页读取成功")
                print("正文长度：", len(page["text"]))
                product_info = extract_product(
                    page["text"],
                    page["url"],
                    search_result.title
                )
                tool_data = product_info.model_dump()
                print("产品信息提取成功")
                print(
                    json.dumps(
                        tool_data,
                        ensure_ascii=False,
                        indent=2
                    )
                )
            except Exception as e:
                print("商品获取失败")
                print("具体异常类型：", type(e).__name__)
                print("具体异常信息：", e)
                tool_data = {
                    "search_query": args.get("query", "")
                    if "args" in locals() else "",
                    "error": str(e),
                    "message": "该商品无法获取可靠数据"
                }
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(
                    tool_data,
                    ensure_ascii=False
                )
            })
            print(f"第 {i} 个商品处理完毕")
        print("开始生成竞品分析")
        response = client.chat.completions.create(
            model="qwen3.7-flash",
            messages=messages,
            response_format={"type": "json_object"}
            )
        content = response.choices[0].message.content
        print("LLM 最终回答：")
        print(content)
        if not content:
            raise ValueError("LLM 没有返回最终分析内容")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("最终结果必须是 JSON 对象")
        if "error" in data:
            return data
        result = CompetitorAnalysis(**data)
        if not result.target_product.product.title:
            return {
                "error": "目标产品数据缺失",
                "message": "目标产品信息为空，暂不生成正式报告"
            }
        if not result.competitor.product.title:
            return {
                "error": "竞品数据缺失",
                "message": "竞品信息为空，暂不生成正式报告"
            }
        print("数据校验成功")
        return result
    except json.JSONDecodeError as e:
        print("JSON 解析失败：", e)
        return {
            "error": "JSON解析失败",
            "message": str(e)
        }
    except ValidationError as e:
        print("数据校验失败：", e)
        return {
            "error": "数据校验失败",
            "message": str(e)
        }
    except Exception as e:
        print("Agent 执行失败：", e)
        return {
            "error": "Agent执行失败",
            "message": str(e)
        }





