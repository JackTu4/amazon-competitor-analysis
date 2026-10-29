import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.workflow.task import Task
task=Task(
    name="search_product"
)
print(task)
task.status="running"
print(task)
task.status="done"
task.result="搜索完成"
print(task)