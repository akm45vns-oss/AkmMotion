import pytest
from uuid import uuid4, UUID
from httpx import AsyncClient
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.models import (
    User,
    Organization,
    Workspace,
    OrganizationMember,
    Project,
    Script,
    Scene,
    AuthProvider
)
from app.core.security import create_access_token


@pytest.fixture
async def rbac_setup():
    """
    Sets up a full enterprise RBAC multi-tenant environment:
    Org 1:
      - Owner: User 1
      - Admin: User 2
      - Editor: User 3
      - Viewer: User 4
      - Default Workspace
      - Team Workspace
    Org 2 (isolated tenant):
      - Owner: User 5
      - Default Workspace
    Outsider: User 6 (no org membership)
    """
    owner_id = uuid4()
    admin_id = uuid4()
    editor_id = uuid4()
    viewer_id = uuid4()
    outsider_id = uuid4()
    org2_owner_id = uuid4()

    async with AsyncSessionLocal() as session:
        # Create users
        users = [
            User(id=owner_id, email=f"owner_{owner_id.hex[:6]}@test.com", full_name="Org Owner", auth_provider=AuthProvider.email, is_active=True),
            User(id=admin_id, email=f"admin_{admin_id.hex[:6]}@test.com", full_name="Org Admin", auth_provider=AuthProvider.email, is_active=True),
            User(id=editor_id, email=f"editor_{editor_id.hex[:6]}@test.com", full_name="Org Editor", auth_provider=AuthProvider.email, is_active=True),
            User(id=viewer_id, email=f"viewer_{viewer_id.hex[:6]}@test.com", full_name="Org Viewer", auth_provider=AuthProvider.email, is_active=True),
            User(id=outsider_id, email=f"outsider_{outsider_id.hex[:6]}@test.com", full_name="Outsider", auth_provider=AuthProvider.email, is_active=True),
            User(id=org2_owner_id, email=f"org2_owner_{org2_owner_id.hex[:6]}@test.com", full_name="Org2 Owner", auth_provider=AuthProvider.email, is_active=True),
        ]
        session.add_all(users)
        await session.flush()

        # Create Org 1
        org1 = Organization(
            name="Matrix Corp",
            slug=f"matrix-corp-{uuid4().hex[:6]}",
            owner_id=owner_id
        )
        session.add(org1)
        await session.flush()

        # Org 1 default workspace
        org1_ws_default = Workspace(
            organization_id=org1.id,
            name="Default Workspace",
            is_default=True
        )
        # Org 1 team workspace
        org1_ws_team = Workspace(
            organization_id=org1.id,
            name="Team Workspace",
            is_default=False
        )
        session.add_all([org1_ws_default, org1_ws_team])
        await session.flush()

        # Org 1 members
        session.add_all([
            OrganizationMember(organization_id=org1.id, user_id=owner_id, role="owner"),
            OrganizationMember(organization_id=org1.id, user_id=admin_id, role="admin"),
            OrganizationMember(organization_id=org1.id, user_id=editor_id, role="editor"),
            OrganizationMember(organization_id=org1.id, user_id=viewer_id, role="viewer"),
        ])

        # Create Org 2 (completely separate organization)
        org2 = Organization(
            name="Rival Enterprise",
            slug=f"rival-ent-{uuid4().hex[:6]}",
            owner_id=org2_owner_id
        )
        session.add(org2)
        await session.flush()

        org2_ws_default = Workspace(
            organization_id=org2.id,
            name="Rival Default",
            is_default=True
        )
        session.add(org2_ws_default)
        session.add(OrganizationMember(organization_id=org2.id, user_id=org2_owner_id, role="owner"))

        # Create a project in Org 1 Team Workspace
        org1_project = Project(
            user_id=owner_id,
            workspace_id=org1_ws_team.id,
            title="Confidential Enterprise Project",
            description="Org 1 shared project",
            style="Cinematic",
            language="en"
        )
        session.add(org1_project)
        await session.flush()

        # Create a script and scene in Org 1 Project
        org1_script = Script(
            project_id=org1_project.id,
            content="Welcome to Matrix Corp confidential briefing.",
            language="en"
        )
        session.add(org1_script)
        await session.flush()

        org1_scene = Scene(
            project_id=org1_project.id,
            script_id=org1_script.id,
            scene_number=1,
            narration="Welcome to Matrix Corp confidential briefing.",
            subtitle="Welcome to Matrix Corp confidential briefing.",
            image_prompt="High-tech corporate boardroom with cinematic lighting"
        )
        session.add(org1_scene)

        # Create a project in Org 2 Default Workspace
        org2_project = Project(
            user_id=org2_owner_id,
            workspace_id=org2_ws_default.id,
            title="Rival Secret Project",
            description="Org 2 proprietary project",
            style="Tech",
            language="en"
        )
        session.add(org2_project)
        await session.commit()

        org1_id = org1.id
        org1_ws_default_id = org1_ws_default.id
        org1_ws_team_id = org1_ws_team.id
        org1_project_id = org1_project.id
        org1_scene_id = org1_scene.id
        org2_id = org2.id
        org2_ws_default_id = org2_ws_default.id
        org2_project_id = org2_project.id

    # Generate bearer tokens
    return {
        "owner": {"id": owner_id, "token": create_access_token(subject=str(owner_id))},
        "admin": {"id": admin_id, "token": create_access_token(subject=str(admin_id))},
        "editor": {"id": editor_id, "token": create_access_token(subject=str(editor_id))},
        "viewer": {"id": viewer_id, "token": create_access_token(subject=str(viewer_id))},
        "outsider": {"id": outsider_id, "token": create_access_token(subject=str(outsider_id))},
        "org2_owner": {"id": org2_owner_id, "token": create_access_token(subject=str(org2_owner_id))},
        "org1_id": org1_id,
        "org1_ws_default_id": org1_ws_default_id,
        "org1_ws_team_id": org1_ws_team_id,
        "org1_project_id": org1_project_id,
        "org1_scene_id": org1_scene_id,
        "org2_id": org2_id,
        "org2_ws_default_id": org2_ws_default_id,
        "org2_project_id": org2_project_id,
    }


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. ORGANIZATION RBAC MATRIX (Create, Read, Update, Delete, Transfer)
# ==============================================================================
@pytest.mark.asyncio
async def test_rbac_organization_matrix(client: AsyncClient, rbac_setup):
    ctx = rbac_setup
    org1_id = str(ctx["org1_id"])

    # 1.1 Read/List Organizations
    # Owner, Admin, Editor, Viewer must see org1
    for role in ["owner", "admin", "editor", "viewer"]:
        res = await client.get("/api/v1/workspaces/organizations", headers=auth_header(ctx[role]["token"]))
        assert res.status_code == 200, f"{role} failed to list organizations"
        org_ids = [o["id"] for o in res.json()["organizations"]]
        assert org1_id in org_ids, f"{role} should see org1"

    # Outsider must NOT see org1
    res = await client.get("/api/v1/workspaces/organizations", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 200
    org_ids = [o["id"] for o in res.json()["organizations"]]
    assert org1_id not in org_ids, "Outsider should not see org1"

    # 1.2 Update Organization (Rename)
    # Owner can rename -> 200
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}", json={"name": "Matrix Corp Renamed By Owner"}, headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 200
    assert res.json()["name"] == "Matrix Corp Renamed By Owner"

    # Admin can rename -> 200
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}", json={"name": "Matrix Corp Renamed By Admin"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 200
    assert res.json()["name"] == "Matrix Corp Renamed By Admin"

    # Editor cannot rename -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}", json={"name": "Hacked By Editor"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Viewer cannot rename -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}", json={"name": "Hacked By Viewer"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Outsider cannot rename -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}", json={"name": "Hacked By Outsider"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # 1.3 Transfer Ownership
    # Non-owners (admin, editor, viewer, outsider) cannot transfer ownership -> 403
    for role in ["admin", "editor", "viewer", "outsider"]:
        res = await client.post(
            f"/api/v1/workspaces/organizations/{org1_id}/transfer",
            json={"new_owner_id": str(ctx["admin"]["id"])},
            headers=auth_header(ctx[role]["token"])
        )
        assert res.status_code == 403, f"{role} should not be allowed to transfer org ownership"

    # Owner cannot transfer to a non-member -> 400
    res = await client.post(
        f"/api/v1/workspaces/organizations/{org1_id}/transfer",
        json={"new_owner_id": str(ctx["outsider"]["id"])},
        headers=auth_header(ctx["owner"]["token"])
    )
    assert res.status_code == 400

    # Owner transfers to admin -> 200
    res = await client.post(
        f"/api/v1/workspaces/organizations/{org1_id}/transfer",
        json={"new_owner_id": str(ctx["admin"]["id"])},
        headers=auth_header(ctx["owner"]["token"])
    )
    assert res.status_code == 200
    assert res.json()["new_owner_id"] == str(ctx["admin"]["id"])

    # Former owner is now admin; cannot transfer back
    res = await client.post(
        f"/api/v1/workspaces/organizations/{org1_id}/transfer",
        json={"new_owner_id": str(ctx["owner"]["id"])},
        headers=auth_header(ctx["owner"]["token"])
    )
    assert res.status_code == 403

    # New owner (admin) transfers back to original owner -> 200
    res = await client.post(
        f"/api/v1/workspaces/organizations/{org1_id}/transfer",
        json={"new_owner_id": str(ctx["owner"]["id"])},
        headers=auth_header(ctx["admin"]["token"])
    )
    assert res.status_code == 200

    # 1.4 Delete Organization
    # Create a disposable org to test delete permissions
    res = await client.post("/api/v1/workspaces/organizations", json={"name": "Disposable Org"}, headers=auth_header(ctx["owner"]["token"]))
    disp_org_id = res.json()["organization"]["id"]

    # Admin, Editor, Viewer, Outsider cannot delete org -> 403
    for role in ["admin", "editor", "viewer", "outsider"]:
        del_res = await client.delete(f"/api/v1/workspaces/organizations/{disp_org_id}", headers=auth_header(ctx[role]["token"]))
        assert del_res.status_code == 403, f"{role} should be forbidden from deleting org"

    # Owner can delete org -> 204
    del_res = await client.delete(f"/api/v1/workspaces/organizations/{disp_org_id}", headers=auth_header(ctx["owner"]["token"]))
    assert del_res.status_code == 204


