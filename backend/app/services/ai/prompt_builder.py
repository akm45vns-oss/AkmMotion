from typing import Dict, Any, List, Optional
from app.schemas.character import CharacterDNA, PromptInjectionSpec


class PromptBuilderService:
    """
    Injects locked Character DNA into visual scene image prompts, ensuring
    100% character facial features, hair, skin, outfit, and multi-character consistency.
    """

    @classmethod
    def build_dna_description(cls, dna: CharacterDNA, name: Optional[str] = None) -> str:
        """Constructs a comprehensive, contradiction-free character appearance prompt segment."""
        features = []

        if name:
            features.append(f"{name}")

        features.append(f"{dna.gender}")
        features.append(f"{dna.age}yo")
        features.append(f"{dna.skin_tone} skin")

        # Hair details (style, length, color)
        hair_parts = []
        if dna.hair_length and dna.hair_length.lower() != "average":
            hair_parts.append(dna.hair_length.lower())
        if dna.hair_style and dna.hair_style.lower() not in (p.lower() for p in hair_parts):
            hair_parts.append(dna.hair_style.lower())
        if dna.hair_color:
            hair_parts.append(dna.hair_color.lower())
        hair_str = " ".join(hair_parts)
        if hair_str:
            features.append(f"{hair_str} hair")

        # Eyes and facial structure
        if dna.eye_color:
            features.append(f"{dna.eye_color.lower()} eyes")
        if dna.face_shape:
            features.append(f"{dna.face_shape.lower()} face")

        # Facial hair
        if dna.beard and dna.beard.lower() not in ("none", "clean shaven", ""):
            features.append(f"{dna.beard.lower()} beard")
        if dna.mustache and dna.mustache.lower() not in ("none", "clean shaven", ""):
            features.append(f"{dna.mustache.lower()} mustache")

        # Body type
        if dna.body_type and dna.body_type.lower() not in ("average", ""):
            features.append(f"{dna.body_type.lower()} build")

        # Attire and shoes
        if dna.outfit:
            features.append(f"wearing {dna.outfit}")
        if dna.shoes:
            features.append(f"with {dna.shoes}")

        # Accessories
        if dna.accessories:
            features.append(f"wearing {', '.join(dna.accessories)}")

        # Expression
        if dna.expression:
            features.append(f"{dna.expression.lower()} expression")

        return f"({', '.join(features)})"

    @classmethod
    def inject_character_dna(
        cls,
        raw_scene_prompt: str,
        character_dna_dict: Dict[str, Any],
        action_description: str = "",
        name: Optional[str] = None
    ) -> str:
        """Injects single character visual DNA into prompt."""
        dna = CharacterDNA.model_validate(character_dna_dict)
        char_desc = cls.build_dna_description(dna, name=name)

        scene_visual = raw_scene_prompt.strip()
        if action_description and action_description != scene_visual and not any(ord(c) > 127 for c in action_description):
            scene_visual = f"{scene_visual}. Action: {action_description}"

        style_hint = f"in {dna.visual_style} style" if dna.visual_style else "cinematic lighting"
        injected_prompt = (
            f"{scene_visual}, featuring character {char_desc}, "
            f"{style_hint}, consistent facial features, 9:16 vertical format, 8k"
        )
        return injected_prompt.strip()

    @classmethod
    def inject_multi_character_dna(
        cls,
        raw_scene_prompt: str,
        characters: List[Dict[str, Any]],
        action_description: str = ""
    ) -> str:
        """
        Injects multiple characters' visual DNA into a single scene prompt without contradictions.
        Each character retains distinct identity, attire, and features.
        """
        if not characters:
            return raw_scene_prompt

        if len(characters) == 1:
            c = characters[0]
            dna_data = c.get("dna", c)
            return cls.inject_character_dna(
                raw_scene_prompt,
                dna_data,
                action_description=action_description,
                name=c.get("name")
            )

        char_descriptions = []
        for idx, c in enumerate(characters):
            dna_data = c.get("dna", c)
            dna = CharacterDNA.model_validate(dna_data)
            c_name = c.get("name", f"Character {idx + 1}")
            char_descriptions.append(cls.build_dna_description(dna, name=c_name))

        if len(char_descriptions) == 2:
            combined_chars = f"{char_descriptions[0]} and {char_descriptions[1]}"
        else:
            combined_chars = ", ".join(char_descriptions[:-1]) + f", and {char_descriptions[-1]}"

        scene_visual = raw_scene_prompt.strip()
        if action_description and action_description != scene_visual and not any(ord(c) > 127 for c in action_description):
            scene_visual = f"{scene_visual}. Action: {action_description}"

        injected_prompt = (
            f"{scene_visual}, featuring {combined_chars}, "
            f"distinct characters, cinematic lighting, consistent character appearance, 9:16 vertical format, 8k"
        )
        return injected_prompt.strip()

    @classmethod
    def generate_injection_spec(cls, character_dna_dict: Dict[str, Any], scene_action: str) -> PromptInjectionSpec:
        dna = CharacterDNA.model_validate(character_dna_dict)
        segment = cls.inject_character_dna(scene_action, character_dna_dict, scene_action)

        locked_attrs = [
            "Face", "Hair Color", "Hair Style", "Hair Length", "Eye Color",
            "Skin Tone", "Face Shape", "Beard", "Mustache", "Outfit", "Shoes",
            "Accessories", "Age", "Gender", "Expression"
        ]

        return PromptInjectionSpec(
            character_id=dna.character_code,
            character_name=f"{dna.age}y {dna.gender} ({dna.visual_style})",
            injected_prompt_segment=segment,
            locked_attributes=locked_attrs
        )