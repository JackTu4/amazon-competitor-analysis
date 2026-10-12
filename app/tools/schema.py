tools=[
    {
          "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索互联网获取实时产品信息，适用于本地知识库资料不足或需要查询最新商品信息的情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要搜索的产品关键词，例如品牌、型号、容量和产品类型"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "检索本地亚马逊产品知识库，获取产品规格、容量、读取速度、接口、保修等信息。应优先调用此工具，再根据检索结果决定是否需要搜索网页",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要检索的产品问题"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回的相关资料数量，默认值为3"
                    }
                },
                "required": ["query"]
            }
        }
    },
        {
            "type": "function",
            "function": {
                "name": "discover_competitors",
                "description": "自动搜索、筛选并验证目标产品的亚马逊竞品，返回候选商品、ASIN、来源网址和参数核验状态。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_product": {
                            "type": "string",
                            "description": "目标产品名称、品牌及规格"
                        }
                    },
                    "required": ["target_product"],
                    "additionalProperties": False
                }
            }
        }
]