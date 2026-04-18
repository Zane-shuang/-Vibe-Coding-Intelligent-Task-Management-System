from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate

def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(
        title=data.title,
        description=data.description,
        status=TaskStatus(data.status),
        priority=TaskPriority(data.priority),
        tags=data.tags,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()

def list_tasks(db: Session) -> list[Task]:
    return db.query(Task).order_by(Task.id.desc()).all()

def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    payload = data.model_dump(exclude_unset=True)
    if "status" in payload:
        payload["status"] = TaskStatus(payload["status"])
    if "priority" in payload:
        payload["priority"] = TaskPriority(payload["priority"])

    for k, v in payload.items():
        setattr(task, k, v)

    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()