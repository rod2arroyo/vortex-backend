"""Update Teams y Team Members

Revision ID: 8071fe172cac
Revises: dd5d8819dd8c
Create Date: 2026-02-20 11:24:23.111686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8071fe172cac'
down_revision: Union[str, Sequence[str], None] = 'dd5d8819dd8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Añadimos la columna permitiendo NULL
    op.add_column('teams', sa.Column('tag', sa.String(length=5), nullable=True))

    # 2. Llenamos con un tag basado en los primeros 3 caracteres del nombre + algo único
    # Esta consulta SQL toma los primeros 3 caracteres y le concatena un número aleatorio o parte del ID
    op.execute("UPDATE teams SET tag = UPPER(SUBSTRING(name FROM 1 FOR 3)) || SUBSTRING(id::text FROM 1 FOR 2)")

    # 3. Ponemos NOT NULL
    op.alter_column('teams', 'tag', nullable=False)

    # 4. Ahora sí, el índice único no fallará porque los tags son distintos
    op.add_column('teams', sa.Column('description', sa.Text(), nullable=True))
    op.create_index(op.f('ix_teams_tag'), 'teams', ['tag'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # El downgrade se mantiene igual, ya que borra la columna por completo
    op.drop_index(op.f('ix_teams_tag'), table_name='teams')
    op.drop_column('teams', 'description')
    op.drop_column('teams', 'tag')
