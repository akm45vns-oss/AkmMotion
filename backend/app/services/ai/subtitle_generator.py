from typing import List, Dict, Any


class SubtitleGeneratorService:
    """
    Generates word-level subtitle timings for karaoke-sync video rendering.
    Returns both word-level and phrase-level formats.
    """

    async def generate_subtitles(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """
        Phrase-level subtitles (4-word chunks) — used for DB storage and simple display.
        """
        words = text.split()
        if not words:
            return []

        time_per_word = total_duration / len(words)
        subtitles = []
        current_time = 0.0
        chunk_size = 4

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            phrase = " ".join(chunk_words)
            duration = round(len(chunk_words) * time_per_word, 2)
            end_time = round(current_time + duration, 2)

            subtitles.append({
                "start": round(current_time, 2),
                "end": end_time,
                "text": phrase
            })
            current_time = end_time

        return subtitles

    async def generate_word_level_subtitles(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """
        Word-level timings for karaoke subtitle sync.
        Each word gets a precise {word, start, end} entry.

        Timing model:
        - Short words (1-3 chars): 0.25x weight
        - Medium words (4-7 chars): 1.0x weight
        - Long words (8+ chars): 1.5x weight
        - A leading pause of 0.2s (natural speech onset) is added.
        """
        words = text.split()
        if not words:
            return []

        # Calculate relative weights per word based on syllable count estimate
        def word_weight(w: str) -> float:
            clean = w.strip(".,!?।-—")
            n = len(clean)
            if n <= 2:
                return 0.5
            elif n <= 5:
                return 1.0
            elif n <= 8:
                return 1.4
            else:
                return 1.8

        weights = [word_weight(w) for w in words]
        total_weight = sum(weights) or 1.0

        # Available duration after onset pause
        onset = 0.25
        available = max(total_duration - onset, 1.0)

        result = []
        current_time = onset

        for i, word in enumerate(words):
            w_duration = round((weights[i] / total_weight) * available, 3)
            end_time = round(current_time + w_duration, 3)

            result.append({
                "word":  word,
                "start": round(current_time, 3),
                "end":   end_time,
                "index": i
            })
            current_time = end_time

        return result

    @staticmethod
    def compute_word_timings_from_text(text: str, total_duration: float) -> List[Dict[str, Any]]:
        """
        Synchronous helper — same logic, usable without async context.
        Returns list of {word, start, end, index}.
        """
        words = text.split()
        if not words or total_duration <= 0:
            return []

        def word_weight(w: str) -> float:
            clean = w.strip(".,!?।-—")
            n = len(clean)
            if n <= 2:   return 0.5
            elif n <= 5: return 1.0
            elif n <= 8: return 1.4
            else:        return 1.8

        weights = [word_weight(w) for w in words]
        total_weight = sum(weights) or 1.0
        onset = 0.25
        available = max(total_duration - onset, 1.0)

        result = []
        current_time = onset
        for i, word in enumerate(words):
            w_dur = round((weights[i] / total_weight) * available, 3)
            end_t = round(current_time + w_dur, 3)
            result.append({"word": word, "start": round(current_time, 3), "end": end_t, "index": i})
            current_time = end_t

        return result
