"""Editing Engine: applies a logo overlay to a downloaded reel using FFmpeg.

Supports:
- Static logos (PNG/JPG) and animated logos (MP4/WEBM/GIF), looped to match
  the reel's duration.
- Fixed position presets (corners, center, full overlay).
- Size (% of reel width) and opacity sliders.
- Chroma key removal of a background color from the logo before overlay.

Output is an H.264/AAC mp4 suitable for Instagram Reels.
"""

import json
import shlex
import subprocess
from pathlib import Path

from app.models.automation import Automation, LogoPosition

ANIMATED_LOGO_TYPES = {"mp4", "webm", "gif"}


def probe_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def _position_overlay_expr(position: LogoPosition, margin: int = 20) -> tuple[str, str]:
    """Returns (x, y) FFmpeg overlay filter expressions for a given position."""
    positions = {
        LogoPosition.TOP_LEFT: (str(margin), str(margin)),
        LogoPosition.TOP_CENTER: ("(main_w-overlay_w)/2", str(margin)),
        LogoPosition.TOP_RIGHT: (f"main_w-overlay_w-{margin}", str(margin)),
        LogoPosition.CENTER: ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
        LogoPosition.BOTTOM_LEFT: (str(margin), f"main_h-overlay_h-{margin}"),
        LogoPosition.BOTTOM_CENTER: ("(main_w-overlay_w)/2", f"main_h-overlay_h-{margin}"),
        LogoPosition.BOTTOM_RIGHT: (f"main_w-overlay_w-{margin}", f"main_h-overlay_h-{margin}"),
        LogoPosition.FULL_OVERLAY: ("0", "0"),
    }
    return positions[position]


def build_filter_complex(automation: Automation) -> tuple[str, str]:
    """Builds the FFmpeg filter_complex graph.

    Returns (filter_complex_string, base_video_label) where base_video_label
    is the label of the (possibly passthrough) main video stream that the
    logo gets overlaid onto.
    """
    parts: list[str] = []
    logo_label = "[1:v]"
    base_label = "[0:v]"

    if automation.logo_position == LogoPosition.FULL_OVERLAY:
        # scale2ref scales the logo (first input) to match the main video's
        # (second input) dimensions; "main_w"/"main_h" refer to the
        # reference (second) input's size.
        parts.append("[1:v][0:v]scale2ref=w=main_w:h=main_h[scaled][base]")
        logo_label = "[scaled]"
        base_label = "[base]"
    else:
        parts.append(f"[1:v]scale=iw*{automation.logo_size_percent / 100:.4f}:-1[scaled]")
        logo_label = "[scaled]"

    if automation.chroma_key_color:
        color = automation.chroma_key_color.lstrip("#")
        parts.append(f"{logo_label}colorkey=0x{color}:0.3:0.1[keyed]")
        logo_label = "[keyed]"

    if automation.logo_opacity_percent < 100:
        opacity = max(0.0, min(1.0, automation.logo_opacity_percent / 100))
        parts.append(f"{logo_label}format=rgba,colorchannelmixer=aa={opacity:.2f}[opacity]")
        logo_label = "[opacity]"

    x_expr, y_expr = _position_overlay_expr(automation.logo_position)
    parts.append(f"{base_label}{logo_label}overlay={x_expr}:{y_expr}:shortest=1[outv]")

    return ";".join(parts), "[outv]"


def build_ffmpeg_command(
    automation: Automation,
    input_video: Path,
    logo_path: Path,
    output_video: Path,
    reel_duration: float,
) -> list[str]:
    logo_input_args = []
    if automation.logo_type in ANIMATED_LOGO_TYPES:
        logo_duration = probe_duration(logo_path)
        if logo_duration < reel_duration:
            # -stream_loop -1 loops the logo input indefinitely; combined
            # with shortest=1 + -t, output is trimmed to the reel's length.
            logo_input_args = ["-stream_loop", "-1"]

    filter_complex, out_label = build_filter_complex(automation)

    return [
        "ffmpeg", "-y",
        "-i", str(input_video),
        *logo_input_args,
        "-i", str(logo_path),
        "-filter_complex", filter_complex,
        "-map", out_label,
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-t", str(reel_duration),
        str(output_video),
    ]


def apply_logo_overlay(
    automation: Automation,
    input_video: Path,
    logo_path: Path,
    output_video: Path,
) -> Path:
    """Runs FFmpeg to overlay the automation's logo onto input_video,
    producing output_video. Looping is applied automatically if the logo
    (animated PNG/GIF/MP4/WEBM) is shorter than the reel."""
    reel_duration = probe_duration(input_video)
    cmd = build_ffmpeg_command(automation, input_video, logo_path, output_video, reel_duration)
    subprocess.run(cmd, check=True, capture_output=True)
    return output_video


def ffmpeg_command_string(automation: Automation, input_video: Path, logo_path: Path, output_video: Path) -> str:
    """Returns the FFmpeg command as a shell string (for logging/debugging)."""
    reel_duration = probe_duration(input_video)
    cmd = build_ffmpeg_command(automation, input_video, logo_path, output_video, reel_duration)
    return " ".join(shlex.quote(c) for c in cmd)
