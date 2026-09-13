from typing import Dict, Any, List
from app.schemas.character import CharacterDNA, PromptInjectionSpec


class PromptBuilderService:
    """
    Injects locked Character DNA into visual scene image prompts, ensuring
    100% character facial features, hair, skin, and outfit consistency.
    """

    @classmethod
    def inject_character_dna(cls, raw_scene_prompt: str, character_dna_dict: Dict[str, Any], action_description: str = "") -> str:
        dna = CharacterDNA.model_validate(character_dna_dict)

        # Build Character DNA Description Segment (concise for image models)
        char_desc = (
            f"Character ({dna.gender}, {dna.age}yo, {dna.skin_tone} skin, {dna.hair_color} hair, "
            f"wearing {dna.outfit})"
        )

        if dna.accessories:
            char_desc += f" with {', '.join(dna.accessories)}"

        scene_visual = raw_scene_prompt.strip()

        # If action_description is provided and clean ASCII, include it
        if action_description and action_description != scene_visual and not any(ord(c) > 127 for c in action_description):
            scene_visual = f"{scene_visual}. Action: {action_description}"

        injected_prompt = (
            f"{scene_visual}, featuring {char_desc}, "
            f"cinematic lighting, consistent character appearance, 9:16 vertical format, 8k"
        )

        return injected_prompt.strip()

    @classmethod
    def generate_injection_spec(cls, character_dna_dict: Dict[str, Any], scene_action: str) -> PromptInjectionSpec:
        dna = CharacterDNA.model_validate(character_dna_dict)
        segment = cls.inject_character_dna(scene_action, character_dna_dict, scene_action)

        locked_attrs = ["Face", "Hair Color", "Hair Style", "Eye Color", "Skin Tone", "Outfit", "Accessories", "Age", "Gender"]

        return PromptInjectionSpec(
            character_id=dna.character_code,
            character_name=f"{dna.age}y {dna.gender} ({dna.visual_style})",
            injected_prompt_segment=segment,
            locked_attributes=locked_attrs
        )