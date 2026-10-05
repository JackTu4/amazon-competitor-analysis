from app.workflow.task import Task
class AnalysisWorkflow:
    def __init__(self):
        self.tasks=[]
    def add_task(self,task):
        self.tasks.append(task)
    def run(self):
        previous_result = None
        for task in self.tasks:
            print(
                "开始执行",
                task.name
            )
            task.status="running"
            try:
                if previous_result is None:
                    result=task.func()
                else:
                    result=task.func(previous_result)
                task.result=result
                previous_result = result
                task.status="done"
            except Exception as e:
                task.status="failed"
                task.error=str(e)
                break
        return self.tasks
        
