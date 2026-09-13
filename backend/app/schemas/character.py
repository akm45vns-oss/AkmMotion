from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class CharacterDNA(BaseModel):
    character_code: str = Field(default_factory=lambda: f"CHR_{uuid4().hex[:6].upper()}")
    age: int = 25
    gender: str = "Male"
    ethnicity: Optional[str] = None
    skin_tone: str = "Medium"
    hair_color: str = "Black"
    hair_style: str = "Short neat"
    hair_length: str = "Short"
    eye_color: str = "Brown"
    face_shape: str = "Oval"
    beard: Optional[str] = None
    mustache: Optional[str] = None
    body_type: str = "Average"
    height_category: str = "Medium"
    outfit: str = "Casual blue hoodie and black jeans"
    shoes: str = "White sneakers"
    accessories: List[str] = Field(default_factory=lambda: ["Silver wristwatch"])
    expression: str = "Friendly smile"
    visual_style: str = "Pixar 3D Render"
    lighting_preference: str = "Cinematic golden hour light"
    camera_preference: str = "Medium eye-level shot"
    primary_color_palette: List[str] = Field(default_factory=lambda: ["#1E3A8A", "#000000"])
    prompt_prefix: str = "Masterpiece 9:16 vertical 8k render"
    prompt_suffix: str = "same facial features, same clothes, consistent identity"
    negative_prompt: str = "deformed face, wrong clothes, inconsistent character"
    consistency_strength: float = 0.95


class CharacterRelationship(BaseModel):
    related_character_id: str
    relationship_type: str  # Father, Mother, Friend, Teacher, Sibling, Enemy, Pet, Boss
    notes: Optional[str] = None


class CharacterVersion(BaseModel):
    version_number: int = 1
    snapshot_dna: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str = "Initial creation"


class CharacterBase(BaseModel):
    name: str
    role: str = "Protagonist"
    description: Optional[str] = None
    is_locked: bool = True
    is_favorite: bool = False
    dna: CharacterDNA = Field(default_factory=CharacterDNA)
    relationships: List[CharacterRelationship] = Field(default_factory=list)


class CharacterCreate(CharacterBase):
    project_id: Optional[UUID] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    is_locked: Optional[bool] = None
    is_favorite: Optional[bool] = None
    dna: Optional[CharacterDNA] = None
    relationships: Optional[List[CharacterRelationship]] = None


class CharacterResponse(CharacterBase):
    id: UUID
    project_id: Optional[UUID] = None
    user_id: UUID
    versions: List[CharacterVersion] = Field(default_factory=list)
    scene_appearances: List[int] = Field(default_factory=list)
    consistency_score: int = 95
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptInjectionSpec(BaseModel):
    character_id: str
    character_name: str
    injected_prompt_segment: str
    locked_attributes: List[str]