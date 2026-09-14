import json
import re
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings


class ScriptAnalyzerService:
    """
    Analyzes and segments raw text scripts into video scenes.
    
    NON-NEGOTIABLE CORE INVARIANT:
    AkmMotion is a strict SCRIPT-TO-VIDEO generator.
    The user's script is the authoritative, immutable source.
    AI must NEVER invent, add, elaborate, expand, explain, or rewrite narration or dialogue.
    The concatenated scene narrations must contain only the user's original words.
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

    @staticmethod
    def calculate_scene_count(script_text: str) -> Tuple[int, int]:
        """
        Calculates (target_scenes, max_scenes) strictly based on script word count and sentences.
        Deterministic policy:
        0–20 words    → 1 scene (or up to min(sentences, 3) if multiple complete sentences exist)
        21–50 words   → 1–2 scenes (max 2)
        51–100 words  → 2–3 scenes (max 3)
        101–180 words → 3–4 scenes (max 4)
        181–300 words → 4–6 scenes (max 6)
        300+ words    → adaptive (~40-60 words/scene, capped at 10)
        """
        words = script_text.strip().split()
        word_count = len(words)

        raw_sentences = [
            s.strip()
            for s in re.split(r'(?<=[.!?।|\n])\s+', script_text)
            if s.strip() and len(s.strip()) > 3
        ]
        sentence_count = max(1, len(raw_sentences))

        if word_count <= 20:
            if sentence_count == 1:
                return 1, 1
            else:
                scenes = min(sentence_count, 3)
                return scenes, scenes
        elif word_count <= 50:
            target = min(sentence_count, 2)
            return max(1, target), 2
        elif word_count <= 100:
            target = min(sentence_count, 3)
            return max(2, target), 3
        elif word_count <= 180:
            target = min(sentence_count, 4)
            return max(3, target), 4
        elif word_count <= 300:
            target = min(sentence_count, 6)
            return max(4, target), 6
        else:
            adaptive = min(10, max(6, (word_count + 49) // 50))
            target = min(sentence_count, adaptive)
            return max(4, target), adaptive

    WORDS_PER_SECOND = 2.2
    MIN_SCENE_DURATION = 3.0
    MAX_SCENE_DURATION = 10.0

    @classmethod
    def calculate_estimated_duration(cls, word_count: int, scene_count: int = 1) -> float:
        """
        Harmonized duration calculator across frontend and backend:
        - 2.2 words per second natural voiceover cadence
        - Bounded between 3.0s and 10.0s per scene
        """
        if word_count <= 0:
            return 0.0
        scene_count = max(1, scene_count)
        words_per_scene = word_count / scene_count
        scene_dur = min(max(round(words_per_scene / cls.WORDS_PER_SECOND, 1), cls.MIN_SCENE_DURATION), cls.MAX_SCENE_DURATION)
        return round(scene_dur * scene_count, 1)

    @staticmethod
    def normalize_tokens(text: str) -> List[str]:
        """
        Extracts lowercase word tokens preserving unicode word characters (including Hindi).
        Strips surrounding punctuation and symbols.
        """
        return re.findall(r"[\w\u0900-\u097F]+", text.lower())

    @classmethod
    def validate_script_fidelity(
        cls,
        original_script: str,
        scenes: List[Dict[str, Any]],
        max_scenes: int
    ) -> Tuple[bool, str]:
        """
        Validates that the generated scenes preserve the user's script verbatim:
        1. Checks scene count does not exceed max_scenes.
        2. Invariant:
           normalize_tokens(original_script) == normalize_tokens(scene_1.narration + " " + scene_2.narration + ...)
           - Preserves exact word order
           - Preserves duplicate words
           - Zero missing words
           - Zero extra/inserted words
           - Zero reordered words
        3. Ensures subtitle matches narration verbatim.
        """
        if not isinstance(scenes, list) or len(scenes) == 0:
            return False, "No scenes produced"

        if len(scenes) > max_scenes:
            return False, f"Scene count {len(scenes)} exceeds maximum allowed {max_scenes}"

        narrations = [str(s.get("narration", "")).strip() for s in scenes]
        if any(not n for n in narrations):
            return False, "One or more scenes have empty narration"

        orig_tokens = cls.normalize_tokens(original_script)
        concatenated_narration = " ".join(narrations)
        scene_tokens = cls.normalize_tokens(concatenated_narration)

        if not orig_tokens:
            return True, "Valid"

        # The core invariant: exact list equality of normalized tokens
        if orig_tokens != scene_tokens:
            if len(scene_tokens) > len(orig_tokens):
                extra_count = len(scene_tokens) - len(orig_tokens)
                return False, f"Inserted/extra words detected: scenes contain {extra_count} extra token(s) (expected {len(orig_tokens)}, got {len(scene_tokens)})"
            elif len(scene_tokens) < len(orig_tokens):
                missing_count = len(orig_tokens) - len(scene_tokens)
                return False, f"Omitted words detected: scenes missing {missing_count} token(s) (expected {len(orig_tokens)}, got {len(scene_tokens)})"
            else:
                for i, (ot, st) in enumerate(zip(orig_tokens, scene_tokens)):
                    if ot != st:
                        return False, f"Word mismatch or reordering at token {i + 1}: expected '{ot}', got '{st}'"
                return False, "Normalized scene tokens do not match original script"

        # Sanitize subtitle to ensure it remains a faithful segment of that scene's narration
        for s in scenes:
            sub = str(s.get("subtitle", "")).strip()
            narr = str(s.get("narration", "")).strip()
            if not sub or cls.normalize_tokens(sub) != cls.normalize_tokens(narr):
                s["subtitle"] = narr

        return True, "Valid"

    def _build_system_prompt(self, target_scenes: int, max_scenes: int) -> str:
        return (
            "You are an elite visual director and cinematographer for vertical videos (1080x1920 vertical).\n"
            "AkmMotion is a strict SCRIPT-TO-VIDEO generator where the user's script is the authoritative, immutable source.\n"
            "\n"
            "CRITICAL NON-NEGOTIABLE SCRIPT FIDELITY RULES (HIGHEST PRIORITY):\n"
            "1. DO NOT INVENT, ADD, ELABORATE, EXPAND, EXPLAIN, OR REWRITE ANY NARRATION OR DIALOGUE.\n"
            "2. DO NOT add hooks, intros, outros, transitions, tips, examples, or extra sentences.\n"
            f"3. Produce exactly {target_scenes} scene(s) (Maximum allowed: {max_scenes}).\n"
            "4. The 'narration' field in each scene MUST be an exact slice copied directly from the supplied script.\n"
            "   Every word of the user's script must appear exactly once in sequence across the scenes. Zero added words.\n"
            "5. The 'subtitle' field MUST be the exact words from that scene's narration in the exact same language.\n"
            "6. You may ONLY be creative in the 'image_prompt' field (describing the visual scene, characters, setting, lighting in vivid 9:16 English).\n"
            "\n"
            "CRITICAL RULES FOR `image_prompt`:\n"
            "- 'image_prompt' MUST ALWAYS BE 100% IN DESCRIPTIVE, VIVID CINEMATIC ENGLISH, regardless of script language.\n"
            "- Ground visuals in authentic characters, setting, actions, and lighting.\n"
            "\n"
            "Return ONLY a valid JSON object with key 'scenes' (array of scene objects). Each scene object MUST contain:\n"
            "- scene_number (int, 1-indexed)\n"
            "- narration (string: exact verbatim segment copied from original script)\n"
            "- subtitle (string: exact words from narration)\n"
            "- image_prompt (string: cinematic 9:16 vertical prompt in rich ENGLISH. Format: [Shot type], [Subject & Setting], [Action & Atmosphere], [Lighting], 9:16 vertical format, 8k photorealistic)\n"
            "- shot_type (one of: wide_shot | medium_shot | close_up | extreme_close_up | over_shoulder | birds_eye | low_angle)\n"
            "- animation_style (one of: zoom | pan | fade | ken_burns | motion_blur | camera_push | camera_pull)\n"
            "- transition (one of: cut | fade | slide | wipe | zoom)\n"
            "- camera_motion (one of: push | pull | static | pan_left | pan_right | tilt_up | tilt_down | orbit)\n"
            "- emotion (string: e.g. '🔥 Hook', '💡 Reveal', '⚡ Shock', '🚀 Climax', '👉 CTA')\n"
            "- estimated_duration (float: between 3.0 and 10.0 seconds)\n"
        )

    def _build_user_prompt(
        self,
        script_text: str,
        style: str,
        language: str,
        target_scenes: int,
        max_scenes: int
    ) -> str:
        cultural_hint = ""
        if re.search(r"[\u0900-\u097F]", script_text) or language.lower() in ["hi", "hindi", "hinglish"]:
            cultural_hint = (
                "\nCULTURAL CONTEXT: Indian Hindi story detected.\n"
                "- Visual prompts must feature authentic Indian characters, settings, and clothing.\n"
                "- Subtitles must be in the exact Hindi text from the script."
            )

        return (
            f"Visual Style: {style}\n"
            f"Language: {language}\n"
            f"Target: exactly {target_scenes} scene(s) (Maximum allowed: {max_scenes})\n"
            f"Source Script (COPY VERBATIM into scene narrations, DO NOT ADD EXTRA WORDS):\n"
            f"\"\"\"\n{script_text}\n\"\"\"\n"
            f"{cultural_hint}"
        )

    async def analyze_script(
        self,
        script_text: str,
        style: str = "Explainer",
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        clean_text = script_text.strip()
        if not clean_text:
            return []

        target_scenes, max_scenes = self.calculate_scene_count(clean_text)

        # Fast path for very short scripts (<= 20 words and single sentence)
        words = clean_text.split()
        raw_sentences = [
            s.strip()
            for s in re.split(r'(?<=[.!?।|\n])\s+', clean_text)
            if s.strip() and len(s.strip()) > 3
        ]
        if len(words) <= 20 and len(raw_sentences) <= 1:
            print(f"[ScriptAnalyzer] Short script fast-path ({len(words)} words) -> 1 scene")
            return self.deterministic_segmentation(clean_text, style=style, target_scenes=1)

        # ── 1. Groq (primary — fast, free, 5-key rotation) ───────────────────
        groq = self._get_groq_manager()
        if groq:
            result = await self._try_groq(groq, clean_text, style, language, target_scenes, max_scenes)
            if result:
                return result

        # ── 2. OpenAI GPT-3.5 (secondary) ───────────────────────────────────
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            result = await self._try_openai(clean_text, style, language, target_scenes, max_scenes)
            if result:
                return result

        # ── 3. Deterministic fallback (100% faithful) ────────────────────────
        print(f"[ScriptAnalyzer] Using deterministic segmentation for {target_scenes} scenes")
        return self.deterministic_segmentation(clean_text, style=style, target_scenes=target_scenes)

    async def _try_groq(
        self,
        groq,
        script_text: str,
        style: str,
        language: str,
        target_scenes: int,
        max_scenes: int
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            content = await groq.chat_with_json(
                messages=[
                    {"role": "system", "content": self._build_system_prompt(target_scenes, max_scenes)},
                    {"role": "user",   "content": self._build_user_prompt(script_text, style, language, target_scenes, max_scenes)},
                ],
                model=groq.BEST_MODEL,
                temperature=0.3,  # Lower temperature for strict fidelity
                max_tokens=4096,
            )
            data = json.loads(content)
            scenes = data.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) >= 1:
                is_valid, reason = self.validate_script_fidelity(script_text, scenes, max_scenes)
                if is_valid:
                    print(f"[ScriptAnalyzer] Groq produced {len(scenes)} valid scenes matching script fidelity.")
                    return scenes
                else:
                    print(f"[ScriptAnalyzer] Groq output failed script fidelity validation: {reason}. Falling back to deterministic segmentation.")
        except Exception as e:
            print(f"[ScriptAnalyzer] Groq attempt failed: {e}")
        return None

    async def _try_openai(
        self,
        script_text: str,
        style: str,
        language: str,
        target_scenes: int,
        max_scenes: int
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._build_system_prompt(target_scenes, max_scenes)},
                    {"role": "user",   "content": self._build_user_prompt(script_text, style, language, target_scenes, max_scenes)},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            data = json.loads(response.choices[0].message.content)
            scenes = data.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) >= 1:
                is_valid, reason = self.validate_script_fidelity(script_text, scenes, max_scenes)
                if is_valid:
                    return scenes
                else:
                    print(f"[ScriptAnalyzer] OpenAI output failed script fidelity validation: {reason}. Falling back to deterministic segmentation.")
        except Exception as e:
            print(f"[ScriptAnalyzer] OpenAI attempt failed: {e}")
        return None

    # ─── Deterministic Segmentation (Guaranteed 100% Fidelity) ─────────────

    def deterministic_segmentation(
        self,
        script_text: str,
        style: str = "Explainer",
        target_scenes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        clean_text = script_text.strip()
        if not clean_text:
            return []

        raw = [
            s.strip()
            for s in re.split(r'(?<=[.!?।|\n])\s+', clean_text)
            if s.strip()
        ]
        if not raw:
            raw = [clean_text]

        if target_scenes is None:
            target_scenes, _ = self.calculate_scene_count(clean_text)

        if target_scenes == 1 or len(raw) == 1:
            sentence_groups = [" ".join(raw)]
        else:
            # If we have fewer sentence units than target_scenes, partition by clause or contiguous word chunks
            if len(raw) < target_scenes:
                clauses = [
                    s.strip()
                    for s in re.split(r'(?<=[,;:\-—])\s+', clean_text)
                    if s.strip()
                ]
                if len(clauses) >= target_scenes:
                    raw = clauses
                else:
                    all_words = clean_text.split()
                    if len(all_words) >= target_scenes:
                        k, m = divmod(len(all_words), target_scenes)
                        raw = []
                        w_start = 0
                        for i in range(target_scenes):
                            w_end = w_start + k + (1 if i < m else 0)
                            chunk = " ".join(all_words[w_start:w_end])
                            if chunk:
                                raw.append(chunk)
                            w_start = w_end

            target_scenes = max(1, min(target_scenes, len(raw)))
            k, m = divmod(len(raw), target_scenes)
            sentence_groups = []
            start = 0
            for i in range(target_scenes):
                end = start + k + (1 if i < m else 0)
                group = " ".join(raw[start:end])
                if group:
                    sentence_groups.append(group)
                start = end

        SHOT_TYPES = [
            ("wide_shot",        "Wide establishing shot"),
            ("medium_shot",      "Medium shot waist up"),
            ("close_up",         "Close-up face, emotional"),
            ("over_shoulder",    "Over-the-shoulder shot"),
            ("low_angle",        "Low-angle hero shot"),
            ("extreme_close_up", "Extreme close-up eyes, intense"),
            ("birds_eye",        "Bird's-eye view overhead"),
            ("medium_shot",      "Medium shot dynamic angle"),
            ("wide_shot",        "Wide pull-back triumphant"),
        ]
        ANIMATIONS  = ['ken_burns', 'pan', 'zoom', 'fade', 'camera_push', 'camera_pull', 'motion_blur']
        TRANSITIONS = ['cut', 'fade', 'slide', 'wipe', 'zoom']
        CAM_MOTIONS = ['push', 'pan_right', 'pan_left', 'pull', 'tilt_up', 'tilt_down', 'orbit']
        EMOTIONS    = ['🔥 HOOK', '💡 CONTEXT', '⚡ KEY POINT', '🎬 SCENE', '🚀 CLIMAX', '👉 CTA']

        STYLE_VISUAL = {
            "Cinematic":  "cinematic dramatic lighting, photorealistic 8k, film grain, masterpiece",
            "Vlog":       "natural daylight, authentic lifestyle photography, vibrant colors, 8k",
            "Anime":      "makoto shinkai anime style, vibrant cel-shaded, beautiful lighting",
            "Explainer":  "cinematic documentary style, natural lighting, authentic subjects, highly detailed",
            "Story":      "cinematic storytelling, warm golden-hour lighting, emotional narrative depth",
            "Finance":    "clean modern aesthetic, crisp architectural lighting, premium detail",
        }
        style_visual = STYLE_VISUAL.get(style, "cinematic atmospheric lighting, photorealistic 8k, ultra-detailed")
        is_hindi = bool(re.search(r"[\u0900-\u097F]", clean_text))

        scenes = []
        for idx, sentence in enumerate(sentence_groups):
            words = sentence.split()
            duration = min(max(round(len(words) / self.WORDS_PER_SECOND, 1), self.MIN_SCENE_DURATION), self.MAX_SCENE_DURATION)
            shot_enum, shot_label = SHOT_TYPES[idx % len(SHOT_TYPES)]

            clean_words = re.sub(r'[\U00010000-\U0010ffff]', '', sentence)
            english_words = re.findall(r'[a-zA-Z0-9]+', clean_words)
            if len(english_words) >= 3:
                subject_desc = " ".join(english_words[:12])
            elif is_hindi:
                subject_desc = "authentic Indian characters in traditional setting engaged in the story moment"
            else:
                subject_desc = "dramatic narrative moment capturing the scene action with characters"

            image_prompt = (
                f"{shot_label}. {subject_desc}. "
                f"{style} style. {style_visual}. "
                f"9:16 vertical format, cinematic composition, photorealistic 8k ultra-detailed, no text overlays"
            )

            scenes.append({
                "scene_number":       idx + 1,
                "narration":          sentence,
                "subtitle":           sentence,
                "image_prompt":       image_prompt,
                "shot_type":          shot_enum,
                "animation_style":    ANIMATIONS[idx % len(ANIMATIONS)],
                "transition":         TRANSITIONS[idx % len(TRANSITIONS)],
                "camera_motion":      CAM_MOTIONS[idx % len(CAM_MOTIONS)],
                "emotion":            EMOTIONS[idx % len(EMOTIONS)],
                "estimated_duration": duration,
            })

        return scenes

    def _heuristic_split(self, script_text: str, style: str) -> List[Dict[str, Any]]:
        """Backward-compatible alias for deterministic_segmentation."""
        return self.deterministic_segmentation(script_text, style=style)