import json
import logging
from pydantic import ValidationError
from app.models.competitor import CompetitorAnalysis
from app.tools.schema import tools
from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
from app.llm.client import client
from app.agent.prompts import system_prompt
from app.tools.knowledge_tool import search_knowledge

logger = logging.getLogger(__name__)


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
                f"竞品：{competitor}\n"
                f"请先检索知识库，再根据资料充分程度决定是否搜索网页。"
            )
        }
    ]
    try:
        knowledge_tools = [
            tool for tool in tools
            if tool["function"]["name"] == "search_knowledge"
        ]
        if not knowledge_tools:
            raise ValueError(
                "tools 中没有定义 search_knowledge"
            )
        response = client.chat.completions.create(
            model="qwen3.7-flash",
            messages=messages,
            tools=tools,
            tool_choice={
                "type": "function",
                "function": {
                    "name": "search_knowledge"
                }
            }
        )
        max_rounds = 5
        for round_num in range(max_rounds):
            message = response.choices[0].message
            logger.info(
                "Agent 第 %s 轮，工具调用数量：%s",
                round_num + 1,
                len(message.tool_calls or []),
            )
            if not message.tool_calls:
                content = message.content
                if not content or not content.strip():
                    raise ValueError("LLM 最终回答为空")
                content = content.strip()
                if content.startswith("```"):    #返回的内容带有前缀‘’‘
                    lines = content.splitlines()
                    if lines and lines[0].strip().startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("最终结果必须是 JSON 对象")
                if data.get("error"):
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
                logger.debug("数据校验成功")
                return result
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
            for call in message.tool_calls:
                logger.info("准备执行工具：%s", call.function.name)
                logger.info("工具参数：%s", call.function.arguments)
                try:
                    args = json.loads(call.function.arguments)
                    tool_name = call.function.name
                    if tool_name == "search_knowledge":
                        logger.info("开始执行知识库检索")
                        tool_data = search_knowledge(
                            query=args["query"],
                            top_k=args.get("top_k", 3)
                        )
                        logger.info("知识库检索完成")
                    elif tool_name == "search_web":
                        search_result = search_web(args["query"])
                        if not search_result or not search_result.url:
                            raise ValueError("没有找到有效的商品网页")
                        try:
                            page = read_webpage(search_result.url)
                            product_info = extract_product(
                                page["text"],
                                page["url"],
                                search_result.title
                            )
                            tool_data = product_info.model_dump()
                        except Exception as e:
                            logger.warning("网页读取或提取失败：%s", e)
                            tool_data = {
                                "title": search_result.title,
                                "url": search_result.url,
                                "content": search_result.content,
                                "extraction_error": str(e)
                            }

                    else:
                        raise ValueError(
                            f"未知工具：{tool_name}"
                        )
                except Exception as tool_error:
                    logger.warning("工具执行失败：%s", tool_error)
                    tool_data = {
                        "error": str(tool_error),
                        "message": "工具执行失败，请根据实际结果决定是否重试"
                    }
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(
                        tool_data,
                        ensure_ascii=False,
                        default=str
                    )
                })
            logger.info(
                "工具执行完毕，准备再次请求大模型，消息数量：%s",
                len(messages)
            )
            response = client.chat.completions.create(
                model="qwen3.7-flash",
                messages=messages,
                tools=tools,
                tool_choice="auto")
            logger.info("大模型再次请求成功")
        raise ValueError(
            f"达到最大工具调用轮数 {max_rounds}，"
            "模型仍未生成最终分析"
        )
    except json.JSONDecodeError as e:
        logger.warning("JSON 解析失败：%s", e)
        return {
            "error": "JSON解析失败",
            "message": str(e)}
    except ValidationError as e:
        logger.warning("数据校验失败：%s", e)
        return {
            "error": "数据校验失败",
            "message": str(e)
        }
    except Exception as e:
        logger.exception("Agent 执行失败")
        return {
            "error": "Agent执行失败",
            "message": str(e)
        }






