import asyncio
import os
import sys
from uuid import uuid4

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.base import Base
from app.models.models import User, Organization, Workspace, OrganizationMember, Project, Script, AuthProvider

LOCAL_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/akmmotion"

async def main():
    print("[Colocated Seed] Creating async engine for local database...")
    engine = create_async_engine(LOCAL_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        print("[Colocated Seed] Creating all tables from SQLAlchemy Base metadata...")
        await conn.run_sync(Base.metadata.create_all)
        print("[Colocated Seed] All tables created.")

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if benchmark user exists
        res = await session.execute(text("SELECT id FROM users WHERE email = 'test@example.com'"))
        user_row = res.first()
        if not user_row:
            print("[Colocated Seed] Seeding benchmark user, org, workspace, projects...")
            user_id = "00000000-0000-0000-0000-000000000001"
            org_id = "00000000-0000-0000-0000-000000000002"
            ws_id = "00000000-0000-0000-0000-000000000003"

            user = User(
                id=user_id,
                email="test@example.com",
                full_name="Production Benchmark User",
                auth_provider=AuthProvider.email,
                is_active=True,
                is_verified=True
            )
            session.add(user)
            await session.flush()

            org = Organization(
                id=org_id,
                name="Test Org",
                slug="test-org",
                owner_id=user.id
            )
            session.add(org)
            await session.flush()

            member = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role="owner"
            )
            session.add(member)

            ws = Workspace(
                id=ws_id,
                organization_id=org.id,
                name="Production Benchmark Workspace",
                is_default=True
            )
            session.add(ws)
            await session.flush()

            # Seed 25 sample projects with scripts
            for i in range(25):
                proj_id = f"00000000-0000-0000-0001-{i:012d}"
                script_id = f"00000000-0000-0000-0002-{i:012d}"
                proj = Project(
                    id=proj_id,
                    user_id=user.id,
                    workspace_id=ws.id,
                    title=f"Vertical Video Project {i+1}",
                    description="Automated Benchmark Project",
                    style="Explainer",
                    language="en"
                )
                session.add(proj)
                await session.flush()

                script = Script(
                    id=script_id,
                    project_id=proj.id,
                    content=f"This is scene script content for automated performance validation project {i+1}. Invariant: Script fidelity 100%.",
                    word_count=18,
                    estimated_duration=5.0,
                    language="en"
                )
                session.add(script)

            await session.commit()
            print("[Colocated Seed] 25 benchmark projects and scripts seeded successfully.")
        else:
            print("[Colocated Seed] Benchmark seed data already present.")

        proj_count = (await session.execute(text("SELECT count(*) FROM projects"))).scalar()
        print(f"[Colocated Seed] Verified projects in local database: {proj_count}")

    await engine.dispose()
    print("[Colocated Seed] Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(main())
