import os
import sys
import shutil
import asyncio
import tempfile
import subprocess
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings


class RenderEngineService:
    """
    Compiles visual scene images, audio narrations, subtitles, and animation effects
    into a 1080x1920 vertical MP4 video (H.264/AAC) using server-side FFmpeg.
    """

    def __init__(self):
        self._ffmpeg_bin: Optional[str] = None

    def get_ffmpeg_binary(self) -> str:
        """
        Discovers the FFmpeg binary in priority order:
        1. settings.FFMPEG_PATH (if valid binary)
        2. System PATH (ffmpeg)
        3. imageio-ffmpeg bundled binary
        """
        if self._ffmpeg_bin and os.path.isfile(self._ffmpeg_bin):
            return self._ffmpeg_bin

        # 1. Configured path
        if settings.FFMPEG_PATH:
            which_res = shutil.which(settings.FFMPEG_PATH)
            if which_res:
                self._ffmpeg_bin = which_res
                return self._ffmpeg_bin
            if os.path.isfile(settings.FFMPEG_PATH):
                self._ffmpeg_bin = settings.FFMPEG_PATH
                return self._ffmpeg_bin

        # 2. System PATH
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            self._ffmpeg_bin = system_ffmpeg
            return self._ffmpeg_bin

        # 3. imageio-ffmpeg
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.isfile(exe):
                self._ffmpeg_bin = exe
                return self._ffmpeg_bin
        except Exception:
            pass

        raise RuntimeError(
            "FFmpeg executable not found. Please install FFmpeg on the system or install imageio-ffmpeg."
        )

    async def _run_ffmpeg(self, args: List[str], timeout: float = 180.0) -> tuple[int, str, str]:
        """Runs FFmpeg asynchronously and captures exit code, stdout, and stderr."""
        ffmpeg_bin = self.get_ffmpeg_binary()
        cmd = [ffmpeg_bin, "-hide_banner", "-loglevel", "error"] + args

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode, stdout_data.decode("utf-8", errors="replace"), stderr_data.decode("utf-8", errors="replace")
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            raise TimeoutError(f"FFmpeg command timed out after {timeout}s: {' '.join(cmd[:6])}...")

    async def compile_video(
        self,
        scenes_data: List[Dict[str, Any]],
        output_path: str,
        progress_callback=None
    ) -> str:
        """
        Main video compilation entrypoint.
        Takes scenes_data, compiles 9:16 vertical MP4 video with Ken Burns animation,
        narration audio, and burnt-in subtitles.
        """
        if progress_callback:
            await progress_callback(5, "Initializing FFmpeg render engine...")

        output_path_specified = bool(output_path)
        # Resolve output path if empty
        if not output_path:
            storage_dir = settings.video_storage_dir
            import uuid
            output_path = os.path.join(storage_dir, f"render_{uuid.uuid4().hex[:12]}.mp4")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Handle empty scenes_data gracefully (used in tests and fallback smoke checks)
        if not scenes_data:
            if progress_callback:
                await progress_callback(20, "Generating baseline test video...")
            await self._render_fallback_card(output_path, "AkmMotion Studio", "Preview Video", duration=3.0)
            if progress_callback:
                await progress_callback(100, "Render completed!")
            if not output_path_specified:
                return f"{settings.BACKEND_URL}/api/v1/render/video/{os.path.splitext(os.path.basename(output_path))[0]}"
            return output_path

        total_scenes = len(scenes_data)
        segment_files = []

        with tempfile.TemporaryDirectory(prefix="akm_render_") as tmp_dir:
            if progress_callback:
                await progress_callback(10, f"Preparing assets for {total_scenes} scenes...")

            for idx, scene in enumerate(scenes_data):
                scene_num = idx + 1
                scene_duration = float(scene.get("duration", 5.0))
                if scene_duration <= 0.5:
                    scene_duration = 5.0

                pct_start = 10 + int((idx / total_scenes) * 80)
                if progress_callback:
                    await progress_callback(
                        pct_start,
                        f"Rendering Scene {scene_num}/{total_scenes} ({scene_duration:.1f}s)..."
                    )

                img_path = os.path.join(tmp_dir, f"scene_{idx}_img.jpg")
                audio_path = os.path.join(tmp_dir, f"scene_{idx}_audio.mp3")
                sub_path = os.path.join(tmp_dir, f"scene_{idx}_sub.txt")
                segment_path = os.path.join(tmp_dir, f"seg_{idx:03d}.mp4")

                # 1. Fetch or generate image
                await self._prepare_image(scene.get("image_url"), img_path, scene_num, tmp_dir)

                # 2. Fetch or synthesize audio
                narration = scene.get("narration", "")
                await self._prepare_audio(scene.get("audio_url"), narration, audio_path, scene_duration)

                # 3. Prepare subtitle text
                subtitle_text = scene.get("subtitle", "") or narration
                has_subtitle = bool(subtitle_text.strip())
                if has_subtitle:
                    with open(sub_path, "w", encoding="utf-8") as sf:
                        # Write single line clean subtitle
                        sf.write(subtitle_text.strip())

                # 4. Render individual scene segment
                camera_motion = scene.get("camera_motion", "push")
                await self._render_scene_segment(
                    img_path=img_path,
                    audio_path=audio_path,
                    sub_path=sub_path if has_subtitle else None,
                    output_segment=segment_path,
                    duration=scene_duration,
                    camera_motion=camera_motion
                )

                if os.path.isfile(segment_path) and os.path.getsize(segment_path) > 0:
                    segment_files.append(segment_path)
                else:
                    raise RuntimeError(f"Failed to render segment for scene {scene_num}")

            # 5. Concatenate all segments into final MP4
            if progress_callback:
                await progress_callback(92, "Stitching scene segments into final MP4...")

            if len(segment_files) == 1:
                shutil.copy2(segment_files[0], output_path)
            else:
                concat_list = os.path.join(tmp_dir, "concat.txt")
                with open(concat_list, "w", encoding="utf-8") as f:
                    for seg in segment_files:
                        escaped_seg = seg.replace("\\", "/")
                        f.write(f"file '{escaped_seg}'\n")

                ret, _, err = await self._run_ffmpeg([
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list,
                    "-c", "copy",
                    output_path
                ])

                if ret != 0 or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                    # Fallback re-encode concat if stream copy fails
                    ret, _, err = await self._run_ffmpeg([
                        "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", concat_list,
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-pix_fmt", "yuv420p",
                        output_path
                    ])
                    if ret != 0 or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                        raise RuntimeError(f"FFmpeg concat failed: {err}")

            # 6. Validate final output
            if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError("Rendered video file is missing or 0 bytes.")

            if progress_callback:
                await progress_callback(100, "Video rendering successfully completed!")

            if not output_path_specified:
                return f"{settings.BACKEND_URL}/api/v1/render/video/{os.path.splitext(os.path.basename(output_path))[0]}"
            return output_path

    async def _prepare_image(self, image_url: Optional[str], dest_path: str, scene_num: int, tmp_dir: str):
        """Downloads the image from URL, or creates a sleek fallback graphic card."""
        downloaded = False
        if image_url:
            # If local file exists
            if os.path.isfile(image_url):
                shutil.copy2(image_url, dest_path)
                downloaded = True
            elif image_url.startswith("http://") or image_url.startswith("https://"):
                try:
                    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                        resp = await client.get(image_url)
                        if resp.status_code == 200 and len(resp.content) > 100:
                            with open(dest_path, "wb") as f:
                                f.write(resp.content)
                            downloaded = True
                except Exception as e:
                    print(f"[RenderEngine] Image download failed for scene {scene_num}: {e}")

        if not downloaded:
            # Generate a 1080x1920 solid gradient/dark card
            await self._run_ffmpeg([
                "-y",
                "-f", "lavfi",
                "-i", "color=c=0x090D16:s=1080x1920:d=1",
                "-vframes", "1",
                dest_path
            ])

    async def _prepare_audio(self, audio_url: Optional[str], narration: str, dest_path: str, duration: float):
        """Downloads the audio, synthesizes via VoiceGeneratorService, or creates silence."""
        obtained = False
        if audio_url:
            if os.path.isfile(audio_url):
                shutil.copy2(audio_url, dest_path)
                obtained = True
            elif audio_url.startswith("http://") or audio_url.startswith("https://"):
                try:
                    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                        resp = await client.get(audio_url)
                        if resp.status_code == 200 and len(resp.content) > 100:
                            with open(dest_path, "wb") as f:
                                f.write(resp.content)
                            obtained = True
                except Exception as e:
                    print(f"[RenderEngine] Audio download failed: {e}")

        if not obtained and narration.strip():
            try:
                from app.services.ai.voice_generator import VoiceGeneratorService
                voice_svc = VoiceGeneratorService()
                audio_bytes = await voice_svc.synthesize_async(narration)
                if audio_bytes and len(audio_bytes) > 200:
                    with open(dest_path, "wb") as f:
                        f.write(audio_bytes)
                    obtained = True
            except Exception as e:
                print(f"[RenderEngine] Narration synthesis notice: {e}")

        if not obtained:
            # Generate silent stereo audio of exact duration
            await self._run_ffmpeg([
                "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                dest_path
            ])

    async def _render_scene_segment(
        self,
        img_path: str,
        audio_path: str,
        sub_path: Optional[str],
        output_segment: str,
        duration: float,
        camera_motion: str = "push"
    ):
        """Renders one 9:16 vertical scene segment with Ken Burns motion and burnt subtitles."""
        fps = 30
        total_frames = max(int(duration * fps), 30)

        # Build zoompan filter based on camera motion
        # Target resolution 1080x1920
        # First scale to at least 1080x1920 maintaining aspect ratio, then crop/zoom
        if camera_motion in ["push", "zoom_in"]:
            zoom_expr = "min(zoom+0.0012,1.18)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif camera_motion == "zoom_out":
            zoom_expr = "max(1.18-0.0012*on,1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif camera_motion == "pan_left":
            # Pan left-to-right: x runs 0 → (iw - iw/zoom) over total_frames.
            # NOTE: FFmpeg's zoompan does NOT expose the 'd' variable in x/y expressions
            # (only in 'z'), so we bake total_frames as a literal integer constant.
            zoom_expr = "1.15"
            x_expr = f"on/{total_frames}*(iw-iw/zoom)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif camera_motion == "pan_right":
            # Pan right-to-left: x runs (iw - iw/zoom) → 0 over total_frames.
            zoom_expr = "1.15"
            x_expr = f"(1-on/{total_frames})*(iw-iw/zoom)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            # Smooth subtle pulse
            zoom_expr = "min(zoom+0.0008,1.12)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        filter_chain = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='{zoom_expr}':d={total_frames}:x='{x_expr}':y='{y_expr}':s=1080x1920:fps={fps}"
        )


        # Subtitle burning via drawtext if subtitle exists
        if sub_path and os.path.isfile(sub_path):
            escaped_sub = sub_path.replace("\\", "/").replace(":", "\\:")
            # Draw subtitle box near bottom center (y=1920-280)
            drawtext_filter = (
                f"drawtext=textfile='{escaped_sub}':"
                f"fontsize=48:fontcolor=yellow:borderw=3:bordercolor=black:"
                f"box=1:boxcolor=black@0.6:boxborderw=10:"
                f"x=(w-text_w)/2:y=h-th-260"
            )
            filter_chain += f",{drawtext_filter}"

        args = [
            "-y",
            "-loop", "1",
            "-t", f"{duration:.2f}",
            "-i", img_path,
            "-i", audio_path,
            "-filter_complex", filter_chain,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-shortest",
            "-preset", "veryfast",
            output_segment
        ]

        ret, _, err = await self._run_ffmpeg(args)
        if ret != 0 or not os.path.isfile(output_segment) or os.path.getsize(output_segment) == 0:
            # If drawtext failed (e.g. font issue), retry without drawtext
            if sub_path:
                plain_filter = (
                    f"scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,"
                    f"zoompan=z='{zoom_expr}':d={total_frames}:x='{x_expr}':y='{y_expr}':s=1080x1920:fps={fps}"
                )
                args[args.index(filter_chain)] = plain_filter
                ret, _, err = await self._run_ffmpeg(args)

            if ret != 0 or not os.path.isfile(output_segment) or os.path.getsize(output_segment) == 0:
                raise RuntimeError(f"FFmpeg scene render error: {err}")

    async def _render_fallback_card(self, output_path: str, title: str, subtitle: str, duration: float = 3.0):
        """Generates a minimal valid 1080x1920 MP4 for testing and smoke validation."""
        args = [
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0D1322:s=1080x1920:d={duration:.2f}",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "128k",
            "-preset", "ultrafast",
            output_path
        ]
        ret, _, err = await self._run_ffmpeg(args)
        if ret != 0 or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"FFmpeg fallback card render failed: {err}")
