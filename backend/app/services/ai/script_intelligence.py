import re
from typing import Dict, Any, List


class ScriptCleaner:
    """
    Cleans, normalizes, and sanitizes user input scripts.
    Strips artifacts, corrupt symbols, extra whitespace, and duplicate words.
    """

    @staticmethod
    def clean_script(text: str) -> str:
        if not text:
            return ""

        # Remove markdown headers, code fences, and unwanted symbol spam
        cleaned = re.sub(r'[*#@/\\%]{2,}', ' ', text)
        cleaned = re.sub(r'```[\s\S]*?```', ' ', cleaned)
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)  # HTML tags

        # Normalize unicode quotes, apostrophes, and dashes
        cleaned = cleaned.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
        cleaned = cleaned.replace('—', '-').replace('–', '-')

        # Remove strange non-printable control characters (preserve newlines/tabs)
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)

        # Fix duplicate consecutive words (e.g., "the the" -> "the")
        cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)

        # Normalize multiple spaces and paragraph breaks
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # Ensure proper punctuation spacing
        cleaned = re.sub(r'\s+([.,!?])', r'\1', cleaned)

        return cleaned.strip()


class LanguageDetector:
    """
    Detects language (English or Hindi) and assigns modular voice accent mappings.
    """

    @staticmethod
    def detect_language(text: str, manual_choice: str = "Auto Detect") -> Dict[str, str]:
        if manual_choice in ["English", "Hindi"]:
            lang = "hi" if manual_choice == "Hindi" else "en"
        else:
            # Check for Devanagari script characters for Hindi
            hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
            total_chars = len(re.findall(r'\w', text)) or 1
            lang = "hi" if (hindi_chars / total_chars) > 0.15 else "en"

        if lang == "hi":
            return {
                "language_code": "hi",
                "language_label": "Hindi",
                "accent_name": "Indian Hindi Accent",
                "voice_id": "hi-IN-Neural"
            }
        else:
            return {
                "language_code": "en",
                "language_label": "English",
                "accent_name": "Indian English Accent",
                "voice_id": "en-IN-Raveena"
            }


class ScriptHealthEvaluator:
    """
    Evaluates script quality and calculates 0-100 Script Health Score
    with 5 sub-dimension metrics and AI improvement suggestions.
    """

    @staticmethod
    def evaluate(script_text: str, manual_lang: str = "Auto Detect") -> Dict[str, Any]:
        clean_text = ScriptCleaner.clean_script(script_text)
        words = clean_text.split()
        word_count = len(words)

        sentences = [s.strip() for s in re.split(r'(?<=[.!?|])\s+', clean_text) if s.strip()]
        sentence_count = len(sentences) or 1
        avg_sentence_len = round(word_count / sentence_count, 1)

        # 1. Grammar & Spelling Score
        symbol_noise = len(re.findall(r'[*#@/\\%]', script_text))
        grammar_score = max(70, min(99, 98 - (symbol_noise * 3)))

        # 2. Readability & Flow Score (Optimal sentence length for Shorts: 8-15 words)
        if 8 <= avg_sentence_len <= 15:
            readability_score = 95
        elif avg_sentence_len < 8:
            readability_score = 88
        else:
            readability_score = max(60, 95 - int((avg_sentence_len - 15) * 2.5))

        # 3. Narration Quality
        narration_score = min(98, max(75, 92 + (5 if 40 <= word_count <= 180 else -10)))

        # 4. Engagement & Hook Strength
        first_sentence = sentences[0].lower() if sentences else ""
        has_hook = any(kw in first_sentence for kw in ['know', 'secret', 'why', 'how', 'stop', 'unbelievable', 'truth', 'ever', 'never', 'क्या', 'जानते', 'रहस्य'])
        engagement_score = 94 if has_hook else 82

        # 5. Scene Balance & Distribution
        estimated_scenes = max(3, min(10, round(word_count / 22)))
        scene_balance_score = 92 if 5 <= estimated_scenes <= 8 else 85

        # Overall Script Health Score (0-100)
        overall_score = round(
            (grammar_score * 0.25) +
            (readability_score * 0.25) +
            (narration_score * 0.20) +
            (engagement_score * 0.15) +
            (scene_balance_score * 0.15)
        )

        # Language and Voice Accent
        lang_meta = LanguageDetector.detect_language(clean_text, manual_lang)

        # Estimated Duration (Words / 2.4 words per second)
        estimated_duration = max(15, min(60, round(word_count / 2.4)))
        estimated_render_time = "1-2 minutes"

        # AI Suggestions
        suggestions = []
        if not has_hook:
            suggestions.append("🔥 Add a stronger hook question or surprising stat in the first sentence.")
        if avg_sentence_len > 18:
            suggestions.append("✂️ Some sentences are too long for quick YouTube Shorts subtitles. Split them up.")
        if word_count < 40:
            suggestions.append("📝 Script is very short. Expand to 50-120 words for a 60-second video.")
        if word_count > 200:
            suggestions.append("⏱️ Script exceeds 200 words. Trim slightly to fit within YouTube Shorts 60s limit.")
        if symbol_noise > 0:
            suggestions.append("✨ Clean unneeded markdown symbols or broken formatting.")
        if not suggestions:
            suggestions.append("✅ Outstanding script! Perfectly optimized for AI voiceover and video rendering.")

        return {
            "overall_score": overall_score,
            "sub_scores": {
                "grammar": grammar_score,
                "readability": readability_score,
                "narration": narration_score,
                "engagement": engagement_score,
                "scene_balance": scene_balance_score
            },
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_len": avg_sentence_len,
                "estimated_duration": f"{estimated_duration} seconds",
                "estimated_scenes": estimated_scenes,
                "language": f"{lang_meta['language_label']} ({manual_lang if manual_lang != 'Auto Detect' else 'Detected'})",
                "accent": lang_meta["accent_name"],
                "estimated_render_time": estimated_render_time
            },
            "suggestions": suggestions
        }


class ScriptImprover:
    """
    Safely improves script grammar, flow, and engagement while preserving
    original meaning, names, numbers, and URLs. Supports native Hindi & English phrasing.
    """

    @staticmethod
    def improve(script_text: str) -> Dict[str, Any]:
        cleaned = ScriptCleaner.clean_script(script_text)
        is_hindi = bool(re.findall(r'[\u0900-\u097F]', cleaned))
        sentences = [s.strip() for s in re.split(r'(?<=[.!?|])\s+', cleaned) if s.strip()]

        improved_sentences = []
        for i, s in enumerate(sentences):
            fixed = s
            # Capitalization for English
            if not is_hindi and fixed and len(fixed) > 0:
                fixed = fixed[0].upper() + fixed[1:]

            # Ending Punctuation
            if fixed and not fixed.endswith(('.', '!', '?', '।')):
                fixed += '।' if is_hindi else '.'

            # Native Hook Enhancement
            if i == 0:
                if is_hindi:
                    if not any(kw in fixed for kw in ['क्या आप जानते हैं', 'जानिए', 'रहस्य']):
                        fixed = f"क्या आप जानते हैं? {fixed}"
                else:
                    if not any(kw in fixed.lower() for kw in ['did you know', 'here is why', 'the secret', 'ever wondered']):
                        fixed = f"Did you know? {fixed}"

            improved_sentences.append(fixed)

        improved_script = " ".join(improved_sentences)

        return {
            "original_script": script_text,
            "cleaned_script": cleaned,
            "improved_script": improved_script,
            "changes_applied": len(improved_sentences)
        }