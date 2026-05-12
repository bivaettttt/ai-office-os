from app.models.task import Task
from app.schemas.protocol import TaskStatus


class TaskManager:

    def __init__(self):

        self.tasks = {}

    # =====================================================
    # CREATE TASK
    # =====================================================

    def create_task(

        self,
        title: str,
        description: str,
        department: str,

    ):

        task = Task(
            title=title,
            description=description,
            department=department,
        )

        self.tasks[task.id] = task

        return task

    # =====================================================
    # GET ALL TASKS
    # =====================================================

    def get_tasks(self):

        return list(
            self.tasks.values()
        )

    # =====================================================
    # GET PENDING TASKS
    # =====================================================

    def get_pending_tasks(
        self,
        department: str,
    ):

        return [

            task

            for task in self.tasks.values()

            if (
                task.department == department
                and task.status
                in {
                    TaskStatus.CREATED,
                    TaskStatus.QUEUED,
                }
            )
        ]

    # =====================================================
    # ASSIGN TASK
    # =====================================================

    def assign_task(
        self,
        task_id: str,
        agent_id: str,
    ):

        task = self.tasks.get(task_id)

        if not task:
            return None

        task.assigned_to = agent_id

        task.status = TaskStatus.IN_PROGRESS

        return task


task_manager = TaskManager()
