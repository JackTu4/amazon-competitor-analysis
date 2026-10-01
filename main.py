from app.agent.agent import competitor_agent
target_product = input("请输入目标产品：")
competitor = input("请输入竞品：")
result = competitor_agent(target_product, competitor)
print("\n分析结果：")
print(result)