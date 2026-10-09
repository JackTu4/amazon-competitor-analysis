from app.rag.qa import answer_question
def main():
    print("=== 亚马逊竞品分析知识库 ===")
    print("输入 exit 退出程序。")
    while True:
        question = input("\n请输入你的问题：").strip()
        if question.lower() == "exit":
            print("已退出知识库。")
            break
        if not question:
            print("问题不能为空，请重新输入。")
            continue
        try:
            answer=answer_question(question)
            print("\n知识库回答:")
            print(answer)
        except Exception as e:
            print(f"\n查询失败:{e}")
if __name__ == "__main__":
    main()