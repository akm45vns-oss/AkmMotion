import io
import re
from app.core.config import settings


class VoiceGeneratorService:
    """
    Synthesizes speech audio for scene narration.
    Priority: OpenAI TTS → gTTS (free, Indian accent).
    Returns audio bytes directly for streaming responses.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    async def generate_voice(
        self,
        text: str,
        voice_id: str = "alloy",
        language: str = "en",
        gender: str = "male"
    ) -> str:
        """
        Returns a placeholder URL or base64 data URI.
        Real audio is served directly via the /api/v1/ai/tts endpoint.
        """
        # Not used for direct streaming — the /tts endpoint handles bytes
        return ""

    def synthesize_to_bytes(
        self,
        text: str,
        language: str = "en",
        gender: str = "male"
    ) -> bytes:
        """
        Synthesizes speech and returns raw MP3 bytes.
        Used by the /tts API endpoint for streaming.

        language: 'en' for Indian English, 'hi' for Hindi
        gender: 'male' | 'female' (gTTS doesn't support gender, but ElevenLabs can)
        """
        clean_text = self._clean_text(text)
        if not clean_text:
            return b""

        # Try OpenAI TTS first (if key available)
        if self.api_key and self.api_key.startswith("sk-"):
            result = self._try_openai_tts_sync(clean_text, language, gender)
            if result:
                return result

        # gTTS fallback — Indian Hindi or Indian English accent
        return self._gtts_synthesize(clean_text, language)

    def _clean_text(self, text: str) -> str:
        """Strip emojis, markdown, and control chars; keep letters + punctuation."""
        clean = re.sub(r'[^\w\s.,?!\'-\u0900-\u097F]', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _gtts_synthesize(self, text: str, language: str = "en") -> bytes:
        """
        gTTS synthesis — returns MP3 bytes.
        - Hindi: lang='hi' (native Devanagari TTS)
        - English: lang='en', tld='co.in' (Indian English accent)
        """
        try:
            from gtts import gTTS
            is_hindi = (language == "hi") or bool(re.search(r'[\u0900-\u097F]', text))
            if is_hindi:
                tts = gTTS(text=text, lang="hi")
            else:
                tts = gTTS(text=text, lang="en", tld="co.in")

            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp.read()
        except Exception as e:
            print(f"[VoiceGenerator] gTTS error: {e}")
            return b""

    def _try_openai_tts_sync(self, text: str, language: str, gender: str) -> bytes | None:
        """
        Synchronous OpenAI TTS call (using httpx under the hood via openai SDK sync client).
        Voice mapping: en-male=onyx, en-female=nova, hi=shimmer (closest to South Asian)
        """
        try:
            import openai
            voice_map = {
                ("en", "male"):   "onyx",
                ("en", "female"): "nova",
                ("hi", "male"):   "onyx",
                ("hi", "female"): "shimmer",
            }
            voice = voice_map.get((language, gender), "onyx")
            client = openai.OpenAI(api_key=self.api_key)
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"[VoiceGenerator] OpenAI TTS error: {e}")
            return None
