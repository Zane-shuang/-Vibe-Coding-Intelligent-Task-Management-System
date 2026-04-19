from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskListOut
from app.crud import task as task_crud
from typing import Optional, Literal
import math

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskOut, status_code=http_status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return task_crud.create_task(db, payload)

@router.get("", response_model=TaskListOut)
def list_tasks(
    # 筛选参数
    status: Optional[str] = Query(None, description="按任务状态筛选（如 pending/in_progress/completed）"),
    priority: Optional[str] = Query(None, description="按优先级筛选（如 low/medium/high）"),
    tag: Optional[str] = Query(None, description="按标签筛选（如 docs/backend）"),
    # 排序参数
    sort_by: Literal["created_at", "priority", "status", "id"] = Query("created_at", description="排序字段"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="排序方式：asc升序/desc降序"),
    # 分页参数
    page: int = Query(1, ge=1, description="当前页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100条"),
    # 数据库依赖
    db: Session = Depends(get_db)
):
    # 调用 CRUD 层的 list_tasks，拿到当前页的任务和总数
    tasks, total = task_crud.list_tasks(
        db=db,
        status=status,
        priority=priority,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    # 计算总页数
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # 按 TaskListOut 的格式返回
    return TaskListOut(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_crud.update_task(db, task, payload)

@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_crud.delete_task(db, task)
    return None