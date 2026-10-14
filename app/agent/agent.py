import json
import logging
from pydantic import ValidationError
from app.models.competitor import CompetitorAnalysis
from app.tools.product_review_tool import analyze_product_reviews_tool
from app.tools.schema import tools
from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
from app.llm.client import client
from app.agent.prompts import system_prompt
from app.tools.knowledge_tool import search_knowledge
import os
from app.agent.result_processor import attach_review_analysis
from dotenv import load_dotenv
load_dotenv()
from app.tools.competitor_tool import discover_competitors_tool
from app.agent.competitor_verifier import extract_asin

logger = logging.getLogger(__name__)

def _parse_final_result(message):
    """把模型的最终 JSON 回答解析为 CompetitorAnalysis 或错误 dict。"""
    content = message.content
    if not content or not content.strip():
        raise ValueError("LLM 最终回答为空")
    content = content.strip()
    if content.startswith("```"):
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
        return {"error": "目标产品数据缺失", "message": "目标产品信息为空，暂不生成正式报告"}
    if not result.competitor.product.title:
        return {"error": "竞品数据缺失", "message": "竞品信息为空，暂不生成正式报告"}
    logger.debug("数据校验成功")
    return result

def competitor_agent(target_product, competitor,target_asin=None):
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
    target_review_analysis = None
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
            model=os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
            messages=messages,
            tools=tools,
            tool_choice={
                "type": "function",
                "function": {
                    "name": "search_knowledge"
                }
            }
        )
        max_rounds = 3
        for round_num in range(max_rounds):
            message = response.choices[0].message
            logger.info(
                "Agent 第 %s 轮，工具调用数量：%s",
                round_num + 1,
                len(message.tool_calls or []),
            )
            if not message.tool_calls:
                result = _parse_final_result(message)
                return attach_review_analysis(
                    result,
                    target_review_analysis
                )
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

                    elif tool_name=="discover_competitors":
                        logger.info("开始执行自动竞品发现")
                        tool_data = discover_competitors_tool(
                            target_product=args["target_product"]
                        )
                        logger.info("自动竞品发现完成")

                    elif tool_name == "analyze_product_reviews":
                        logger.info("开始执行商品评论分析")
                        try:
                            asin = (target_asin or args.get("asin", "")).strip().upper()

                            if not asin or len(asin) != 10 or not asin.isalnum():
                                raise ValueError(f"无效的 ASIN：{asin}")

                            logger.info("准备分析评论，ASIN：%s", asin)
                            tool_data = analyze_product_reviews_tool(asin=asin)
                            target_review_analysis = tool_data

                            logger.info(
                                "评论分析结果已保存，字段：%s",
                                list(target_review_analysis.keys())
                            )
                            logger.info("商品评论分析完成")
                        except Exception:
                            logger.exception("商品评论分析失败")
                            target_review_analysis = None
                            tool_data = {
                                "error": "商品评论分析失败"
                            }



                    elif tool_name == "search_web":
                        search_results = search_web(args["query"])
                        if not search_results:
                            raise ValueError("没有找到有效的商品网页")
                        search_result = search_results[0]
                        try:
                            page = read_webpage(search_result.url)
                            product_info = extract_product(
                                page["text"],
                                page["url"],
                                search_result.title
                            )
                            tool_data = product_info.model_dump()
                            asin = extract_asin(page["url"])
                            if asin and not tool_data.get("product", {}).get("asin"):
                                tool_data["product"]["asin"] = asin
                            tool_data["search_snippet"] = search_result.content
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
            if round_num == max_rounds - 1:
                # 最后一轮：强制模型停止调用工具，直接输出最终 JSON
                messages.append({
                    "role": "system",
                    "content": (
                        "已达到最大工具调用次数，请立即停止调用工具，"
                        "根据已获取的所有信息直接输出最终 JSON。"
                        "缺失字段填 null，缺失列表填 []，不得再调用任何工具。"
                    )
                })
                response = client.chat.completions.create(
                    model=os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
                    messages=messages,
                    tools=tools,
                    tool_choice="none",
                )
            else:
                response = client.chat.completions.create(
                    model=os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            logger.info("大模型再次请求成功")
        message = response.choices[0].message
        if not message.tool_calls:
            result = _parse_final_result(message)
            return attach_review_analysis(result, target_review_analysis)
        raise ValueError(
            f"达到最大工具调用轮数 {max_rounds}，"
            "模型仍未生成最终分析")

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






