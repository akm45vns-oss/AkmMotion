from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user_id
from app.services.ai.character_memory import CharacterMemoryService
from app.services.ai.character_detector import CharacterDetectorService
from app.services.ai.character_evaluator import CharacterEvaluatorService
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse, CharacterDNA
from app.models.character import DBCharacter

router = APIRouter(prefix="/characters", tags=["Character Memory Engine"])


def format_character_response(char: DBCharacter) -> CharacterResponse:
    profile_role = char.profile.role if (char.profile and char.profile.role) else "Protagonist"
    profile_desc = char.profile.summary if char.profile else None

    dna_dict = char.dna.attributes_json if (char.dna and char.dna.attributes_json) else {}
    if char.dna and not dna_dict:
        dna_dict = {
            "character_code": char.character_code,
            "skin_tone": char.dna.skin_tone,
            "hair_color": char.dna.hair_color,
            "hair_style": char.dna.hair_style,
            "hair_length": char.dna.hair_length,
            "eye_color": char.dna.eye_color,
            "face_shape": char.dna.face_shape,
            "outfit": char.dna.outfit,
            "shoes": char.dna.shoes,
            "expression": char.dna.expression,
            "visual_style": char.dna.visual_style,
            "prompt_prefix": char.dna.prompt_prefix,
            "prompt_suffix": char.dna.prompt_suffix,
            "negative_prompt": char.dna.negative_prompt,
            "consistency_strength": char.dna.consistency_strength or 0.95
        }
    if "character_code" not in dna_dict:
        dna_dict["character_code"] = char.character_code

    dna_obj = CharacterDNA.model_validate(dna_dict)

    return CharacterResponse(
        id=char.id,
        user_id=char.user_id,
        project_id=char.project_id,
        character_code=char.character_code,
        name=char.name,
        role=profile_role,
        description=profile_desc,
        is_locked=char.is_locked if char.is_locked is not None else True,
        is_favorite=char.is_favorite if char.is_favorite is not None else False,
        consistency_score=char.consistency_score if char.consistency_score is not None else 95,
        dna=dna_obj,
        versions=[],
        scene_appearances=[],
        created_at=char.created_at,
        updated_at=char.updated_at
    )


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    data: CharacterCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = CharacterMemoryService(db)
    character = await service.create_character(UUID(current_user_id), data)
    return format_character_response(character)


@router.get("", response_model=List[CharacterResponse])
async def list_characters(
    project_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = CharacterMemoryService(db)
    characters = await service.list_characters(UUID(current_user_id), project_id, search)
    return [format_character_response(c) for c in characters]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = CharacterMemoryService(db)
    character = await service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return format_character_response(character)


@router.post("/{character_id}/lock", response_model=CharacterResponse)
async def lock_character(
    character_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = CharacterMemoryService(db)
    character = await service.set_lock_status(character_id, is_locked=True)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return format_character_response(character)


@router.post("/{character_id}/unlock", response_model=CharacterResponse)
async def unlock_character(
    character_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = CharacterMemoryService(db)
    character = await service.set_lock_status(character_id, is_locked=False)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return format_character_response(character)


@router.post("/extract")
async def extract_characters_from_script(payload: dict = Body(...)):
    script_text = payload.get("script", "")
    detected = CharacterDetectorService.detect_characters(script_text)
    return {"detected_characters": detected}


@router.post("/evaluate")
async def evaluate_character_consistency(payload: dict = Body(...)):
    scene_prompt = payload.get("scene_prompt", "")
    character_dna = payload.get("dna", {})
    report = CharacterEvaluatorService.evaluate_consistency(scene_prompt, character_dna)
    return report