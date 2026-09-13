import json
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


class ScriptAnalyzerService:
    """
    Analyzes raw text script using Groq LLM (5-key round-robin, best free model)
    or OpenAI as secondary, with a local heuristic fallback.
    Targets 7-9 scenes for 60-90s YouTube Shorts / Instagram Reels.
    Supports English & Native Hindi scripts.
    """

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY

    def _get_groq_manager(self):
        """Lazy-load the GroqKeyManager singleton."""
        try:
            from app.services.ai.groq_key_manager import GroqKeyManager
            return GroqKeyManager.get_instance()
        except Exception as e:
            print(f"[ScriptAnalyzer] GroqKeyManager unavailable: {e}")
            return None

    def _build_system_prompt(self) -> str:
        return (
            "You are an elite visual director and cinematographer for YouTube Shorts and Instagram Reels (1080x1920 vertical). "
            "Your goal is to produce exactly 5 to 7 high-retention, visually stunning scenes totaling 45-75 seconds. "
            "\n"
            "CRITICAL RULES FOR `image_prompt` (HIGHEST PRIORITY):\n"
            "1. 'image_prompt' MUST ALWAYS BE 100% IN DESCRIPTIVE, VIVID CINEMATIC ENGLISH, regardless of the script's language.\n"
            "   Even if the script or narration is in Hindi, Spanish, or any other language, NEVER put non-English or Devanagari characters in 'image_prompt'.\n"
            "2. VISUAL RELEVANCE TO STORY: Each scene's image prompt must accurately and specifically depict THAT scene's action and setting.\n"
            "   - If the story is historical or cultural (e.g. ancient Indian kingdom, drought, village, prince), the visuals MUST accurately match that world (ancient mud houses, cracked dry earth, royal traditional robes, dhotis, turbans, flowing river), NOT modern Western clothes or generic 3D cartoons.\n"
            "   - If the scene is an environment, landscape, object, or crowd shot (e.g. cracked parched soil, gushing water stream, celebration in village), describe that environment vividly without forcing a single person into every shot.\n"
            "3. CHARACTER CONSISTENCY: If the story features recurring named characters, maintain consistent, period-appropriate appearance across their scenes, but ONLY include the character in scenes where they actually participate.\n"
            "4. NO TEXT: No text overlays, subtitles, watermarks, or speech bubbles in the image.\n"
            "\n"
            "Return ONLY a valid JSON object with key 'scenes' (array of scene objects). Each scene object MUST contain:\n"
            "- scene_number (int, 1-indexed)\n"
            "- narration (string: spoken voiceover in the ORIGINAL script language)\n"
            "- subtitle (string: bold, punchy uppercase caption, max 10 words)\n"
            "- image_prompt (string: cinematic 9:16 vertical prompt in rich ENGLISH. Format: [Shot type], [Subject & Setting], [Action & Atmosphere], [Lighting], 9:16 vertical format, 8k resolution)\n"
            "- shot_type (one of: wide_shot | medium_shot | close_up | extreme_close_up | over_shoulder | birds_eye | low_angle)\n"
            "- animation_style (one of: zoom | pan | fade | ken_burns | motion_blur | camera_push | camera_pull)\n"
            "- transition (one of: cut | fade | slide | wipe | zoom)\n"
            "- camera_motion (one of: push | pull | static | pan_left | pan_right | tilt_up | tilt_down | orbit)\n"
            "- emotion (string: e.g. '🔥 Hook', '💡 Reveal', '⚡ Shock', '🚀 Climax', '👉 CTA')\n"
            "- estimated_duration (float: between 6.0 and 10.0 seconds)\n"
        )

    def _build_user_prompt(self, script_text: str, style: str, language: str) -> str:
        return (
            f"Visual Style: {style}\n"
            f"Language: {language}\n"
            f"Target: 60-90 seconds total, 7-9 scenes\n"
            f"Script:\n{script_text}"
        )

    async def analyze_script(
        self,
        script_text: str,
        style: str = "Explainer",
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Run the full analysis pipeline:
        1. Groq llama-3.3-70b (5-key round-robin, best free quality)
        2. OpenAI GPT-3.5 (if key available)
        3. Local heuristic fallback (always works)
        """
        # ── 1. Groq (primary — best quality, free, 5-key rotation) ──────────
        groq = self._get_groq_manager()
        if groq:
            result = await self._try_groq(groq, script_text, style, language)
            if result:
                return result

        # ── 2. OpenAI GPT-3.5 (secondary) ───────────────────────────────────
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            result = await self._try_openai(script_text, style, language)
            if result:
                return result

        # ── 3. Heuristic fallback (always works, no API) ─────────────────────
        print("[ScriptAnalyzer] Using heuristic fallback (no LLM key available)")
        return self._heuristic_split(script_text, style)

    async def _try_groq(
        self,
        groq,
        script_text: str,
        style: str,
        language: str
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            content = await groq.chat_with_json(
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user",   "content": self._build_user_prompt(script_text, style, language)},
                ],
                model=groq.BEST_MODEL,
                temperature=0.75,
                max_tokens=4096,
            )
            data = json.loads(content)
            scenes = data.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) >= 4:
                print(f"[ScriptAnalyzer] Groq produced {len(scenes)} scenes.")
                return scenes
        except Exception as e:
            print(f"[ScriptAnalyzer] Groq attempt failed: {e}")
        return None

    async def _try_openai(
        self,
        script_text: str,
        style: str,
        language: str
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user",   "content": self._build_user_prompt(script_text, style, language)},
                ],
                response_format={"type": "json_object"},
                temperature=0.75,
            )
            data = json.loads(response.choices[0].message.content)
            scenes = data.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) >= 4:
                return scenes
        except Exception as e:
            print(f"[ScriptAnalyzer] OpenAI attempt failed: {e}")
        return None

    # ─── Heuristic fallback ─────────────────────────────────────────────────

    def _heuristic_split(self, script_text: str, style: str) -> List[Dict[str, Any]]:
        raw = [
            s.strip()
            for s in re.split(r'(?<=[.!?।|\n])\s+', script_text)
            if s.strip() and len(s.strip()) > 3
        ]
        if not raw:
            raw = [script_text.strip()]

        sentences = self._normalize_to_target_count(raw, target=8)

        SHOT_TYPES = [
            ("wide_shot",        "Extreme wide establishing shot"),
            ("medium_shot",      "Medium shot waist up"),
            ("close_up",         "Tight close-up face, emotional"),
            ("over_shoulder",    "Over-the-shoulder shot"),
            ("low_angle",        "Low-angle hero shot"),
            ("extreme_close_up", "Extreme close-up eyes, intense"),
            ("birds_eye",        "Bird's-eye view overhead"),
            ("medium_shot",      "Medium shot dynamic angle"),
            ("wide_shot",        "Wide pull-back triumphant"),
        ]
        ANIMATIONS    = ['camera_push','ken_burns','zoom','camera_pull','pan','motion_blur','camera_push','ken_burns','zoom']
        TRANSITIONS   = ['cut','fade','zoom','cut','slide','cut','fade','wipe','cut']
        CAM_MOTIONS   = ['push','tilt_up','pull','pan_left','orbit','pan_right','tilt_down','push','pull']
        EMOTIONS      = ['🔥 HOOK','💡 CONTEXT','⚡ SECRET','🎬 DEEP DIVE','🚀 IMPACT','😱 SHOCK','🎯 PROOF','👉 CALL TO ACTION','✅ CLOSE']

        STYLE_VISUAL = {
            "Cinematic":  "dramatic cinematic lighting, film grain, shallow depth of field, anamorphic lens flare",
            "Vlog":       "warm natural daylight, hand-held feel, vibrant colors, lifestyle aesthetic",
            "Anime":      "anime art style, vibrant colors, cel-shaded, manga panel composition",
            "Explainer":  "clean bright studio lighting, professional corporate aesthetic",
            "Story":      "golden-hour warm light, emotional close-ups, narrative atmosphere",
            "Finance":    "clean corporate environment, professional lighting, trust-building composition",
        }
        style_visual = STYLE_VISUAL.get(style, "cinematic atmospheric lighting, premium visual quality")

        scenes = []
        for idx, sentence in enumerate(sentences):
            words        = sentence.split()
            duration     = min(max(round(len(words) / 2.1, 1), 7.0), 11.0)
            shot_enum, shot_label = SHOT_TYPES[idx % len(SHOT_TYPES)]

            formatted_subtitle = " ".join([
                w.upper() if len(w) > 3 and i % 2 == 0 else w
                for i, w in enumerate(words)
            ])[:80]

            clean = re.sub(r'[\U00010000-\U0010ffff]', '', sentence)
            # Only keep English characters for image prompt to ensure diffusion model compatibility
            english_words = re.findall(r'[a-zA-Z0-9]+', clean)
            if len(english_words) >= 3:
                subject_desc = " ".join(english_words[:12])
            else:
                subject_desc = f"atmospheric {style.lower()} scene capturing the dramatic narrative"

            image_prompt = (
                f"{shot_label}. {subject_desc}. "
                f"{style} style. {style_visual}. "
                f"9:16 vertical format, cinematic composition, photorealistic 8k ultra-detailed, no text overlays"
            )

            scenes.append({
                "scene_number":       idx + 1,
                "narration":          sentence,
                "subtitle":           formatted_subtitle,
                "image_prompt":       image_prompt,
                "shot_type":          shot_enum,
                "animation_style":    ANIMATIONS[idx % len(ANIMATIONS)],
                "transition":         TRANSITIONS[idx % len(TRANSITIONS)],
                "camera_motion":      CAM_MOTIONS[idx % len(CAM_MOTIONS)],
                "emotion":            EMOTIONS[idx % len(EMOTIONS)],
                "estimated_duration": duration,
            })

        return scenes

    def _normalize_to_target_count(self, sentences: List[str], target: int = 8) -> List[str]:
        """Merge shortest adjacent pairs until at or below target count."""
        while len(sentences) > target:
            min_len = min(len(s) for s in sentences)
            merged = False
            for i, s in enumerate(sentences):
                if len(s) == min_len and i + 1 < len(sentences):
                    sentences[i] = s + " " + sentences.pop(i + 1)
                    merged = True
                    break
            if not merged:
                break
        return sentences