import re
import logging
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def sanitize_error(message: Any) -> str:
    """Masks any API keys or tokens in error strings to prevent credential leakage."""
    if not message:
        return ""
    msg_str = str(message)
    # Redact Authorization Key/Bearer patterns
    cleaned = re.sub(r'(Key\s+|Bearer\s+|key=)[a-zA-Z0-9_\-\:]+', r'\1[REDACTED]', msg_str, flags=re.IGNORECASE)
    # Redact configured FAL_KEY if present
    if settings.FAL_KEY and len(settings.FAL_KEY) > 5:
        cleaned = cleaned.replace(settings.FAL_KEY, "[REDACTED]")
    return cleaned


class FalVideoService:
    """
    Client for fal.ai Text-to-Video Queue API.
    All calls run securely on the backend.
    """

    @property
    def model(self) -> str:
        return settings.FAL_VIDEO_MODEL or "fal-ai/kling-video/v1/standard/text-to-video"

    @property
    def enabled(self) -> bool:
        return settings.FAL_VIDEO_ENABLED

    @property
    def api_key(self) -> str:
        key = settings.FAL_KEY or ""
        return key.strip()

    def _get_headers(self) -> Dict[str, str]:
        key = self.api_key
        if not key:
            raise ValueError("fal.ai API key is not configured.")
        return {
            "Authorization": f"Key {key}",
            "Content-Type": "application/json"
        }

    async def submit_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration: str = "5",
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits a text-to-video prompt to the fal.ai queue.
        Returns request_id, status_url, response_url.
        """
        if not self.enabled:
            raise RuntimeError("fal.ai video provider is currently disabled.")
        
        headers = self._get_headers()
        model_id = (model_override or self.model).strip("/")
        queue_url = f"https://queue.fal.run/{model_id}"

        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": str(duration)
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(queue_url, json=payload, headers=headers)
                if res.status_code >= 400:
                    sanitized = sanitize_error(res.text)
                    logger.error(f"[FalVideoService] Queue submission failed ({res.status_code}): {sanitized}")
                    raise RuntimeError(f"fal.ai API error ({res.status_code}): {sanitized}")
                
                data = res.json()
                request_id = data.get("request_id")
                status_url = data.get("status_url") or f"https://queue.fal.run/{model_id}/requests/{request_id}/status"
                response_url = data.get("response_url") or f"https://queue.fal.run/{model_id}/requests/{request_id}"

                return {
                    "request_id": request_id,
                    "status_url": status_url,
                    "response_url": response_url,
                    "provider": "fal.ai",
                    "model": model_id
                }
        except Exception as e:
            msg = sanitize_error(str(e))
            logger.error(f"[FalVideoService] Submission exception: {msg}")
            raise RuntimeError(f"Failed to submit video generation to fal.ai: {msg}")

    async def check_status(self, status_url: str) -> Dict[str, Any]:
        """
        Checks the status of a pending video generation request.
        """
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(status_url, headers=headers)
                if res.status_code >= 400:
                    sanitized = sanitize_error(res.text)
                    logger.error(f"[FalVideoService] Status check failed ({res.status_code}): {sanitized}")
                    raise RuntimeError(f"Status check failed: {sanitized}")
                
                data = res.json()
                raw_status = (data.get("status") or "").upper()
                
                # Normalize status: IN_QUEUE, IN_PROGRESS, COMPLETED, FAILED
                if raw_status in ("IN_QUEUE", "QUEUED"):
                    normalized = "in_queue"
                elif raw_status in ("IN_PROGRESS", "RUNNING", "PROCESSING"):
                    normalized = "in_progress"
                elif raw_status in ("COMPLETED", "OK"):
                    normalized = "completed"
                elif raw_status in ("FAILED", "ERROR"):
                    normalized = "failed"
                else:
                    normalized = "in_progress" if raw_status else "in_queue"

                return {
                    "status": normalized,
                    "raw_status": raw_status,
                    "data": data
                }
        except Exception as e:
            msg = sanitize_error(str(e))
            logger.error(f"[FalVideoService] check_status error: {msg}")
            raise RuntimeError(f"Failed to check fal.ai status: {msg}")

    async def fetch_result(self, response_url: str) -> Dict[str, Any]:
        """
        Retrieves the completed result from response_url and extracts the video URL.
        """
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(response_url, headers=headers)
                if res.status_code >= 400:
                    sanitized = sanitize_error(res.text)
                    logger.error(f"[FalVideoService] Result fetch failed ({res.status_code}): {sanitized}")
                    raise RuntimeError(f"Result fetch failed: {sanitized}")
                
                data = res.json()
                video_url = None

                # Kling / Fal standard structure: {"video": {"url": "https://..."}}
                if isinstance(data.get("video"), dict) and "url" in data["video"]:
                    video_url = data["video"]["url"]
                elif isinstance(data.get("video_url"), str):
                    video_url = data["video_url"]
                elif isinstance(data.get("videos"), list) and len(data["videos"]) > 0:
                    first = data["videos"][0]
                    if isinstance(first, dict) and "url" in first:
                        video_url = first["url"]
                    elif isinstance(first, str):
                        video_url = first
                
                if not video_url:
                    raise RuntimeError("No video URL found in fal.ai result payload.")

                return {
                    "video_url": video_url,
                    "raw_data": data
                }
        except Exception as e:
            msg = sanitize_error(str(e))
            logger.error(f"[FalVideoService] fetch_result error: {msg}")
            raise RuntimeError(f"Failed to retrieve fal.ai result: {msg}")


fal_video_service = FalVideoService()
