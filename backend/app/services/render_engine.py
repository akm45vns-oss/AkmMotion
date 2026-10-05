import os
import sys
import shutil
import asyncio
import tempfile
import subprocess
import socket
import ipaddress
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.secure_downloader import secure_download_media, is_safe_url, SSRFSecurityError, DownloadError


class RenderEngineService:
    """
    Compiles visual scene images, audio narrations, subtitles, and animation effects
    into a 1080x1920 vertical MP4 video (H.264/AAC) using server-side FFmpeg.
    """

    TRANSITION_MAP = {
        "fade": "fade",
        "slide": "slideleft",
        "wipe": "wipeleft",
        "zoom": "zoomin",
    }

    def __init__(self):
        self._ffmpeg_bin: Optional[str] = None

    @staticmethod
    def _escape_ffmpeg_path(path: str) -> str:
        """
        Safely escape a filesystem path for FFmpeg filtergraph options (e.g. drawtext textfile='...').
        Converts Windows backslashes to forward slashes and escapes colons and quotes.
        """
        p = path.replace("\\", "/")
        p = p.replace("'", r"\'")
        p = p.replace(":", r"\:")
        return p

    @staticmethod
    def _is_safe_download_url(url: str) -> bool:
        """Centralized SSRF Guard check."""
        safe, _ = is_safe_url(url)
        return safe

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
                vid_path = os.path.join(tmp_dir, f"scene_{idx}_vid.mp4")
                audio_path = os.path.join(tmp_dir, f"scene_{idx}_audio.mp3")
                sub_path = os.path.join(tmp_dir, f"scene_{idx}_sub.txt")
                segment_path = os.path.join(tmp_dir, f"seg_{idx:03d}.mp4")

                # 1. Check if scene has a video clip (e.g. from fal.ai) or image
                has_video = False
                if scene.get("video_url"):
                    has_video = await self._prepare_video(scene.get("video_url"), vid_path, scene_num)

                if not has_video:
                    # Fetch or generate image
                    await self._prepare_image(scene.get("image_url"), img_path, scene_num, tmp_dir)

                # 2. Fetch or synthesize audio
                narration = scene.get("narration", "")
                await self._prepare_audio(scene.get("audio_url"), narration, audio_path, scene_duration)

                # 3. Prepare subtitle text with timed ASS format
                subtitle_text = scene.get("subtitle", "") or narration
                has_subtitle = bool(subtitle_text.strip())
                if has_subtitle:
                    sub_path = os.path.join(tmp_dir, f"scene_{idx}_sub.ass")
                    self._create_ass_subtitle_file(
                        sub_path,
                        subtitle_text,
                        scene_duration,
                        word_timings=scene.get("word_timings")
                    )
                else:
                    sub_path = None

                # 4. Render individual scene segment
                camera_motion = scene.get("camera_motion", "push")
                await self._render_scene_segment(
                    img_path=img_path if not has_video else "",
                    video_path=vid_path if has_video else None,
                    audio_path=audio_path,
                    sub_path=sub_path,
                    output_segment=segment_path,
                    duration=scene_duration,
                    camera_motion=camera_motion
                )

                if os.path.isfile(segment_path) and os.path.getsize(segment_path) > 0:
                    segment_files.append(segment_path)
                else:
                    raise RuntimeError(f"Failed to render segment for scene {scene_num}")

            # 5. Concatenate all segments into final MP4 with real transitions (fade, slide, wipe, zoom)
            if progress_callback:
                await progress_callback(92, "Stitching scene segments with transitions into final MP4...")

            scene_transitions = [str(s.get("transition", "fade")).lower() for s in scenes_data]
            scene_durations = [float(s.get("duration", 5.0)) for s in scenes_data]

            if len(segment_files) == 1:
                shutil.copy2(segment_files[0], output_path)
            else:
                has_dynamic_transitions = any(
                    t in ("fade", "slide", "wipe", "zoom")
                    for t in scene_transitions[1:]
                )
                transition_success = False
                if has_dynamic_transitions:
                    try:
                        transition_success = await self._concatenate_with_transitions(
                            segment_files,
                            scene_transitions,
                            scene_durations,
                            output_path,
                            tmp_dir
                        )
                    except Exception as trans_err:
                        print(f"[RenderEngine] Transition render notice: {trans_err}; falling back to concat.")
                        transition_success = False

                if not transition_success:
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
                    await secure_download_media(image_url, dest_path=dest_path, max_bytes=25 * 1024 * 1024)
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

    async def _prepare_video(self, video_url: Optional[str], dest_path: str, scene_num: int) -> bool:
        """Downloads a video clip from URL or copies local video file."""
        if not video_url:
            return False
        if os.path.isfile(video_url):
            try:
                shutil.copy2(video_url, dest_path)
                return True
            except Exception as e:
                print(f"[RenderEngine] Failed to copy local video for scene {scene_num}: {e}")
                return False
        if video_url.startswith("http://") or video_url.startswith("https://"):
            try:
                await secure_download_media(video_url, dest_path=dest_path, max_bytes=100 * 1024 * 1024)
                return True
            except Exception as e:
                print(f"[RenderEngine] Video clip download failed for scene {scene_num}: {e}")
        return False

    async def _prepare_audio(self, audio_url: Optional[str], narration: str, dest_path: str, duration: float):
        """Downloads the audio, synthesizes via VoiceGeneratorService, or creates silence."""
        obtained = False
        if audio_url:
            if os.path.isfile(audio_url):
                shutil.copy2(audio_url, dest_path)
                obtained = True
            elif audio_url.startswith("http://") or audio_url.startswith("https://"):
                try:
                    await secure_download_media(audio_url, dest_path=dest_path, max_bytes=25 * 1024 * 1024)
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
        camera_motion: str = "push",
        video_path: Optional[str] = None
    ):
        """Renders one 9:16 vertical scene segment with Ken Burns motion or video clip and burnt subtitles."""
        fps = 30
        total_frames = max(int(duration * fps), 30)

        # 1. Video clip branch: if a video clip is provided, loop/trim and burn subtitles
        if video_path and os.path.isfile(video_path):
            filter_chain = (
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                f"fps={fps}"
            )
            if sub_path and os.path.isfile(sub_path):
                escaped_sub = self._escape_ffmpeg_path(sub_path)
                if sub_path.endswith(".ass"):
                    sub_filter = f"ass='{escaped_sub}'"
                else:
                    sub_filter = (
                        f"drawtext=textfile='{escaped_sub}':"
                        f"fontsize=48:fontcolor=yellow:borderw=3:bordercolor=black:"
                        f"box=1:boxcolor=black@0.6:boxborderw=10:"
                        f"x=(w-text_w)/2:y=h-th-260"
                    )
                filter_chain += f",{sub_filter}"

            args = [
                "-y",
                "-stream_loop", "-1",
                "-t", f"{duration:.2f}",
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex", filter_chain,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-af", "apad",
                "-t", f"{duration:.2f}",
                "-preset", "veryfast",
                output_segment
            ]

            ret, _, err = await self._run_ffmpeg(args)
            if ret != 0 or not os.path.isfile(output_segment) or os.path.getsize(output_segment) == 0:
                if sub_path:
                    plain_filter = (
                        "scale=1080:1920:force_original_aspect_ratio=increase,"
                        "crop=1080:1920,"
                        f"fps={fps}"
                    )
                    args[args.index(filter_chain)] = plain_filter
                    ret, _, err = await self._run_ffmpeg(args)

                if ret != 0 or not os.path.isfile(output_segment) or os.path.getsize(output_segment) == 0:
                    raise RuntimeError(f"FFmpeg video scene render error: {err}")
            return

        # 2. Image animation branch: build zoompan filter based on camera motion
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


        # Subtitle burning via ASS or drawtext if subtitle exists
        if sub_path and os.path.isfile(sub_path):
            escaped_sub = self._escape_ffmpeg_path(sub_path)
            if sub_path.endswith(".ass"):
                sub_filter = f"ass='{escaped_sub}'"
            else:
                sub_filter = (
                    f"drawtext=textfile='{escaped_sub}':"
                    f"fontsize=48:fontcolor=yellow:borderw=3:bordercolor=black:"
                    f"box=1:boxcolor=black@0.6:boxborderw=10:"
                    f"x=(w-text_w)/2:y=h-th-260"
                )
            filter_chain += f",{sub_filter}"

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
            "-af", "apad",
            "-t", f"{duration:.2f}",
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

    @staticmethod
    def _create_ass_subtitle_file(
        output_file: str,
        text: str,
        duration: float,
        word_timings: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Creates an Advanced SubStation Alpha (ASS) file with exact timed events
        and vertical 9:16 layout (1080x1920).
        """
        from app.services.ai.subtitle_generator import SubtitleGeneratorService

        timings = word_timings or SubtitleGeneratorService.compute_word_timings_from_text(text, duration)

        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,40,40,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            cs = int(round((seconds - int(seconds)) * 100))
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        events = []
        if timings:
            chunk_size = 4
            for i in range(0, len(timings), chunk_size):
                chunk = timings[i:i + chunk_size]
                chunk_start = float(chunk[0].get("start", 0.0))
                chunk_end = float(chunk[-1].get("end", duration))
                chunk_text = " ".join(str(item.get("word", "")) for item in chunk)
                events.append(f"Dialogue: 0,{fmt_time(chunk_start)},{fmt_time(chunk_end)},Default,,0,0,0,,{chunk_text}")
        else:
            events.append(f"Dialogue: 0,0:00:00.20,{fmt_time(duration)},Default,,0,0,0,,{text.strip()}")

        content = header + "\n".join(events) + "\n"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        return output_file

    async def _concatenate_with_transitions(
        self,
        segment_files: List[str],
        transitions: List[str],
        durations: List[float],
        output_path: str,
        tmp_dir: str
    ) -> bool:
        """
        Concatenates video segments with smooth video crossfade transitions (xfade)
        and audio crossfade (acrossfade).
        """
        if len(segment_files) < 2:
            shutil.copy2(segment_files[0], output_path)
            return True

        cmd = ["-y"]
        for seg in segment_files:
            cmd.extend(["-i", seg])

        filter_parts = []
        trans_duration = 0.5
        current_offset = max(durations[0] - trans_duration, 0.1) if durations else 2.5

        last_v = "0:v"
        last_a = "0:a"

        for i in range(1, len(segment_files)):
            t_name = transitions[i] if i < len(transitions) else "fade"
            xfade_type = self.TRANSITION_MAP.get(t_name, "fade")
            out_v = f"v{i}"
            out_a = f"a{i}"

            offset_val = max(current_offset, 0.1)
            filter_parts.append(
                f"[{last_v}][{i}:v]xfade=transition={xfade_type}:duration={trans_duration}:offset={offset_val:.2f}[{out_v}]"
            )
            filter_parts.append(
                f"[{last_a}][{i}:a]acrossfade=d={trans_duration}[{out_a}]"
            )
            last_v = out_v
            last_a = out_a
            if i < len(durations):
                current_offset += max(durations[i] - trans_duration, 0.1)

        filter_graph = ";".join(filter_parts)
        cmd.extend([
            "-filter_complex", filter_graph,
            "-map", f"[{last_v}]",
            "-map", f"[{last_a}]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-preset", "veryfast",
            output_path
        ])

        ret, _, err = await self._run_ffmpeg(cmd, timeout=300.0)
        return ret == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0
