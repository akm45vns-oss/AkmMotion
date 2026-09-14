from uuid import UUID
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.models import Project, Script, Scene, SceneAsset, AssetType, ProjectStatus, SceneStatus, ScriptStatus, AnimationStyle, TransitionType, CameraMotion
from app.services.ai.script_analyzer import ScriptAnalyzerService
from app.services.ai.image_generator import ImageGeneratorService
from app.services.ai.voice_generator import VoiceGeneratorService
from app.services.ai.subtitle_generator import SubtitleGeneratorService
from app.services.ai.character_detector import CharacterDetectorService
from app.services.ai.prompt_builder import PromptBuilderService
from app.services.ai.character_memory import CharacterMemoryService
from app.schemas.character import CharacterCreate, CharacterDNA


class AIPipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analyzer = ScriptAnalyzerService()
        self.image_gen = ImageGeneratorService()
        self.voice_gen = VoiceGeneratorService()
        self.sub_gen = SubtitleGeneratorService()

    async def run_pipeline(self, project_id: UUID, user_id: Optional[UUID] = None) -> Project:
        # 1. Fetch Project & Script
        query = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.script), selectinload(Project.scenes))
        )
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if user_id and project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if not project.script or not project.script.content.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project does not have a valid script to analyze")

        # Cache script and project attributes locally to prevent lazy-load issues later
        script_content = project.script.content.strip()
        script_id = project.script.id
        project_style = project.style or "Explainer"
        project_lang = getattr(project, "language", "en") or "en"
        actual_user_id = user_id or project.user_id

        # Update Project & Script status
        project.status = ProjectStatus.analyzing
        project.script.status = ScriptStatus.analyzing
        await self.db.commit()

        # 2. CME Character Memory Engine: Detect & Load Locked Character DNA
        cme_service = CharacterMemoryService(self.db)
        primary_char_dna: Dict[str, Any] = {}
        primary_char_portrait_url: str = None

        try:
            detected_chars = CharacterDetectorService.detect_characters(script_content)
            if detected_chars:
                primary = detected_chars[0]
                
                # Generate Pro Studio reference portrait for the main character
                dna = primary.get("dna", {})
                desc = f"{dna.get('age', '25')}yo {dna.get('gender', 'person')}, {dna.get('hair', '')}, {dna.get('clothing', '')}"
                primary_char_portrait_url = await self.image_gen.generate_character_portrait(desc, project_style)

                char_create = CharacterCreate(
                    name=primary["name"],
                    role=primary["role"],
                    project_id=project.id,
                    is_locked=True,
                    dna=CharacterDNA.model_validate(dna)
                )
                db_char = await cme_service.create_character(actual_user_id, char_create)
                primary_char_dna = dna
                await self.db.commit()
        except Exception as cme_err:
            print(f"CME Character Detection Notice: {cme_err}")
            await self.db.rollback()

        # 3. Step A: LLM Script Analysis into Scenes
        raw_scenes = await self.analyzer.analyze_script(
            script_text=script_content,
            style=project_style,
            language=project_lang
        )

        # Delete existing scenes if any
        # Re-fetch project to ensure clean session state
        query_scenes = select(Scene).where(Scene.project_id == project_id)
        existing_scenes = (await self.db.execute(query_scenes)).scalars().all()
        for old_scene in existing_scenes:
            await self.db.delete(old_scene)
        await self.db.flush()

        # 4. Create Scene & Asset records in DB with CME Character Prompt Injection
        created_scenes = []
        for s_data in raw_scenes:
            # Map strings to enums safely
            try:
                anim_enum = AnimationStyle(s_data.get("animation_style", "ken_burns"))
            except ValueError:
                anim_enum = AnimationStyle.ken_burns

            try:
                trans_enum = TransitionType(s_data.get("transition", "fade"))
            except ValueError:
                trans_enum = TransitionType.fade

            try:
                cam_enum = CameraMotion(s_data.get("camera_motion", "push"))
            except ValueError:
                cam_enum = CameraMotion.push

            raw_prompt = s_data.get("image_prompt", "")
            
            # Enrich prompt with shot type if not already included
            shot_type_label = s_data.get("shot_type", "")
            if shot_type_label and shot_type_label.replace('_', ' ').lower() not in raw_prompt.lower():
                raw_prompt = f"{shot_type_label.replace('_', ' ').title()} shot. {raw_prompt}"

            # Check if this scene actually features a character
            scene_text_lower = (s_data.get("narration", "") + " " + raw_prompt).lower()
            char_keywords = ["character", "person", "man", "woman", "prince", "king", "queen", "farmer", "worker", "villager", "hero", "face", "eyes", "close-up", "portrait", "standing", "walking", "he ", "she "]
            has_character_focus = any(kw in scene_text_lower for kw in char_keywords) or s_data.get("shot_type") in ["close_up", "medium_shot", "over_shoulder", "extreme_close_up"]

            # INJECT CME CHARACTER DNA INTO PROMPT only when character is part of the scene
            if primary_char_dna and has_character_focus:
                injected_prompt = PromptBuilderService.inject_character_dna(
                    raw_scene_prompt=raw_prompt,
                    character_dna_dict=primary_char_dna
                )
            else:
                injected_prompt = raw_prompt

            scene = Scene(
                project_id=project_id,
                script_id=script_id,
                scene_number=s_data["scene_number"],
                duration=s_data.get("estimated_duration", 7.0),
                narration=str(s_data.get("narration", "")).strip(),
                subtitle=str(s_data.get("subtitle", s_data.get("narration", ""))).strip(),
                image_prompt=injected_prompt,
                animation_style=anim_enum,
                transition=trans_enum,
                camera_motion=cam_enum,
                emotion=s_data.get("emotion", "neutral"),
                status=SceneStatus.generating
            )
            self.db.add(scene)
            await self.db.flush()

            # 5. Generate Image & Audio Assets for Scene
            # Language detection: use project language field, fallback to Hindi detection
            voice_lang = project_lang
            image_url = await self.image_gen.generate_image(scene.image_prompt, style=project_style, reference_image_url=primary_char_portrait_url)
            audio_url = ""  # Audio is generated on-demand via /api/v1/ai/tts endpoint
            subtitles = await self.sub_gen.generate_subtitles(scene.subtitle, total_duration=scene.duration)

            # Store Image Asset
            image_asset = SceneAsset(
                scene_id=scene.id,
                asset_type=AssetType.image,
                url=image_url,
                storage_path=f"images/{scene.id}.jpg",
                metadata_json={"prompt": scene.image_prompt, "cme_injected": bool(primary_char_dna)}
            )
            self.db.add(image_asset)

            # Store Audio Asset
            audio_asset = SceneAsset(
                scene_id=scene.id,
                asset_type=AssetType.audio,
                url=audio_url,
                storage_path=f"audio/{scene.id}.mp3",
                metadata_json={"voice": "alloy"}
            )
            self.db.add(audio_asset)

            # Store Subtitle Asset
            sub_asset = SceneAsset(
                scene_id=scene.id,
                asset_type=AssetType.subtitle,
                url="",
                storage_path=f"subtitles/{scene.id}.json",
                metadata_json={"subtitles": subtitles}
            )
            self.db.add(sub_asset)

            scene.status = SceneStatus.ready
            created_scenes.append(scene)

        # Update Project & Script status
        await self.db.execute(
            update(Project).where(Project.id == project_id).values(status=ProjectStatus.completed)
        )
        await self.db.execute(
            update(Script).where(Script.id == script_id).values(
                status=ScriptStatus.analyzed,
                analysis_result={"scenes_count": len(created_scenes), "cme_character_detected": bool(primary_char_dna)}
            )
        )
        await self.db.commit()
        
        # Eager-load scenes and assets before returning
        reload_stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.scenes).selectinload(Scene.assets),
                selectinload(Project.script)
            )
        )
        reload_res = await self.db.execute(reload_stmt)
        return reload_res.scalar_one()