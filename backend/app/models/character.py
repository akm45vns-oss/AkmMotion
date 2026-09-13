import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class DBCharacter(Base):
    """
    Main Character entity in the Character Memory Engine.
    Manages lock status, favorite status, and project associations.
    """
    __tablename__ = "characters"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    character_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    is_locked = Column(Boolean, default=True, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    consistency_score = Column(Integer, default=95, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = relationship("DBCharacterProfile", back_populates="character", uselist=False, cascade="all, delete-orphan")
    dna = relationship("DBCharacterDNA", back_populates="character", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("DBCharacterEmbedding", back_populates="character", cascade="all, delete-orphan")
    styles = relationship("DBCharacterStyle", back_populates="character", cascade="all, delete-orphan")
    outfits = relationship("DBCharacterOutfit", back_populates="character", cascade="all, delete-orphan")
    accessories = relationship("DBCharacterAccessory", back_populates="character", cascade="all, delete-orphan")
    relationships = relationship("DBCharacterRelationship", back_populates="character", foreign_keys="[DBCharacterRelationship.character_id]", cascade="all, delete-orphan")
    reference_images = relationship("DBCharacterReferenceImage", back_populates="character", cascade="all, delete-orphan")
    scene_assignments = relationship("DBCharacterSceneAssignment", back_populates="character", cascade="all, delete-orphan")
    versions = relationship("DBCharacterVersion", back_populates="character", cascade="all, delete-orphan")


class DBCharacterProfile(Base):
    __tablename__ = "character_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String(64), default="Protagonist", nullable=False)
    age = Column(Integer, default=25, nullable=False)
    gender = Column(String(32), default="Male", nullable=False)
    ethnicity = Column(String(64), nullable=True)
    summary = Column(Text, nullable=True)
    
    character = relationship("DBCharacter", back_populates="profile")


class DBCharacterDNA(Base):
    __tablename__ = "character_dna"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    skin_tone = Column(String(64), default="Medium")
    hair_color = Column(String(64), default="Black")
    hair_style = Column(String(64), default="Short neat")
    hair_length = Column(String(64), default="Short")
    eye_color = Column(String(64), default="Brown")
    face_shape = Column(String(64), default="Oval")
    beard = Column(String(64), nullable=True)
    mustache = Column(String(64), nullable=True)
    body_type = Column(String(64), default="Average")
    height_category = Column(String(64), default="Medium")
    outfit = Column(String(255), default="Casual blue hoodie and black jeans")
    shoes = Column(String(128), default="White sneakers")
    expression = Column(String(128), default="Friendly smile")
    visual_style = Column(String(128), default="Pixar 3D Render")
    lighting_preference = Column(String(128), default="Cinematic golden hour light")
    camera_preference = Column(String(128), default="Medium eye-level shot")
    prompt_prefix = Column(Text, default="Masterpiece 9:16 vertical 8k render")
    prompt_suffix = Column(Text, default="same facial features, same clothes, consistent identity")
    negative_prompt = Column(Text, default="deformed face, wrong clothes, inconsistent character")
    consistency_strength = Column(Float, default=0.95)
    attributes_json = Column(JSON, nullable=True)

    character = relationship("DBCharacter", back_populates="dna")


class DBCharacterEmbedding(Base):
    __tablename__ = "character_embeddings"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    embedding_vector = Column(JSON, nullable=True)
    model_version = Column(String(64), default="v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    character = relationship("DBCharacter", back_populates="embeddings")


class DBCharacterStyle(Base):
    __tablename__ = "character_styles"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    style_name = Column(String(64), default="Pixar 3D Render", nullable=False)
    rendering_engine = Column(String(64), default="Pollinations FLUX")
    style_prompt_modifiers = Column(Text, nullable=True)

    character = relationship("DBCharacter", back_populates="styles")


class DBCharacterOutfit(Base):
    __tablename__ = "character_outfits"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    outfit_name = Column(String(128), default="Default Outfit", nullable=False)
    top_clothing = Column(String(128), default="Blue Hoodie")
    bottom_clothing = Column(String(128), default="Black Jeans")
    footwear = Column(String(128), default="White Sneakers")
    color_palette = Column(JSON, nullable=True)

    character = relationship("DBCharacter", back_populates="outfits")


class DBCharacterAccessory(Base):
    __tablename__ = "character_accessories"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    accessory_type = Column(String(64), nullable=False)
    item_description = Column(String(128), nullable=False)

    character = relationship("DBCharacter", back_populates="accessories")


class DBCharacterRelationship(Base):
    __tablename__ = "character_relationships"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    related_character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    relationship_type = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)

    character = relationship("DBCharacter", back_populates="relationships", foreign_keys=[character_id])


class DBCharacterReferenceImage(Base):
    __tablename__ = "character_reference_images"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    image_url = Column(Text, nullable=False)
    extracted_metadata = Column(JSON, nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    character = relationship("DBCharacter", back_populates="reference_images")


class DBCharacterSceneAssignment(Base):
    __tablename__ = "character_scene_assignments"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    character = relationship("DBCharacter", back_populates="scene_assignments")


class DBCharacterVersion(Base):
    __tablename__ = "character_versions"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    version_number = Column(Integer, nullable=False)
    dna_snapshot = Column("dna_snapshot", JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def snapshot_dna(self):
        return self.dna_snapshot

    @snapshot_dna.setter
    def snapshot_dna(self, value):
        self.dna_snapshot = value

    character = relationship("DBCharacter", back_populates="versions")