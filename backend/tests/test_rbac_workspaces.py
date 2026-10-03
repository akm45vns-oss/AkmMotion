import pytest
from uuid import uuid4
from app.db.session import AsyncSessionLocal
from app.models.models import Organization, Workspace, OrganizationMember, User, AuthProvider
from app.core.dependencies import check_role_permission, verify_workspace_access


def test_role_hierarchy_permissions():
    # Owner has all permissions
    assert check_role_permission("owner", "owner") is True
    assert check_role_permission("owner", "admin") is True
    assert check_role_permission("owner", "editor") is True
    assert check_role_permission("owner", "viewer") is True

    # Admin has admin, editor, viewer, but not owner
    assert check_role_permission("admin", "owner") is False
    assert check_role_permission("admin", "admin") is True
    assert check_role_permission("admin", "editor") is True
    assert check_role_permission("admin", "viewer") is True

    # Editor has editor and viewer
    assert check_role_permission("editor", "owner") is False
    assert check_role_permission("editor", "admin") is False
    assert check_role_permission("editor", "editor") is True
    assert check_role_permission("editor", "viewer") is True

    # Viewer only has viewer
    assert check_role_permission("viewer", "editor") is False
    assert check_role_permission("viewer", "viewer") is True


@pytest.mark.asyncio
async def test_workspace_rbac_access():
    async with AsyncSessionLocal() as db:
        owner_id = uuid4()
        editor_id = uuid4()
        outsider_id = uuid4()

        # Seed users
        db.add_all([
            User(id=owner_id, email=f"owner_{owner_id}@test.com", full_name="Owner", auth_provider=AuthProvider.email),
            User(id=editor_id, email=f"editor_{editor_id}@test.com", full_name="Editor", auth_provider=AuthProvider.email),
            User(id=outsider_id, email=f"outsider_{outsider_id}@test.com", full_name="Outsider", auth_provider=AuthProvider.email)
        ])
        await db.flush()

        # Create Organization
        org = Organization(
            name="Test Org",
            slug=f"test-org-{uuid4().hex[:6]}",
            owner_id=owner_id
        )
        db.add(org)
        await db.flush()

        # Create Workspace
        ws = Workspace(
            organization_id=org.id,
            name="Production Workspace",
            is_default=True
        )
        db.add(ws)
        await db.flush()

        # Add editor as member
        editor_member = OrganizationMember(
            organization_id=org.id,
            user_id=editor_id,
            role="editor"
        )
        db.add(editor_member)
        await db.commit()

        # Verify Owner access (all roles)
        assert await verify_workspace_access(ws.id, owner_id, "admin", db) is True
        assert await verify_workspace_access(ws.id, owner_id, "editor", db) is True
        assert await verify_workspace_access(ws.id, owner_id, "viewer", db) is True

        # Verify Editor access (editor and viewer, but NOT admin)
        assert await verify_workspace_access(ws.id, editor_id, "viewer", db) is True
        assert await verify_workspace_access(ws.id, editor_id, "editor", db) is True
        assert await verify_workspace_access(ws.id, editor_id, "admin", db) is False

        # Verify Outsider access (rejected for all)
        assert await verify_workspace_access(ws.id, outsider_id, "viewer", db) is False
