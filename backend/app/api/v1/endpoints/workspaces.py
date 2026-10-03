from typing import List, Optional
from uuid import UUID, uuid4
import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import (
    get_db,
    get_current_authenticated_user_id,
    check_role_permission,
    verify_workspace_access
)
from app.models.models import Organization, Workspace, OrganizationMember, User

router = APIRouter(prefix="/workspaces", tags=["Workspaces & RBAC"])


# Schemas
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)


class WorkspaceCreate(BaseModel):
    organization_id: UUID
    name: str = Field(..., min_length=2, max_length=100)


class MemberAdd(BaseModel):
    email: str
    role: str = Field("editor", pattern="^(owner|admin|editor|viewer)$")


class MemberUpdateRole(BaseModel):
    role: str = Field(..., pattern="^(admin|editor|viewer)$")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)


class OrganizationTransfer(BaseModel):
    new_owner_id: UUID


class WorkspaceUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "org"


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new organization, registers owner, and initializes default workspace."""
    user_id = UUID(user_id_str)
    base_slug = payload.slug or slugify(payload.name)
    slug = f"{base_slug}-{uuid4().hex[:6]}"

    org = Organization(
        name=payload.name.strip(),
        slug=slug,
        owner_id=user_id
    )
    db.add(org)
    await db.flush()

    # Add owner as organization member
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user_id,
        role="owner"
    )
    db.add(member)

    # Initialize default workspace
    default_ws = Workspace(
        organization_id=org.id,
        name="Default Workspace",
        is_default=True
    )
    db.add(default_ws)
    await db.commit()
    await db.refresh(org)
    await db.refresh(default_ws)

    return {
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "owner_id": str(org.owner_id)
        },
        "default_workspace": {
            "id": str(default_ws.id),
            "name": default_ws.name,
            "is_default": default_ws.is_default
        }
    }


@router.get("/organizations")
async def list_user_organizations(
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Lists organizations owned by or shared with the authenticated user."""
    user_id = UUID(user_id_str)

    # Find organizations where user is owner or member
    query = (
        select(Organization, OrganizationMember.role)
        .outerjoin(OrganizationMember, (OrganizationMember.organization_id == Organization.id) & (OrganizationMember.user_id == user_id))
        .where((Organization.owner_id == user_id) | (OrganizationMember.user_id == user_id))
    )
    res = await db.execute(query)
    rows = res.all()

    orgs = []
    seen = set()
    for org, member_role in rows:
        if org.id in seen:
            continue
        seen.add(org.id)
        effective_role = "owner" if org.owner_id == user_id else (member_role or "viewer")
        orgs.append({
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "owner_id": str(org.owner_id),
            "role": effective_role
        })

    return {"organizations": orgs}


