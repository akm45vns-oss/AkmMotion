"""enterprise_hardening_models

Revision ID: 5d2bf1514ae4
Revises: 
Create Date: 2026-09-16 17:23:17.512819

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5d2bf1514ae4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely without destructive drops of legacy tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Organizations
    if "organizations" not in existing_tables:
        op.create_table(
            'organizations',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('slug', sa.String(length=255), nullable=False),
            sa.Column('owner_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 2. Workspaces
    if "workspaces" not in existing_tables:
        op.create_table(
            'workspaces',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('organization_id', sa.UUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_workspaces_organization_id'), 'workspaces', ['organization_id'], unique=False)

    # 3. Organization Members
    if "organization_members" not in existing_tables:
        op.create_table(
            'organization_members',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('organization_id', sa.UUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False, default='editor'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_organization_members_organization_id'), 'organization_members', ['organization_id'], unique=False)
        op.create_index(op.f('ix_organization_members_user_id'), 'organization_members', ['user_id'], unique=False)

    # 4. Refresh Tokens
    if "refresh_tokens" not in existing_tables:
        op.create_table(
            'refresh_tokens',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('family_id', sa.UUID(), nullable=False),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
            sa.Column('device_info', sa.String(length=255), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_refresh_tokens_family_id'), 'refresh_tokens', ['family_id'], unique=False)
        op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
        op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # 5. User Usage
    if "user_usage" not in existing_tables:
        op.create_table(
            'user_usage',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('ai_requests_today', sa.Integer(), nullable=False, default=0),
            sa.Column('video_generations_today', sa.Integer(), nullable=False, default=0),
            sa.Column('render_jobs_today', sa.Integer(), nullable=False, default=0),
            sa.Column('rendered_seconds_total', sa.Float(), nullable=False, default=0.0),
            sa.Column('storage_bytes_total', sa.BigInteger(), nullable=False, default=0),
            sa.Column('estimated_cost_cents', sa.Integer(), nullable=False, default=0),
            sa.Column('last_reset_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_user_usage_user_id'), 'user_usage', ['user_id'], unique=True)

    # 6. Optional workspace_id column on projects
    if "projects" in existing_tables:
        project_columns = [col['name'] for col in inspector.get_columns('projects')]
        if "workspace_id" not in project_columns:
            op.add_column('projects', sa.Column('workspace_id', sa.UUID(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True))
            op.create_index(op.f('ix_projects_workspace_id'), 'projects', ['workspace_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "projects" in existing_tables:
        project_columns = [col['name'] for col in inspector.get_columns('projects')]
        if "workspace_id" in project_columns:
            op.drop_index(op.f('ix_projects_workspace_id'), table_name='projects')
            op.drop_column('projects', 'workspace_id')

    if "user_usage" in existing_tables:
        op.drop_index(op.f('ix_user_usage_user_id'), table_name='user_usage')
        op.drop_table('user_usage')

    if "refresh_tokens" in existing_tables:
        op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
        op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
        op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
        op.drop_table('refresh_tokens')

    if "organization_members" in existing_tables:
        op.drop_index(op.f('ix_organization_members_user_id'), table_name='organization_members')
        op.drop_index(op.f('ix_organization_members_organization_id'), table_name='organization_members')
        op.drop_table('organization_members')

    if "workspaces" in existing_tables:
        op.drop_index(op.f('ix_workspaces_organization_id'), table_name='workspaces')
        op.drop_table('workspaces')

    if "organizations" in existing_tables:
        op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
        op.drop_table('organizations')
