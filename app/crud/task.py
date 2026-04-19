from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority, TaskDependency
from app.schemas.task import TaskCreate, TaskUpdate, DependencyCreate
from sqlalchemy import func
from typing import Optional, Tuple, List

# 新增：依赖相关CRUD
def add_task_dependency(
        db: Session,
        *,
        task_id: int,
        dep_data: DependencyCreate
) -> TaskDependency:
    """给任务添加一个依赖关系"""
    # 1. 先查当前任务和被依赖的任务是否存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"任务{task_id}不存在")

    dep_task = db.query(Task).filter(Task.id == dep_data.depends_on_task_id).first()
    if not dep_task:
        raise ValueError(f"被依赖的任务{dep_data.depends_on_task_id}不存在")

    # 2. 校验：不能自己依赖自己
    if task_id == dep_data.depends_on_task_id:
        raise ValueError("任务不能依赖自己")

    # 3. 校验：不能重复添加同一个依赖
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id == dep_data.depends_on_task_id
    ).first()
    if existing:
        raise ValueError("该依赖关系已存在")

    # 4. 校验：添加后会不会形成循环依赖（核心！）
    if _would_create_cycle(db, from_task_id=dep_data.depends_on_task_id, target_task_id=task_id):
        raise ValueError("不能创建循环依赖")

    # 5. 都没问题，就创建依赖关系
    new_dep = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dep_data.depends_on_task_id
    )
    db.add(new_dep)
    db.commit()
    db.refresh(new_dep)
    return new_dep

def remove_task_dependency(
    db: Session,
    *,
    task_id: int,
    depends_on_task_id: int
) -> None:
    """删除一个依赖关系"""
    dep = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id == depends_on_task_id
    ).first()
    if not dep:
        raise ValueError("依赖关系不存在")
    db.delete(dep)
    db.commit()

def _would_create_cycle(db: Session, from_task_id: int, target_task_id: int) -> bool:
    """
    用BFS判断：从from_task_id出发，顺着依赖链走，能不能走到target_task_id
    如果能，说明添加依赖后会形成循环
    """
    visited = set()
    queue = [from_task_id]

    while queue:
        current_id = queue.pop(0)
        if current_id == target_task_id:
            return True  # 找到目标，会形成循环
        if current_id in visited:
            continue
        visited.add(current_id)

        # 找所有当前任务的依赖（也就是所有「任务X依赖current_id」的X）
        next_tasks = db.query(TaskDependency.task_id).filter(
            TaskDependency.depends_on_task_id == current_id
        ).all()
        # 把这些任务加入队列
        for (next_id,) in next_tasks:
            if next_id not in visited:
                queue.append(next_id)
    return False  # 没找到，不会形成循环

def assert_can_complete_task(db: Session, task_id: int) -> None:
    """
    校验：任务的所有依赖是否都已完成
    如果有没完成的依赖，直接抛异常，让用户不能把任务标为completed
    """
    # 1. 找出当前任务的所有依赖
    dependencies = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id
    ).all()
    if not dependencies:
        return  # 没有依赖，直接通过

    # 2. 查这些依赖任务的状态
    dep_task_ids = [dep.depends_on_task_id for dep in dependencies]
    dep_tasks = db.query(Task).filter(Task.id.in_(dep_task_ids)).all()

    # 3. 找出没完成的依赖
    incomplete_deps = [t.id for t in dep_tasks if t.status != "completed"]
    if incomplete_deps:
        raise ValueError(f"任务无法完成，以下依赖任务未完成：{incomplete_deps}")

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
    # 新增：如果用户要把任务标为completed，先校验依赖是否都完成了
    if "status" in payload and payload["status"] == "completed":
        assert_can_complete_task(db, task.id)
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