@router.get("")
async def list_user_workspaces(
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Lists all workspaces accessible to the user across all their organizations."""
    user_id = UUID(user_id_str)

    query = (
        select(Workspace, Organization.name.label("org_name"), Organization.owner_id)
        .join(Organization, Workspace.organization_id == Organization.id)
        .outerjoin(OrganizationMember, (OrganizationMember.organization_id == Organization.id) & (OrganizationMember.user_id == user_id))
        .where((Organization.owner_id == user_id) | (OrganizationMember.user_id == user_id))
    )
    res = await db.execute(query)
    rows = res.all()

    workspaces = []
    seen = set()
    for ws, org_name, owner_id in rows:
        if ws.id in seen:
            continue
        seen.add(ws.id)
        workspaces.append({
            "id": str(ws.id),
            "organization_id": str(ws.organization_id),
            "organization_name": org_name,
            "name": ws.name,
            "is_default": ws.is_default,
            "is_owner": (owner_id == user_id)
        })

    return {"workspaces": workspaces}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new workspace within an organization (requires admin or owner role)."""
    user_id = UUID(user_id_str)

    # Check org permission
    org_res = await db.execute(select(Organization).where(Organization.id == payload.organization_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != user_id:
        member_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user_id
            )
        )
        member = member_res.scalar_one_or_none()
        if not member or not check_role_permission(str(member.role), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    ws = Workspace(
        organization_id=payload.organization_id,
        name=payload.name.strip(),
        is_default=False
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)

    return {
        "workspace": {
            "id": str(ws.id),
            "organization_id": str(ws.organization_id),
            "name": ws.name,
            "is_default": ws.is_default
        }
    }


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: UUID,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Gets workspace details if user has viewer access or higher."""
    user_id = UUID(user_id_str)
    has_access = await verify_workspace_access(workspace_id, user_id, "viewer", db)
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to workspace denied")

    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = ws_res.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    return {
        "id": str(ws.id),
        "organization_id": str(ws.organization_id),
        "name": ws.name,
        "is_default": ws.is_default
    }


@router.post("/organizations/{org_id}/members", status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: UUID,
    payload: MemberAdd,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Adds a member to an organization (requires admin or owner)."""
    user_id = UUID(user_id_str)

    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != user_id:
        member_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user_id
            )
        )
        member = member_res.scalar_one_or_none()
        if not member or not check_role_permission(str(member.role), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    # Find target user by email
    target_res = await db.execute(select(User).where(User.email == payload.email.strip().lower()))
    target_user = target_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")

    # Check if already a member
    existing_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == target_user.id
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member")

    new_member = OrganizationMember(
        organization_id=org.id,
        user_id=target_user.id,
        role=payload.role
    )
    db.add(new_member)
    await db.commit()

    return {
        "status": "added",
        "member": {
            "user_id": str(target_user.id),
            "email": target_user.email,
            "role": payload.role
        }
    }


@router.delete("/organizations/{org_id}/members/{target_user_id}")
async def remove_organization_member(
    org_id: UUID,
    target_user_id: UUID,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Removes a member from an organization (requires admin or owner)."""
    user_id = UUID(user_id_str)

    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if target_user_id == org.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove organization owner")

    if org.owner_id != user_id:
        member_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user_id
            )
        )
        member = member_res.scalar_one_or_none()
        if not member or not check_role_permission(str(member.role), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    mem_to_del = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == target_user_id
        )
    )
    target_member = mem_to_del.scalar_one_or_none()
    if not target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in organization")

    await db.delete(target_member)
    await db.commit()

    return {"status": "removed", "user_id": str(target_user_id)}


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: UUID,
    payload: OrganizationUpdate,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Renames or updates organization (requires admin or owner)."""
    user_id = UUID(user_id_str)
    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != user_id:
        member_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user_id
            )
        )
        member = member_res.scalar_one_or_none()
        if not member or not check_role_permission(str(member.role), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    if payload.name is not None:
        org.name = payload.name.strip()
    if payload.slug is not None:
        org.slug = slugify(payload.slug)

    await db.commit()
    await db.refresh(org)
    return {"id": str(org.id), "name": org.name, "slug": org.slug, "owner_id": str(org.owner_id)}


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Deletes organization and all associated resources (strictly OWNER only)."""
    user_id = UUID(user_id_str)
    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only organization owner can delete the organization")

    await db.delete(org)
    await db.commit()
    return None


@router.post("/organizations/{org_id}/transfer")
async def transfer_organization_ownership(
    org_id: UUID,
    payload: OrganizationTransfer,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Transfers ownership of organization to another member (strictly OWNER only)."""
    user_id = UUID(user_id_str)
    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only organization owner can transfer ownership")

    if payload.new_owner_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already the organization owner")

    # Verify target user is a member
    mem_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == payload.new_owner_id
        )
    )
    target_member = mem_res.scalar_one_or_none()
    if not target_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New owner must be an existing organization member")

    # Update org owner
    org.owner_id = payload.new_owner_id
    target_member.role = "owner"

    # Demote old owner to admin member
    old_owner_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user_id
        )
    )
    old_member = old_owner_res.scalar_one_or_none()
    if old_member:
        old_member.role = "admin"

    await db.commit()
    return {"status": "transferred", "organization_id": str(org.id), "new_owner_id": str(payload.new_owner_id)}


@router.put("/{workspace_id}")
async def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Updates workspace name (requires admin or owner)."""
    user_id = UUID(user_id_str)
    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = ws_res.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    has_admin = await verify_workspace_access(workspace_id, user_id, "admin", db)
    if not has_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    ws.name = payload.name.strip()
    await db.commit()
    await db.refresh(ws)
    return {"id": str(ws.id), "organization_id": str(ws.organization_id), "name": ws.name, "is_default": ws.is_default}


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a workspace (requires admin or owner; cannot delete default workspace)."""
    user_id = UUID(user_id_str)
    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = ws_res.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if ws.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete default workspace")

    has_admin = await verify_workspace_access(workspace_id, user_id, "admin", db)
    if not has_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    await db.delete(ws)
    await db.commit()
    return None


@router.put("/organizations/{org_id}/members/{target_user_id}")
async def update_organization_member_role(
    org_id: UUID,
    target_user_id: UUID,
    payload: MemberUpdateRole,
    user_id_str: str = Depends(get_current_authenticated_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Updates a member's role (requires admin or owner). Cannot change owner role."""
    user_id = UUID(user_id_str)
    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if target_user_id == org.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify role of organization owner")

    if org.owner_id != user_id:
        member_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user_id
            )
        )
        caller_member = member_res.scalar_one_or_none()
        if not caller_member or not check_role_permission(str(caller_member.role), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")

    mem_to_update = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == target_user_id
        )
    )
    target_member = mem_to_update.scalar_one_or_none()
    if not target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in organization")

    target_member.role = payload.role
    await db.commit()
    return {"status": "updated", "user_id": str(target_user_id), "role": payload.role}