# ==============================================================================
# 2. WORKSPACE RBAC MATRIX (Create, Read, Update, Delete)
# ==============================================================================
@pytest.mark.asyncio
async def test_rbac_workspace_matrix(client: AsyncClient, rbac_setup):
    ctx = rbac_setup
    org1_id = str(ctx["org1_id"])
    default_ws_id = str(ctx["org1_ws_default_id"])
    team_ws_id = str(ctx["org1_ws_team_id"])

    # 2.1 Workspace Read (Get Workspace)
    # Owner, Admin, Editor, Viewer can view -> 200
    for role in ["owner", "admin", "editor", "viewer"]:
        res = await client.get(f"/api/v1/workspaces/{team_ws_id}", headers=auth_header(ctx[role]["token"]))
        assert res.status_code == 200, f"{role} should be able to view workspace"

    # Outsider cannot view -> 403
    res = await client.get(f"/api/v1/workspaces/{team_ws_id}", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # 2.2 Workspace Create
    # Viewer cannot create workspace -> 403
    res = await client.post("/api/v1/workspaces", json={"organization_id": org1_id, "name": "Viewer WS"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot create workspace -> 403
    res = await client.post("/api/v1/workspaces", json={"organization_id": org1_id, "name": "Editor WS"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot create workspace in org1 -> 403
    res = await client.post("/api/v1/workspaces", json={"organization_id": org1_id, "name": "Outsider WS"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Admin can create workspace -> 201
    res = await client.post("/api/v1/workspaces", json={"organization_id": org1_id, "name": "Admin Created WS"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 201
    admin_ws_id = res.json()["workspace"]["id"]

    # Owner can create workspace -> 201
    res = await client.post("/api/v1/workspaces", json={"organization_id": org1_id, "name": "Owner Created WS"}, headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 201
    owner_ws_id = res.json()["workspace"]["id"]

    # 2.3 Workspace Update (Rename)
    # Viewer cannot update -> 403
    res = await client.put(f"/api/v1/workspaces/{admin_ws_id}", json={"name": "Viewer Modified"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot update -> 403
    res = await client.put(f"/api/v1/workspaces/{admin_ws_id}", json={"name": "Editor Modified"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot update -> 403
    res = await client.put(f"/api/v1/workspaces/{admin_ws_id}", json={"name": "Outsider Modified"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Admin can update -> 200
    res = await client.put(f"/api/v1/workspaces/{admin_ws_id}", json={"name": "Admin Modified OK"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 200

    # Owner can update -> 200
    res = await client.put(f"/api/v1/workspaces/{admin_ws_id}", json={"name": "Owner Modified OK"}, headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 200

    # 2.4 Workspace Delete
    # Cannot delete default workspace even as owner -> 400
    res = await client.delete(f"/api/v1/workspaces/{default_ws_id}", headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 400

    # Viewer cannot delete non-default workspace -> 403
    res = await client.delete(f"/api/v1/workspaces/{admin_ws_id}", headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot delete non-default workspace -> 403
    res = await client.delete(f"/api/v1/workspaces/{admin_ws_id}", headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot delete non-default workspace -> 403
    res = await client.delete(f"/api/v1/workspaces/{admin_ws_id}", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Admin can delete non-default workspace -> 204
    res = await client.delete(f"/api/v1/workspaces/{admin_ws_id}", headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 204

    # Owner can delete non-default workspace -> 204
    res = await client.delete(f"/api/v1/workspaces/{owner_ws_id}", headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 204


# ==============================================================================
# 3. MEMBER MANAGEMENT RBAC MATRIX (Invite, Change Role, Remove)
# ==============================================================================
@pytest.mark.asyncio
async def test_rbac_member_management_matrix(client: AsyncClient, rbac_setup):
    ctx = rbac_setup
    org1_id = str(ctx["org1_id"])

    # Create a fresh user to invite
    invitee_id = uuid4()
    invitee_email = f"invitee_{invitee_id.hex[:6]}@test.com"
    async with AsyncSessionLocal() as session:
        session.add(User(id=invitee_id, email=invitee_email, full_name="Invitee User", auth_provider=AuthProvider.email, is_active=True))
        await session.commit()

    # 3.1 Invite / Add Member
    # Viewer cannot invite -> 403
    res = await client.post(f"/api/v1/workspaces/organizations/{org1_id}/members", json={"email": invitee_email, "role": "editor"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot invite -> 403
    res = await client.post(f"/api/v1/workspaces/organizations/{org1_id}/members", json={"email": invitee_email, "role": "editor"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot invite -> 403
    res = await client.post(f"/api/v1/workspaces/organizations/{org1_id}/members", json={"email": invitee_email, "role": "editor"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Admin can invite -> 201
    res = await client.post(f"/api/v1/workspaces/organizations/{org1_id}/members", json={"email": invitee_email, "role": "editor"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 201
    assert res.json()["member"]["email"] == invitee_email

    # 3.2 Update Member Role
    # Viewer cannot update role -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", json={"role": "viewer"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot update role -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", json={"role": "viewer"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot update role -> 403
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", json={"role": "viewer"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Cannot update organization owner's role -> 400
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{ctx['owner']['id']}", json={"role": "viewer"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 400

    # Admin can update member role -> 200
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", json={"role": "viewer"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 200
    assert res.json()["role"] == "viewer"

    # Owner can update member role -> 200
    res = await client.put(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", json={"role": "admin"}, headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 200
    assert res.json()["role"] == "admin"

    # 3.3 Remove Member
    # Viewer cannot remove -> 403
    res = await client.delete(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot remove -> 403
    res = await client.delete(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot remove -> 403
    res = await client.delete(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code == 403

    # Cannot remove organization owner -> 400
    res = await client.delete(f"/api/v1/workspaces/organizations/{org1_id}/members/{ctx['owner']['id']}", headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 400

    # Admin can remove member -> 200
    res = await client.delete(f"/api/v1/workspaces/organizations/{org1_id}/members/{invitee_id}", headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 200
    assert res.json()["status"] == "removed"


# ==============================================================================
# 4. PROJECT & SCENE RBAC MATRIX (Create, Read, Update, Delete)
# ==============================================================================
@pytest.mark.asyncio
async def test_rbac_project_matrix(client: AsyncClient, rbac_setup):
    ctx = rbac_setup
    team_ws_id = str(ctx["org1_ws_team_id"])
    project_id = str(ctx["org1_project_id"])

    # 4.1 Project Read
    # Viewer, Editor, Admin, Owner can read -> 200
    for role in ["viewer", "editor", "admin", "owner"]:
        res = await client.get(f"/api/v1/projects/{project_id}", headers=auth_header(ctx[role]["token"]))
        assert res.status_code == 200, f"{role} should be able to read project in workspace"

    # Outsider cannot read -> 403 or 404
    res = await client.get(f"/api/v1/projects/{project_id}", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code in [403, 404], "Outsider should not have access to project"

    # 4.2 Project Create in Workspace
    # Viewer cannot create in workspace -> 403
    res = await client.post(
        "/api/v1/projects",
        json={"title": "Viewer Proj", "workspace_id": team_ws_id, "style": "Explainer", "language": "en"},
        headers=auth_header(ctx["viewer"]["token"])
    )
    assert res.status_code == 403

    # Outsider cannot create in workspace -> 403
    res = await client.post(
        "/api/v1/projects",
        json={"title": "Outsider Proj", "workspace_id": team_ws_id, "style": "Explainer", "language": "en"},
        headers=auth_header(ctx["outsider"]["token"])
    )
    assert res.status_code == 403

    # Editor can create in workspace -> 201
    res = await client.post(
        "/api/v1/projects",
        json={"title": "Editor Proj", "workspace_id": team_ws_id, "style": "Explainer", "language": "en"},
        headers=auth_header(ctx["editor"]["token"])
    )
    assert res.status_code == 201
    editor_proj_id = res.json()["id"]

    # Admin can create in workspace -> 201
    res = await client.post(
        "/api/v1/projects",
        json={"title": "Admin Proj", "workspace_id": team_ws_id, "style": "Explainer", "language": "en"},
        headers=auth_header(ctx["admin"]["token"])
    )
    assert res.status_code == 201
    admin_proj_id = res.json()["id"]

    # 4.3 Project Update
    # Viewer cannot update project -> 403
    res = await client.put(f"/api/v1/projects/{editor_proj_id}", json={"title": "Viewer Hacked Title"}, headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Outsider cannot update project -> 403 or 404
    res = await client.put(f"/api/v1/projects/{editor_proj_id}", json={"title": "Outsider Hacked Title"}, headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code in [403, 404]

    # Editor can update project -> 200
    res = await client.put(f"/api/v1/projects/{editor_proj_id}", json={"title": "Editor Updated Title"}, headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 200
    assert res.json()["title"] == "Editor Updated Title"

    # Admin can update project -> 200
    res = await client.put(f"/api/v1/projects/{editor_proj_id}", json={"title": "Admin Updated Title"}, headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 200

    # 4.4 Project Delete
    # Viewer cannot delete project -> 403
    res = await client.delete(f"/api/v1/projects/{editor_proj_id}", headers=auth_header(ctx["viewer"]["token"]))
    assert res.status_code == 403

    # Editor cannot delete workspace project owned by another user -> 403
    res = await client.delete(f"/api/v1/projects/{admin_proj_id}", headers=auth_header(ctx["editor"]["token"]))
    assert res.status_code == 403

    # Outsider cannot delete project -> 403 or 404
    res = await client.delete(f"/api/v1/projects/{editor_proj_id}", headers=auth_header(ctx["outsider"]["token"]))
    assert res.status_code in [403, 404]

    # Admin can delete workspace project -> 204
    res = await client.delete(f"/api/v1/projects/{editor_proj_id}", headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 204

    # Owner can delete workspace project -> 204
    res = await client.delete(f"/api/v1/projects/{admin_proj_id}", headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code == 204


# ==============================================================================
# 5. CROSS-ORGANIZATION & CROSS-WORKSPACE ISOLATION
# ==============================================================================
@pytest.mark.asyncio
async def test_rbac_cross_organization_isolation(client: AsyncClient, rbac_setup):
    ctx = rbac_setup
    org1_proj_id = str(ctx["org1_project_id"])
    org2_proj_id = str(ctx["org2_project_id"])
    org1_ws_id = str(ctx["org1_ws_team_id"])
    org2_ws_id = str(ctx["org2_ws_default_id"])

    # Org 2 Owner tries to access Org 1 Project -> 403/404
    res = await client.get(f"/api/v1/projects/{org1_proj_id}", headers=auth_header(ctx["org2_owner"]["token"]))
    assert res.status_code in [403, 404]

    # Org 1 Owner tries to access Org 2 Project -> 403/404
    res = await client.get(f"/api/v1/projects/{org2_proj_id}", headers=auth_header(ctx["owner"]["token"]))
    assert res.status_code in [403, 404]

    # Org 2 Owner tries to access Org 1 Workspace -> 403
    res = await client.get(f"/api/v1/workspaces/{org1_ws_id}", headers=auth_header(ctx["org2_owner"]["token"]))
    assert res.status_code == 403

    # Org 1 Admin tries to access Org 2 Workspace -> 403
    res = await client.get(f"/api/v1/workspaces/{org2_ws_id}", headers=auth_header(ctx["admin"]["token"]))
    assert res.status_code == 403

    # Org 2 Owner tries to delete Org 1 Workspace -> 403
    res = await client.delete(f"/api/v1/workspaces/{org1_ws_id}", headers=auth_header(ctx["org2_owner"]["token"]))
    assert res.status_code == 403

    # Tampered X-User-ID header cannot bypass JWT bearer token
    # Attacker passes Viewer token but sets X-User-ID to Owner
    res = await client.put(
        f"/api/v1/workspaces/organizations/{ctx['org1_id']}",
        json={"name": "Spoofed Attack"},
        headers={
            "Authorization": f"Bearer {ctx['viewer']['token']}",
            "X-User-ID": str(ctx["owner"]["id"])
        }
    )
    # Must still be evaluated as viewer -> 403 Forbidden!
    assert res.status_code == 403
