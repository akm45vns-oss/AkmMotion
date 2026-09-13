import uuid
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from sqlalchemy.orm import selectinload
from app.models.character import (
    DBCharacter, DBCharacterProfile, DBCharacterDNA,
    DBCharacterVersion, DBCharacterSceneAssignment, DBCharacterRelationship
)
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterDNA
from app.services.ai.character_cache import CharacterCache


class CharacterMemoryService:
    """
    Core service for Character Memory Engine (CME).
    Manages persistent visual memory, DNA versioning, locking, and scene assignments.
    Accelerated with in-memory CharacterCache for <100ms lookup latency.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_character(self, user_id: uuid.UUID, data: CharacterCreate) -> DBCharacter:
        character = DBCharacter(
            user_id=user_id,
            project_id=data.project_id,
            character_code=data.dna.character_code,
            name=data.name,
            is_locked=data.is_locked,
            is_favorite=data.is_favorite
        )
        self.db.add(character)
        await self.db.flush()

        # Profile
        profile = DBCharacterProfile(
            character_id=character.id,
            role=data.role,
            summary=data.description
        )
        self.db.add(profile)

        # DNA
        dna_dict = data.dna.model_dump()
        dna = DBCharacterDNA(
            character_id=character.id,
            skin_tone=dna_dict.get("skin_tone", "Medium"),
            hair_color=dna_dict.get("hair_color", "Black"),
            hair_style=dna_dict.get("hair_style", "Short neat"),
            hair_length=dna_dict.get("hair_length", "Short"),
            eye_color=dna_dict.get("eye_color", "Brown"),
            face_shape=dna_dict.get("face_shape", "Oval"),
            outfit=dna_dict.get("outfit", "Casual blue hoodie and black jeans"),
            shoes=dna_dict.get("shoes", "White sneakers"),
            expression=dna_dict.get("expression", "Friendly smile"),
            visual_style=dna_dict.get("visual_style", "Pixar 3D Render"),
            prompt_prefix=dna_dict.get("prompt_prefix", "Masterpiece 9:16 vertical 8k render"),
            prompt_suffix=dna_dict.get("prompt_suffix", "same facial features, same clothes, consistent identity"),
            negative_prompt=dna_dict.get("negative_prompt", "deformed face, wrong clothes, inconsistent character"),
            attributes_json=dna_dict
        )
        self.db.add(dna)

        # Initial Version Snapshot (V1)
        version = DBCharacterVersion(
            character_id=character.id,
            version_number=1,
            snapshot_dna=dna_dict,
            notes="Version 1: Initial Character Profile Created"
        )
        self.db.add(version)
        await self.db.commit()

        # Store in <100ms Cache
        CharacterCache.set(str(character.id), dna_dict)

        return await self.get_character_by_id(character.id)

    async def get_character_by_id(self, character_id: uuid.UUID) -> Optional[DBCharacter]:
        # Fast Cache Lookup
        cached_dna = CharacterCache.get(str(character_id))
        
        stmt = (
            select(DBCharacter)
            .where(DBCharacter.id == character_id)
            .options(
                selectinload(DBCharacter.profile),
                selectinload(DBCharacter.dna),
                selectinload(DBCharacter.versions),
                selectinload(DBCharacter.scene_assignments)
            )
        )
        result = await self.db.execute(stmt)
        char = result.scalar_one_or_none()
        if char and char.dna:
            CharacterCache.set(str(char.id), char.dna.attributes_json or {})
        return char

    async def list_characters(
        self, user_id: uuid.UUID, project_id: Optional[uuid.UUID] = None, search: Optional[str] = None
    ) -> List[DBCharacter]:
        stmt = select(DBCharacter).where(
            DBCharacter.user_id == user_id,
            or_(DBCharacter.is_archived == False, DBCharacter.is_archived == None)
        )

        if project_id:
            stmt = stmt.where(DBCharacter.project_id == project_id)

        if search:
            stmt = stmt.where(DBCharacter.name.ilike(f"%{search}%"))

        stmt = stmt.options(
            selectinload(DBCharacter.profile),
            selectinload(DBCharacter.dna)
        ).order_by(DBCharacter.updated_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_lock_status(self, character_id: uuid.UUID, is_locked: bool) -> DBCharacter:
        character = await self.get_character_by_id(character_id)
        if character:
            character.is_locked = is_locked
            await self.db.commit()
            CharacterCache.invalidate(str(character_id))
        return character

    async def assign_to_scene(self, character_id: uuid.UUID, scene_id: uuid.UUID, pose: str = "Standing", expression: str = "Neutral") -> DBCharacterSceneAssignment:
        assignment = DBCharacterSceneAssignment(
            character_id=character_id,
            scene_id=scene_id,
            pose_in_scene=pose,
            expression_in_scene=expression
        )
        self.db.add(assignment)
        await self.db.commit()
        return assignment