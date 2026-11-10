"""reports formats pdf xlsx

Revision ID: c4a91e2d7b53
Revises: b7f0d4e4825f
Create Date: 2026-11-11 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c4a91e2d7b53'
down_revision: Union[str, Sequence[str], None] = 'b7f0d4e4825f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Оставляет в reports.file_format только pdf и xlsx."""
    op.execute(
        "UPDATE reports SET file_format = NULL "
        "WHERE file_format IN ('txt', 'csv')"
    )
    op.drop_constraint('reports_format_check', 'reports', type_='check')
    op.create_check_constraint(
        'reports_format_check',
        'reports',
        "file_format IN ('pdf', 'xlsx')",
    )


def downgrade() -> None:
    """Возвращает прежний набор форматов."""
    op.drop_constraint('reports_format_check', 'reports', type_='check')
    op.create_check_constraint(
        'reports_format_check',
        'reports',
        "file_format IN ('pdf', 'xlsx', 'txt', 'csv')",
    )
