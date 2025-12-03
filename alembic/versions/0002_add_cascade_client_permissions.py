"""
add cascade to client_permissions foreign keys

Revision ID: 0002
Revises: 0001_initial
Create Date: 2025-11-27
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop existing foreign key constraints
    op.drop_constraint('client_permissions_client_id_fkey', 'client_permissions', type_='foreignkey')
    op.drop_constraint('client_permissions_permission_id_fkey', 'client_permissions', type_='foreignkey')
    
    # Recreate foreign key constraints with CASCADE
    op.create_foreign_key(
        'client_permissions_client_id_fkey',
        'client_permissions', 'clients',
        ['client_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'client_permissions_permission_id_fkey',
        'client_permissions', 'permissions',
        ['permission_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop CASCADE foreign key constraints
    op.drop_constraint('client_permissions_client_id_fkey', 'client_permissions', type_='foreignkey')
    op.drop_constraint('client_permissions_permission_id_fkey', 'client_permissions', type_='foreignkey')
    
    # Recreate foreign key constraints without CASCADE
    op.create_foreign_key(
        'client_permissions_client_id_fkey',
        'client_permissions', 'clients',
        ['client_id'], ['id']
    )
    op.create_foreign_key(
        'client_permissions_permission_id_fkey',
        'client_permissions', 'permissions',
        ['permission_id'], ['id']
    )
