from pydantic import ValidationError
from app.models.competitor import CompetitorAnalysis
from app.tools.schema import tools
from app.tools.web_search import search_web
from app.llm.client import client
from app.agent.prompts import system_prompt
import json
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
            model="qwen3.8-27b",
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
                args=json.loads(tool_call.function.arguments)  #将 LLM 返回的 JSON 字符串解析成 Python 字典。
                search_result = search_web(args["query"])
                print("搜索结果")
                print(search_result)
        #把结果加入到messages中去
                messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call.id,
                    "content":json.dumps(
                        search_result.model_dump(),
                        ensure_ascii=False,
                )
            })
            print("准备第二次调用LLM")
            print("messages=",messages)
            response=client.chat.completions.create(
                model="qwen3.8-27b",
                messages=messages,
            )
            final_content = response.choices[0].message.content
            print("LLM最终回答：")
            print(final_content)
            data=json.loads(final_content)
            result=CompetitorAnalysis(**data)
            return result  #  最终结果结构化输出
        else:
            content = message.content
            data=json.loads(content)
            result=CompetitorAnalysis(**data)
            return result
    except json.JSONDecodeError:
        print("LLM返回不是JSON")
    except ValidationError as e:
        print("数据校验错误")
        print(e)
    except Exception as e:
        print(f"未知错误:{e}")