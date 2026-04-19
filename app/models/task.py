import enum
from sqlalchemy import String, Text, DateTime, Enum, func, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)

    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index(
            "idx_tasks_status_priority_created_at",
            "status",
            "priority",
            "created_at",
        ),
    )

class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    # 当前任务（依赖别人的那个）
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    # 被依赖的任务（必须先完成的那个）
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False)

    # 约束1：同一个依赖关系不能重复添加（比如不能让任务5重复依赖任务3两次）
    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="_task_depends_on_uc"),
        # 约束2：不能自己依赖自己（比如任务5不能依赖任务5）
        CheckConstraint("task_id != depends_on_task_id", name="_no_self_dep_ck"),
        Index("idx_task_dependencies_task_id", "task_id"),
        Index("idx_task_dependencies_depends_on_task_id", "depends_on_task_id"),
    )

    # ORM关系映射，方便查询
    task = relationship("Task", foreign_keys="[TaskDependency.task_id]", backref="dependencies")
    depends_on_task = relationship("Task", foreign_keys="[TaskDependency.depends_on_task_id]", backref="dependents")