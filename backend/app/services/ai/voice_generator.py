import io
import re
import asyncio
import hashlib
from typing import Optional, Dict
from app.core.config import settings

# In-memory audio cache to prevent redundant synthesis and ensure 0ms replay
_AUDIO_CACHE: Dict[str, bytes] = {}


class VoiceGeneratorService:
    """
    Synthesizes studio-grade neural speech audio for scene narration.
    Priority:
      1. Microsoft Edge Neural TTS (Free, ultra-realistic studio voices, native Hindi & Indian English)
      2. OpenAI TTS (if API key configured)
      3. gTTS (Google Translate fallback)
    """

    VOICE_PRESETS = {
        "voice_indian_en": "en-IN-PrabhatNeural",       # Rishi (Indian Accent English Male)
        "voice_indian_hi": "hi-IN-SwaraNeural",         # Heera (Native Hindi Female)
        "voice_alloy":     "en-US-GuyNeural",           # Alloy (Calm & Direct Male)
        "voice_echo":      "en-US-ChristopherNeural",   # Echo (Upbeat & Energetic Male)
        "voice_fable":     "en-US-JennyNeural",         # Fable (Warm Storyteller Female)
        "voice_onyx":      "en-US-GuyNeural",           # Onyx (Authoritative & Deep Male)
    }

    DEFAULT_VOICES = {
        ("hi", "male"):   "hi-IN-MadhurNeural",
        ("hi", "female"): "hi-IN-SwaraNeural",
        ("en", "male"):   "en-IN-PrabhatNeural",
        ("en", "female"): "en-IN-NeerjaNeural",
    }

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    def _clean_text(self, text: str) -> str:
        """Strip emojis, markdown, and control chars; keep letters + punctuation."""
        clean = re.sub(r"[^\w\s.,?!'\-\u0900-\u097F]", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _resolve_voice(self, text: str, language: str, gender: str, voice_preset: Optional[str] = None) -> str:
        """Resolve the best neural voice ID."""
        if voice_preset and voice_preset in self.VOICE_PRESETS:
            return self.VOICE_PRESETS[voice_preset]

        # Auto-detect Hindi script
        if bool(re.search(r"[\u0900-\u097F]", text)):
            language = "hi"

        lang_key = "hi" if language == "hi" else "en"
        gender_key = "female" if gender == "female" else "male"
        return self.DEFAULT_VOICES.get((lang_key, gender_key), "en-IN-PrabhatNeural")

    async def synthesize_async(
        self,
        text: str,
        language: str = "en",
        gender: str = "male",
        voice: Optional[str] = None
    ) -> bytes:
        """Asynchronously synthesize speech to MP3 bytes using Edge Neural TTS."""
        clean_text = self._clean_text(text)
        if not clean_text:
            return b""

        resolved_voice = self._resolve_voice(clean_text, language, gender, voice)
        cache_key = hashlib.md5(f"{clean_text}:{resolved_voice}".encode("utf-8")).hexdigest()
        if cache_key in _AUDIO_CACHE:
            return _AUDIO_CACHE[cache_key]

        # 1. Edge Neural TTS (Studio Quality)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, resolved_voice)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            audio_bytes = b"".join(chunks)
            if audio_bytes and len(audio_bytes) > 200:
                _AUDIO_CACHE[cache_key] = audio_bytes
                return audio_bytes
        except Exception as e:
            print(f"[VoiceGenerator] Edge TTS error: {e}")

        # 2. OpenAI TTS (if API key available)
        if self.api_key and self.api_key.startswith("sk-"):
            try:
                res = self._try_openai_tts_sync(clean_text, language, gender)
                if res and len(res) > 200:
                    _AUDIO_CACHE[cache_key] = res
                    return res
            except Exception as e:
                print(f"[VoiceGenerator] OpenAI TTS error: {e}")

        # 3. gTTS Fallback
        gtts_bytes = self._gtts_synthesize(clean_text, language)
        if gtts_bytes:
            _AUDIO_CACHE[cache_key] = gtts_bytes
        return gtts_bytes

    def synthesize_to_bytes(
        self,
        text: str,
        language: str = "en",
        gender: str = "male",
        voice: Optional[str] = None
    ) -> bytes:
        """Synchronous wrapper for synthesize_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.synthesize_async(text, language, gender, voice))
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.synthesize_async(text, language, gender, voice))
        except Exception as err:
            print(f"[VoiceGenerator] sync runner error: {err}")
            return self._gtts_synthesize(self._clean_text(text), language)

    def _gtts_synthesize(self, text: str, language: str = "en") -> bytes:
        try:
            from gtts import gTTS
            is_hindi = (language == "hi") or bool(re.search(r"[\u0900-\u097F]", text))
            tts = gTTS(text=text, lang="hi") if is_hindi else gTTS(text=text, lang="en", tld="co.in")
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp.read()
        except Exception as e:
            print(f"[VoiceGenerator] gTTS fallback error: {e}")
            return b""

    def _try_openai_tts_sync(self, text: str, language: str, gender: str) -> Optional[bytes]:
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
