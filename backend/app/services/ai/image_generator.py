import os
import uuid
import hashlib
import urllib.parse
from app.core.config import settings


class ImageGeneratorService:
    """
    Generates 9:16 vertical 1080x1920 AI images for scenes using Replicate (Pro Studio),
    OpenAI DALL-E 3 API, or Pollinations AI engine for 100% prompt-accurate visual rendering 
    and CME character identity locking.
    """

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.replicate_token = settings.REPLICATE_API_TOKEN
        
    async def generate_character_portrait(self, character_description: str, style: str = "Explainer") -> str:
        """Generates a reference face/portrait for a new character using fast Flux."""
        if self.replicate_token:
            try:
                import replicate
                os.environ["REPLICATE_API_TOKEN"] = self.replicate_token
                prompt = f"Portrait photo, face clearly visible, character: {character_description}, {style} style, 8k resolution, highly detailed"
                # Using black-forest-labs/flux-schnell as requested
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "go_fast": True,
                        "megapixels": "1",
                        "num_outputs": 1,
                        "output_format": "jpg",
                        "output_quality": 100,
                        "aspect_ratio": "3:4"
                    }
                )
                if output and isinstance(output, list):
                    return str(output[0])
            except Exception as e:
                print(f"[ImageGenerator] Replicate Portrait generation failed: {e}")
                
        # If Replicate fails or missing, fallback to Pollinations for a random reference
        return self._generate_pollinations_url(character_description, style, aspect_ratio="3:4")

    async def generate_image(self, prompt: str, style: str = "Explainer", reference_image_url: str = None) -> str:
        # 1. Pro Studio: Replicate FaceID (PuLID) for Perfect Consistency
        if self.replicate_token and reference_image_url:
            try:
                import replicate
                os.environ["REPLICATE_API_TOKEN"] = self.replicate_token
                
                # Using a standard PuLID/FaceID model on Replicate
                output = replicate.run(
                    "zsxkib/flux-pulid:8baa7ea13ed8d2c9748ec0f93539fc9f622ad31526685741fbd6d07e5f32a537",
                    input={
                        "prompt": f"{prompt}, 9:16 vertical aspect ratio, highly detailed 8k resolution {style} style visual",
                        "main_face_image": reference_image_url,
                        "num_steps": 20,
                        "guidance": 4.0,
                        "true_cfg": 1.0,
                        "width": 1024,
                        "height": 1792
                    }
                )
                if output:
                    # Depending on model, output might be a list or a direct URL string
                    return str(output[0]) if isinstance(output, list) else str(output)
            except Exception as e:
                print(f"[ImageGenerator] Replicate FaceID failed, falling back: {e}")

        # 2. Try DALL-E 3 if API Key exists
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            try:
                import openai
                client = openai.AsyncOpenAI(api_key=self.openai_api_key)

                response = await client.images.generate(
                    model="dalle-3",
                    prompt=f"{prompt}, 9:16 vertical aspect ratio, highly detailed 8k resolution {style} style visual",
                    size="1024x1792",
                    quality="hd",
                    n=1
                )
                return response.data[0].url
            except Exception as e:
                print(f"[ImageGenerator] DALL-E 3 call notice, switching to Pollinations AI: {e}")

        # 3. Real AI Image Generator via Pollinations AI (100% topic accurate)
        return self._generate_pollinations_url(prompt, style, aspect_ratio="9:16")

    def _generate_pollinations_url(self, prompt: str, style: str, aspect_ratio: str = "9:16") -> str:
        import re
        # Clean prompt: remove markdown and non-ASCII chars to keep diffusion models happy
        clean_prompt = prompt.replace("**", "").replace("*", "").replace("#", "").strip()
        clean_prompt = re.sub(r'[^\x00-\x7F]+', ' ', clean_prompt)
        clean_prompt = re.sub(r'\s+', ' ', clean_prompt).strip()
        
        # Build prompt preserving CME character DNA attributes
        format_text = "vertical 9:16 format" if aspect_ratio == "9:16" else "portrait 3:4 format"
        width = 1080 if aspect_ratio == "9:16" else 768
        height = 1920 if aspect_ratio == "9:16" else 1024

        style_visual = {
            "Cinematic": "cinematic lighting, film grain, anamorphic lens, masterpiece",
            "Story": "cinematic storytelling, golden hour lighting, emotional narrative atmosphere",
            "Vlog": "natural lighting, vibrant colors, lifestyle photography",
            "Anime": "makoto shinkai anime style, vibrant cel shaded, beautiful lighting",
            "Explainer": "clean professional studio lighting, clear composition",
            "Finance": "clean corporate aesthetic, crisp architectural lighting",
        }.get(style, "cinematic lighting, photorealistic 8k")
        
        full_ai_prompt = f"{clean_prompt}, {style_visual}, {format_text}, high quality, no text overlays"
        encoded_prompt = urllib.parse.quote(full_ai_prompt)
        
        # Unique seed derived from prompt hash to prevent image repetition across scenes
        seed = int(hashlib.md5(clean_prompt.encode("utf-8")).hexdigest(), 16) % 999999
        
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={seed}"