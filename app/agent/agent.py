import json
import logging
from openai import BadRequestError
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
from app.agent.competitor_verifier import extract_asin

logger = logging.getLogger(__name__)


def _create_completion(messages, analysis_tools, tool_choice):
    """统一发起模型请求。

    思考模式模型（如 qwen3.8）不支持把 tool_choice 指定为具体函数，
    遇到该报错时自动降级，避免换模型后整条分析链路失效。
    """
    model = os.getenv("LLM_MODEL_NAME", "qwen3.7-flash")

    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=analysis_tools,
            tool_choice=tool_choice,
        )
    except BadRequestError as e:
        error_text = str(e)
        if "tool_choice" not in error_text or "thinking" not in error_text:
            raise

        if tool_choice == "none":
            # 连 tool_choice="none" 都不支持时，退化为纯文本请求
            logger.warning(
                "当前模型为思考模式，无法携带工具请求，改为纯文本请求"
            )
            return client.chat.completions.create(
                model=model,
                messages=messages,
            )

        logger.warning(
            "当前模型为思考模式，不支持指定 tool_choice=%s，自动改用 auto",
            tool_choice,
        )
        return client.chat.completions.create(
            model=model,
            messages=[
                *messages,
                {
                    "role": "system",
                    "content": "请先调用 search_knowledge 工具检索知识库，再决定后续步骤。",
                },
            ],
            tools=analysis_tools,
            tool_choice="auto",
        )


def _parse_final_result(
    message,
    target_asin=None,
    target_title=None,
    competitor_title=None,
    competitor_brand=None,
):
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
    expected_asin = (target_asin or "").strip().upper()
    actual_asin = (result.target_product.product.asin or "").strip().upper()

    if expected_asin and actual_asin and actual_asin != expected_asin:
        return {
            "error": "目标商品 ASIN 不一致",
            "message": (
                f"期望目标 ASIN {expected_asin}，"
                f"模型实际输出 {actual_asin}"
            ),
        }
    if expected_asin and not actual_asin:
        logger.warning(
            "模型未输出目标商品 ASIN，按已核验 ASIN 回填：%s",
            expected_asin,
        )
        result.target_product.product.asin = expected_asin

    # 目标页可能被 Amazon 降级页拦截，用发现阶段已核验的标题兜底
    if target_title and not result.target_product.product.title:
        logger.warning(
            "模型未输出目标产品标题，按已核验标题回填：%s",
            target_title,
        )
        result.target_product.product.title = target_title

    # 竞品页同样可能被降级页拦截，用发现阶段的搜索结果标题兜底
    if competitor_title and not result.competitor.product.title:
        logger.warning(
            "模型未输出竞品标题，按搜索结果标题回填：%s",
            competitor_title,
        )
        result.competitor.product.title = competitor_title

    # 品牌缺失会让竞品有效性判断失败，用发现阶段的品牌兜底
    if competitor_brand and not result.competitor.product.brand:
        logger.warning(
            "模型未输出竞品品牌，按发现阶段结果回填：%s",
            competitor_brand,
        )
        result.competitor.product.brand = competitor_brand

    logger.info(
        "最终结果校验：目标产品标题=%r，竞品标题=%r",
        result.target_product.product.title,
        result.competitor.product.title,
    )
    if not result.target_product.product.title:
        return {"error": "目标产品数据缺失", "message": "目标产品信息为空，暂不生成正式报告"}
    if not result.competitor.product.title:
        return {"error": "竞品数据缺失", "message": "竞品信息为空，暂不生成正式报告"}
    logger.debug("数据校验成功")
    return result

def competitor_agent(
      target_product,
      competitor,
      target_asin=None,
      competitor_asin=None,
      competitor_url=None,
      target_title=None,
      competitor_title=None,
      competitor_brand=None,
  ):
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
                  + (f"目标产品标题（已核验）：{target_title}\n"
                     if target_title else "")
                  + f"目标产品 ASIN（已核验，必须使用）：{target_asin or '未知'}\n"
                  f"竞品：{competitor}\n"
                  + (f"竞品标题（已核验）：{competitor_title}\n"
                     if competitor_title else "")
                  + (f"竞品品牌（已核验）：{competitor_brand}\n"
                     if competitor_brand else "")
                  + (f"竞品 ASIN（已核验，如提供必须使用）：{competitor_asin}\n"
                     if competitor_asin else "")
                  + (f"竞品链接：{competitor_url}\n"
                     if competitor_url else "")
                  + "请先检索知识库，再根据资料充分程度决定是否搜索网页。"
  )
        }
    ]
    target_review_analysis = None
    try:
        allowed_tools = {
            "search_knowledge",
            "search_web",
            "analyze_product_reviews",
        }
        analysis_tools = [
            tool for tool in tools
            if tool["function"]["name"] in allowed_tools
        ]

        if not any(
                tool["function"]["name"] == "search_knowledge"
                for tool in analysis_tools
        ):
            raise ValueError("tools 中没有定义 search_knowledge")

        response = _create_completion(
            messages,
            analysis_tools,
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge"
                }
            },
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
                result = _parse_final_result(
                    message,
                    target_asin,
                    target_title,
                    competitor_title,
                    competitor_brand,
                )
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

                        expected_asin = (args.get("asin") or "").strip().upper()

                        try:

                            if expected_asin:

                                if (

                                        len(expected_asin) != 10

                                        or not expected_asin.isalnum()

                                ):
                                    raise ValueError(

                                        f"无效的 ASIN：{expected_asin}"

                                    )

                                # 已知 ASIN 时直接读取详情页，不再自由搜索

                                page_url = (

                                    f"https://www.amazon.com/dp/{expected_asin}"

                                )

                                page = read_webpage(page_url)

                                if not page or not page.get("text"):
                                    raise ValueError(

                                        f"目标 ASIN 页面读取失败：{expected_asin}"

                                    )

                                product_info = extract_product(

                                    page["text"],

                                    page["url"],

                                    f"Amazon product {expected_asin}",

                                )

                                tool_data = product_info.model_dump()

                                tool_data.setdefault("product", {})

                                tool_data["product"]["asin"] = expected_asin

                                tool_data["search_snippet"] = ""


                            else:

                                search_results = search_web(args["query"])

                                if not search_results:
                                    raise ValueError(

                                        "没有找到有效的商品网页"

                                    )

                                search_result = search_results[0]

                                page = read_webpage(search_result.url)

                                product_info = extract_product(

                                    page["text"],

                                    page["url"],

                                    search_result.title,

                                )

                                tool_data = product_info.model_dump()

                                asin = extract_asin(page["url"])

                                if (

                                        asin

                                        and not tool_data.get("product", {}).get("asin")

                                ):
                                    tool_data["product"]["asin"] = asin

                                tool_data["search_snippet"] = search_result.content


                        except Exception as e:

                            logger.warning("网页读取或提取失败：%s", e)

                            tool_data = {

                                "url": (

                                    f"https://www.amazon.com/dp/{expected_asin}"

                                    if expected_asin else ""

                                ),
                                "extraction_error": str(e),
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
                response = _create_completion(
                    messages,
                    analysis_tools,
                    "none",
                )
            else:
                response = _create_completion(
                    messages,
                    analysis_tools,
                    "auto",
                )
            logger.info("大模型再次请求成功")
        message = response.choices[0].message
        if not message.tool_calls:
            result = _parse_final_result(
                message,
                target_asin,
                target_title,
                competitor_title,
                competitor_brand,
            )
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






