from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from sqlalchemy import func
from typing import Optional, Tuple

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

def list_tasks(
    db: Session,
    *,
    status: Optional[str] = None,  # 筛选：任务状态
    priority: Optional[str] = None, # 筛选：优先级
    tag: Optional[str] = None,     # 筛选：包含某个标签
    sort_by: str = "created_at",  # 排序字段，默认按创建时间
    sort_order: str = "desc",     # 排序方式，默认倒序（新的在前）
    page: int = 1,               # 当前页码，默认第1页
    page_size: int = 20          # 每页条数，默认20条
) -> Tuple[list[Task], int]:
    # 1. 基础查询：从 Task 表查数据
    query = db.query(Task)

    # 2. 加筛选条件（Filtering）
    # 按状态筛选
    if status:
        query = query.filter(Task.status == status)
    # 按优先级筛选
    if priority:
        query = query.filter(Task.priority == priority)
    # 按标签筛选（MySQL JSON 数组筛选，比如 tags 是 ["docs", "backend"]，筛选包含"docs"的）
    if tag:
        # func.json_contains 是 MySQL 的 JSON 筛选函数，注意参数要和你存的 JSON 格式一致
        query = query.filter(func.json_contains(Task.tags, f'"{tag}"'))

    # 3. 加排序（Sorting）
    # 先定义「允许排序的字段白名单」，防止用户传不存在的字段或 SQL 注入
    allowed_sort_fields = {
        "created_at": Task.created_at,
        "priority": Task.priority,
        "status": Task.status,
        "id": Task.id
    }
    # 如果用户传的 sort_by 不在白名单里，就用默认的 created_at
    sort_column = allowed_sort_fields.get(sort_by, Task.created_at)
    # 升序还是降序
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 4. 先算「筛选后的总条数」（给分页用，注意：总数查询不要加 order/limit，只加筛选条件）
    total = query.count()

    # 5. 加分页（Pagination）：offset 是跳过多少条，limit 是取多少条
    offset = (page - 1) * page_size  # 比如第2页，每页20条，就是跳过20条，从第21条开始取
    query = query.offset(offset).limit(page_size)

    # 6. 执行查询，拿到当前页的数据
    tasks = query.all()

    # 返回：当前页的任务列表 + 筛选后的总条数
    return tasks, total

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