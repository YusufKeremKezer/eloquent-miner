import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings


def validate_youtube_url(url: str) -> bool:
    """Validates that the URL is a YouTube URL."""
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"(https?://)?(www\.)?youtu\.be/[\w-]{11}",
        r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}",
        r"(https?://)?(www\.)?youtube\.com/embed/[\w-]{11}",
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def extract_video_id(url: str) -> Optional[str]:
    """Extracts the video ID from a YouTube URL."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_info(url: str) -> dict:
    """Fetches video metadata without downloading."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--js-runtimes", "node,deno,bun",  # <-- FIX: Tell yt-dlp to use Node.js
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch video info: {result.stderr}")
    
    return json.loads(result.stdout)


def download_audio(url: str, output_dir: Path, video_id: str) -> str:
    """Downloads audio from YouTube and converts to MP3."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "source.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", settings.youtube_audio_format,
        "--audio-quality", "0",
        "--js-runtimes", "node,deno,bun",  # <-- FIX: Tell yt-dlp to use Node.js
        "-o", output_template,
        "--no-playlist",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to download audio: {result.stderr}")
    
    # Find the downloaded file
    audio_file = output_dir / f"source.{settings.youtube_audio_format}"
    if audio_file.exists():
        return str(audio_file)
    
    # Fallback: look for any source file
    for ext in ["mp3", "wav", "m4a", "ogg", "flac", "webm", "mp4"]:
        fallback = output_dir / f"source.{ext}"
        if fallback.exists():
            return str(fallback)
    
    raise RuntimeError("Audio file was not created after download.")


def download_subtitles(url: str, output_dir: Path, video_id: str) -> Optional[str]:
    """Downloads subtitles from YouTube. Returns the subtitle file path or None."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "subs")
    
    langs = settings.youtube_subtitle_langs.split(",")
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", ",".join(langs),
        "--sub-format", "srt/vtt/best",
        "--convert-subs", "srt",
        "--js-runtimes", "node,deno,bun",  # <-- FIX: Added here too
        "-o", output_template,
        "--no-playlist",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to download subtitles: {result.stderr}")
    
    # Look for the downloaded subtitle file
    for lang in langs:
        for ext in ["srt", "vtt"]:
            sub_file = output_dir / f"subs.{lang}.{ext}"
            if sub_file.exists():
                return str(sub_file)
    
    # Fallback: look for any subtitle file
    for ext in ["srt", "vtt"]:
        for sub_file in output_dir.glob(f"subs*.{ext}"):
            if sub_file.exists():
                return str(sub_file)
    
    return None


def process_youtube_url(url: str, job_id: str) -> Tuple[str, Optional[str], dict]:
    """
    Downloads audio and subtitles for a YouTube URL.
    Returns: (audio_path, subtitle_path_or_None, video_info)
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    job_media_dir = Path(settings.media_dir) / job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)
    
    video_info = get_video_info(url)
    audio_path = download_audio(url, job_media_dir, video_id)
    subtitle_path = download_subtitles(url, job_media_dir, video_id)
    
    return audio_path, subtitle_path, video_info