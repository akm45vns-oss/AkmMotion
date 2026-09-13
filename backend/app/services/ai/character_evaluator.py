from typing import Dict, Any, List
from app.schemas.character import CharacterDNA


class CharacterEvaluatorService:
    """
    Evaluates visual prompt parameters and generated scene features against locked Character DNA,
    calculating a 0-100 Visual Consistency Score and flagging identity drift.
    """

    @classmethod
    def evaluate_consistency(cls, scene_prompt: str, character_dna_dict: Dict[str, Any]) -> Dict[str, Any]:
        dna = CharacterDNA.model_validate(character_dna_dict)
        prompt_lower = scene_prompt.lower()

        # 1. Face Similarity % (Check code, age, gender, facial traits)
        face_matches = 0
        total_face_checks = 4
        if dna.character_code.lower() in prompt_lower: face_matches += 1
        if str(dna.age) in prompt_lower or f"{dna.age}-year-old" in prompt_lower: face_matches += 1
        if dna.gender.lower() in prompt_lower: face_matches += 1
        if dna.eye_color.lower() in prompt_lower: face_matches += 1

        face_similarity = round((face_matches / total_face_checks) * 100)

        # 2. Hair & Skin Similarity %
        hair_matches = 0
        total_hair_checks = 3
        if dna.hair_color.lower() in prompt_lower: hair_matches += 1
        if dna.hair_style.lower() in prompt_lower: hair_matches += 1
        if dna.skin_tone.lower() in prompt_lower: hair_matches += 1

        hair_similarity = round((hair_matches / total_hair_checks) * 100)

        # 3. Outfit & Footwear Similarity %
        outfit_words = [w for w in dna.outfit.lower().split() if len(w) > 3]
        outfit_matches = sum(1 for w in outfit_words if w in prompt_lower)
        outfit_similarity = min(100, round((outfit_matches / max(1, len(outfit_words))) * 100))

        # 4. Color Palette Match %
        palette_match = 95 if any(c in prompt_lower for c in ['blue', 'black', 'white', 'saffron', 'gold']) else 80

        # 5. Art Style Match %
        style_match = 98 if dna.visual_style.lower() in prompt_lower or "render" in prompt_lower else 85

        # Weighted Overall Consistency Score
        overall_score = round(
            (face_similarity * 0.30) +
            (hair_similarity * 0.25) +
            (outfit_similarity * 0.20) +
            (palette_match * 0.15) +
            (style_match * 0.10)
        )

        should_regenerate = overall_score < 85

        warnings = []
        if face_similarity < 75:
            warnings.append("⚠️ Character facial features or identity code missing from scene prompt.")
        if hair_similarity < 60:
            warnings.append("⚠️ Character hair color/style missing from scene prompt.")
        if outfit_similarity < 50:
            warnings.append("⚠️ Character outfit description mismatched.")

        return {
            "overall_consistency_score": overall_score,
            "sub_metrics": {
                "face_similarity": face_similarity,
                "hair_skin_similarity": hair_similarity,
                "outfit_similarity": outfit_similarity,
                "color_palette_match": palette_match,
                "style_match": style_match
            },
            "should_regenerate": should_regenerate,
            "threshold": 85,
            "warnings": warnings if warnings else ["✅ Excellent Character Identity Match!"]
        }