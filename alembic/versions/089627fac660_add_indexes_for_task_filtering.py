"""add indexes for task filtering

Revision ID: 089627fac660
Revises: 185e2219cd6f
Create Date: 2026-04-19 13:41:03.191291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '089627fac660'
down_revision: Union[str, Sequence[str], None] = '185e2219cd6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 给常用筛选字段加索引
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])

def downgrade() -> None:
    """Downgrade schema."""
    # 回滚的时候删除索引
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_priority", table_name="tasks")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
